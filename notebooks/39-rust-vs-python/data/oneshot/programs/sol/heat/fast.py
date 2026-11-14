import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        h, w, steps = map(int, f.readline().split())
        cells = np.frombuffer(f.read().replace(b"\n", b""), dtype=np.uint8).reshape(h, w)

    open_mask = cells == 46
    open_positions = np.flatnonzero(open_mask)

    if steps == 0 or not np.any(cells >= 49):
        r, c = divmod(int(open_positions[0]), w)
        sys.stdout.write(f"sum 0\nmax 0 {r} {c}\nchecksum 0\n")
        return

    walls = np.ones((h + 2, w + 2), dtype=np.int32)
    walls[1:-1, 1:-1] = cells == 35
    coefficient = (
        walls[:-2, 1:-1]
        + walls[2:, 1:-1]
        + walls[1:-1, :-2]
        + walls[1:-1, 2:]
        + 4
    )

    closed_positions = np.flatnonzero(~open_mask)
    fixed_positions = (
        closed_positions + 2 * (closed_positions // w) + w + 3
    )
    fixed_values = np.maximum(
        cells.reshape(-1)[closed_positions].astype(np.int32) - 48, 0
    )
    fixed_values *= 1000

    a = np.zeros((h + 2, w + 2), dtype=np.int32)
    b = np.zeros_like(a)
    a.reshape(-1)[fixed_positions] = fixed_values

    def views(grid):
        return (
            grid[1:-1, 1:-1],
            grid[:-2, 1:-1],
            grid[2:, 1:-1],
            grid[1:-1, :-2],
            grid[1:-1, 2:],
            grid.reshape(-1),
        )

    current = views(a)
    scratch = views(b)
    multiply = np.multiply
    add = np.add
    right_shift = np.right_shift

    for _ in range(steps):
        old, up, down, left, right, _flat = current
        new = scratch[0]
        multiply(old, coefficient, out=new)
        add(new, up, out=new)
        add(new, down, out=new)
        add(new, left, out=new)
        add(new, right, out=new)
        right_shift(new, 3, out=new)
        scratch[5][fixed_positions] = fixed_values
        current, scratch = scratch, current

    values = current[0][open_mask]
    best = int(values.argmax())
    maximum = int(values[best])
    r, c = divmod(int(open_positions[best]), w)
    total = int(values.sum(dtype=np.int64))
    checksum = int(np.dot(values.astype(np.int64), open_positions + 1))

    sys.stdout.write(
        f"sum {total}\n"
        f"max {maximum} {r} {c}\n"
        f"checksum {checksum}\n"
    )


if __name__ == "__main__":
    main()
