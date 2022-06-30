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
    round2,
    collectAtKey,
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


# Format: nb_streams, duration, bit_rate, format_name, format_long_name

# def getStats(stats):
#     return


if pargs.dry:
    runCmd = print

def getStats():
    pass

def mainLoop(file):
    outFile = file.with_name(f"{pargs.cVideo}_{pargs.qVideo}_{pargs.speed}_{file.name}")

    getSlctMetaP = lambda f, cdc: getSlctMeta(ffprobePath, f, meta, cdc)
    videoMetaIn = getSlctMetaP(file, "video")

    ov = optsVideo(
        videoMetaIn["height"], videoMetaIn["r_frame_rate"], pargs.res, pargs.fps
    )
    ca = selectCodec(pargs.cAudio, pargs.qAudio)
    cv = selectCodec(pargs.cVideo, pargs.qVideo, pargs.speed)
    cmd = getffmpegCmd(ffmpegPath, file, outFile, ca, cv, ov)

    cmdOut, timeTaken = trackTime(lambda: runCmd(cmd))

    videoMetaOut = getSlctMetaP(outFile, "video")
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
    sumLengths, meanlengths = sum(lenghts), fmean(lenghts)
    bitsInMean, bitsOutMean = fmean(bitsIn), fmean(bitsOut)

    printStats = (
        "\n"
        f"Processed {len(fileList)} file(s): {readableTime(sumLengths)}/{readableSize(inSum)}"
        f" in: {readableTime(sumTimes)}/{readableSize(outSum)}"
        f" at speed: x{round2(sumLengths/sumTimes)}."
        "\n"
        f"Total size reduced by: {(readableSize(inSum-outSum))} "
        f"to {(readableSize(outSum))} at an average of:"
        f" {round2(((inMean-outMean)/inMean)*100)}% size reduction."
        "\n"
        f"Average processing time: {readableTime(meanTimes)} "
        f"& average speed: x{round2(meanlengths/meanTimes)}."
        "\n"
        f"Average input size: {(readableSize(inMean))}"
        f" & average output size: {(readableSize(outMean))}."
        "\n"
        f"Average input bitrate: {(readableSize(bitsInMean))}"
        f" & average output bitrate: {(readableSize(bitsOutMean))}."
    )

    print(printStats)

    # logFile.write_text()
    # readableKeys(videoMetaIn)


main()

# Processed 2 file(s): 0:00:19/585.32 KB in: 0:00:12/289.66 KB at speed: x1.52.
# Total size reduced by: 295.66 KB to 289.66 KB at an average of: 50.51% size reduction.
# Average processing time: 0:00:06 & average speed: x1.52.
# Average input size: 292.66 KB & average output size: 144.83 KB.
# Average input bitrate: 96.09 KB & average output bitrate: 52.62 KB.
