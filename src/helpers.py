import math
from datetime import timedelta
from functools import reduce
from operator import getitem
from pathlib import Path
from shutil import which
from subprocess import run
from time import time
from traceback import format_exc
from zlib import adler32

round2 = lambda x: round(float(x), ndigits=2)

readableTime = lambda sec: str(timedelta(seconds=sec)).split(".")[0]

emap = lambda func, itr: tuple(map(func, itr))

efilter = lambda func, itr: tuple(filter(func, itr))

range1 = lambda l, f=1, s=1: range(f, l + 1, s)

strSum = lambda datum: adler32(datum.encode("utf8"))

collectAtIndex = lambda itr, idx: [x[idx] for x in itr]

getByPath = lambda root, keys: reduce(getitem, keys, root)

collectAtKey = lambda itr, key: [getByPath(i, key) for i in itr]

findPercentage = lambda part, whole: f"{round2(float(part)/float(whole) * 100)}%"

findPercentOf = lambda prcnt, of: round2((prcnt * of) / 100.0)

posDivision = lambda x, y: round2(max(x, y) / min(x, y))


def exitIfEmpty(x):
    if not x:
        print("Nothing to do.")
        exit()


def waitN(n):
    print("\n")
    for i in reversed(range(0, n)):
        print(
            f"Waiting for {str(i).zfill(3)} seconds.", end="\r", flush=True
        )  # padding for clearing digits left from multi digit coundown
        sleep(1)
    print("\r")


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
        return o if not isinstance(o, Exception) else reportErrExit(o)


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
    if isinstance(files, (list, tuple)) and not isinstance(files, str):
        for f in files:
            removeFile(f)


def rmEmptyDir(path):
    if isinstance(path, Path) and path.exists():
        if path.is_dir() and not list(path.iterdir()):
            path.rmdir()


def rmEmptyDirs(paths):
    if isinstance(paths, (list, tuple)) and not isinstance(paths, str):
        for path in paths:
            rmEmptyDir(path)


def makeTargetDir(dirPath):
    if not dirPath.exists():
        dirPath.mkdir()
    return dirPath


def makeTargetDirs(dirPath, names=None):
    if names:
        return [makeTargetDir(dirPath / n) for n in names]
    else:
        return makeTargetDir(dirPath)


def extractKeysDict(dic, keys, asDict=False):
    if isinstance(keys, str):
        return dic.get(keys)
    elif isinstance(keys, (list, tuple)):
        if asDict:
            return {k: dic[k] for k in keys if dic.get(k)}
        else:
            return [dic[k] for k in keys if dic.get(k)]


def readableDict(dic):
    return "".join([f"{k}: {v}; " for k, v in dic.items()])


def readableSize(sBytes):
    if sBytes == 0:
        return "0B"
    if sBytes < 0:
        return sBytes  # better fix?
    sName = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(sBytes, 1024)))
    p = math.pow(1024, i)
    s = round(sBytes / p, 2)
    return f"{s} {sName[i]}"


def trackTime(func, *funcArgs):
    strtTime = time()
    funcOut = func(*funcArgs)
    timeTaken = float(time() - strtTime)
    return (funcOut, timeTaken)


def appendFile(file, contents):
    # if not file.exists():
    #     file.touch()
    with open(file, "a") as f:
        f.write(str(contents))


def cleanUp(paths):
    for path in paths:
        if path.exists():
            if path.is_dir():
                rmEmptyDir(path)
            elif path.is_file():
                removeFile(path)
