"""Single-threaded NumPy stencil with reusable, contiguous uint32 buffers."""

import os
import sys

# Keep NumPy's optional numerical backends single-threaded as well.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        tokens = f.read().split()
    h, w, steps = map(int, tokens[:3])
    cells = np.frombuffer(b"".join(tokens[3:]), dtype=np.uint8).reshape(h, w)
    is_open = cells == 46
    open_positions = np.flatnonzero(is_open)
    first = int(open_positions[0])
    if steps == 0 or not np.any((cells >= 49) & (cells <= 57)):
        r, c = divmod(first, w)
        print(f"sum 0\nmax 0 {r} {c}\nchecksum 0")
        return

    stride = w + 2
    shape = (h + 2, stride)
    walls = np.ones(shape, dtype=np.bool_)
    walls[1:-1, 1:-1] = cells == 35
    weights = np.zeros((h, stride), dtype=np.uint32)
    weights[:, 1:-1] = 4
    weights[:, 1:-1] += walls[:-2, 1:-1]
    weights[:, 1:-1] += walls[2:, 1:-1]
    weights[:, 1:-1] += walls[1:-1, :-2]
    weights[:, 1:-1] += walls[1:-1, 2:]
    weights = weights.ravel()
    fixed = np.ones((h, stride), dtype=np.bool_)
    fixed[:, 1:-1] = ~is_open
    fixed = fixed.ravel()

    a = np.zeros(shape, dtype=np.uint32)
    a[1:-1, 1:-1] = (np.maximum(cells, 48).astype(np.uint32) - 48) * 1000
    a = a.ravel()
    b = a.copy()
    fixed_indices = np.flatnonzero(fixed)
    fixed_values = a[stride:-stride][fixed_indices]
    # Include side padding so each ufunc sees a contiguous array. Scatter only
    # the fixed cells back to their initial values after each update.
    for step in range(steps):
        out = b[stride:-stride]
        np.multiply(a[stride:-stride], weights, out=out)
        np.add(out, a[:-2 * stride], out=out)
        np.add(out, a[2 * stride:], out=out)
        np.add(out, a[stride - 1:-stride - 1], out=out)
        np.add(out, a[stride + 1:-stride + 1], out=out)
        np.right_shift(out, 3, out=out)
        out[fixed_indices] = fixed_values
        a, b = b, a
        if step & 31 == 0 and np.array_equal(a, b):
            break

    values = a.reshape(shape)[1:-1, 1:-1][is_open].astype(np.int64)
    total = int(values.sum())
    best = int(values.argmax())
    maximum = int(values[best])
    r, c = divmod(int(open_positions[best]), w)
    checksum = int(np.dot(values, open_positions.astype(np.int64) + 1))
    print(f"sum {total}\nmax {maximum} {r} {c}\nchecksum {checksum}")


if __name__ == "__main__":
    sys.stdout.reconfigure(newline="\n")
    main()
