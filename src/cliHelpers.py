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
