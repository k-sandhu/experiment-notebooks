import sys

import numpy as np


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        raw = f.read()

    nl = raw.find(b"\n")
    h, w, s = map(int, raw[:nl].split())
    body = raw[nl + 1:]
    lines = [ln.rstrip(b"\r") for ln in body.split(b"\n")]
    while lines and lines[-1] == b"":
        lines.pop()

    cells = np.frombuffer(b"".join(lines[:h]), dtype=np.uint8).reshape(h, w)

    is_wall = cells == 35          # '#'
    is_src = (cells >= 49) & (cells <= 57)
    openmask = ~(is_wall | is_src)

    vals = np.where(is_src, (cells.astype(np.int32) - 48) * 1000, 0).astype(np.int32)
    srcvals = vals.copy()

    # Number of missing (wall or outside) neighbours for every cell.
    wp = np.ones((h + 2, w + 2), dtype=np.int32)
    wp[1:-1, 1:-1] = is_wall
    miss = (wp[:-2, 1:-1] + wp[2:, 1:-1] + wp[1:-1, :-2] + wp[1:-1, 2:])
    coeff = miss + 4          # 4*old plus one old value per missing neighbour

    # Wall and source cells are forced to 0 / their source value every step.
    keep = -openmask.astype(np.int32)   # -1 where open, 0 elsewhere

    padded = np.zeros((h + 2, w + 2), dtype=np.int32)
    padded[1:-1, 1:-1] = vals

    tmp = np.empty((h, w), dtype=np.int32)
    scaled = np.empty((h, w), dtype=np.int32)
    for _ in range(s):
        np.add(padded[:-2, 1:-1], padded[2:, 1:-1], out=tmp)
        tmp += padded[1:-1, :-2]
        tmp += padded[1:-1, 2:]
        np.multiply(vals, coeff, out=scaled)
        tmp += scaled
        np.right_shift(tmp, 3, out=tmp)
        np.bitwise_and(tmp, keep, out=tmp)
        np.bitwise_or(tmp, srcvals, out=tmp)
        vals, tmp = tmp, vals
        padded[1:-1, 1:-1] = vals

    total = int(vals[openmask].sum(dtype=np.int64))
    masked = np.where(openmask, vals, np.int32(-1))
    best_i = int(masked.argmax())
    best = int(masked.flat[best_i])

    idxs = np.flatnonzero(openmask)
    checksum = int(np.sum(vals.ravel()[idxs].astype(np.int64) * (idxs.astype(np.int64) + 1)))

    r, c = divmod(best_i, w)
    sys.stdout.buffer.write(
        ("sum %d\nmax %d %d %d\nchecksum %d\n" % (total, best, r, c, checksum)).encode())


main()
