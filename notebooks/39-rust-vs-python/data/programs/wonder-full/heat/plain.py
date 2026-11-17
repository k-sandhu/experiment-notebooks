import sys

LANE = 24  # bits per cell in the packed big integer (3 bytes)
ALL_ONES = b"\xff\xff\xff"
OPEN_LANE = b"\xff\xff\x1f"  # low LANE-3 bits set: clears >>3 lane leak
ZERO_LANE = b"\x00\x00\x00"


def main():
    data = open(sys.argv[1], "rb").read().split()
    h = int(data[0]); w = int(data[1]); steps = int(data[2])
    rows = data[3:3 + h]

    wp = w + 2
    n = wp * (h + 2)
    nbytes = n * 3

    # Packed-lane masks, built as byte arrays then read as one big int.
    # x packs every padded cell into a 24-bit lane (values 0..9000, step
    # sums <= 72000 < 2^24, so lane-wise adds/shifts never carry across
    # lanes). Walls and padding hold 0. For a wall/outside neighbour the
    # raw shifted neighbour is 0, and adding (x & wall_mask_dir)
    # substitutes the cell's own value, exactly as specified.
    fixed_b = bytearray(nbytes)
    open_b = bytearray(OPEN_LANE * n)
    mu_b = bytearray(nbytes)
    md_b = bytearray(nbytes)
    ml_b = bytearray(nbytes)
    mr_b = bytearray(nbytes)

    WALL = 35  # '#'
    # Padding lanes are not open.
    open_b[:wp * 3] = ZERO_LANE * wp
    open_b[(n - wp) * 3:] = ZERO_LANE * wp

    for r in range(h):
        row = rows[r]
        up = rows[r - 1] if r > 0 else None
        down = rows[r + 1] if r + 1 < h else None
        base = (r + 1) * wp + 1
        o_base = base * 3
        open_b[(base - 1) * 3:(base - 1) * 3 + 3] = ZERO_LANE
        open_b[(base + w) * 3:(base + w) * 3 + 3] = ZERO_LANE
        for c in range(w):
            ch = row[c]
            o = o_base + c * 3
            if ch != 46:  # not '.'
                open_b[o:o + 3] = ZERO_LANE
                if ch != WALL:  # digit source
                    fixed_b[o:o + 3] = (1000 * (ch - 48)).to_bytes(3, "little")
            if up is None or up[c] == WALL:
                mu_b[o:o + 3] = ALL_ONES
            if down is None or down[c] == WALL:
                md_b[o:o + 3] = ALL_ONES
            if c == 0 or row[c - 1] == WALL:
                ml_b[o:o + 3] = ALL_ONES
            if c + 1 == w or row[c + 1] == WALL:
                mr_b[o:o + 3] = ALL_ONES

    fixed = int.from_bytes(fixed_b, "little")
    open_mask = int.from_bytes(open_b, "little")
    mu = int.from_bytes(mu_b, "little")
    md = int.from_bytes(md_b, "little")
    ml = int.from_bytes(ml_b, "little")
    mr = int.from_bytes(mr_b, "little")
    del fixed_b, open_b, mu_b, md_b, ml_b, mr_b

    stride = wp * LANE
    x = fixed
    for _ in range(steps):
        raw = (x << stride) + (x >> stride) + (x << LANE) + (x >> LANE)
        wall = (x & mu) + (x & md) + (x & ml) + (x & mr)
        nxt = (((x << 2) + raw + wall) >> 3 & open_mask) | fixed
        if nxt == x:
            break
        x = nxt

    b = x.to_bytes(nbytes, "little")
    total = 0
    checksum = 0
    best = -1
    best_r = best_c = 0
    for r in range(h):
        row = rows[r]
        o = ((r + 1) * wp + 1) * 3
        idx = r * w
        for c in range(w):
            if row[c] == 46:
                v = b[o] | (b[o + 1] << 8) | (b[o + 2] << 16)
                total += v
                checksum += v * (idx + c + 1)
                if v > best:
                    best = v
                    best_r = r
                    best_c = c
            o += 3
    sys.stdout.write(f"sum {total}\nmax {best} {best_r} {best_c}\nchecksum {checksum}\n")


if __name__ == "__main__":
    main()
