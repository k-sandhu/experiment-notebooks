import json
import sys

import numpy as np


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        rates = json.loads(f.readline())["rates"]

        loads = json.loads
        counted = 0
        net = 0
        channels = {}
        accounts = {}
        ch_get = channels.get
        ac_get = accounts.get

        for line in f:
            o = loads(line)
            ty = o["type"]
            if ty == "void":
                continue
            tags = o["tags"]
            if tags and "test" in tags:
                continue

            amt = o["amount"]
            dot = amt.find(".")
            if dot < 0:
                h = int(amt) * 100
            else:
                h = int(amt[:dot]) * 100
                fr = amt[dot + 1:]
                h += int(fr) * (10 if len(fr) == 1 else 1)

            usd = (h * rates[o["currency"]]) // 1000000
            if ty == "debit":
                usd = -usd

            counted += 1
            net += usd

            c = o["meta"]["channel"]
            e = ch_get(c)
            if e is None:
                channels[c] = [1, usd]
            else:
                e[0] += 1
                e[1] += usd

            a = o["account"]
            v = ac_get(a)
            accounts[a] = usd if v is None else v + usd

    out = ["counted %d\nnet %d\n" % (counted, net)]
    for name in sorted(channels):
        c, s = channels[name]
        out.append("channel %s %d %d\n" % (name, c, s))

    # Rank accounts by net desc, then id asc, using NumPy for the selection.
    n = len(accounts)
    if n:
        names = list(accounts.keys())
        sums = np.fromiter((accounts[k] for k in names), dtype=np.int64, count=n)
        if n > 10:
            thr = np.partition(sums, n - 10)[n - 10]
            part = np.flatnonzero(sums >= thr)
        else:
            part = np.arange(n)
        cand = sorted(part.tolist(), key=lambda i: (-int(sums[i]), names[i]))[:10]
        for i in cand:
            out.append("account %s %d\n" % (names[i], int(sums[i])))

    sys.stdout.buffer.write("".join(out).encode())


main()
