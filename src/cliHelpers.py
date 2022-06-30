from pathlib import Path
from argparse import ArgumentTypeError

from .helpers import efilter


def checkDirPath(pth):
    pthObj = Path(pth)
    if pthObj.is_dir():
        return pthObj
    else:
        raise ArgumentTypeError("Invalid Directory path")


def sepExts(exts):
    if "," in exts:
        return efilter(len, exts.strip().split(","))
    else:
        return [exts]
        # raise ArgumentTypeError("Invalid extensions list")


def checkValIn(val, valIn, typ):
    val = val.lower()
    if val in valIn:
        return typ(val)
    else:
        raise ArgumentTypeError("Invalid Value")


def addCliDir(parser):
    parser.add_argument("dir", help="Directory path.", type=checkDirPath)
    return parser


def addCliRec(parser):
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Process files recursively in all child directories.",
    )
    return parser


def addCliDry(parser):
    parser.add_argument(
        "-n",
        "--dry",
        action="store_true",
        help="Dry run.",
    )
    return parser


def addCliOnly(parser):
    parser.add_argument(
        "-o",
        "--only",
        default=None,
        type=int,
        help="Only process N files.",
    )
    return parser


def addCliExt(parser, defaults=None):
    parser.add_argument(
        "-e",
        "--extensions",
        default=defaults,
        help="Comma separated file extensions. (default: .mp4, .mov)",
        type=sepExts,
    )
    return parser
