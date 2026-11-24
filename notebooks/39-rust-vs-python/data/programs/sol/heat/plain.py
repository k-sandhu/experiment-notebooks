"""Single-threaded integer stencil using Python's arbitrary-precision integers.

Each cell occupies a 17-bit lane: even the largest numerator (8 * 9000)
fits without carrying into another lane. A zero lane between rows prevents
horizontal shifts from connecting cells on opposite edges.
"""

import sys


def main():
    with open(sys.argv[1], "rb") as f:
        tokens = f.read().split()
    h, w, steps = map(int, tokens[:3])
    rows = tokens[3:]
    first = next(r * w + row.index(b".") for r, row in enumerate(rows) if b"." in row)
    if steps == 0 or not any(49 <= ch <= 57 for row in rows for ch in row):
        r, c = divmod(first, w)
        print(f"sum 0\nmax 0 {r} {c}\nchecksum 0")
        return

    stride = w + 1
    nbytes = (h * stride * 17 + 7) // 8 + 2
    sources = bytearray(nbytes)
    opens = bytearray(nbytes)
    reflect_one = bytearray(nbytes)
    reflect_two = bytearray(nbytes)

    def put(buf, lane, value):
        bit = lane * 17
        byte = bit >> 3
        value <<= bit & 7
        buf[byte] |= value & 255
        buf[byte + 1] |= (value >> 8) & 255
        buf[byte + 2] |= value >> 16

    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            lane = r * stride + c
            if ch == 46:
                put(opens, lane, 16383)
                blocked = ((r == 0 or rows[r - 1][c] == 35)
                           + (r + 1 == h or rows[r + 1][c] == 35)
                           + (c == 0 or row[c - 1] == 35)
                           + (c + 1 == w or row[c + 1] == 35))
                if blocked & 1:
                    put(reflect_one, lane, 16383)
                if blocked & 2:
                    put(reflect_two, lane, 16383)
                # Four blocked neighbours imply an isolated, permanently zero cell.
            elif 49 <= ch <= 57:
                put(sources, lane, (ch - 48) * 1000)

    sources = int.from_bytes(sources, "little")
    opens = int.from_bytes(opens, "little")
    reflect_one = int.from_bytes(reflect_one, "little")
    reflect_two = int.from_bytes(reflect_two, "little")
    state = sources
    vertical = 17 * stride
    for _ in range(steps):
        # Keeping only 14 bits per lane after division discards the three bits
        # shifted down from the next lane, as well as every wall/source result.
        new = (((state << 2) + (state << 17) + (state >> 17)
                + (state << vertical) + (state >> vertical)
                + (state & reflect_one) + ((state & reflect_two) << 1)) >> 3) & opens
        new |= sources
        if new == state:
            break
        state = new

    packed = state.to_bytes(nbytes, "little")
    total = checksum = 0
    maximum = -1
    best = first
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == 46:
                bit = (r * stride + c) * 17
                byte = bit >> 3
                value = ((packed[byte] | (packed[byte + 1] << 8)
                          | (packed[byte + 2] << 16)) >> (bit & 7)) & 16383
                index = r * w + c
                total += value
                checksum += value * (index + 1)
                if value > maximum:
                    maximum = value
                    best = index
    r, c = divmod(best, w)
    print(f"sum {total}\nmax {maximum} {r} {c}\nchecksum {checksum}")


if __name__ == "__main__":
    sys.stdout.reconfigure(newline="\n")
    main()
