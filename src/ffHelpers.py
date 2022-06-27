from json import loads

from .helpers import runCmd


def getMetaData(ffprobePath, file):
    ffprobeCmd = getffprobeCmd(ffprobePath, file)
    cmdOut = runCmd(ffprobeCmd)
    if isinstance(cmdOut, Exception):
        return cmdOut
    metaData = loads(cmdOut)
    return metaData


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


def getFormatKeys(meta, keys):
    fmt = meta["format"]
    return [fmt[k] for k in keys]


def getFormatData(meta):
    fmt = meta["format"]
    return (float(fmt["duration"]), float(fmt["bit_rate"]), float(fmt["nb_streams"]))
