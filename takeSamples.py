from argparse import ArgumentParser

from src.cliHelpers import addCliDir, addCliRec, addCliDry, sepExts
from src.ffHelpers import (
    ffmpegConcatCmd,
    ffmpegTrimCmd,
    getFormatKeys,
    getMetaData,
)
from src.helpers import checkPaths, emap, runCmd, exitIfEmpty, getFileList, range1, removeFiles, strSum

# Note: WIP


def parseArgs():

    parser = ArgumentParser(
        description=(
            "Trim specific number of samples from Video content "
            "for specified lengths and concatenate them into a single file."
        )
    )
    parser = addCliDir(parser)
    parser = addCliRec(parser)
    parser = addCliDry(parser)
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
        "-s",
        "--samples",
        default=5,
        type=int,
        help="Number of samples samples.",
    )

    return parser.parse_args()


pargs = parseArgs()

ffprobePath, ffmpegPath = checkPaths(
    {
        "ffprobe": r"D:\PortableApps\bin\ffprobe.exe",
        "ffmpeg": r"D:\PortableApps\bin\ffmpeg.exe",
    }
)

runCmd = print  # test


def makeSplits(file, splits, length):
    outFiles = []
    nameSum = strSum(file.name)
    for i, s in enumerate(splits, start=1):
        outFile = file.with_stem(f"tmp_{nameSum}_{i}")
        runCmd(ffmpegTrimCmd(ffmpegPath, file, outFile, s, length))
        outFiles = [*outFiles, outFile]

    concat = "\n".join([f"file '{f}'\n" for f in outFiles])
    splitsFile = file.with_suffix(".splits")
    if not pargs.dry:
        splitsFile.write_text(concat)
    return (splitsFile, outFiles)


def concatSplits(splitsFile, outFile):
    runCmd(ffmpegConcatCmd(ffmpegPath, splitsFile, outFile))


def calcSplits(secs, splits, length):
    s = float(secs) / splits
    return [(s * i - length) for i in range1(splits)]


def doStuff(file):

    outFile = file.with_name(f"trm_{file.name}") # outfiles?
    metaData = getMetaData(ffprobePath, file)
    duration = getFormatKeys(metaData, "duration")
    splits = calcSplits(duration, pargs.samples, pargs.length)
    splitsFile = makeSplits(file, splits, pargs.length)
    concatSplits(splitsFile[0], outFile)
    if not pargs.dry:
        removeFiles([splitsFile[0], *splitsFile[1]])

    print(duration, splits, splitsFile)

def main():

    fileList = getFileList(pargs.dir.resolve(), pargs.extensions, pargs.recursive)

    exitIfEmpty(fileList)

    emap(doStuff, fileList)

main()


# different algos for splits
# find 20 40 60 80 % of the video / divide dur by N splits
# follow symlinks?
