from argparse import ArgumentParser
from statistics import fmean

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
    checkPaths,
    emap,
    exitIfEmpty,
    getFileList,
    runCmd,
    trackTime,
    readableTime,
    readableSize,
    readableDict,
    round2,
)

# Note: WIP


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
        help="Limit video resolution; can be 480, 540, 720, etc. (default: 720)",
    )
    parser.add_argument(
        "-fr",
        "--fps",
        default=30,
        type=int,
        help="Limit video frame rate; can be 24, 25, 30, 60, etc. (default: 30)",
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


def getStats(stats):
    times = [float(x["timeTaken"]) for x in stats]
    inSizes = [float(x["input"]["size"]) for x in stats]
    # times = collectAtKey(stats, ["timeTaken"])
    # inSizes = collectAtKey(stats, ["input", "size"])
    outSizes = [float(x["output"]["size"]) for x in stats]
    lenghts = [float(x["input"]["meta"]["duration"]) for x in stats]
    bitsIn = [float(x["input"]["meta"]["bit_rate"]) for x in stats]
    bitsOut = [float(x["output"]["meta"]["bit_rate"]) for x in stats]
    inSum, inMean = sum(inSizes), fmean(inSizes)
    outSum, outMean = sum(outSizes), fmean(outSizes)
    sumTimes, meanTimes = sum(times), fmean(times)
    sumLengths, meanLengths = sum(lenghts), fmean(lenghts)
    bitsInMean, bitsOutMean = fmean(bitsIn), fmean(bitsOut)

    return (
        "\n"
        f"Size averages:: Reduction: {round2(((inMean-outMean)/inMean)*100)}%"
        f", Input: {(readableSize(inMean))}"
        f", Output: {(readableSize(outMean))}."
        "\n"
        f"Size totals:: Reduction: {(readableSize(inSum-outSum))}"
        f", Input: {readableSize(inSum)}"
        f", Output: {readableSize(outSum)}."
        "\n"
        f"Processing averages:: Speed: x{round2(meanLengths/meanTimes)}"
        f", Time: {readableTime(meanTimes)}"
        f", Length: {readableTime(meanLengths)}."
        "\n"
        f"Processing totals:: Files: {len(stats)}"
        f", Time: {readableTime(sumTimes)}"
        f", Length: {readableTime(sumLengths)}."
        "\n"
        f"Video bitrate averages:: Reduction: {round2(((bitsInMean-bitsOutMean)/bitsInMean)*100)}%"
        f", Input: {(readableSize(bitsInMean))}"
        f", Output: {(readableSize(bitsOutMean))}."
    )


def mainLoop(file):

    getSlctMetaP = lambda f, cdc: getSlctMeta(ffprobePath, f, meta, cdc)
    videoMetaIn = getSlctMetaP(file, "video")

    ov = optsVideo(
        videoMetaIn["height"], videoMetaIn["r_frame_rate"], pargs.res, pargs.fps
    )
    ca = selectCodec(pargs.cAudio, pargs.qAudio)

    outFile = file.with_name(f"{pargs.cVideo}_{cv[5]}_{cv[3]}_{file.name}")

    cv = selectCodec(pargs.cVideo, pargs.qVideo, pargs.speed)

    cmd = getffmpegCmd(ffmpegPath, file, outFile, ca, cv, ov)

    cmdOut, timeTaken = trackTime(lambda: runCmd(cmd))

    videoMetaOut = getSlctMetaP(outFile, "video")

    # print(f"\nVideo Input:: {readableDict(readableKeys(videoMetaIn))}")
    # print(f"\nVideo Output:: {readableDict(readableKeys(videoMetaOut))}")

    return {
        "cmd": cmd,
        "timeTaken": timeTaken,
        "input": {
            "file": str(file),
            "size": file.stat().st_size,
            "meta": videoMetaIn,
        },
        "output": {
            "file": str(outFile),
            "size": outFile.stat().st_size,
            "meta": videoMetaOut,
        },
    }


def main():
    dirPath = pargs.dir.resolve()
    fileList = getFileList(dirPath, pargs.extensions)

    exitIfEmpty(fileList)
    if pargs.only:
        fileList = fileList[: pargs.only]

    logFile = dirPath / f"{dirPath.name}.log"

    stats = emap(mainLoop, fileList)

    print(getStats(stats))

    # logFile.write_text()
    #


main()

# Size averages:: Reduction: 52.95%, Input: 292.66 KB, Output: 137.71 KB.
# Size totals:: Reduction: 309.91 KB, Input: 585.32 KB, Output: 275.41 KB.
# Processing averages:: Speed: x2.16, Time: 0:00:04, Length: 0:00:09.
# Processing totals:: Files: 2, Time: 0:00:08, Length: 0:00:19.
# Bitrate averages:: Reduction: 51.35%, Input: 96.09 KB, Output: 46.74 KB.

# Processed 2 file(s) at average speed: x2.17 with 52.95% average size reduction.
# Processed 0:00:19 in 0:00:08 at average processing time: 0:00:04.
# Size Reduction from: 585.32 KB to: 275.41 KB by: 309.91 KB.
# Size averages:: input: 292.66 KB, output: 137.71 KB
# Bitrate averages:: input: 96.09 KB, output: 46.74 KB.
