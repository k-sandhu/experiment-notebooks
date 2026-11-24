import sys

import numpy as np


def main() -> None:
    path = sys.argv[1]
    with open(path, "r") as f:
        text = f.read()
    lines = text.split("\n")
    header = lines[0].rstrip("\r")
    H, W, S = (int(x) for x in header.split())
    rows = [line.rstrip("\r") for line in lines[1 : 1 + H]]
    flat = "".join(rows)
    n = H * W

    cur = np.fromiter(
        (1000 * (ord(ch) - 48) if ch not in (".", "#") else 0 for ch in flat),
        dtype=np.int64,
        count=n,
    ).reshape(H, W)
    walkable = np.fromiter(
        (ch != "#" for ch in flat), dtype=bool, count=n
    ).reshape(H, W)
    open_mask = np.fromiter(
        (ch == "." for ch in flat), dtype=bool, count=n
    ).reshape(H, W)

    # Neighbour is usable when it is in bounds and not a wall (open or source).
    up_valid = np.zeros((H, W), dtype=bool)
    up_valid[1:, :] = walkable[:-1, :]
    down_valid = np.zeros((H, W), dtype=bool)
    down_valid[:-1, :] = walkable[1:, :]
    left_valid = np.zeros((H, W), dtype=bool)
    left_valid[:, 1:] = walkable[:, :-1]
    right_valid = np.zeros((H, W), dtype=bool)
    right_valid[:, :-1] = walkable[:, 1:]

    for _ in range(S):
        up = np.empty((H, W), dtype=np.int64)
        up[0, :] = cur[0, :]
        up[1:, :] = cur[:-1, :]
        down = np.empty((H, W), dtype=np.int64)
        down[-1, :] = cur[-1, :]
        down[:-1, :] = cur[1:, :]
        left = np.empty((H, W), dtype=np.int64)
        left[:, 0] = cur[:, 0]
        left[:, 1:] = cur[:, :-1]
        right = np.empty((H, W), dtype=np.int64)
        right[:, -1] = cur[:, -1]
        right[:, :-1] = cur[:, 1:]
        up = np.where(up_valid, up, cur)
        down = np.where(down_valid, down, cur)
        left = np.where(left_valid, left, cur)
        right = np.where(right_valid, right, cur)
        s = 4 * cur + up + down + left + right
        s >>= 3  # floor division by 8; all values are non-negative
        cur[open_mask] = s[open_mask]

    vals = cur[open_mask]
    total = int(vals.sum())
    k = int(np.argmax(vals))  # first maximum in row-major order
    cell_rows = np.argwhere(open_mask)
    r = int(cell_rows[k, 0])
    c = int(cell_rows[k, 1])
    v = int(vals[k])
    weights = (np.arange(n, dtype=np.int64).reshape(H, W) + 1)[open_mask]
    chk = int((vals * weights).sum())

    out = f"sum {total}\nmax {v} {r} {c}\nchecksum {chk}\n"
    sys.stdout.buffer.write(out.encode("ascii"))


if __name__ == "__main__":
    main()
