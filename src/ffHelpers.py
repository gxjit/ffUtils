from fractions import Fraction

from .helpers import (
    dictToNspace,
    dictToNTuple,
    extractKeysDict,
    readableSize,
    readableTime,
    round2,
)
from .osHelpers import runCmdJson


def audioCfg(codec, quality=None, speed=None):
    return dictToNspace(locals())


def videoCfg(codec, quality=None, speed=None, res=None, fps=None):
    return dictToNspace(locals())


def fmtMeta(metaData):
    m = metaData["format"].get
    data = {
        "file": m("filename"),
        "size": m("size"),
        "format": m("format_name"),
        "streams": m("nb_streams"),
        "duration": m("duration"),
        "bits": m("bit_rate"),
    }
    return dictToNTuple("FormatMeta", data)


def streamMeta(metaData, strm):
    m = metaData["streams"][strm].get
    data = {
        "type": m("codec_type"),
        "codec": m("codec_name"),
        "profile": m("profile"),
        "duration": m("duration"),
        "bits": m("bit_rate"),
    }
    if data["type"] == "audio":
        data = {**data, "channels": m("channels"), "samples": m("sample_rate")}
    elif data["type"] == "video":
        data = {
            **data,
            "height": m("height"),
            "fps": m("r_frame_rate"),
            "pixFmt": m("pix_fmt"),
        }  # "color_range" "color_primaries"

    return dictToNTuple("StreamMeta", data)


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
    "-c",
    "copy",
    "-avoid_negative_ts",
    "1",
    "-t",
    str(int(length)),
    "-loglevel",
    "24",  # warning: 24 / info: 32 / error: 16
    "-nostdin",
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
    "-loglevel",
    "24",
    "-nostdin",
    str(outFile),
]

getffmpegCmd = lambda ffmpegPath, file, outFile, opts=[]: [
    ffmpegPath,
    "-i",
    str(file),
    *opts,
    "-loglevel",
    "24",
    "-nostdin",
    str(outFile),
]


def getMetaData(ffprobePath, file):
    ffprobeCmd = getffprobeCmd(ffprobePath, file)
    return runCmdJson(ffprobeCmd)


def findStream(meta, sType):
    nbStreams = int(meta["format"]["nb_streams"])
    strms = meta["streams"]
    for strm in range(nbStreams):
        cType = strms[strm].get("codec_type")
        if cType == sType:
            return strm
    return None


def getMeta(ffprobePath, file, cdcType=None, fmt=True):
    metaData = getMetaData(ffprobePath, file)
    fmtData = fmtMeta(metaData)
    if cdcType is None:
        return fmtData
    elif isinstance(cdcType, str):
        strm = findStream(metaData, cdcType)
        strmData = streamMeta(metaData, strm)
        return (fmtData, strmData) if fmt else strmData
    elif isinstance(cdcType, (list, tuple)):
        strmData = [streamMeta(metaData, findStream(metaData, cdc)) for cdc in cdcType]
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


def readableMeta(meta):
    if isinstance(meta, tuple) and hasattr(meta, "_asdict"):
        data = meta._asdict()
    elif isinstance(meta, dict):
        data = {**meta}  # Don't mutate source

    bitR = data.get("bits")
    if bitR:
        data["bits"] = readableSize(float(bitR))

    dur = data.get("duration")
    if dur:
        data["duration"] = readableTime(float(dur))

    fps = data.get("fps")
    if fps:
        data["fps"] = round2(float(Fraction(fps)))

    return data


def selectCodec(codec, quality=None, speed=None):

    # if quality:
    #     quality = str(quality)
    quality = quality and str(quality)

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
            "32000",  # sample rate limit?
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
            "-g",  # -g fps*10
            "240",
        ]

    return cdc


def selectFormat(codec=None):
    if codec is None:
        return (".m4a", ".opus", ".mp4")
    elif codec in ("aac", "he"):
        return ".m4a"
    elif codec in ("opus"):
        return ".opus"
    elif codec in ("hevc", "avc", "av1"):
        return ".mp4"


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


def ffCmdOpts(audio=None, video=None, audioMeta=None, videoMeta=None):
    if videoMeta:
        ov = optsVideo(videoMeta.height, videoMeta.fps, video.res, video.fps)
        cv = selectCodec(video.codec, video.quality, video.speed)
        outExt = selectFormat(video.codec)
    else:
        ov, cv = [], []
        outExt = selectFormat(audio.codec)

    ca = selectCodec(audio.codec, audio.quality) if audioMeta else []

    return ([*ca, *cv, *ov], outExt)


def absFloatDiff(src, out, n=1):
    try:
        diff = abs(float(src) - float(out))
    except ValueError:
        return None
    return diff if diff > n else False


def negFloatDiff(src, out):
    try:
        if float(out) > float(src):
            return float(out) - float(src)
        else:
            return False
    except ValueError:
        return None


def compMeta(
    diffFunc,
    diffParam,
    fmtIn,
    fmtOut,
    audioMetaIn=None,
    audioMetaOut=None,
    videoMetaIn=None,
    videoMetaOut=None,
):

    diff = diffFunc(getattr(fmtIn, diffParam), getattr(fmtOut, diffParam))

    diffs = [(diff, "format")] if diff else []

    adoDur = audioMetaIn and getattr(audioMetaIn, diffParam)
    vdoDur = videoMetaIn and getattr(videoMetaIn, diffParam)

    if adoDur:
        diff = diffFunc(adoDur, getattr(audioMetaOut, diffParam))
        if diff:
            diffs = [*diffs, (diff, "audio")]

    if vdoDur:
        diff = diffFunc(vdoDur, getattr(videoMetaOut, diffParam))
        if diff:
            diffs = [*diffs, (diff, "audio")]

    if any(diffs):
        return diffs
    else:
        return False


def compDur(
    fmtIn,
    fmtOut,
    audioMetaIn=None,
    audioMetaOut=None,
    videoMetaIn=None,
    videoMetaOut=None,
):
    compMeta(absFloatDiff, "duration", **locals())


def compBits(
    fmtIn,
    fmtOut,
    audioMetaIn=None,
    audioMetaOut=None,
    videoMetaIn=None,
    videoMetaOut=None,
):
    compMeta(negFloatDiff, "bits", **locals())


# streams=False "-show_streams" if streams else *[]
