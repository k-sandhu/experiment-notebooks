import sys
import json
import heapq
from collections import defaultdict


def main():
    path = sys.argv[1]
    loads = json.loads

    counted = 0
    net = 0
    ch_count = defaultdict(int)
    ch_sum = defaultdict(int)
    acc_sum = defaultdict(int)

    with open(path, "rb") as f:
        first = f.readline()
        rates = loads(first)["rates"]

        for line in f:
            if len(line) < 3:
                continue
            t = loads(line)
            if t["type"] == "void":
                continue
            if "test" in t["tags"]:
                continue

            a, _, b = t["amount"].partition(".")
            hundredths = int(a) * 100 + int((b + "00")[:2])
            usd = hundredths * rates[t["currency"]] // 1000000

            if t["type"] == "debit":
                v = -usd
            else:
                v = usd

            counted += 1
            net += v
            ch = t["meta"]["channel"]
            ch_count[ch] += 1
            ch_sum[ch] += v
            acc_sum[t["account"]] += v

    out = ["counted %d" % counted, "net %d" % net]
    for ch in sorted(ch_count):
        out.append("channel %s %d %d" % (ch, ch_count[ch], ch_sum[ch]))
    top = heapq.nsmallest(10, acc_sum.items(), key=lambda kv: (-kv[1], kv[0]))
    for acc, v in top:
        out.append("account %s %d" % (acc, v))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
