import sys


def main():
    with open(sys.argv[1], "rb") as f:
        lines = f.read().splitlines()

    height, width, steps = map(int, lines[0].split())
    stride = width + 2
    border = b"#" * stride
    grid = border + b"".join(
        b"#" + row + b"#" for row in lines[1:height + 1]
    ) + border

    first = grid.find(b".")
    if steps == 0:
        r, c = divmod(first, stride)
        sys.stdout.write(f"sum 0\nmax 0 {r - 1} {c - 1}\nchecksum 0\n")
        return

    # Each 17-bit lane holds one cell. An update numerator is at most
    # 8 * 9000, so additions cannot carry between lanes.
    lane_bits = 17
    value_mask = (1 << 14) - 1
    zero = "0" * lane_bits
    selected = "000" + "1" * 14
    source_patterns = [format(1000 * d, "017b") for d in range(10)]

    size = len(grid)
    source_fields = [zero] * size
    open_fields = [zero] * size
    odd_fields = [zero] * size
    twice_fields = [zero] * size
    positions = []

    for i, cell in enumerate(grid):
        if cell == 46:
            positions.append(i)
            blocked = (
                (grid[i - stride] == 35)
                + (grid[i + stride] == 35)
                + (grid[i - 1] == 35)
                + (grid[i + 1] == 35)
            )

            # Completely enclosed open cells remain zero forever.
            if blocked != 4:
                open_fields[i] = selected
                if blocked & 1:
                    odd_fields[i] = selected
                if blocked & 2:
                    twice_fields[i] = selected
        elif 49 <= cell <= 57:
            source_fields[i] = source_patterns[cell - 48]

    sources = int("".join(reversed(source_fields)), 2)
    del source_fields
    open_mask = int("".join(reversed(open_fields)), 2)
    del open_fields
    odd_mask = int("".join(reversed(odd_fields)), 2)
    del odd_fields
    twice_mask = int("".join(reversed(twice_fields)), 2)
    del twice_fields

    state = sources
    vertical_shift = stride * lane_bits

    if sources and open_mask:
        for _ in range(steps):
            numerator = (
                (state << 2)
                + (state >> vertical_shift)
                + (state << vertical_shift)
                + (state >> lane_bits)
                + (state << lane_bits)
                + (state & odd_mask)
                + ((state & twice_mask) << 1)
            )
            # The mask also removes bits shifted in from adjacent lanes.
            updated = ((numerator >> 3) & open_mask) | sources
            if updated == state:
                break
            state = updated

    packed = state.to_bytes((size * lane_bits + 7) // 8, "little") + b"\0\0"
    total = 0
    checksum = 0
    maximum = -1
    best_position = first
    from_bytes = int.from_bytes

    for i in positions:
        bit_position = i * lane_bits
        byte_position = bit_position >> 3
        value = (
            from_bytes(packed[byte_position:byte_position + 3], "little")
            >> (bit_position & 7)
        ) & value_mask

        total += value
        r, c = divmod(i, stride)
        checksum += value * ((r - 1) * width + c)

        if value > maximum:
            maximum = value
            best_position = i

    r, c = divmod(best_position, stride)
    sys.stdout.write(
        f"sum {total}\n"
        f"max {maximum} {r - 1} {c - 1}\n"
        f"checksum {checksum}\n"
    )


if __name__ == "__main__":
    main()
