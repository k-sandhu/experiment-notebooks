import sys
import json

import numpy as np


def main():
    path = sys.argv[1]
    data = open(path, "rb").read()
    rates = json.loads(data[: data.find(b"\n") + 1])["rates"]
    loads = json.loads
    tc_map = {"credit": 1, "debit": 2, "refund": 3}

    hv = []  # amount in integer hundredths
    rr = []  # exchange rate (millionths of USD per unit)
    tc = []  # type code: 1 credit, 2 debit, 3 refund
    ch = []  # channel names
    ac = []  # account ids
    hv_a = hv.append
    rr_a = rr.append
    tc_a = tc.append
    ch_a = ch.append
    ac_a = ac.append

    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    n = len(lines)
    loads_map = map
    CH = 65536
    i = 1  # skip the rates line
    while i < n:
        j = i + CH if i + CH < n else n
        for o in loads_map(loads, lines[i:j]):
            typ = o["type"]
            if typ == "void" or "test" in o["tags"]:
                continue
            s = o["amount"]
            p = s.find(".")
            if p < 0:
                h = int(s) * 100
            else:
                h = int(s.replace(".", ""))
                if len(s) - p == 2:  # one fractional digit
                    h *= 10
            hv_a(h)
            rr_a(rates[o["currency"]])
            tc_a(tc_map[typ])
            ch_a(o["meta"]["channel"])
            ac_a(o["account"])
        i = j

    # ---- vectorized conversion and aggregation ----
    usd = np.array(hv, np.int64) * np.array(rr, np.int64) // 1000000
    signed = np.where(np.array(tc, np.int64) == 2, -usd, usd)
    N = len(hv)
    T = int(signed.sum())

    def group(names):
        """names: numpy str array (counted lines only, in line order).
        Returns (uniq, counts, nets) with names ascending."""
        uniq, inv = np.unique(names, return_inverse=True)
        inv = np.asarray(inv).ravel()
        ordv = np.argsort(inv, kind="stable")
        gi = inv[ordv]
        starts = np.flatnonzero(np.r_[True, gi[1:] != gi[:-1]])
        cnt = np.bincount(inv, minlength=len(uniq))
        nets = np.zeros(len(uniq), np.int64)
        if len(starts):
            nets[gi[starts]] = np.add.reduceat(signed[ordv], starts)
        return uniq, cnt, nets

    uniq_c, cnt_c, nets_c = group(np.array(ch))
    uniq_a, _, nets_a = group(np.array(ac))

    out = ["counted %d" % N, "net %d" % T]
    for k in range(len(uniq_c)):
        out.append("channel %s %d %d" % (uniq_c[k], cnt_c[k], nets_c[k]))
    if len(uniq_a):
        order = np.lexsort((uniq_a, -nets_a))
        for k in order[: min(10, len(uniq_a))]:
            out.append("account %s %d" % (uniq_a[k], nets_a[k]))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


main()
