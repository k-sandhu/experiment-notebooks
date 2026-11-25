import sys
from operator import mul

# The whole grid is packed into one Python int, one F-bit field per cell
# (SWAR). Each step is then a handful of big-int shifts, adds and masks that
# run in C over the whole grid at once.
#
# Every value stays in [0, 9000] < 2**14, and the pre-division total
# 4*old + 4 neighbour terms is at most 8*9000 = 72000 < 2**17, so 17-bit
# fields never carry into each other.
F = 17
FIELD = (1 << F) - 1


def pack(cells, table):
    # cells: one byte per cell, field 0 first. table: byte -> F-char binary.
    return int("".join(map(table.__getitem__, cells[::-1])), 2)


def main():
    with open(sys.argv[1], "rb") as f:
        lines = f.read().split(b"\n")
    h, w, s = map(int, lines[0].split())

    # Row stride P = W + 1: one wall column after each row keeps rows apart.
    p = w + 1
    n = h * p
    grid = b"".join(ln.strip()[:w] + b"#" for ln in lines[1:1 + h])
    zero = "0" * F
    one = zero[:-1] + "1"

    # Wall/outside count per cell, using a copy with wall rows above/below.
    t_wall = [zero] * 256
    t_wall[35] = one
    wall = pack(b"#" * p + grid + b"#" * p, t_wall)
    pf = p * F
    cnt = ((wall << pf) + (wall >> pf) + (wall << F) + (wall >> F)) >> pf

    t_open = [zero] * 256
    t_open[46] = "1" * F
    m_open_full = pack(grid, t_open)
    m_open = m_open_full & (((1 << (F - 3)) - 1) * (m_open_full // FIELD))
    rep1 = m_open_full // FIELD          # 1 in every open field
    # k = 4 + c with c = wall neighbours; c == 4 cells stay 0 and can be
    # ignored, so c*old = (old & B0) + 2*(old & B1).
    m_b0 = (cnt & rep1) * FIELD
    m_b1 = ((cnt >> 1) & rep1) * FIELD

    t_fix = [zero] * 256
    for d in range(1, 10):
        t_fix[48 + d] = format(1000 * d, "b").zfill(F)
    fixed = pack(grid, t_fix)

    x = fixed
    for _ in range(s):
        t = (((x << 1) + (x & m_b1)) << 1) + (x & m_b0)
        t += (x << pf) + (x >> pf) + (x << F) + (x >> F)
        x = ((t >> 3) & m_open) | fixed

    # Unpack: binary string, most significant field first.
    x &= m_open
    tot = n * F
    bits = format(x, "b").zfill(tot)
    vals = list(map(int, (bits[i:i + F] for i in range(0, tot, F)),
                    [2] * n))
    vals.reverse()

    tsum = sum(vals)
    chk = 0
    for r in range(h):
        b = r * p
        chk += sum(map(mul, vals[b:b + w], range(r * w + 1, r * w + w + 1)))
    vmax = max(vals)
    best = vals.index(vmax) if vmax else grid.find(b".")
    br, bc = divmod(best, p)
    sys.stdout.buffer.write(
        f"sum {tsum}\nmax {vmax} {br} {bc}\nchecksum {chk}\n".encode())


main()
