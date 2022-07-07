from fractions import Fraction
from json import loads

from .helpers import extractKeysDict, readableSize, readableTime, runCmd

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

getffmpegCmd = lambda ffmpegPath, file, outFile, ca=[], cv=[], ov=[]: [
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


def findStream(meta, sType):
    nbStreams = int(meta["format"]["nb_streams"])
    strms = meta["streams"]
    for strm in range(nbStreams):
        cType = strms[strm].get("codec_type")
        if cType == sType:
            return strm
    return None


def getFormatData(meta):
    return meta["format"]


def getStreamData(meta, strm):
    return meta["streams"][strm] if strm is not None else None


def getMeta(ffprobePath, file, cdcType=None, fmt=True):
    metaData = getMetaData(ffprobePath, file)
    fmtData = getFormatData(metaData)
    if cdcType is None:
        return fmtData
    elif isinstance(cdcType, str):
        strm = findStream(metaData, cdcType)
        strmData = getStreamData(metaData, strm)
        return (fmtData, strmData) if fmt else strmData
    elif isinstance(cdcType, (list, tuple)):
        strmData = [
            getStreamData(metaData, findStream(metaData, cdc)) for cdc in cdcType
        ]
        return (fmtData, *strmData) if fmt else strmData


def getFormatKeys(meta, keys, asDict=False):
    fmt = meta["format"]
    return extractKeysDict(fmt, keys, asDict)


def getStreamKeys(meta, strm, keys, asDict=False):
    strm = meta["streams"][strm]
    return extractKeysDict(strm, keys, asDict)


def getTagKeys(meta, keys, asDict=False):
    tags = meta["format"]["tags"]
    return extractKeysDict(tags, keys, asDict)


# def getStreamData(metaData, strm, meta):
#     if strm is None:
#         return None
#     else:
#         return getStreamKeys(metaData, strm, meta, asDict=True)


# def getFormatData(metaData):
#     getFormatKeys(
#         metaData, ("format_name", "nb_streams", "duration", "bit_rate"), asDict=True
#     )


# def getSlctMeta(ffprobePath, file, meta=None, cdcType=None, fmt=True):
#     metaData = getMetaData(ffprobePath, file)
#     fmtData = getFormatData(metaData)
#     if cdcType is None:
#         return fmtData
#     elif isinstance(cdcType, str):
#         strm = findStream(metaData, cdcType)
#         strmData = getStreamData(metaData, strm, meta)
#         if fmt:
#             return (fmtData, strmData)
#         else:
#             return strmData
#     elif isinstance(cdcType, (list, tuple)):
#         strmData = [
#             getStreamData(metaData, findStream(metaData, cdc), meta) for cdc in cdcType
#         ]
#         if fmt:
#             return (
#                 fmtData,
#                 *strmData,
#             )
#         else:
#             return strmData


def readableKeys(meta):
    retr = {}
    bitR = meta.get("bit_rate")
    if bitR:
        retr = {**meta, "bit_rate": readableSize(float(bitR))}
    dur = meta.get("duration")
    if dur:
        retr = {**retr, "duration": readableTime(float(dur))}
    return retr


def selectFormat(codec):
    if codec in ("aac", "he"):
        return ".m4a"
    elif codec in ("opus"):
        return ".opus"
    elif codec in ("hevc", "avc", "av1"):
        return ".mp4"
    else:
        return (".m4a", ".opus", ".mp4")


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
        ]

    return cdc


def optsVideo(srcRes, srcFps, limitRes, limitFps):

    opts = [
        "-pix_fmt",
        "yuv420p",
        "-vsync",
        "vfr",
    ]  # -g fps*10

    if limitFps:
        if float(Fraction(srcFps)) > limitFps:
            opts = [*opts, "-r", str(limitFps)]

    if limitRes:
        if int(srcRes) > limitRes:
            opts = [*opts, "-vf", f"scale=-2:{str(limitRes)}"]

    return opts


def floatDiff(src, out, n=1):
    try:
        diff = abs(float(src) - float(out))
    except ValueError:
        return None
    return diff if diff > n else False

# def compDur():
#     pass


# if diff:
#     msg = f"\n\nINFO: Mismatched {strmType} source and output duration."
# msg = (
#     f"\n********\nWARNING: Differnce between {strmType} source and output "
#     f"durations({str(round2(diff))} seconds) is more than {str(n)} second(s).\n"
# )
# printNLog(msg)


# streams=False "-show_streams" if streams else *[]
