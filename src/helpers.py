import math
from collections import namedtuple
from datetime import datetime, timedelta
from functools import reduce
from itertools import chain
from operator import getitem
from re import compile
from time import time
from types import SimpleNamespace
from zlib import adler32

flatten = chain.from_iterable

flatMap = lambda x, y: list(flatten(map(x, y)))

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

dictToNTuple = lambda name, dic: namedtuple(name, dic)(**dic)

dictToNspace = lambda dic: SimpleNamespace(**dic)

prefixDots = lambda vals: [f".{v}" for v in vals]

now = lambda: str(datetime.now()).split(".")[0]

timeNow = lambda: str(datetime.now().time()).split(".")[0]

dateNow = lambda: str(datetime.now().date()).split(".")[0]

strDTime = lambda: datetime.now().strftime("%y%m%d-%H%M%S")


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


def csvToList(vals):
    if "," in vals:
        return efilter(len, vals.strip().split(","))
    else:
        return [vals]


def nSort(s, nsre=compile("([0-9]+)")):
    return [int(text) if text.isdigit() else text.lower() for text in nsre.split(s)]
