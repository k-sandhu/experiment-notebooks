"""Integer heat diffusion with single-threaded NumPy integer ufuncs."""

import os
import sys

# NumPy's integer kernels are single-threaded; also prevent its bundled BLAS
# from creating a thread pool during import.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        height, width, steps = map(int, f.readline().split())
        data = b"".join(f.readline().strip() for _ in range(height))

    cells = np.frombuffer(data, dtype=np.uint8).reshape(height, width)
    open_indices = np.flatnonzero(cells.ravel() == 46)
    sources = (cells >= 49) & (cells <= 57)
    if steps == 0 or not np.any(sources):
        row, col = divmod(int(open_indices[0]), width)
        print(f"sum 0\nmax 0 {row} {col}\nchecksum 0")
        return

    # Fold reflections into centre weights; keep an unchanged zero halo.
    walls = np.ones((height + 2, width + 2), dtype=np.int32)
    walls[1:-1, 1:-1] = cells == 35
    weights = (4 + walls[:-2, 1:-1] + walls[2:, 1:-1]
               + walls[1:-1, :-2] + walls[1:-1, 2:])
    stride = width + 2
    coefficients = np.zeros((height, stride), dtype=np.int32)
    coefficients[:, 1:-1] = weights
    weights = coefficients.ravel()
    old = np.zeros((height + 2, stride), dtype=np.int32)
    old[1:-1, 1:-1][sources] = (cells[sources].astype(np.int32) - 48) * 1000
    padded = np.full((height, stride), 35, dtype=np.uint8)
    padded[:, 1:-1] = cells
    fixed_indices = np.flatnonzero(padded.ravel() != 46) + stride
    old = old.ravel()
    new = old.copy()
    fixed_values = old[fixed_indices].copy()
    del walls, sources, padded, cells, data, coefficients

    multiply = np.multiply
    add = np.add
    shift = np.right_shift
    for step in range(steps):
        # Including the side halo makes these contiguous one-dimensional
        # passes. Restore the halo together with walls and sources below.
        centre = old[stride:-stride]
        out = new[stride:-stride]
        multiply(centre, weights, out=out)
        add(out, old[:-2 * stride], out=out)
        add(out, old[2 * stride:], out=out)
        add(out, old[stride - 1:-stride - 1], out=out)
        add(out, old[stride + 1:1 - stride], out=out)
        shift(out, 3, out=out)
        new[fixed_indices] = fixed_values
        if (step & 31) == 31 and np.array_equal(new, old):
            old = new
            break
        old, new = new, old

    values = old.reshape(height + 2, stride)[1:-1, 1:-1].ravel()[open_indices]
    best = int(np.argmax(values))
    row, col = divmod(int(open_indices[best]), width)
    total = int(values.sum(dtype=np.int64))
    checksum = int(np.dot(values.astype(np.int64), open_indices.astype(np.int64) + 1))
    print(f"sum {total}\nmax {int(values[best])} {row} {col}\nchecksum {checksum}")


if __name__ == "__main__":
    main()
