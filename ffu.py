from argparse import ArgumentParser

from checkMedia import cliArgs as cliCm
from checkMedia import main as cm
from optimizeAV import cliArgs as cliOav
from optimizeAV import main as oav
from takeSamples import cliArgs as cliTs
from takeSamples import main as ts

parser = ArgumentParser(prog="ffUtils")
# parser.add_argument('-v', action='store_true', help='Print version Info & exit')

subparsers = parser.add_subparsers(dest="cmd", help="Various ffmpeg Utilities", required=True)

parserOav = subparsers.add_parser(
    "optimizeAV",
    aliases=["o"],
    help="Optimize Video/Audio files by encoding to avc/hevc/aac/opus.",
)

parserOav = cliOav(parserOav)

parserCm = subparsers.add_parser(
    "checkMedia",
    aliases=["c"],
    help=(
        "Calculate Sum/Mean/Mode statistics for Video/Audio "
        "file metadata(bitrate, duration etc) using ffprobe."
    ),
)

parserCm = cliCm(parserCm)

parserTs = subparsers.add_parser(
    "takeSamples",
    aliases=["s"],
    help=(
        "Trim specific number of samples from Video content "
        "for specified lengths and concatenate them into a single file."
    ),
)

parserTs = cliTs(parserTs)

pargs = parser.parse_args()

if pargs.cmd == "optimizeAV":
    oav(pargs)
elif pargs.cmd == "checkMedia":
    cm(pargs)
elif pargs.cmd == "takeSamples":
    ts(pargs)
