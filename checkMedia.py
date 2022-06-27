from argparse import ArgumentParser
from statistics import fmean, mode

from src.ffHelpers import getFormatData, getMetaData
from src.helpers import (
    checkPath,
    collectAtElement,
    convertSize,
    getFileList,
    round2,
    secsToHMS,
    exitIfEmpty,
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

cmdOut = [getMetaData(ffprobePath, f) for f in fileList]

formatData = [getFormatData(o) for o in cmdOut]

durations = collectAtElement(formatData, 0)

bitRates = collectAtElement(formatData, 1)

sumDur = round2(sum(durations))

meanDur = round2(fmean(durations))

sumBitR = round2(sum(bitRates))

meanBitR = round2(fmean(bitRates))

modeStreams = mode(collectAtElement(formatData, 2))


print(
    f"\nContainer format summary for {len(formatData)} files:\n"
    f"Sum Duration: {secsToHMS(sumDur)}\n"
    f"Mean Duration: {secsToHMS(meanDur)}\n"
    f"Sum Bit Rate: {convertSize(sumBitR)}\n"
    f"Mean Bit Rate: {convertSize(meanBitR)}\n"
    f"Mode Number of Streams: {int(modeStreams)}"
)


# Format: nb_streams, duration, bit_rate, format_name, format_long_name
# Audio: codec_name, codec_type, sample_rate, channels
# Video: codec_name, codec_type, height, r_frame_rate, pix_fmt
# sum: duration
# median: duration, bit_rate,
# mode: codec_name