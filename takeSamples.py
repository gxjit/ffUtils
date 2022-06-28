from argparse import ArgumentParser

from src.cliHelpers import addCliDir, addCliRec, sepExts
from src.ffHelpers import (
    ffmpegConcatCmd,
    ffmpegTrimCmd,
    getFormatKeys,
    getMetaData,
    runCmd,
)
from src.helpers import checkPath, emap, exitIfEmpty, getFileList, range1

# Note: WIP


def parseArgs():

    parser = ArgumentParser(
        description=(
            "Trim specific number of samples from Video/Audio content "
            "for specified lengths and concatenate them into a single file."
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
    parser.add_argument(
        "-l",
        "--length",
        default=30,
        type=int,
        help="Length/Duration to be used for taking samples.",
    )
    parser.add_argument(
        "-n",
        "--samples",
        default=5,
        type=int,
        help="Number of samples samples.",
    )

    return parser.parse_args()


pargs = parseArgs()

ffprobePath = checkPath("ffprobe", r"D:\PortableApps\bin\ffprobe.exe")
ffmpegPath = checkPath("ffmpeg", r"D:\PortableApps\bin\ffmpeg.exe")

runCmd = print  # test


def makeSplits(file, splits, length):
    outFiles = []
    for i, s in enumerate(splits, start=1):
        outFile = file.with_stem(f"tmp{i}")

        runCmd(ffmpegTrimCmd(ffmpegPath, file, outFile, s, length))
        outFiles = [*outFiles, outFile]

    concat = "\n".join([f"file '{f}'\n" for f in outFiles])
    splitsFile = file.with_suffix(".splits")
    # splitsFile.write_text(concat)
    return (splitsFile, outFiles)


def concatSplits(splitsFile, outFile):
    runCmd(ffmpegConcatCmd(ffmpegPath, splitsFile, outFile))


def calcDurs(secs, splits, length):
    s = float(secs) / splits
    return [(s * i - length) for i in range1(splits)]


def doStuff(file):

    # metaData = [getMetaData(ffprobePath, f) for f in fileList]
    outFile = outFile = file.with_name(f"trm_{file.name}")
    metaData = getMetaData(ffprobePath, file)
    duration = getFormatKeys(metaData, "duration")
    splits = calcDurs(duration, pargs.samples, pargs.length)
    splitsFile = makeSplits(file, splits, pargs.length)
    concatSplits(splitsFile[0], outFile)
    # remove temp files

    print(duration, splits, splitsFile)
    exit()


fileList = getFileList(pargs.dir.resolve(), pargs.extensions, pargs.recursive)

exitIfEmpty(fileList)

emap(doStuff, fileList)

# different algos for splits
# find 20 40 60 80 % of the video / divide dur by N splits
# follow symlinks?
