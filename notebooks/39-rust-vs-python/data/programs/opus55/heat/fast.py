import sys

import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read().split()
    H, W, S = int(data[0]), int(data[1]), int(data[2])

    # Flat padded layout: row stride LR = W + 1 (one wall column shared
    # between neighbouring rows) and a wall row above and below.  Cell (r, c)
    # is element (r+1)*LR + c + 1.  Walls hold 0, so a wall neighbour adds
    # nothing and is instead accounted for in the centre weight 4 + k.
    LR = W + 1
    N = (H + 2) * LR
    g = np.full((H + 2, LR), ord("#"), dtype=np.uint8)
    g[1:H + 1, 1:] = np.frombuffer(b"".join(data[3:3 + H]), dtype=np.uint8).reshape(H, W)
    g = g.ravel()

    is_open = g == ord(".")
    is_wall = g == ord("#")
    src = np.where(is_open | is_wall, 0, (g.astype(np.int32) - ord("0")) * 1000).astype(np.int32)

    k = np.zeros(N, dtype=np.int32)
    k[1:] += is_wall[:-1]
    k[:-1] += is_wall[1:]
    k[LR:] += is_wall[:-LR]
    k[:-LR] += is_wall[LR:]

    # Every step works on the slice [lo, hi) between the top and bottom pad rows.
    lo, hi = LR, N - LR
    coef = (4 + k[lo:hi]).astype(np.int32)
    keep = np.where(is_open[lo:hi], -1, 0).astype(np.int32)
    fixed = src[lo:hi].copy()

    a = src.copy()
    b = src.copy()
    t = np.empty(hi - lo, dtype=np.int32)
    mul, add, rshift, band, bor = np.multiply, np.add, np.right_shift, np.bitwise_and, np.bitwise_or
    for _ in range(S):
        mul(a[lo:hi], coef, out=t)
        add(t, a[lo - LR:hi - LR], out=t)
        add(t, a[lo + LR:hi + LR], out=t)
        add(t, a[lo - 1:hi - 1], out=t)
        add(t, a[lo + 1:hi + 1], out=t)
        rshift(t, 3, out=t)
        band(t, keep, out=t)
        bor(t, fixed, out=b[lo:hi])
        a, b = b, a

    v = np.where(is_open, a, 0).astype(np.int64)
    total = int(v.sum())
    p = int(v.argmax())
    best = int(v[p])
    if best == 0:
        p = int(is_open.argmax())
    idx = np.arange(N, dtype=np.int64)
    idx -= idx // LR + W
    chk = int(v @ idx)
    r, c = divmod(p, LR)
    sys.stdout.buffer.write(
        f"sum {total}\nmax {best} {r - 1} {c - 1}\nchecksum {chk}\n".encode())


main()
