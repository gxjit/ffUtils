from json import loads
from collections.abc import Iterable

from .helpers import runCmd


getffprobeCmd = lambda ffprobePath, file: [
    ffprobePath,
    "-v",
    "quiet",
    "-print_format",
    "json",
    "-show_format",
    # "-show_streams",
    str(file),
]

ffmpegTrimCmd = lambda ffmpegPath, file, outFile, start, length: [
    ffmpegPath,
    "-i",
    str(file),
    "-map_metadata",
    "-1",
    "-ss",
    str(int(start)),
    # "-c:v",
    # "copy",
    # "-c:a",
    # "copy",
    "-c",
    "copy",
    "-avoid_negative_ts",
    "1",
    "-t",
    str(int(length)),
    "-loglevel",
    "warning",  # or info
    str(outFile),
]

ffmpegConcatCmd = lambda ffmpegPath, splitsFile, outFile: [
    ffmpegPath,
    "-f",
    "concat",
    "-i",
    str(splitsFile),
    "-c",
    "copy",
    str(outFile),
]


def getMetaData(ffprobePath, file):
    ffprobeCmd = getffprobeCmd(ffprobePath, file)
    cmdOut = runCmd(ffprobeCmd)
    if isinstance(cmdOut, Exception):
        return cmdOut
    metaData = loads(cmdOut)
    return metaData


def getFormatKeys(meta, keys):
    fmt = meta["format"]
    if isinstance(keys, str):
        return fmt[keys]
    elif isinstance(keys, Iterable):
        return [fmt[k] for k in keys]
