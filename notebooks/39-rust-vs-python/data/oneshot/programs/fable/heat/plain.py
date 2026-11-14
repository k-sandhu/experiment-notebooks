import sys
from math import sumprod
from struct import unpack


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    lines = data.replace(b'\r', b'').split(b'\n')
    H, W, S = map(int, lines[0].split())
    rows = lines[1:1 + H]
    if len(rows) < H:
        rows.extend([b''] * (H - len(rows)))
    for i, r in enumerate(rows):
        if len(r) != W:
            rows[i] = r[:W].ljust(W, b'#')

    Wp = W + 1                      # one padding (wall) column per row
    N = H * Wp
    cells = b'#'.join(rows) + b'#' * (1 + (-N) % 8)
    G = len(cells) >> 3             # groups of 8 cells = 17 bytes (17-bit fields)

    def build(valmap):
        # Pack small per-cell values into 17-bit fields of one big integer.
        buf = bytearray(17 * G)
        for j in range(8):
            lo = bytearray(256)
            hi = bytearray(256)
            for ch, v in valmap.items():
                x = v << j
                lo[ch] = x & 255
                hi[ch] = x >> 8
            sub = cells[j::8]
            buf[2 * j::17] = sub.translate(lo)
            buf[2 * j + 1::17] = sub.translate(hi)
        return int.from_bytes(buf, 'little')

    digits = {49 + i: i + 1 for i in range(9)}
    OPN1 = build({46: 1})
    DIG = build(digits)
    nwmap = {46: 1}
    for ch in digits:
        nwmap[ch] = 1
    NW1 = build(nwmap)

    s1 = 17
    sW = 17 * Wp

    # number of real (open/source) neighbours per cell
    CNT = (NW1 << s1) + (NW1 >> s1) + (NW1 << sW) + (NW1 >> sW)
    b0 = CNT & OPN1
    b1 = (CNT >> 1) & OPN1
    FM = 0x3FFF
    A1 = b0 * FM                    # open cells with odd count of wall neighbours
    A2 = (b0 ^ b1) * FM             # open cells with 2 or 3 wall neighbours
    OPEN = OPN1 * FM
    SRC = DIG * 1000

    V = SRC
    for _ in range(S):
        X = ((((V << 2) + (V >> s1) + (V << s1) + (V >> sW) + (V << sW)
               + (V & A1) + ((V & A2) << 1)) >> 3) & OPEN) | SRC
        if X == V:
            break
        V = X

    U = V & OPEN

    # Extract fields in bulk
    b = U.to_bytes(17 * G, 'little')
    n4 = 4 * G
    M32 = int.from_bytes(b'\xff\x3f\x00\x00' * G, 'little')
    fmt = '<%dI' % G
    vals = [0] * (8 * G)
    for j in range(8):
        buf = bytearray(n4)
        o = 2 * j
        buf[0::4] = b[o::17]
        buf[1::4] = b[o + 1::17]
        buf[2::4] = b[o + 2::17]
        x = (int.from_bytes(buf, 'little') >> j) & M32
        vals[j::8] = unpack(fmt, x.to_bytes(n4, 'little'))

    T = sum(vals)
    m = max(vals)
    if m > 0:
        p = vals.index(m)
    else:
        p = cells.find(b'.')
        if p < 0:
            p = 0
    R, C = divmod(p, Wp)

    wts = []
    ext = wts.extend
    app = wts.append
    for r in range(H):
        base = r * W
        ext(range(base + 1, base + W + 1))
        app(0)
    if len(wts) < 8 * G:
        ext([0] * (8 * G - len(wts)))
    K = sumprod(vals, wts)

    sys.stdout.write("sum %d\nmax %d %d %d\nchecksum %d\n" % (T, m, R, C, K))


main()
