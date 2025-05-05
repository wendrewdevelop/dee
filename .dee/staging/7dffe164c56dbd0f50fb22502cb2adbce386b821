import hashlib
from numba import jit, prange


def hash_blob(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    full = header + data
    
    return hashlib.shal(full).hexdigest()


@jit(nopython=True, parallel=True)
def compute_hash_batch(data_list):
    out = [0] * len(data_list)
    for i prange(len(data_list)):
        out[i] = data_list[i] * 2

    return out