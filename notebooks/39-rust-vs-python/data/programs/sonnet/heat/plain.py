import sys
from array import array

# The whole padded grid is packed into one big integer, one 24-bit lane per
# cell, so every step is a handful of big-int operations instead of a Python
# loop over cells.
L = 24


def pack(a):
    # 4-byte array items -> 3-byte lanes as one little-endian integer
    b = a.tobytes()
    out = bytearray(3 * len(a))
    out[0::3] = b[0::4]
    out[1::3] = b[1::4]
    out[2::3] = b[2::4]
    return int.from_bytes(out, "little")


def main():
    with open(sys.argv[1], "r") as f:
        tokens = f.read().split()
    h, w, steps = int(tokens[0]), int(tokens[1]), int(tokens[2])
    rows = tokens[3:3 + h]
    wp = w + 2
    n = (h + 2) * wp

    vals = array("I", bytes(4 * n))
    openm = array("I", bytes(4 * n))     # open (non-source) cells
    fixed = array("I", bytes(4 * n))     # source values
    wall = [array("I", bytes(4 * n)) for _ in range(4)]  # up, down, left, right is wall
    FULL = 0xFFFFFFFF
    for r in range(h):
        row = rows[r]
        base = (r + 1) * wp + 1
        for c in range(w):
            ch = row[c]
            if ch == "#":
                continue
            i = base + c
            if ch == ".":
                openm[i] = FULL
            else:
                v = 1000 * (ord(ch) - 48)
                vals[i] = v
                fixed[i] = v
            if r == 0 or rows[r - 1][c] == "#":
                wall[0][i] = FULL
            if r == h - 1 or rows[r + 1][c] == "#":
                wall[1][i] = FULL
            if c == 0 or row[c - 1] == "#":
                wall[2][i] = FULL
            if c == w - 1 or row[c + 1] == "#":
                wall[3][i] = FULL

    X = pack(vals)
    # keep result: divide by 8 leaves 3 stray bits in the top of each lane
    keep = pack(openm) & int.from_bytes(bytes((255, 255, 31)) * n, "little")
    F = pack(fixed)
    W0, W1, W2, W3 = (pack(a) for a in wall)
    # a source cell contributes its own value to wall-adjacent neighbours too,
    # which the wall masks handle because X holds the source value.
    up_sh = wp * L
    for _ in range(steps):
        s = (X << 2) + (X << up_sh) + (X >> up_sh) + (X << L) + (X >> L)
        s += (X & W0) + (X & W1) + (X & W2) + (X & W3)
        X = ((s >> 3) & keep) | F
    X &= keep  # only '.' cells count in the statistics

    raw = X.to_bytes(3 * n, "little")
    buf = bytearray(4 * n)
    buf[0::4] = raw[0::3]
    buf[1::4] = raw[1::3]
    buf[2::4] = raw[2::3]
    res = array("I")
    res.frombytes(buf)
    total = sum(res)
    best = max(res)
    if best > 0:
        idx = res.index(best)
        br, bc = divmod(idx, wp)
        br -= 1
        bc -= 1
    else:
        for r in range(h):
            c = rows[r].find(".")
            if c >= 0:
                br, bc = r, c
                break
    checksum = 0
    for r in range(h):
        b = (r + 1) * wp + 1
        seg = res[b:b + w]
        if not any(seg):
            continue
        wb = r * w + 1
        checksum += sum(map(int.__mul__, seg, range(wb, wb + w)))
    sys.stdout.buffer.write(f"sum {total}\nmax {best} {br} {bc}\nchecksum {checksum}\n".encode())


main()
