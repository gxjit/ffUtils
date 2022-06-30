from json import loads
from collections.abc import Iterable
from fractions import Fraction

from .helpers import runCmd, readableSize, readableTime


getffprobeCmd = lambda ffprobePath, file: [
    ffprobePath,
    "-v",
    "quiet",
    "-print_format",
    "json",
    "-show_format",
    "-show_streams",
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

getffmpegCmd = lambda ffmpegPath, file, outFile, ca, cv, ov=[]: [
    ffmpegPath,
    "-i",
    str(file),
    *cv,
    *ov,
    *ca,
    "-loglevel",
    "warning",  # or info
    str(outFile),
]

ffmpegConcatCmd = lambda ffmpegPath, splitsFile, outFile: [
    ffmpegPath,
    "-f",
    "concat",
    "-safe",
    "0",
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


def extractKeysDict(dic, keys, asDict=False):
    if isinstance(keys, str):
        return dic.get(keys, "N/A")
    elif isinstance(keys, Iterable):
        if asDict:
            return {k: dic.get(k, "N/A") for k in keys}
        else:
            return [dic.get(k, "N/A") for k in keys]


def getFormatKeys(meta, keys, asDict=False):
    fmt = meta["format"]
    return extractKeysDict(fmt, keys, asDict)


def getStreamKeys(meta, strm, keys, asDict=False):
    strm = meta["streams"][strm]
    return extractKeysDict(strm, keys, asDict)


def getTagKeys(meta, keys, asDict=False):
    tags = meta["format"]["tags"]
    return extractKeysDict(tags, keys, asDict)


def findStream(meta, sType):
    nbStreams = int(meta["format"]["nb_streams"])
    for strm in range(nbStreams):
        cType = getStreamKeys(meta, strm, "codec_type")
        if cType == sType:
            return strm

def getSlctMeta(ffprobePath, file, slctMeta, cdcType):
    metaData = getMetaData(ffprobePath, file)
    return getStreamKeys(
        metaData, findStream(metaData, cdcType), slctMeta(cdcType), asDict=True
    )

def readableKeys(meta):
    bitR = meta.get("bit_rate")
    if bitR:
        meta["bit_rate"] = readableSize(float(bitR))
    dur = meta.get("duration")
    if dur:
        meta["duration"] = readableTime(float(dur))
    return meta


def selectCodec(codec, quality=None, speed=None):

    if quality:
        quality = str(quality)

    if codec == "ac":
        cdc = ["-c:a", "copy"]

    elif codec == "vc":
        cdc = ["-c:v", "copy"]

    elif codec == "vn":
        cdc = ["-vn"]

    elif codec == "aac":
        cdc = [
            "-c:a",
            "libfdk_aac",
            "-b:a",
            f'{quality or "72"}k',
            "-afterburner",
            "1",
            "-cutoff",
            "15500",
            "-ar",
            "32000",
        ]
        # fdk_aac defaults to a LPF cutoff around 14k
        # https://wiki.hydrogenaud.io/index.php?title=Fraunhofer_FDK_AAC#Bandwidth

    elif codec == "he":
        cdc = [
            "-c:a",
            "libfdk_aac",
            "-profile:a",
            "aac_he",
            "-b:a",
            f'{quality or "56"}k',
            "-afterburner",
            "1",
        ]
        # mono he-aac encodes are reported as stereo by ffmpeg/ffprobe
        # https://trac.ffmpeg.org/ticket/3361

    elif codec == "opus":
        cdc = [
            "-c:a",
            "libopus",
            "-b:a",
            f'{quality or "48"}k',
            "-vbr",
            "on",
            "-compression_level",
            "10",
            "-frame_duration",
            "20",
        ]

    elif codec == "avc":
        cdc = [
            "-c:v",
            "libx264",
            "-preset:v",
            speed or "slow",
            "-crf",
            quality or "28",
            "-profile:v",
            "high",
        ]

    elif codec == "hevc":
        cdc = [
            "-c:v",
            "libx265",
            "-preset:v",
            speed or "medium",
            "-crf",
            quality or "32",
        ]

    elif codec == "av1":
        cdc = [
            "-c:v",
            "libsvtav1",
            "-crf",
            quality or "52",
            "-preset:v",
            speed or "8",
            "-g",
            "240",
        ]  # -g fps*10

    return cdc


def optsVideo(srcRes, srcFps, limitRes, limitFps):

    opts = [
        "-pix_fmt",
        "yuv420p",
        "-vsync",
        "vfr",
    ]

    if float(Fraction(srcFps)) > limitFps:
        opts = [*opts, "-r", str(limitFps)]

    if int(srcRes) > limitRes:
        opts = [*opts, "-vf", f"scale=-2:{str(limitRes)}"]

    return opts

# streams=False "-show_streams" if streams else *[]
