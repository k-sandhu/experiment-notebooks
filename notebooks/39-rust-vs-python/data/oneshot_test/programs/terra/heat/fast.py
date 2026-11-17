import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        h, w, steps = map(int, f.readline().split())
        data = b"".join(f.readline().strip() for _ in range(h))

    grid = np.frombuffer(data, dtype=np.uint8).reshape(h, w)
    open_mask = grid == ord(".")
    fixed_mask = ~open_mask

    walls = np.ones((h + 2, w + 2), dtype=np.uint8)
    walls[1:-1, 1:-1] = grid == ord("#")

    coeff = (
        4
        + walls[:-2, 1:-1]
        + walls[2:, 1:-1]
        + walls[1:-1, :-2]
        + walls[1:-1, 2:]
    )

    a = np.zeros((h + 2, w + 2), dtype=np.int32)
    b = np.zeros_like(a)
    source_mask = (grid >= ord("1")) & (grid <= ord("9"))
    a_core = a[1:-1, 1:-1]
    a_core[source_mask] = (grid[source_mask].astype(np.int32) - ord("0")) * 1000
    fixed_values = a_core[fixed_mask].copy()

    for _ in range(steps):
        a_core = a[1:-1, 1:-1]
        b_core = b[1:-1, 1:-1]
        np.multiply(a_core, coeff, out=b_core)
        np.add(b_core, a[:-2, 1:-1], out=b_core)
        np.add(b_core, a[2:, 1:-1], out=b_core)
        np.add(b_core, a[1:-1, :-2], out=b_core)
        np.add(b_core, a[1:-1, 2:], out=b_core)
        np.right_shift(b_core, 3, out=b_core)
        b_core[fixed_mask] = fixed_values
        a, b = b, a

    values = a[1:-1, 1:-1][open_mask].astype(np.int64)
    indices = np.flatnonzero(open_mask)
    max_pos = int(np.argmax(values))
    max_index = int(indices[max_pos])
    total = int(values.sum())
    checksum = int(np.dot(values, indices.astype(np.int64) + 1))

    print("sum", total)
    print("max", int(values[max_pos]), max_index // w, max_index % w)
    print("checksum", checksum)


if __name__ == "__main__":
    main()
