import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read().split()
    H = int(data[0]); W = int(data[1]); S_steps = int(data[2])
    rows = data[3:3 + H]
    g = np.frombuffer(b"".join(rows), dtype=np.uint8).reshape(H, W)

    is_open = (g == 46)
    is_src = (g >= 49) & (g <= 57)
    passable = (g != 35)

    F = np.where(is_src, (g.astype(np.int32) - 48) * 1000, 0).astype(np.int32)
    M = np.where(is_open, -1, 0).astype(np.int32)

    pp = np.zeros((H + 2, W + 2), dtype=np.int32)
    pp[1:-1, 1:-1] = passable
    k = pp[:-2, 1:-1] + pp[2:, 1:-1] + pp[1:-1, :-2] + pp[1:-1, 2:]
    C = (8 - k).astype(np.int32)

    P = np.zeros((H + 2, W + 2), dtype=np.int32)
    P[1:-1, 1:-1] = F
    interior = P[1:-1, 1:-1]
    up = P[:-2, 1:-1]
    down = P[2:, 1:-1]
    left = P[1:-1, :-2]
    right = P[1:-1, 2:]

    S = np.empty((H, W), dtype=np.int32)
    T = np.empty((H, W), dtype=np.int32)

    add = np.add
    mul = np.multiply
    for _ in range(S_steps):
        add(up, down, out=S)
        S += left
        S += right
        mul(C, interior, out=T)
        S += T
        S >>= 3
        S &= M
        S |= F
        interior[...] = S

    vals = interior.astype(np.int64)
    total = int(vals[is_open].sum())
    masked = np.where(is_open, vals, -1)
    idx = int(np.argmax(masked))
    r, c = divmod(idx, W)
    v = int(masked.reshape(-1)[idx])
    weights = np.arange(1, H * W + 1, dtype=np.int64).reshape(H, W)
    ck = int((np.where(is_open, vals, 0) * weights).sum())

    sys.stdout.write("sum %d\nmax %d %d %d\nchecksum %d\n" % (total, v, r, c, ck))


main()
