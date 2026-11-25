import sys
from json import loads


def main():
    path = sys.argv[1]
    rates = None
    sign = {"credit": 1, "refund": 1, "debit": -1}
    acc = {}
    chc = {}
    chn = {}
    count = 0
    total = 0
    acc_get = acc.get
    chc_get = chc.get
    chn_get = chn.get

    with open(path, "r", encoding="utf-8", newline="\n", buffering=1 << 22) as f:
        first = f.readline()
        rates = loads(first)["rates"]
        for line in f:
            d = loads(line)
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
                if len(fr) == 1:
                    h = int(a[:i]) * 100 + int(fr) * 10
                else:
                    h = int(a[:i]) * 100 + int(fr)
            usd = (h * rates[d["currency"]]) // 1000000
            if t == "debit":
                usd = -usd
            count += 1
            total += usd
            k = d["account"]
            acc[k] = acc_get(k, 0) + usd
            c = d["meta"]["channel"]
            chc[c] = chc_get(c, 0) + 1
            chn[c] = chn_get(c, 0) + usd

    out = ["counted %d" % count, "net %d" % total]
    for c in sorted(chc):
        out.append("channel %s %d %d" % (c, chc[c], chn[c]))
    top = sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for k, v in top:
        out.append("account %s %d" % (k, v))
    sys.stdout.write("\n".join(out) + "\n")


main()
