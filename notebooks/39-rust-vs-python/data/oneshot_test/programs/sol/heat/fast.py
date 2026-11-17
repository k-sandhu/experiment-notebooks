import os
import sys

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        h, w, steps = map(int, f.readline().split())
        grid = np.frombuffer(
            b"".join(f.read().splitlines()), dtype=np.uint8
        ).reshape(h, w)

    open_positions = np.flatnonzero(grid.ravel() == 46)

    if steps == 0 or not np.any(grid >= 49):
        r, c = divmod(int(open_positions[0]), w)
        print(f"sum 0\nmax 0 {r} {c}\nchecksum 0")
        return

    pitch = w + 2
    padded = np.full((h + 2, pitch), 35, dtype=np.uint8)
    padded[1:-1, 1:-1] = grid
    chars = padded.ravel()

    walls = chars == 35
    coefficient = np.full(h * pitch, 4, dtype=np.int32)
    coefficient += walls[:-2 * pitch]
    coefficient += walls[2 * pitch:]
    coefficient += walls[pitch - 1:-pitch - 1]
    coefficient += walls[pitch + 1:1 - pitch]

    first = np.zeros(chars.size, dtype=np.int32)
    second = np.zeros_like(first)

    sources = np.flatnonzero(chars >= 49)
    first[sources] = (chars[sources].astype(np.int32) - 48) * 1000

    fixed_indices = np.flatnonzero(chars != 46)
    fixed_values = first[fixed_indices]

    def make_state(buffer):
        return (
            buffer[pitch:-pitch],
            buffer[:-2 * pitch],
            buffer[2 * pitch:],
            buffer[pitch - 1:-pitch - 1],
            buffer[pitch + 1:1 - pitch],
            buffer,
        )

    old = make_state(first)
    new = make_state(second)

    multiply = np.multiply
    add = np.add
    right_shift = np.right_shift

    for _ in range(steps):
        center, up, down, left, right, _ = old
        target = new[0]

        multiply(center, coefficient, out=target)
        add(target, up, out=target)
        add(target, down, out=target)
        add(target, left, out=target)
        add(target, right, out=target)
        right_shift(target, 3, out=target)

        new[5][fixed_indices] = fixed_values
        old, new = new, old

    padded_positions = (
        open_positions + 2 * (open_positions // w) + pitch + 1
    )
    values = old[5][padded_positions]

    best = int(values.argmax())
    position = int(open_positions[best])
    r, c = divmod(position, w)

    total = int(values.sum(dtype=np.int64))
    maximum = int(values[best])
    weights = open_positions.astype(np.int64)
    weights += 1
    checksum = int(np.dot(values.astype(np.int64), weights))

    print(
        f"sum {total}\n"
        f"max {maximum} {r} {c}\n"
        f"checksum {checksum}"
    )


if __name__ == "__main__":
    main()
