from argparse import ArgumentParser

from src.ffHelpers import getMetaData, getFormatKeys
from src.helpers import checkPath, getFileList, exitIfEmpty
from src.cliHelpers import sepExts, addCliDir, addCliRec

# Note: WIP

def parseArgs():

    parser = ArgumentParser(
        description=(
            "Trim samples from Video/Audio content"
            "for specific N start times and N1 lengths."
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
        default=40,
        type=int,
        help="Length/Duration to be used for taking samples.",
    )

    return parser.parse_args()


def makeSplits(durs, length):
    pass


ffprobePath = checkPath("ffprobe", r"D:\PortableApps\bin\ffprobe.exe")

pargs = parseArgs()

fileList = getFileList(pargs.dir.resolve(), pargs.extensions, pargs.recursive)

exitIfEmpty(fileList)

cmdOut = [getMetaData(ffprobePath, f) for f in fileList]

durations = [getFormatKeys(meta, ["duration"]) for meta in cmdOut]

print(durations)

# get dur with ffprobe
# find 20 40 60 80 % of the video / divide dur by N splits
# trim at that
# follow symlinks?

# outPreFix = "trm"; st = "600"; tt = "90";
#     ffmpeg -i @(f) -map_metadata -1 -ss @(st) \
#     -c:v copy -c:a copy -avoid_negative_ts 1 -t @(tt) @(f"{outPreFix}_{f}")

# -avoid_negative_ts 1
# ffmpeg -i input.mp4 -ss 00:02:00 -t 00:07:28 part1.mp4
# ffmpeg -i input.mp4 -ss 00:10:50 -t 00:51:30 part2.mp4
# ffmpeg -i input.mp4 -ss 01:19:00 -t 00:08:05 part3.mp4
# inputs.txt
# file 'part1.mp4'
# file 'part2.mp4'
# file 'part3.mp4'
# ffmpeg -f concat -i inputs.txt -c copy output.mp4

# Input seeking
# The -ss parameter needs to be specified somewhere before -i:
# ffmpeg -ss 00:23:00 -i Mononoke.Hime.mkv -frames:v 1 out1.jpg
# Output seeking

# The -ss parameter needs to be specified after -i:
# ffmpeg -i Mononoke.Hime.mkv -ss 00:23:00 -frames:v 1 out2.jpg
#  To extract only a small segment in the middle of a movie, it can be used in combination with -t which specifies the duration, like -ss 60 -t 10 to capture from second 60 to 70. Or you can use the -to option to specify an out point, like -ss 60 -to 70 to capture from second 60 to 70. -t and -to are mutually exclusive. If you use both, -t will be used.
#  Note that if you specify -ss before -i only, the timestamps will be reset to zero, so -t and -to will have the same effect. If you want to keep the original timestamps, add the -copyts option.
#  The first command will cut from 00:01:00 to 00:03:00 (in the original), using the faster seek.
# The second command will cut from 00:01:00 to 00:02:00, as intended, using the slower seek.
# The third command will cut from 00:01:00 to 00:02:00, as intended, using the faster seek.

# ffmpeg -ss 00:01:00 -i video.mp4 -to 00:02:00 -c copy cut.mp4
# ffmpeg -i video.mp4 -ss 00:01:00 -to 00:02:00 -c copy cut.mp4
# ffmpeg -ss 00:01:00 -i video.mp4 -to 00:02:00 -c copy -copyts cut.mp4
# If you cut with stream copy (-c copy) you need to use the -avoid_negative_ts 1 option if you want to use that segment with the concat demuxer .
# ffmpeg -ss 00:03:00 -i video.mp4 -t 60 -c copy -avoid_negative_ts 1 cut.mp4

# this is a comment
# file '/path/to/file1.wav'
# file '/path/to/file2.wav'
# file '/path/to/file3.wav'
# ffmpeg -f concat -safe 0 -i mylist.txt -c copy output.wav
# The -safe 0 above is not required if the paths are relative.
