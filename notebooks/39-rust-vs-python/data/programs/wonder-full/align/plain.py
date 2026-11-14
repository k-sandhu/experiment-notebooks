import sys


def main() -> None:
    with open(sys.argv[1], "rb") as f:
        toks = f.read().split()
    alphabet = toks[0]
    a = len(alphabet)
    table = bytearray(256)
    for i, ch in enumerate(alphabet):
        table[ch] = i
    table = bytes(table)

    pos = 1
    ins = list(map(int, toks[pos:pos + a])); pos += a
    dele = list(map(int, toks[pos:pos + a])); pos += a
    sub = list(map(int, toks[pos:pos + a * a])); pos += a * a
    p = int(toks[pos]); pos += 1

    out = []
    total = 0
    for _ in range(p):
        sb = toks[pos]; tb = toks[pos + 1]; pos += 2
        if sb == tb:
            out.append("0")
            continue
        s = sb.translate(table)
        t = tb.translate(table)
        # Orient so there are as few rows as possible.
        if len(s) <= len(t):
            rows = s; cols = t
            rowcost = dele
            colins = ins
            # smi[r][j] = sub[r][cols[j]] - ins[cols[j]]
            smi = [[sub[r * a + cc] - ins[cc] for cc in cols] for r in range(a)]
        else:
            rows = t; cols = s
            rowcost = ins
            colins = dele
            # sub'[r][c] = sub[c][r]; inserting a column char costs del[c]
            smi = [[sub[cc * a + r] - dele[cc] for cc in cols] for r in range(a)]
        m = len(cols)
        pref_m = 0
        for cc in cols:
            pref_m += colins[cc]

        # Reduced coordinates: P[j] = Dprev[j] - prefIns[j]; row 0 is all zero.
        # The candidate for column j is min(P[j+1] + del, P[j] + sub - ins_j),
        # and the new row in reduced coordinates is the running (prefix)
        # minimum of those candidates starting from cur0, which is exactly
        # the effect of the left (insertion) edge. The walrus in the
        # comprehension carries that running minimum along the row.
        prev = [0] * (m + 1)
        cur0 = 0
        for rc in rows:
            d = rowcost[rc]
            cur0 += d
            run = cur0
            prev = [run] + [run := min(run, up + d, diag + sm)
                            for up, diag, sm in zip(prev[1:], prev, smi[rc])]
        cost = prev[m] + pref_m
        total += cost
        out.append(str(cost))

    out.append("total " + str(total))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
