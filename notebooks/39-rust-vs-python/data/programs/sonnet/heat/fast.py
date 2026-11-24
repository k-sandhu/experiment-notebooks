import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        tokens = f.read().split()
    h, w, steps = int(tokens[0]), int(tokens[1]), int(tokens[2])
    g = np.frombuffer(b"".join(tokens[3:3 + h]), dtype=np.uint8).reshape(h, w)

    is_wall = g == 35
    is_open = ~is_wall
    is_src = (g >= 49) & (g <= 57)
    # padded open map: outside counts as wall
    po = np.zeros((h + 2, w + 2), dtype=np.int32)
    po[1:-1, 1:-1] = is_open
    cnt = po[:-2, 1:-1] + po[2:, 1:-1] + po[1:-1, :-2] + po[1:-1, 2:]

    # new = (((8 - open_neighbours) * old + sum of neighbours) >> 3) & mask | fixed
    coef = (8 - cnt).astype(np.int32)
    mask = np.where(is_open & ~is_src, -1, 0).astype(np.int32)
    fixed = np.where(is_src, (g.astype(np.int32) - 48) * 1000, 0).astype(np.int32)

    cur = np.zeros((h + 2, w + 2), dtype=np.int32)
    nxt = np.zeros((h + 2, w + 2), dtype=np.int32)
    cur[1:-1, 1:-1] = fixed
    tmp = np.empty((h, w), dtype=np.int32)

    mul, add, rsh, band, bor = np.multiply, np.add, np.right_shift, np.bitwise_and, np.bitwise_or
    for _ in range(steps):
        mul(cur[1:-1, 1:-1], coef, out=tmp)
        add(tmp, cur[:-2, 1:-1], out=tmp)
        add(tmp, cur[2:, 1:-1], out=tmp)
        add(tmp, cur[1:-1, :-2], out=tmp)
        add(tmp, cur[1:-1, 2:], out=tmp)
        rsh(tmp, 3, out=tmp)
        band(tmp, mask, out=tmp)
        bor(tmp, fixed, out=nxt[1:-1, 1:-1])
        cur, nxt = nxt, cur

    v = cur[1:-1, 1:-1].astype(np.int64)
    v[~(g == 46)] = 0  # only '.' cells count
    total = int(v.sum())
    best = int(v.max())
    if best > 0:
        idx = int(v.argmax())
    else:
        idx = int(np.argmax(g == 46))
    br, bc = divmod(idx, w)
    weights = np.arange(1, h * w + 1, dtype=np.int64).reshape(h, w)
    checksum = int((v * weights).sum())
    sys.stdout.buffer.write(f"sum {total}\nmax {best} {br} {bc}\nchecksum {checksum}\n".encode())


main()
