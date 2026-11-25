import sys


def main():
    with open(sys.argv[1], 'rb') as f:
        h, w, steps = map(int, f.readline().split())
        rows = [f.readline().strip() for _ in range(h)]

    size = h * w
    grid = b''.join(rows)
    values = [0] * size
    cells = []
    for i, ch in enumerate(grid):
        if ch == 46:
            r, c = divmod(i, w)
            up = i - w if r and grid[i - w] != 35 else i
            down = i + w if r + 1 < h and grid[i + w] != 35 else i
            left = i - 1 if c and grid[i - 1] != 35 else i
            right = i + 1 if c + 1 < w and grid[i + 1] != 35 else i
            cells.append((i, up, down, left, right))
        elif ch != 35:
            values[i] = (ch - 48) * 1000
    other = values.copy()
    for _ in range(steps):
        changed = False
        for i, u, d, l, r in cells:
            v = (4 * values[i] + values[u] + values[d] + values[l] + values[r]) >> 3
            other[i] = v
            changed |= v != values[i]
        values, other = other, values
        if not changed:
            break
    total = checksum = 0
    maximum = -1
    max_i = 0
    for i, _, _, _, _ in cells:
        v = values[i]
        total += v
        checksum += v * (i + 1)
        if v > maximum:
            maximum, max_i = v, i
    sys.stdout.buffer.write(f'sum {total}\nmax {maximum} {max_i // w} {max_i % w}\nchecksum {checksum}\n'.encode())


if __name__ == '__main__':
    main()
