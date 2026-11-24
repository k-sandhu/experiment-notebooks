"""Heat on a grid with NumPy.

The grid is one flat int32 array with a one-cell ring of walls, so the neighbours of
every cell are fixed offsets in the array. Each step is a few contiguous vector operations
over all cells, written into a second buffer that is then swapped in.
"""
import sys

import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        tokens = f.read().split()
    h, w, steps = int(tokens[0]), int(tokens[1]), int(tokens[2])
    grid = np.frombuffer(b"".join(tokens[3:3 + h]), dtype=np.uint8).reshape(h, w)
    is_open = grid == ord(".")
    is_src = (grid >= ord("1")) & (grid <= ord("9"))

    shape = (h + 2, w + 2)
    stride = w + 2
    open2 = np.zeros(shape, dtype=bool)
    open2[1:-1, 1:-1] = is_open
    # solid: walls and the outside ring. A solid neighbour contributes the cell's own value.
    solid = np.ones(shape, dtype=bool)
    solid[1:-1, 1:-1] = ~(is_open | is_src)
    blocked = (solid[:-2, 1:-1].astype(np.int32) + solid[2:, 1:-1]
               + solid[1:-1, :-2] + solid[1:-1, 2:])
    coef2 = np.zeros(shape, dtype=np.int32)
    coef2[1:-1, 1:-1] = 4 + blocked

    heat2 = np.zeros(shape, dtype=np.int32)
    digit = grid.astype(np.int32) - ord("0")
    heat2[1:-1, 1:-1] = np.where(is_src, 1000 * digit, 0)

    coef = coef2.ravel()
    open_flat = open2.ravel()
    cur = heat2.ravel().copy()
    nxt = cur.copy()
    lo, hi = stride, cur.size - stride
    acc = np.empty(hi - lo, dtype=np.int32)

    for _ in range(steps):
        np.multiply(cur[lo:hi], coef[lo:hi], out=acc)
        acc += cur[lo - 1:hi - 1]
        acc += cur[lo + 1:hi + 1]
        acc += cur[lo - stride:hi - stride]
        acc += cur[lo + stride:hi + stride]
        acc >>= 3
        # Write only open cells. Walls and sources keep the same value in both buffers.
        np.copyto(nxt[lo:hi], acc, where=open_flat[lo:hi])
        cur, nxt = nxt, cur

    vals = cur.reshape(shape)[1:-1, 1:-1]
    open_vals = np.where(is_open, vals, 0).astype(np.int64)
    total = int(open_vals.sum())
    masked = np.where(is_open, vals, -1)
    idx = int(np.argmax(masked))  # first maximum in row-major order
    best_r, best_c = divmod(idx, w)
    best = int(masked.flat[idx])
    weights = np.arange(1, h * w + 1, dtype=np.int64).reshape(h, w)
    checksum = int((open_vals * weights).sum())

    out = f"sum {total}\nmax {best} {best_r} {best_c}\nchecksum {checksum}\n"
    sys.stdout.buffer.write(out.encode())


if __name__ == "__main__":
    main()
