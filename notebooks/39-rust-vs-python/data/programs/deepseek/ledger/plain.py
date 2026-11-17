import json
import sys


def main():
    path = sys.argv[1]
    f = open(path, "rb")
    loads = json.loads

    rates = loads(f.readline())["rates"]

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
        if "test" in tags:
            continue

        amt = o["amount"]
        dot = amt.find(".")
        if dot < 0:
            h = int(amt) * 100
        else:
            h = int(amt[:dot]) * 100
            frac = amt[dot + 1:]
            if len(frac) == 1:
                h += int(frac) * 10
            else:
                h += int(frac)

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
        if v is None:
            accounts[a] = usd
        else:
            accounts[a] = v + usd

    out = ["counted %d\nnet %d\n" % (counted, net)]
    for name in sorted(channels):
        c, n = channels[name]
        out.append("channel %s %d %d\n" % (name, c, n))
    top = sorted(accounts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for name, n in top:
        out.append("account %s %d\n" % (name, n))
    sys.stdout.buffer.write("".join(out).encode())


main()
