from argparse import ArgumentParser
from statistics import fmean, mode

from src.ffHelpers import getFormatKeys, getMetaData
from src.helpers import (
    checkPath,
    collectAtIndex,
    getFileList,
    round2,
    readableSize,
    readableTime,
    exitIfEmpty,
    emap,
)
from src.cliHelpers import sepExts, addCliDir, addCliRec


def parseArgs():

    parser = ArgumentParser(
        description=(
            "Calculate Sum/Mean/Mode statistics for Video/Audio "
            "file metadata(bitrate, duration etc) using ffprobe."
        )
    )
    parser = addCliDir(parser)
    parser = addCliRec(parser)
    parser.add_argument(
        "-e",
        "--extensions",
        default=(".mp4", ".mov"),
        help="Comma separated file extensions. (default: .mp4, .mov)",
        type=sepExts,
    )

    return parser.parse_args()


ffprobePath = checkPath("ffprobe", r"D:\PortableApps\bin\ffprobe.exe")


pargs = parseArgs()

fileList = getFileList(pargs.dir.resolve(), pargs.extensions, pargs.recursive)

exitIfEmpty(fileList)

metaData = [getMetaData(ffprobePath, f) for f in fileList]

keys = ("duration", "bit_rate", "nb_streams")

formatData = [emap(float, getFormatKeys(m, keys)) for m in metaData]

durations = collectAtIndex(formatData, 0)

bitRates = collectAtIndex(formatData, 1)

streams = collectAtIndex(formatData, 2)

sumDur = round2(sum(durations))

meanDur = round2(fmean(durations))

sumBitR = round2(sum(bitRates))

meanBitR = round2(fmean(bitRates))

modeStreams = mode(streams)


print(
    f"\nContainer format summary for {len(formatData)} files:\n"
    f"Sum Duration: {readableTime(sumDur)}\n"
    f"Mean Duration: {readableTime(meanDur)}\n"
    f"Sum Bit Rate: {readableSize(sumBitR)}\n"
    f"Mean Bit Rate: {readableSize(meanBitR)}\n"
    f"Mode Number of Streams: {int(modeStreams)}"
)

