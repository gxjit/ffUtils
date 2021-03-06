from json import loads
from pathlib import Path
from shutil import which
from subprocess import run
from time import sleep
from traceback import format_exc

from .pkgState import getLogFile


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


def checkExceptions(output):
    for o in iter(output):
        return o if not isinstance(o, Exception) else reportErr(o)


def runCmd(cmd):
    try:
        cmdOut = run(cmd, check=True, capture_output=True, text=True)
        cmdOut = cmdOut.stdout
    except Exception as callErr:
        reportErr(callErr)
        # return callErr
    return cmdOut


def runCmdJson(cmd):
    cmdOut = runCmd(cmd)
    if isinstance(cmdOut, Exception):
        return cmdOut
    data = loads(cmdOut)
    return data


def checkPath(path, absPath=None):
    path = which(path)
    if path:
        return path
    elif absPath and which(absPath):
        return absPath
    else:
        raise Exception(f"{path} or {absPath} is not an executable.")


def checkPaths(paths):
    if isinstance(paths, dict):
        return [checkPath(p, ap) for p, ap in paths.items()]


def getFileList(dirPath, exts, rec=False):
    if rec:
        return [f for f in dirPath.rglob("*.*") if f.suffix.lower() in exts]
    else:
        return [
            f for f in dirPath.iterdir() if f.is_file() and f.suffix.lower() in exts
        ]


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


def appendFile(file, contents):
    # if not file.exists():
    #     file.touch()
    with open(file, "a") as f:
        f.write(str(contents))


def log(msg):  # prefix="[lvl] now(): msg"
    msg = str(msg)
    logFile = getLogFile()
    print(msg)
    if logFile:
        appendFile(logFile, f"{msg}\n")


# def logWarn(), logError()
# debug info warn error critical


def reportErr(exp=None, ext=True):
    log("\n------\nERROR: Something went wrong.")
    if exp and exp.stderr:
        log(f"\nStdErr: {exp.stderr}\nReturn Code: {exp.returncode}")
    if exp:
        log(
            f"\nException:\n{exp}\n\nAdditional Details:\n{format_exc()}",
        )
    if ext:
        exit()


def cleanUp(paths):
    for path in paths:
        if path.exists():
            if path.is_dir():
                rmEmptyDir(path)
            elif path.is_file():
                removeFile(path)


def getInput():
    print("\nPress Enter Key continue or input 'e' to exit.")
    try:
        choice = input("\n> ")
        if choice not in ["e", ""]:
            raise ValueError

    except ValueError:
        print("\nInvalid input.")
        choice = getInput()

    if choice == "e":
        exit()


def areYouSure():
    print("\nAre you sure you want to continue? (y/n)")
    try:
        choice = str(input("\n> ")).lower()
        if choice not in ["y", "n"]:
            raise ValueError
    except ValueError:
        print("\nInvalid input.")
        areYouSure()

    if choice == "y":
        return
    else:
        exit()
