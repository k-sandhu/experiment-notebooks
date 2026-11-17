import sys


def main():
    with open(sys.argv[1], "rb") as f:
        h, w, steps = map(int, f.readline().split())
        rows = f.read().splitlines()[:h]

    largest_char = max(map(max, rows))

    if steps == 0 or largest_char < 49:
        for r, row in enumerate(rows):
            c = row.find(b".")
            if c >= 0:
                print(f"sum 0\nmax 0 {r} {c}\nchecksum 0")
                return

    maximum = (largest_char - 48) * 1000
    bits = maximum.bit_length() + 3
    value_mask = (1 << (bits - 3)) - 1

    # Separate rows with zero lanes; byte-aligned rows simplify packing.
    stride = (w // 8 + 1) * 8
    vertical = stride * bits
    row_bytes = vertical // 8

    border = b"#" * (w + 2)
    padded = [border]
    padded.extend(b"#" + row + b"#" for row in rows)
    padded.append(border)

    source_parts = []
    open_parts = []
    one_parts = []
    two_parts = []

    for r in range(1, h + 1):
        above = padded[r - 1]
        middle = padded[r]
        below = padded[r + 1]

        source_row = 0
        open_row = 0
        one_row = 0
        two_row = 0

        shift = 0
        for c in range(1, w + 1):
            ch = middle[c]
            if ch == 46:
                blocked = (
                    (above[c] == 35)
                    + (below[c] == 35)
                    + (middle[c - 1] == 35)
                    + (middle[c + 1] == 35)
                )

                # Completely enclosed cells remain zero forever.
                if blocked != 4:
                    field = value_mask << shift
                    open_row |= field
                    if blocked & 1:
                        one_row |= field
                    if blocked & 2:
                        two_row |= field
            elif ch != 35:
                source_row |= ((ch - 48) * 1000) << shift

            shift += bits

        source_parts.append(source_row.to_bytes(row_bytes, "little"))
        open_parts.append(open_row.to_bytes(row_bytes, "little"))
        one_parts.append(one_row.to_bytes(row_bytes, "little"))
        two_parts.append(two_row.to_bytes(row_bytes, "little"))

    sources = int.from_bytes(b"".join(source_parts), "little")
    open_mask = int.from_bytes(b"".join(open_parts), "little")
    one_mask = int.from_bytes(b"".join(one_parts), "little")
    two_mask = int.from_bytes(b"".join(two_parts), "little")

    del source_parts, open_parts, one_parts, two_parts, padded

    state = sources

    # Each integer lane has enough headroom for the entire weighted sum,
    # so additions cannot carry into adjacent cells.
    for _ in range(steps):
        updated = (
            (
                (
                    (state << 2)
                    + (state >> vertical)
                    + (state << vertical)
                    + (state >> bits)
                    + (state << bits)
                    + (state & one_mask)
                    + ((state & two_mask) << 1)
                )
                >> 3
            )
            & open_mask
        ) | sources

        if updated == state:
            break
        state = updated

    packed = state.to_bytes(h * row_bytes, "little")
    total = 0
    checksum = 0
    best_value = -1
    best_position = 0

    for r, row in enumerate(rows):
        start = r * row_bytes
        row_state = int.from_bytes(packed[start:start + row_bytes], "little")
        base = r * w

        for c, ch in enumerate(row):
            if ch == 46:
                value = row_state & value_mask
                position = base + c
                total += value
                checksum += value * (position + 1)
                if value > best_value:
                    best_value = value
                    best_position = position

            row_state >>= bits

    best_r, best_c = divmod(best_position, w)
    print(
        f"sum {total}\n"
        f"max {best_value} {best_r} {best_c}\n"
        f"checksum {checksum}"
    )


if __name__ == "__main__":
    main()
