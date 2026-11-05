import sys

import numpy as np


def main():
    data = open(sys.argv[1], "rb").read().split()
    h = int(data[0]); w = int(data[1]); steps = int(data[2])
    rows = data[3:3 + h]
    chars = np.frombuffer(b"".join(rows), dtype=np.uint8).reshape(h, w)

    is_open = chars == 46  # '.'
    is_wall = chars == 35  # '#'
    digit = (chars >= 49) & (chars <= 57)

    fixed_in = np.zeros((h, w), dtype=np.int32)
    fixed_in[digit] = (chars[digit].astype(np.int32) - 48) * 1000

    # Padded wall map: border counts as wall.
    wall_pad = np.ones((h + 2, w + 2), dtype=bool)
    wall_pad[1:-1, 1:-1] = is_wall
    # coeff = 4 + number of wall/outside neighbours. Walls hold value 0,
    # so they add nothing via the neighbour sum and the extra coefficient
    # makes them contribute the cell's own value, as specified.
    coeff = (4 + wall_pad[:-2, 1:-1].astype(np.int32)
             + wall_pad[2:, 1:-1] + wall_pad[1:-1, :-2] + wall_pad[1:-1, 2:]).astype(np.int32)

    cur = np.zeros((h + 2, w + 2), dtype=np.int32)
    nxt = np.zeros((h + 2, w + 2), dtype=np.int32)
    cur[1:-1, 1:-1] = fixed_in

    # Flat (padded) indices of non-open real cells, restored each step.
    nonopen_pad = np.zeros((h + 2, w + 2), dtype=bool)
    nonopen_pad[1:-1, 1:-1] = ~is_open
    nonopen_idx = np.flatnonzero(nonopen_pad)
    nonopen_vals = cur.ravel()[nonopen_idx].copy()
    nxt_flat = nxt.ravel()

    for _ in range(steps):
        out = nxt[1:-1, 1:-1]
        np.multiply(coeff, cur[1:-1, 1:-1], out=out)
        out += cur[:-2, 1:-1]
        out += cur[2:, 1:-1]
        out += cur[1:-1, :-2]
        out += cur[1:-1, 2:]
        out >>= 3
        if nonopen_idx.size:
            nxt_flat[nonopen_idx] = nonopen_vals
        if np.array_equal(cur, nxt):
            break
        cur, nxt = nxt, cur
        nxt_flat = nxt.ravel()

    flat = cur[1:-1, 1:-1].ravel()
    open_pos = np.flatnonzero(is_open.ravel())
    vals = flat[open_pos].astype(np.int64)
    total = int(vals.sum())
    k = int(vals.argmax())
    pos = int(open_pos[k])
    checksum = int(np.dot(vals, open_pos.astype(np.int64) + 1))
    sys.stdout.write(f"sum {total}\nmax {int(vals[k])} {pos // w} {pos % w}\nchecksum {checksum}\n")


if __name__ == "__main__":
    main()
