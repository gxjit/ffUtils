from argparse import ArgumentParser
from statistics import fmean
from functools import reduce

from src.cliHelpers import (
    addCliDir,
    addCliDry,
    addCliExt,
    addCliOnly,
    addCliRec,
    checkValIn,
)
from src.ffHelpers import (
    getffmpegCmd,
    getSlctMeta,
    optsVideo,
    readableKeys,
    selectCodec,
)
from src.helpers import (
    appendFile,
    checkPaths,
    emap,
    exitIfEmpty,
    getFileList,
    readableDict,
    readableSize,
    readableTime,
    round2,
    runCmd,
    trackTime,
)


def parseArgs():

    aCodec = lambda v: checkValIn(v, ["opus", "he", "aac", "ac"], str)
    vCodec = lambda v: checkValIn(v, ["avc", "hevc", "av1", "vn", "vc"], str)

    parser = ArgumentParser(description="FFmpeg Video/Audio Encoder testing.")
    parser = addCliDir(parser)
    parser = addCliRec(parser)
    parser = addCliDry(parser)
    parser = addCliOnly(parser)
    parser = addCliExt(parser, (".mp4", ".mov"))
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
    return parser.parse_args()


pargs = parseArgs()

ffprobePath, ffmpegPath = checkPaths(
    {
        "ffprobe": r"D:\PortableApps\bin\ffprobe.exe",
        "ffmpeg": r"D:\PortableApps\bin\ffmpeg.exe",
    }
)


def meta(cType=None):
    basic = ["codec_type", "codec_name", "profile", "duration", "bit_rate"]
    if cType == "audio":
        return [*basic, "channels", "sample_rate"]
    elif cType == "video":
        return [*basic, "height", "r_frame_rate", "pix_fmt"]
    else:
        return basic


if pargs.dry:
    runCmd = print

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
        f'\nVideo Input:: {readableDict(readableKeys(results[-1]["input"]["meta"]["video"]))}'
        f'\nVideo Output:: {readableDict(readableKeys(results[-1]["output"]["meta"]["video"]))}'
        "\n\n"
        f"Size averages:: Reduction: {round2(((inMean-outMean)/inMean)*100)}%"
        f", Input: {(readableSize(inMean))}"
        f" & Output: {(readableSize(outMean))}."
        "\n"
        f"Size totals:: Reduction: {(readableSize(inSum-outSum))}"
        f", Input: {readableSize(inSum)}"
        f" & Output: {readableSize(outSum)}."
        "\n"
        f"Processing averages:: Speed: x{round2(meanLengths/meanTimes)}"
        f", Time: {readableTime(meanTimes)}"
        f" & Length: {readableTime(meanLengths)}."
        "\n"
        f"Processing totals:: Files: {len(results)}"
        f", Time: {readableTime(sumTimes)}"
        f" & Length: {readableTime(sumLengths)}."
        "\n"
        f"Video bitrate averages:: Reduction: {round2(((VidBitsInMean-VidBitsOutMean)/VidBitsInMean)*100)}%"
        f", Input: {(readableSize(VidBitsInMean))}"
        f" & Output: {(readableSize(VidBitsOutMean))}."
    )


def mainLoop(acc, file, dirPath, pargs, ffmpegPath, ffprobePath):
    getSlctMetaP = lambda f, cdc: getSlctMeta(ffprobePath, f, meta, cdc)
    videoMetaIn = getSlctMetaP(file, "video")

    ov = optsVideo(
        videoMetaIn["height"], videoMetaIn["r_frame_rate"], pargs.res, pargs.fps
    )
    ca = selectCodec(pargs.cAudio, pargs.qAudio)
    cv = selectCodec(pargs.cVideo, pargs.qVideo, pargs.speed)
    fmtName = f"{(cv[1]).replace('lib', '')}_{cv[5]}_{cv[3]}"
    outFile = file.with_name(f"{fmtName}_{file.name}")
    logFile = dirPath / f"{fmtName}_{dirPath.name}.log"

    cmd = getffmpegCmd(ffmpegPath, file, outFile, ca, cv, ov)

    cmdOut, timeTaken = trackTime(lambda: runCmd(cmd))

    videoMetaOut = getSlctMetaP(outFile, "video")

    results = [
        *acc,
        {
            "cmd": cmd,
            "timeTaken": timeTaken,
            "input": {
                "file": file,
                "size": file.stat().st_size,
                "meta": {"video": videoMetaIn},
            },
            "output": {
                "file": outFile,
                "size": outFile.stat().st_size,
                "meta": {"video": videoMetaOut},
            },
        },
    ]

    stats = getStats(results)
    print(stats)
    appendFile(logFile, stats)

    return results


def main():
    dirPath = pargs.dir.resolve()
    fileList = getFileList(dirPath, pargs.extensions)

    exitIfEmpty(fileList)
    if pargs.only:
        fileList = fileList[: pargs.only]

    mainLoopP = lambda acc, f: mainLoop(acc, f, dirPath, pargs, ffmpegPath, ffprobePath)
    results = reduce(mainLoopP, fileList, [])


main()
