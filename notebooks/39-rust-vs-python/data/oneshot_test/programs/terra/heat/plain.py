import sys


def main():
    with open(sys.argv[1], "rb") as f:
        lines = f.read().splitlines()

    h, w, steps = map(int, lines[0].split())
    stride = w + 2
    border = b"#" * stride
    grid = border + b"".join(b"#" + row + b"#" for row in lines[1:h + 1]) + border
    size = len(grid) * 3

    initial = bytearray(size)
    open_mask = bytearray(size)
    blocked_one = bytearray(size)
    blocked_two = bytearray(size)
    blocked_four = bytearray(size)
    positions = []

    for r in range(h):
        base = (r + 1) * stride + 1
        weight = r * w + 1
        for c in range(w):
            p = base + c
            cell = grid[p]
            offset = p * 3
            if cell == 46:  # .
                positions.append((offset, weight + c))
                open_mask[offset] = 255
                open_mask[offset + 1] = 63
                blocked = (
                    (grid[p - stride] == 35)
                    + (grid[p + stride] == 35)
                    + (grid[p - 1] == 35)
                    + (grid[p + 1] == 35)
                )
                if blocked & 1:
                    blocked_one[offset] = 255
                    blocked_one[offset + 1] = 63
                if blocked & 2:
                    blocked_two[offset] = 255
                    blocked_two[offset + 1] = 63
                if blocked & 4:
                    blocked_four[offset] = 255
                    blocked_four[offset + 1] = 63
            elif cell != 35:  # source
                value = (cell - 48) * 1000
                initial[offset] = value & 255
                initial[offset + 1] = value >> 8

    sources = int.from_bytes(initial, "little")
    mask = int.from_bytes(open_mask, "little")
    one = int.from_bytes(blocked_one, "little")
    two = int.from_bytes(blocked_two, "little")
    four = int.from_bytes(blocked_four, "little")
    vertical = stride * 24
    state = sources

    for _ in range(steps):
        total = (
            (state << 2)
            + (state << 24)
            + (state >> 24)
            + (state << vertical)
            + (state >> vertical)
            + (state & one)
            + ((state & two) << 1)
            + ((state & four) << 2)
        )
        new_state = ((total >> 3) & mask) | sources
        if new_state == state:
            break
        state = new_state

    values = state.to_bytes(size, "little")
    result_sum = 0
    checksum = 0
    maximum = -1
    max_weight = 1

    for offset, weight in positions:
        value = values[offset] | (values[offset + 1] << 8)
        result_sum += value
        checksum += value * weight
        if value > maximum:
            maximum = value
            max_weight = weight

    row, col = divmod(max_weight - 1, w)
    print(f"sum {result_sum}\nmax {maximum} {row} {col}\nchecksum {checksum}")


if __name__ == "__main__":
    main()
