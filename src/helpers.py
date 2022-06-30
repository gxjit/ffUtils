import math
from datetime import timedelta
from shutil import which
from subprocess import run
from traceback import format_exc
from collections.abc import Iterable
from pathlib import Path
from zlib import adler32
from time import time
from functools import reduce
from operator import getitem


round2 = lambda x: round(float(x), ndigits=2)

readableTime = lambda sec: str(timedelta(seconds=sec)).split(".")[0]

collectAtIndex = lambda itr, idx: [x[idx] for x in itr]

emap = lambda func, itr: tuple(map(func, itr))

efilter = lambda func, itr: tuple(filter(func, itr))

range1 = lambda l, f=1, s=1: range(f, l + 1, s)

strSum = lambda datum: adler32(datum.encode("utf8"))

getByPath = lambda root, keys: reduce(getitem, keys, root)

collectAtKey = lambda itr, key: [getByPath(i, key) for i in itr]


def exitIfEmpty(x):
    if not x:
        print("Nothing to do.")
        exit()


def runCmd(cmd):
    try:
        cmdOut = run(cmd, check=True, capture_output=True, text=True)
        cmdOut = cmdOut.stdout
    except Exception as callErr:
        reportErrExit(callErr)
        # return callErr
    return cmdOut


def checkPath(path, absPath=None):
    path = which(path)
    if path:
        return path
    elif absPath and which(absPath):
        return absPath
    else:
        raise f"{path} or {absPath} is not an executable."


def checkPaths(paths):
    if isinstance(paths, dict):
        return [checkPath(p, ap) for p, ap in paths.items()]


def checkExceptions(output):
    for o in iter(output):
        if isinstance(o, Exception):
            reportErrExit(o)
        else:
            return o


def getFileList(dirPath, exts, rec=False):
    if rec:
        return [f for f in dirPath.rglob("*.*") if f.suffix.lower() in exts]
    else:
        return [
            f for f in dirPath.iterdir() if f.is_file() and f.suffix.lower() in exts
        ]


def reportErrExit(exp=None):
    print("\n------\nERROR: Something went wrong.")
    if exp and exp.stderr:
        print(f"\nStdErr: {exp.stderr}\nReturn Code: {exp.returncode}")
    if exp:
        print(
            f"\nException:\n{exp}\n\nAdditional Details:\n{format_exc()}",
        )
    exit()


def removeFile(file):
    if isinstance(file, Path):
        if file.exists() and file.is_file():
            file.unlink()


def removeFiles(files):
    if isinstance(files, Iterable) and not isinstance(files, str):
        for f in files:
            removeFile(f)


def readableDict(dic):
    return "".join([f"{k}: {v}; " for k, v in dic.items()])


def readableSize(sBytes):
    if sBytes == 0:
        return "0B"
    if sBytes < 0:
        return sBytes
    sName = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(sBytes, 1024)))
    p = math.pow(1024, i)
    s = round(sBytes / p, 2)
    return f"{s} {sName[i]}"


def trackTime(func):
    strtTime = time()
    funcOut = func()
    timeTaken = float(time() - strtTime)
    return (funcOut, timeTaken)
