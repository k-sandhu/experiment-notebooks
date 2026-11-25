import sys
from array import array


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        raw = f.read()

    nl = raw.find(b"\n")
    h, w, s = map(int, raw[:nl].split())
    body = raw[nl + 1:]
    lines = [ln.rstrip(b"\r") for ln in body.split(b"\n")]
    while lines and lines[-1] == b"":
        lines.pop()

    n = h * w
    FF = b"\xff\xff\xff\xff"

    avail = bytearray(4 * n)
    srcm = bytearray(4 * n)
    valb = bytearray(4 * n)
    leftok = bytearray(4 * n)
    rightok = bytearray(4 * n)
    open_cells = []

    for r in range(h):
        row = lines[r]
        base = r * w
        for c in range(w):
            ch = row[c]
            i = base + c
            off = 4 * i
            if ch != 35:
                avail[off:off + 4] = FF
                if ch == 46:
                    open_cells.append(i)
                else:
                    srcm[off:off + 4] = FF
                    valb[off:off + 4] = ((ch - 48) * 1000).to_bytes(4, "little")
            if c > 0:
                leftok[off:off + 4] = FF
            if c + 1 < w:
                rightok[off:off + 4] = FF

    A = int.from_bytes(avail, "little")
    SM = int.from_bytes(srcm, "little")
    SV = int.from_bytes(valb, "little")
    LO = int.from_bytes(leftok, "little")
    RO = int.from_bytes(rightok, "little")

    allmask = (1 << (32 * n)) - 1
    outmask = int.from_bytes(b"\xff\xff\x0f\x00" * n, "little")
    clearmask = outmask & ~SM

    wb = 32 * w
    upa = (A << wb) & allmask
    downa = A >> wb
    lefta = (A << 32) & allmask & LO
    righta = (A >> 32) & RO

    g = SV
    for _ in range(s):
        gn = g << wb
        upe = g ^ ((g ^ gn) & upa)
        gd = g >> wb
        dne = g ^ ((g ^ gd) & downa)
        gl = g << 32
        lfe = g ^ ((g ^ gl) & lefta)
        gr = g >> 32
        rte = g ^ ((g ^ gr) & righta)
        tot = (g << 2) + upe + dne + lfe + rte
        g = ((tot >> 3) & clearmask) | SV

    values = array("I")
    values.frombytes(g.to_bytes(4 * n, "little"))
    if sys.byteorder != "little":
        values.byteswap()

    total = 0
    checksum = 0
    best = -1
    best_i = 0
    for i in open_cells:
        v = values[i]
        total += v
        checksum += v * (i + 1)
        if v > best:
            best = v
            best_i = i

    out = "sum %d\nmax %d %d %d\nchecksum %d\n" % (
        total, best, best_i // w, best_i % w, checksum)
    sys.stdout.buffer.write(out.encode())


main()
