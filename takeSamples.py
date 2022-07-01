from argparse import ArgumentParser

from src.cliHelpers import addCliDir, addCliDry, addCliRec,     addCliExt
from src.ffHelpers import ffmpegConcatCmd, ffmpegTrimCmd, getFormatKeys, getMetaData
from src.helpers import (
    checkPaths,
    emap,
    exitIfEmpty,
    getFileList,
    range1,
    removeFiles,
    runCmd,
    strSum,
)


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
    parser = addCliExt(parser, (".mp4", ".mov"))
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
    parser.add_argument(
        "-o",
        "--only",
        default=None,
        type=int,
        help="Only process N files.",
    )
    return parser.parse_args()


pargs = parseArgs()

ffprobePath, ffmpegPath = checkPaths(
    {
        "ffprobe": r"D:\PortableApps\bin\ffprobe.exe",
        "ffmpeg": r"D:\PortableApps\bin\ffmpeg.exe",
    }
)

if pargs.dry:
    runCmd = print


def calcSplits(secs, splits, length):
    s = float(secs) / splits
    return [(s * i - length * i) for i in range1(splits)]


def makeSplits(ffmpegPath, file, splits, length):
    outFiles = []
    nameSum = strSum(file.name)
    for i, s in enumerate(splits, start=1):
        outFile = file.with_stem(f"tmp_{nameSum}_{i}")
        runCmd(ffmpegTrimCmd(ffmpegPath, file, outFile, s, length))
        outFiles = [*outFiles, outFile]
    concat = "\n".join([f"file '{f}'" for f in outFiles])
    splitsFile = file.with_suffix(".splits")
    if not pargs.dry:
        splitsFile.write_text(concat)
    else:
        print(concat)
    return (splitsFile, outFiles)


def concatSplits(ffmpegPath, splitsFile, tmpFiles, outFile):
    runCmd(ffmpegConcatCmd(ffmpegPath, splitsFile, outFile))
    if not pargs.dry:
        removeFiles([splitsFile, *tmpFiles])


def go(file, pargs, ffmpegPath, ffprobePath):
    outFile = file.with_name(f"trm_{file.name}")  # outfiles?
    metaData = getMetaData(ffprobePath, file)
    duration = getFormatKeys(metaData, "duration")
    splits = calcSplits(duration, pargs.samples, pargs.length)
    splitsFile, tmpFiles = makeSplits(ffmpegPath, file, splits, pargs.length)
    concatSplits(ffmpegPath, splitsFile, tmpFiles, outFile)


def main():
    fileList = getFileList(pargs.dir.resolve(), pargs.extensions, pargs.recursive)

    exitIfEmpty(fileList)

    if pargs.only:
        fileList = fileList[: pargs.only]

    goP = lambda f: go(f, pargs, ffmpegPath, ffprobePath)

    emap(goP, fileList)


main()


# different algos for splits
# follow symlinks?
