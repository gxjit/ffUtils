from argparse import ArgumentTypeError
from pathlib import Path

from .helpers import csvToList, prefixDots


def checkDirPath(pth):
    pthObj = Path(pth)
    if pthObj.is_dir():
        return pthObj
    else:
        raise ArgumentTypeError("Invalid Directory path")


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
        help=f'Comma separated file extensions. (default: {", ".join(defaults)})',
        default=defaults,
        type=lambda e: prefixDots(csvToList(e)),
    )
    return parser


def addCliWait(parser, dft=10):
    parser.add_argument(
        "-w",
        "--wait",
        nargs="?",
        default=None,
        const=dft,
        type=int,
        help=f"Wait time in seconds between each iteration, default is {dft}",
    )
    return parser
