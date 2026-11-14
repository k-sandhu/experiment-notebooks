import sys

import numpy as np


def main() -> None:
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()

    parts = data.split()
    if len(parts) < 3:
        return
    h = int(parts[0])
    w = int(parts[1])
    s = int(parts[2])
    n = h * w

    rows = parts[3:3 + h]
    grid = b"".join(rows)
    if len(grid) != n:
        grid = b"".join(parts[3:])[:n]

    chars = np.frombuffer(grid, dtype=np.uint8)
    is_wall = chars == 35  # '#'
    is_open = chars == 46  # '.'
    # Digits '1'..'9' are everything else (grid chars are only ., #, 1-9).
    is_source = ~(is_wall | is_open)

    fixed_flat = np.zeros(n, dtype=np.int32)
    if np.any(is_source):
        fixed_flat[is_source] = (chars[is_source].astype(np.int32) - 48) * 1000

    wall2 = is_wall.reshape(h, w)
    open2 = is_open.reshape(h, w)
    fixed2 = fixed_flat.reshape(h, w)

    # Coefficient: 4 + number of invalid (wall / outside) neighbours.
    # Neighbour sums below use raw values with walls = 0 and no padding,
    # so invalid neighbours contribute 0 there and coef compensates with
    # (4 + invalid) * old instead of 4 * old.
    nonwall = ~wall2
    nv = np.zeros((h + 2, w + 2), dtype=bool)
    nv[1:-1, 1:-1] = nonwall
    valid_count = (
        nv[:-2, 1:-1].astype(np.int32)
        + nv[2:, 1:-1].astype(np.int32)
        + nv[1:-1, :-2].astype(np.int32)
        + nv[1:-1, 2:].astype(np.int32)
    )
    coef = (8 - valid_count).astype(np.int32)  # 4 + (4 - valid_count)

    a = fixed2.copy()
    b = fixed2.copy()

    # Non-open cells: restore fixed values (sources, 0 for walls) each step.
    nonopen_idx = np.flatnonzero(~open2.reshape(-1))
    nonopen_fixed = fixed_flat[nonopen_idx]

    for _ in range(s):
        np.multiply(a, coef, out=b)
        if h > 1:
            b[1:, :] += a[:-1, :]
            b[:-1, :] += a[1:, :]
        if w > 1:
            b[:, 1:] += a[:, :-1]
            b[:, :-1] += a[:, 1:]
        b >>= 3
        if nonopen_idx.size:
            b.flat[nonopen_idx] = nonopen_fixed
        a, b = b, a

    flat = a.reshape(-1)
    open_idx = np.flatnonzero(open2.reshape(-1))
    open_vals = flat[open_idx]
    if open_idx.size:
        total_sum = int(open_vals.sum(dtype=np.int64))
        k = int(np.argmax(open_vals))  # first max; open_idx is row-major
        best = int(open_vals[k])
        best_orig = int(open_idx[k])
        br = best_orig // w
        bc = best_orig % w
        weights = open_idx.astype(np.int64) + 1
        checksum = int((open_vals.astype(np.int64) * weights).sum())
    else:
        total_sum = 0
        best = 0
        br = 0
        bc = 0
        checksum = 0

    sys.stdout.buffer.write(f"sum {total_sum}\nmax {best} {br} {bc}\nchecksum {checksum}\n".encode())


if __name__ == "__main__":
    main()
