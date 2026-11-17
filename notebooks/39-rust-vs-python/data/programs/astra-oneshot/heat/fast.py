import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        h, w, steps = map(int, f.readline().split())
        grid = np.frombuffer(f.read(), dtype=np.uint8).reshape(h, w + 1)[:, :w]

    open_cells = grid == ord(".")
    open_indices = np.flatnonzero(open_cells)

    if steps == 0 or not np.any(grid >= ord("1")):
        r, c = divmod(int(open_indices[0]), w)
        sys.stdout.write(f"sum 0\nmax 0 {r} {c}\nchecksum 0\n")
        return

    fixed = np.maximum(grid.astype(np.int32) - ord("0"), 0)
    fixed *= 1000
    closed_cells = ~open_cells

    blocked = np.ones((h + 2, w + 2), dtype=np.bool_)
    blocked[1:-1, 1:-1] = grid == ord("#")

    weight = np.full((h, w), 4, dtype=np.int32)
    weight += blocked[:-2, 1:-1]
    weight += blocked[2:, 1:-1]
    weight += blocked[1:-1, :-2]
    weight += blocked[1:-1, 2:]

    a = np.zeros((h + 2, w + 2), dtype=np.int32)
    b = np.zeros_like(a)
    av = a[1:-1, 1:-1]
    bv = b[1:-1, 1:-1]
    av[:] = fixed

    a_neighbors = (
        a[:-2, 1:-1],
        a[2:, 1:-1],
        a[1:-1, :-2],
        a[1:-1, 2:],
    )
    b_neighbors = (
        b[:-2, 1:-1],
        b[2:, 1:-1],
        b[1:-1, :-2],
        b[1:-1, 2:],
    )

    multiply = np.multiply
    add = np.add
    right_shift = np.right_shift
    copyto = np.copyto

    for _ in range(steps):
        multiply(av, weight, out=bv)
        add(bv, a_neighbors[0], out=bv)
        add(bv, a_neighbors[1], out=bv)
        add(bv, a_neighbors[2], out=bv)
        add(bv, a_neighbors[3], out=bv)
        right_shift(bv, 3, out=bv)
        copyto(bv, fixed, where=closed_cells)

        av, bv = bv, av
        a_neighbors, b_neighbors = b_neighbors, a_neighbors

    values = av.ravel()[open_indices].astype(np.int64)
    total = int(values.sum(dtype=np.int64))
    best = int(values.argmax())
    maximum = int(values[best])
    r, c = divmod(int(open_indices[best]), w)
    positions = open_indices.astype(np.int64)
    positions += 1
    checksum = int(np.sum(values * positions, dtype=np.int64))

    sys.stdout.write(
        f"sum {total}\n"
        f"max {maximum} {r} {c}\n"
        f"checksum {checksum}\n"
    )


if __name__ == "__main__":
    main()
