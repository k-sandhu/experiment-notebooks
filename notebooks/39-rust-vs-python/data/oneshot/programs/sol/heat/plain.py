import sys


def main():
    with open(sys.argv[1], "rb") as f:
        lines = f.read().splitlines()

    height, width, steps = map(int, lines[0].split())
    rows = lines[1:height + 1]

    # Pack cells into 24-bit lanes. The padding prevents row wrapping.
    stride = width + 2
    byte_count = (height + 2) * stride * 3
    row_shift = stride * 24

    open_flags = bytearray(byte_count)
    wall_flags = bytearray(b"\x01\x00\x00") * ((height + 2) * stride)
    source_data = bytearray(byte_count)
    positions = []

    for r, row in enumerate(rows):
        offset = ((r + 1) * stride + 1) * 3
        weight = r * width + 1

        for cell in row:
            if cell == 46:
                open_flags[offset] = 1
                wall_flags[offset] = 0
                positions.append((offset, weight))
            elif cell != 35:
                wall_flags[offset] = 0
                value = (cell - 48) * 1000
                source_data[offset] = value & 255
                source_data[offset + 1] = value >> 8

            offset += 3
            weight += 1

    def output_zero():
        r, c = divmod(positions[0][1] - 1, width)
        sys.stdout.write(f"sum 0\nmax 0 {r} {c}\nchecksum 0\n")

    if steps == 0:
        output_zero()
        return

    sources = int.from_bytes(source_data, "little")
    if not sources:
        output_zero()
        return

    open_bits = int.from_bytes(open_flags, "little")
    open_mask = open_bits * 0x3FFF

    # Source contributions are constant throughout the simulation.
    source_heat = (
        (sources >> 24)
        + (sources << 24)
        + (sources >> row_shift)
        + (sources << row_shift)
    )
    source_heat &= open_bits * 0x1FFFF

    if not source_heat:
        output_zero()
        return

    walls = int.from_bytes(wall_flags, "little")
    blocked = (
        (walls >> 24)
        + (walls << 24)
        + (walls >> row_shift)
        + (walls << row_shift)
    )

    reflect_one = (blocked & open_bits) * 0x3FFF
    reflect_two = ((blocked >> 1) & open_bits) * 0x3FFF

    # Cells with four blocked neighbours remain zero, so need no correction.
    del open_flags, wall_flags, source_data
    del walls, blocked, open_bits, sources

    values = (source_heat >> 3) & open_mask

    for _ in range(steps - 1):
        values = (
            (
                (values << 2)
                + (values >> 24)
                + (values << 24)
                + (values >> row_shift)
                + (values << row_shift)
                + (values & reflect_one)
                + ((values & reflect_two) << 1)
                + source_heat
            )
            >> 3
        ) & open_mask

    packed = values.to_bytes(byte_count, "little")
    total = 0
    checksum = 0
    maximum = -1
    maximum_weight = positions[0][1]

    for offset, weight in positions:
        value = packed[offset] | (packed[offset + 1] << 8)
        total += value
        checksum += value * weight

        if value > maximum:
            maximum = value
            maximum_weight = weight

    r, c = divmod(maximum_weight - 1, width)
    sys.stdout.write(
        f"sum {total}\n"
        f"max {maximum} {r} {c}\n"
        f"checksum {checksum}\n"
    )


if __name__ == "__main__":
    main()
