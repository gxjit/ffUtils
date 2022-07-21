from argparse import ArgumentParser
from statistics import fmean, mode

from src.cliHelpers import addCliDir, addCliRec, addCliExt
from src.ffHelpers import getFormatKeys, getMetaData
from src.helpers import collectAtIndex, emap, readableSize, readableTime, round2
from src.osHelpers import checkPath, exitIfEmpty, getFileList


def cliArgs(parser):
    parser = addCliDir(parser)
    parser = addCliRec(parser)
    parser = addCliExt(parser, (".mp4", ".mov"))

    return parser


def main(pargs):
    ffprobePath = checkPath("ffprobe", r"D:\PortableApps\bin\ffprobe.exe")

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


if __name__ == "__main__":
    parser = ArgumentParser(
        description=(
            "Calculate Sum/Mean/Mode statistics for Video/Audio "
            "file metadata(bitrate, duration etc) using ffprobe."
        )
    )
    main(cliArgs(parser).parse_args())
