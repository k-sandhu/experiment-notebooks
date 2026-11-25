import sys


def main():
    data = open(sys.argv[1]).read().split()
    H = int(data[0]); W = int(data[1]); S = int(data[2])
    rows = data[3:3 + H]
    g = ''.join(rows)
    N = H * W
    L = 24
    fb = int.from_bytes
    tbl = bytes([0, 255] + [0] * 254)

    def lanes(flags):
        f = flags.translate(tbl)
        ba = bytearray(3 * N)
        ba[0::3] = f
        ba[1::3] = f
        ba[2::3] = f
        return fb(ba, 'little')

    t_open = bytearray([1]) * 256
    t_open[35] = 0
    opn = g.encode().translate(bytes(t_open))
    t_dot = bytearray(256)
    t_dot[46] = 1
    dot = g.encode().translate(bytes(t_dot))

    def band(a, b):
        return (fb(a, 'little') & fb(b, 'little')).to_bytes(N, 'little')

    colnot0 = (b'\0' + b'\x01' * (W - 1)) * H
    colnotlast = (b'\x01' * (W - 1) + b'\0') * H

    up = bytes(W) + opn[:N - W]
    down = opn[W:] + bytes(W)
    left = band(b'\0' + opn[:N - 1], colnot0)
    right = band(opn[1:] + b'\0', colnotlast)

    Mu = lanes(up)
    Md = lanes(down)
    Ml = lanes(left)
    Mr = lanes(right)
    Mupd = lanes(dot)

    ones = fb(b'\x01' * N, 'little')
    s = fb(up, 'little') + fb(down, 'little') + fb(left, 'little') + fb(right, 'little')
    c = 4 * ones - s  # wall count per byte
    b0 = (c & ones).to_bytes(N, 'little')
    b1 = ((c >> 1) & ones).to_bytes(N, 'little')
    b2 = ((c >> 2) & ones).to_bytes(N, 'little')
    B0 = lanes(b0)
    B1 = lanes(b1)
    B2 = lanes(b2)

    sba = bytearray(3 * N)
    for i, ch in enumerate(g):
        if '1' <= ch <= '9':
            v = 1000 * (ord(ch) - 48)
            sba[3 * i] = v & 255
            sba[3 * i + 1] = v >> 8
    SRC = fb(sba, 'little')

    WL = W * L
    old = SRC
    for _ in range(S):
        t = ((old << 2) + (old & B0) + ((old & B1) << 1) + ((old & B2) << 2)
             + ((old << WL) & Mu) + ((old >> WL) & Md)
             + ((old << L) & Ml) + ((old >> L) & Mr))
        old = ((t >> 3) & Mupd) | SRC

    b = old.to_bytes(3 * N, 'little')
    lo = b[0::3]
    mid = b[1::3]
    vals = [l | (m << 8) for l, m in zip(lo, mid)]
    total = sum(vals)
    V = max(vals)
    if V == 0:
        idx = 0
        for i, ch in enumerate(g):
            if ch != '#':
                idx = i
                break
    else:
        idx = vals.index(V)
    R, C = divmod(idx, W)
    chk = 0
    for i, v in enumerate(vals):
        if v:
            chk += v * (i + 1)
    print("sum %d" % total)
    print("max %d %d %d" % (V, R, C))
    print("checksum %d" % chk)


main()
