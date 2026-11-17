import sys

import numpy as np


def main() -> None:
    with open(sys.argv[1], "rb") as f:
        lines = f.read().splitlines()

    h, w, s = map(int, lines[0].split())
    wp = w + 2

    # Parse grid bytes into one flat buffer (rows padded/clipped to w).
    rows = [ln[:w] if len(ln) >= w else ln.ljust(w, b"#") for ln in lines[1 : 1 + h]]
    arr = np.frombuffer(b"".join(rows[:h]), dtype=np.uint8).reshape(h, w)

    is_open_int = (arr != ord("#")).astype(np.int8)
    digit = (arr >= ord("1")) & (arr <= ord("9"))
    src_vals = np.where(digit, (arr.astype(np.int32) - ord("0")) * 1000, 0)

    # Padded grids: border cells act as walls (never open, value 0).
    cur = np.zeros((h + 2, wp), dtype=np.int32)
    op = np.zeros((h + 2, wp), dtype=bool)
    cur[1 : h + 1, 1 : w + 1] = src_vals  # only sources carry a value
    op[1 : h + 1, 1 : w + 1] = is_open_int.astype(bool)

    # m = 4 + number of blocked neighbours, zeroed on walls/sources.
    m = np.zeros((h + 2, wp), dtype=np.int32)
    cnt = (
        op[:-2, 1:-1].astype(np.int32)
        + op[2:, 1:-1]
        + op[1:-1, :-2]
        + op[1:-1, 2:]
    )
    m[1:-1, 1:-1] = 8 - cnt  # 4 + (4 - cnt)
    m *= op
    m[1:-1, 1:-1][digit] = 0  # sources are fixed, not updated

    # After each step: restore walls/padding to 0 and sources to their value.
    fixmask = ~op
    fixmask[1:-1, 1:-1] |= digit
    fr, fc = np.nonzero(fixmask)
    fv = cur[fr, fc].copy()  # 0 at walls/padding, 1000*d at sources

    nxt = np.zeros_like(cur)
    mcore = m[1:-1, 1:-1]

    def views(g):
        return (
            g[1:-1, 1:-1],
            g[:-2, 1:-1],
            g[2:, 1:-1],
            g[1:-1, :-2],
            g[1:-1, 2:],
        )

    VA, VB = views(cur), views(nxt)
    for _ in range(s):
        cB, upB, dnB, lfB, rtB = VB  # write target
        cA, upA, dnA, lfA, rtA = VA  # read source
        np.multiply(mcore, cA, out=cB)
        np.add(cB, upA, out=cB)
        np.add(cB, dnA, out=cB)
        np.add(cB, lfA, out=cB)
        np.add(cB, rtA, out=cB)
        np.right_shift(cB, 3, out=cB)
        nxt[fr, fc] = fv  # walls/padding -> 0, sources -> fixed value
        cur, nxt = nxt, cur
        VA, VB = VB, VA

    # Stats over open ('.') cells only - sources are not open cells.
    sm = np.zeros((h + 2, wp), dtype=bool)
    sm[1:-1, 1:-1] = digit
    rr, cc = np.nonzero(op & ~sm)  # row-major order
    vals = cur[rr, cc]
    if vals.size == 0:  # out of spec (no open cell); stay consistent
        sys.stdout.buffer.write(b"sum 0\nmax -1 0 0\nchecksum 0\n")
        return
    total = int(vals.sum(dtype=np.int64))
    am = int(np.argmax(vals))  # first maximum in row-major order
    r0 = int(rr[am]) - 1
    c0 = int(cc[am]) - 1
    weights = rr.astype(np.int64) * w + cc - w  # (rr-1)*w + (cc-1) + 1
    chk = int((vals.astype(np.int64) * weights).sum())

    sys.stdout.buffer.write(
        f"sum {total}\nmax {vals[am]} {r0} {c0}\nchecksum {chk}\n".encode()
    )


if __name__ == "__main__":
    main()
