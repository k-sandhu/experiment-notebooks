import sys


def main() -> None:
    with open(sys.argv[1], "rb") as f:
        lines = f.read().splitlines()

    h, w, s = map(int, lines[0].split())
    wp = w + 2
    n = (h + 2) * wp

    # Padded grid as row lists; border cells are permanent walls (value 0).
    rows = [[0] * wp for _ in range(h + 2)]
    isopen = bytearray(n)
    issrc = bytearray(n)

    for r in range(h):
        line = lines[1 + r]
        base = (r + 1) * wp + 1
        for c in range(min(w, len(line))):
            ch = line[c]
            if ch == 35:  # '#'
                continue
            isopen[base + c] = 1
            if ch != 46:  # digit '1'-'9'
                issrc[base + c] = 1
                rows[r + 1][c + 1] = 1000 * (ch - 48)

    # Classify open cells:
    #  - "simple" cells (open, not a source, all 4 neighbours open) form
    #    horizontal runs [a, b) updated with a uniform multiplier of 4;
    #  - every other open non-source cell is "special" (multiplier 4+blocked).
    segs = [[] for _ in range(h + 2)]
    spec = [[] for _ in range(h + 2)]
    for r in range(1, h + 1):
        base = r * wp
        seg_r = segs[r]
        spec_r = spec[r]
        run = -1
        for c in range(1, w + 1):
            i = base + c
            if not isopen[i] or issrc[i]:
                if run >= 0:
                    seg_r.append((run, c))
                    run = -1
                continue
            if (
                isopen[i - 1]
                and isopen[i + 1]
                and isopen[i - wp]
                and isopen[i + wp]
            ):
                if run < 0:
                    run = c
            else:
                if run >= 0:
                    seg_r.append((run, c))
                    run = -1
                mm = 4
                if not isopen[i - 1]:
                    mm += 1
                if not isopen[i + 1]:
                    mm += 1
                if not isopen[i - wp]:
                    mm += 1
                if not isopen[i + wp]:
                    mm += 1
                spec_r.append((c, mm))
        if run >= 0:
            seg_r.append((run, w + 1))

    for _ in range(s):
        new_rows = rows[:]  # share unchanged rows, copy only updated ones
        for r in range(1, h + 1):
            seg_r = segs[r]
            spec_r = spec[r]
            if not seg_r and not spec_r:
                continue
            row = rows[r]
            up = rows[r - 1]
            dn = rows[r + 1]
            nrow = row[:]
            new_rows[r] = nrow
            for a, b in seg_r:
                nrow[a:b] = [
                    (4 * v + u + d + l + rr) >> 3
                    for v, u, d, l, rr in zip(
                        row[a:b], up[a:b], dn[a:b], row[a - 1 : b - 1], row[a + 1 : b + 1]
                    )
                ]
            for c, mm in spec_r:
                nrow[c] = (mm * row[c] + row[c - 1] + row[c + 1] + up[c] + dn[c]) >> 3
        rows = new_rows

    total = 0
    best = -1
    br = bc = 0
    chk = 0
    for r in range(h):
        row = rows[r + 1]
        base = (r + 1) * wp + 1
        wk = r * w
        for c in range(w):
            if isopen[base + c] and not issrc[base + c]:
                v = row[c + 1]
                total += v
                chk += v * (wk + c + 1)
                if v > best:
                    best = v
                    br = r
                    bc = c

    sys.stdout.buffer.write(
        f"sum {total}\nmax {best} {br} {bc}\nchecksum {chk}\n".encode()
    )


if __name__ == "__main__":
    main()
