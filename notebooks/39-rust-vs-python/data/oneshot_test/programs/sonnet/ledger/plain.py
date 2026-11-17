import sys
import json
from itertools import islice


def main():
    path = sys.argv[1]
    loads = json.loads
    total_n = 0
    total_net = 0
    ch_cnt = {}
    ch_net = {}
    acc = {}

    with open(path, "rb", buffering=1 << 20) as f:
        rates = loads(f.readline())["rates"]
        CH = 20000
        while True:
            lines = list(islice(f, CH))
            if not lines:
                break
            objs = loads(b"[" + b",".join(lines) + b"]")
            for d in objs:
                t = d["type"]
                if t == "void":
                    continue
                if "test" in d["tags"]:
                    continue
                a = d["amount"]
                i = a.find(".")
                if i < 0:
                    h = int(a) * 100
                else:
                    fr = a[i + 1:]
                    h = int(a[:i]) * 100 + (int(fr) * 10 if len(fr) == 1 else int(fr))
                usd = h * rates[d["currency"]] // 1000000
                if t == "debit":
                    usd = -usd
                total_n += 1
                total_net += usd
                c = d["meta"]["channel"]
                if c in ch_cnt:
                    ch_cnt[c] += 1
                    ch_net[c] += usd
                else:
                    ch_cnt[c] = 1
                    ch_net[c] = usd
                k = d["account"]
                if k in acc:
                    acc[k] += usd
                else:
                    acc[k] = usd

    out = ["counted %d" % total_n, "net %d" % total_net]
    for c in sorted(ch_cnt):
        out.append("channel %s %d %d" % (c, ch_cnt[c], ch_net[c]))
    top = sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for k, v in top:
        out.append("account %s %d" % (k, v))
    sys.stdout.write("\n".join(out) + "\n")


main()
