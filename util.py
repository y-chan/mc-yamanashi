import hashlib
from time import time as now_time


def sha256(x: bytes) -> bytes:
    return bytes(hashlib.sha256(x).digest())


def sha256d(x: bytes) -> bytes:
    return bytes(sha256(sha256(x)))


def ripemd160(x: bytes) -> bytes:
    md = hashlib.new('ripemd160')
    md.update(x)
    return md.digest()


def hash160(x: bytes) -> bytes:
    return bytes(ripemd160(sha256(x)))


def now_unixtime() -> int:
    return int(now_time())
