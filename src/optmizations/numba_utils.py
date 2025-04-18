from numba import njit
import numpy as np


@njit
def fast_checksum(data):
    checksum = 0
    for b in data:
        checksum += b
        checksum %= 2**32
    return checksum
