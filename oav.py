from argparse import ArgumentParser
from atexit import register as atexit
from functools import reduce
from statistics import fmean
from sys import version_info

from src.cliHelpers import (
    addCliDir,
    addCliDry,
    addCliExt,
    addCliOnly,
    addCliRec,
    addCliWait,
    checkValIn,
)
from src.ffHelpers import (
    floatDiff,
    getffmpegCmd,
    getMeta,
    optsVideo,
    readableKeys,
    selectCodec,
    selectFormat,
    ffCmdOpts,
)
from src.helpers import (
    appendFile,
    checkPaths,
    cleanUp,
    exitIfEmpty,
    getFileList,
    makeTargetDir,
    readableDict,
    readableSize,
    readableTime,
    round2,
    runCmd,
    strSum,
    trackTime,
)

# Note: WIP


def parseArgs():

    aCodec = lambda v: checkValIn(v, ["opus", "he", "aac", "ac"], str)
    vCodec = lambda v: checkValIn(v, ["avc", "hevc", "av1", "vn", "vc"], str)
    inExts = (
        *(".mp4", ".mov", ".mkv", ".webm", ".avi", ".wmv"),
        *(".flac", ".wav", ".m4a", ".mp3"),
    )

    parser = ArgumentParser(
        description="Optimize Video/Audio files by encoding to avc/hevc/aac/opus."
    )
    parser = addCliDir(parser)
    parser = addCliRec(parser)
    parser = addCliDry(parser)
    parser = addCliOnly(parser)
    parser = addCliExt(parser, inExts)
    parser = addCliWait(parser)
    parser.add_argument(
        "-rs",
        "--res",
        default=720,
        type=int,
        help=(
            "Limit video resolution; can be 480, 540, 720, etc."
            " (default: 720, disable: 0)"
        ),
    )
    parser.add_argument(
        "-fr",
        "--fps",
        default=30,
        type=int,
        help=(
            "Limit video frame rate; can be 24, 25, 30, 60, etc."
            " (default: 30, disable: 0)"
        ),
    )
    parser.add_argument(
        "-s",
        "--speed",
        default=None,
        type=str,
        help="Video encoding speed; avc & hevc: slow, medium and fast etc; "
        "av1: 0-13/6-8 (lower is slower and efficient). "
        "(defaults:: avc: slow, hevc: medium and av1: 8)",
    )
    parser.add_argument(
        "-ca",
        "--cAudio",
        default="he",
        type=aCodec,
        help='Select an audio codec from AAC-LC: "aac", HE-AAC/AAC-LC with SBR: "he" '
        ', Opus: "opus" and copy: "ac". (default: he)',
    )
    parser.add_argument(
        "-cv",
        "--cVideo",
        default="hevc",
        type=vCodec,
        help='Select a video codec from HEVC/H265: "hevc", AVC/H264: "avc" , '
        'AV1: "av1", copy: "vc" and no video: "vn". (default: hevc)',
    )
    parser.add_argument(
        "-qv",
        "--qVideo",
        default=None,
        type=int,
        help="Video Quality(CRF) setting; avc:23:17-28, hevc:28:20-32 and av1:50:0-63, "
        "lower crf means less compression. (defaults:: avc: 28, hevc: 32 and av1: 52)",
    )
    parser.add_argument(
        "-qa",
        "--qAudio",
        default=None,
        type=int,
        help="Audio Quality/bitrate in kbps; (defaults:: opus: 48, he: 56 and aac: 72)",
    )
    parser.add_argument(
        "-fm",
        "--format",
        action="store_true",
        help="Use metadata from container format for duration comparison.",
    )
    # parser.add_argument(
    #     "-fa",
    #     "--fAudio",
    #     default="m4a",
    #     type=aCodec,
    #     help="Audio container format; can be m4a, opus, etc. (default: m4a)",
    # )
    # parser.add_argument(
    #     "-fv",
    #     "--fVideo",
    #     default="mp4",
    #     type=aCodec,
    #     help="Video container format; can be mp4, mkv, etc. (default: mp4)",
    # )

    return parser.parse_args()


def meta(cType=None):
    basic = ["codec_type", "codec_name", "profile", "duration", "bit_rate"]
    if cType == "audio":
        return [*basic, "channels", "sample_rate"]
    elif cType == "video":
        return [*basic, "height", "r_frame_rate", "pix_fmt"]
    else:
        return basic


# Format: nb_streams, duration, bit_rate, format_name, format_long_name


def getStats(results):
    times = [float(x["timeTaken"]) for x in results]
    inSizes = [float(x["input"]["size"]) for x in results]
    # times = collectAtKey(results, ["timeTaken"])
    # inSizes = collectAtKey(results, ["input", "size"])
    outSizes = [float(x["output"]["size"]) for x in results]
    lenghts = [float(x["input"]["meta"]["video"]["duration"]) for x in results]
    VidBitsIn = [float(x["input"]["meta"]["video"]["bit_rate"]) for x in results]
    VidBitsOut = [float(x["output"]["meta"]["video"]["bit_rate"]) for x in results]

    inSum, inMean = sum(inSizes), fmean(inSizes)
    outSum, outMean = sum(outSizes), fmean(outSizes)
    sumTimes, meanTimes = sum(times), fmean(times)
    sumLengths, meanLengths = sum(lenghts), fmean(lenghts)
    VidBitsInMean, VidBitsOutMean = fmean(VidBitsIn), fmean(VidBitsOut)

    return (
        f"\n"
        f'\nProcessed file: {results[-1]["input"]["file"].name}'
        f'\nVideo Input:: {readableDict(readableKeys(results[-1]["input"]["meta"]["video"]))}'  # noqa
        f'\nVideo Output:: {readableDict(readableKeys(results[-1]["output"]["meta"]["video"]))}'  # noqa
        "\n\n"
        f"Size averages:: Reduction: {round2(((inMean-outMean)/inMean)*100)}%"
        f", Input: {(readableSize(inMean))}"
        f" & Output: {(readableSize(outMean))}."
        "\n"
        f"Size totals:: Reduction: {(readableSize(inSum-outSum))}"
        f", Input: {readableSize(inSum)}"
        f" & Output: {readableSize(outSum)}."
        "\n"
        f"Processing averages:: Speed: x{round2(max(meanLengths, meanTimes)/min(meanLengths, meanTimes))}"
        f" {'slower' if meanTimes > meanLengths else 'faster'}"
        f", Time: {readableTime(meanTimes)}"
        f" & Length: {readableTime(meanLengths)}."
        "\n"
        f"Processing totals:: Files: {len(results)}"
        f", Time: {readableTime(sumTimes)}"
        f" & Length: {readableTime(sumLengths)}."
        "\n"
        f"Video bitrate averages:: Reduction: {round2(((VidBitsInMean-VidBitsOutMean)/VidBitsInMean)*100)}%"  # noqa
        f", Input: {(readableSize(VidBitsInMean))}"
        f" & Output: {(readableSize(VidBitsOutMean))}."
    )


def mainLoop(acc, files, addFiles, pargs, ffPaths):
    file, outFile = files
    tmpFile, logFile = addFiles
    ffprobePath, ffmpegPath = ffPaths

    getMetaP = lambda f, cdc: getMeta(ffprobePath, f, cdc)
    fmtIn, videoMetaIn, audioMetaIn = getMetaP(file, ("video", "audio"))

    ffCmdOpts(
        (pargs.cVideo, pargs.qVideo, pargs.speed, pargs.res, pargs.fps),
        (pargs.cAudio, pargs.qAudio),
        audioMetaIn,
        videoMetaIn,
    )

    if videoMetaIn:
        ov = optsVideo(
            videoMetaIn["height"], videoMetaIn["r_frame_rate"], pargs.res, pargs.fps
        )
        cv = selectCodec(pargs.cVideo, pargs.qVideo, pargs.speed)
        outExt = selectFormat(pargs.cVideo)
    else:
        ov, cv = [], []
        outExt = selectFormat(pargs.cAudio)

    ca = selectCodec(pargs.cAudio, pargs.qAudio) if audioMetaIn else []

    tmpFile = tmpFile.with_suffix(outExt)
    outFile = outFile.with_suffix(outExt)
    cmd = getffmpegCmd(ffmpegPath, file, tmpFile, ca, cv, ov)

    cmdOut, timeTaken = trackTime(runCmd, cmd)

    if pargs.recursive and not outFile.parent.exists():
        outFile.parent.mkdir(parents=True)
    tmpFile.rename(outFile)

    fmtOut, videoMetaOut, audioMetaOut = getMetaP(outFile, ("video", "audio"))

    vdoDur = videoMetaIn and videoMetaIn.get("duration")
    adoDur = audioMetaIn and audioMetaIn.get("duration")
    if vdoDur:
        vDiff = (floatDiff(vdoDur, videoMetaOut["duration"]), "video")
    elif adoDur:
        vDiff = (floatDiff(adoDur, audioMetaOut["duration"]), "audio")
    else:
        vDiff = (floatDiff(fmtIn["duration"], fmtOut["duration"]), "format")
    if vDiff:
        diff, src = vDiff
        print(
            f"\n********\n"
            f"WARNING: Differnce between {src} source and output "
            f"durations is {str(round2(diff))} second(s)."
            f"\n********\n"
        )

    results = [
        *acc,
        {
            "cmd": cmd,
            "timeTaken": timeTaken,
            "input": {
                "file": file,
                "size": file.stat().st_size,
                "meta": {"video": videoMetaIn, "audio": audioMetaIn},
            },
            "output": {
                "file": outFile,
                "size": outFile.stat().st_size,
                "meta": {"video": videoMetaOut, "audio": audioMetaOut},
            },
        },
    ]

    stats = getStats(results)
    print(stats)
    appendFile(logFile, stats)

    # if pargs.wait:
    #     waitN(int(pargs.wait))
    # else:
    #     waitN(int(dynWait(timeTaken)))

    return results


def main():
    pargs = parseArgs()

    ffPaths = checkPaths(
        {
            "ffprobe": r"D:\PortableApps\bin\ffprobe.exe",
            "ffmpeg": r"D:\PortableApps\bin\ffmpeg.exe",
        }
    )

    dirPath = pargs.dir.resolve()
    fileList = getFileList(dirPath, pargs.extensions, pargs.recursive)
    exitIfEmpty(fileList)

    outDir = makeTargetDir(dirPath / f"out_{dirPath.name}")
    tmpFile = outDir / f"tmp_{strSum(dirPath.name)}.tmp"
    logFile = outDir / f"log_{dirPath.name}.log"
    outFileList = getFileList(outDir, selectFormat(), pargs.recursive)
    if pargs.recursive:
        if version_info >= (3, 9):
            fileList = [
                f
                for f in fileList
                if not f.is_relative_to(outDir) or f not in outFileList
            ]
        else:
            fileList = [f for f in fileList if not (str(outDir) in str(f))]

    outFiles = [outDir / f.relative_to(dirPath).with_suffix(outExt) for f in fileList]
    files = tuple(zip(fileList, outFiles))

    if pargs.only:
        fileList = fileList[: pargs.only]

    atexit(cleanUp, (outDir, tmpFile))

    mainLoopP = lambda acc, f: mainLoop(acc, f, (tmpFile, logFile), pargs, ffPaths)
    results = reduce(mainLoopP, fileList, [])


main()


# setLogFile(outDir.joinpath(f"{dirPath.name}.log"))
# filesLeft = len(fileList) - (idx + 1)
# "\n"
# f"Output estimates:: Time left: "
# f"{readableTime(fmean(totalTime) * filesLeft)}, size: {readableSize(outMean * len(fileList))}"
