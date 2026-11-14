"""Heat on a grid in pure Python, using one big integer as a packed grid.

Each cell is a 24-bit field of a single int, laid out row by row in a grid with a
one-cell ring of walls. Shifting the int by one field moves every cell's value to a
neighbour's position, and & with a mask selects cells, so each step is about 20
big-int operations run in C. No Python loop runs over the cells during the simulation.
"""
import sys

FIELD = 24  # bits per cell; the largest intermediate sum is 8 * 9000 < 2**17
FIELD_BYTES = 3
FULL = 0xFFFFFF  # all bits of one field
LOW = 0xFFFF  # the low 16 bits of one field, which hold the value after >> 3


def pack(values):
    return int.from_bytes(b"".join(v.to_bytes(FIELD_BYTES, "little") for v in values), "little")


def main():
    with open(sys.argv[1], "rb") as f:
        tokens = f.read().split()
    h, w, steps = int(tokens[0]), int(tokens[1]), int(tokens[2])

    stride = w + 2
    n = stride * (h + 2)
    # kind per padded cell: 0 = wall or outside, 1 = open, 2 = source
    kind = [0] * n
    heat = [0] * n
    for r in range(h):
        row = tokens[3 + r]
        base = (r + 1) * stride + 1
        for c, ch in enumerate(row):
            if ch == 46:  # '.'
                kind[base + c] = 1
            elif ch != 35:  # not '#', so a digit
                kind[base + c] = 2
                heat[base + c] = 1000 * (ch - 48)

    open_cells = [i for i in range(n) if kind[i] == 1]

    x = pack(heat)
    # blk: fields of walls and outside cells. Shifting it gives, for each cell,
    # whether its neighbour in that direction is blocked.
    blk = pack([FULL if k == 0 else 0 for k in kind])
    blocked_up = blk << (stride * FIELD)
    blocked_down = blk >> (stride * FIELD)
    blocked_left = blk << FIELD
    blocked_right = blk >> FIELD
    low_open = pack([LOW if k == 1 else 0 for k in kind])
    fixed = pack([0 if k == 1 else FULL for k in kind])  # walls and sources keep their value
    row_shift = stride * FIELD

    for _ in range(steps):
        # 4 * old, plus the stored neighbour values (0 for walls),
        # plus the cell's own old value for each blocked direction.
        total = (x << 2) + (x >> FIELD) + (x << FIELD) + (x >> row_shift) + (x << row_shift)
        total += (x & blocked_up) + (x & blocked_down) + (x & blocked_left) + (x & blocked_right)
        x = ((total >> 3) & low_open) | (x & fixed)

    raw = x.to_bytes(FIELD_BYTES * n, "little")
    total_sum = 0
    best = -1
    best_r = best_c = 0
    checksum = 0
    for i in open_cells:
        v = int.from_bytes(raw[FIELD_BYTES * i:FIELD_BYTES * i + FIELD_BYTES], "little")
        pr, pc = divmod(i, stride)  # padded coordinates; the real cell is (pr - 1, pc - 1)
        total_sum += v
        if v > best:
            best = v
            best_r = pr - 1
            best_c = pc - 1
        checksum += v * ((pr - 1) * w + pc)

    out = f"sum {total_sum}\nmax {best} {best_r} {best_c}\nchecksum {checksum}\n"
    sys.stdout.buffer.write(out.encode())


if __name__ == "__main__":
    main()
