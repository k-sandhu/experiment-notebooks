import sys

import numpy as np


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
    sub_list = list(map(int, toks[pos:pos + a * a])); pos += a * a
    p = int(toks[pos]); pos += 1

    sub32 = np.array(sub_list, dtype=np.int32).reshape(a, a)
    sub64 = None
    ins32 = np.array(ins, dtype=np.int32)
    dele32 = np.array(dele, dtype=np.int32)
    ins64 = dele64 = None

    np_add = np.add
    np_min = np.minimum
    np_acc = np.minimum.accumulate
    frombuffer = np.frombuffer

    out = []
    total = 0

    for _ in range(p):
        sb = toks[pos]; tb = toks[pos + 1]; pos += 2
        if sb == tb:
            out.append("0")
            continue
        s = sb.translate(table)
        t = tb.translate(table)
        # int32 unless values could overflow: |reduced values| are below
        # about 1000 * (n + m + 2).
        if (len(s) + len(t) + 2) * 1000 < 2_147_483_647:
            dt = np.int32
            sub_np = sub32; ins_np = ins32; dele_np = dele32
        else:
            if sub64 is None:
                sub64 = sub32.astype(np.int64)
                ins64 = ins32.astype(np.int64)
                dele64 = dele32.astype(np.int64)
            dt = np.int64
            sub_np = sub64; ins_np = ins64; dele_np = dele64

        if len(s) <= len(t):
            rows = s; colsb = t
            rowcost = dele
            cols = frombuffer(colsb, dtype=np.uint8).astype(np.intp)
            col_ins = ins_np[cols]
            smi = sub_np[:, cols] - col_ins
        else:
            rows = t; colsb = s
            rowcost = ins
            cols = frombuffer(colsb, dtype=np.uint8).astype(np.intp)
            col_ins = dele_np[cols]
            smi = sub_np.T[:, cols] - col_ins
        m = len(colsb)
        pref_m = int(col_ins.sum())
        smi_rows = [smi[r] for r in range(a)]

        buf_a = np.zeros(m + 1, dtype=dt)
        buf_b = np.empty(m + 1, dtype=dt)
        tmp = np.empty(m, dtype=dt)
        # (full, head=[:-1], tail=[1:]) views, swapped as a unit.
        prev = (buf_a, buf_a[:-1], buf_a[1:])
        cur = (buf_b, buf_b[:-1], buf_b[1:])

        cur0 = 0
        for rc in rows:
            d = rowcost[rc]
            cur0 += d
            cf, _ch, ct = cur
            _pf, ph, pt = prev
            cf[0] = cur0
            np_add(pt, d, out=ct)
            np_add(ph, smi_rows[rc], out=tmp)
            np_min(ct, tmp, out=ct)
            np_acc(cf, out=cf)
            prev, cur = cur, prev

        cost = int(prev[0][m]) + pref_m
        total += cost
        out.append(str(cost))

    out.append("total " + str(total))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
