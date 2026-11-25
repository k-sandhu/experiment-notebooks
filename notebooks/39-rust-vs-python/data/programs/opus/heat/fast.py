import sys

import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        lines = f.read().split(b"\n")
    h, w, s = map(int, lines[0].split())
    grid = np.frombuffer(b"".join(ln.strip() for ln in lines[1:1 + h]),
                         dtype=np.uint8).reshape(h, w)

    # Padded layout: one wall row above and below, one wall column after each
    # row (shared as the left pad of the next row). Flat index with stride P.
    p = w + 1
    pad = np.full((h + 2, p), ord("#"), dtype=np.uint8)
    pad[1:h + 1, :w] = grid
    flat = pad.ravel()
    wall = flat == ord("#")
    is_open = flat == ord(".")

    n = h * p          # interior span (rows 1..h incl. pad column)
    lo = p
    hi = p + n

    # k = 4 + number of wall/outside neighbours: those contribute own value.
    k = 4 + (wall[lo - p:hi - p].astype(np.int32) + wall[lo + p:hi + p]
             + wall[lo - 1:hi - 1] + wall[lo + 1:hi + 1])
    keep = np.where(is_open[lo:hi], -1, 0).astype(np.int32)
    src = np.where(is_open | wall, 0,
                   (flat.astype(np.int32) - ord("0")) * 1000).astype(np.int32)
    fixed = src[lo:hi].copy()

    a = src.copy()
    b = src.copy()
    acc = np.empty(n, dtype=np.int32)
    tmp = np.empty(n, dtype=np.int32)
    add = np.add
    for _ in range(s):
        add(a[lo - p:hi - p], a[lo + p:hi + p], out=acc)
        add(acc, a[lo - 1:hi - 1], out=acc)
        add(acc, a[lo + 1:hi + 1], out=acc)
        np.multiply(a[lo:hi], k, out=tmp)
        add(acc, tmp, out=acc)
        np.right_shift(acc, 3, out=acc)
        np.bitwise_and(acc, keep, out=acc)
        np.bitwise_or(acc, fixed, out=b[lo:hi])
        a, b = b, a

    vals = a[lo:hi].reshape(h, p)[:, :w].astype(np.int64)
    om = is_open[lo:hi].reshape(h, p)[:, :w]
    vals = np.where(om, vals, -1)
    flatv = vals.ravel()
    best = int(np.argmax(flatv))
    vmax = int(flatv[best])
    pos = np.where(om.ravel(), flatv, 0)
    tsum = int(pos.sum())
    chk = int(np.dot(pos, np.arange(1, h * w + 1, dtype=np.int64)))
    r, c = divmod(best, w)
    sys.stdout.buffer.write(
        f"sum {tsum}\nmax {vmax} {r} {c}\nchecksum {chk}\n".encode())


main()
