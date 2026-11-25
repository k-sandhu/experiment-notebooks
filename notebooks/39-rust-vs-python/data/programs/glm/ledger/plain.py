import sys
import json


def process(lines, rates, ch, acc):
    loads = json.loads
    n = 0
    t = 0
    for o in map(loads, lines):
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
        h = h * rates[o["currency"]] // 1000000
        if typ == "debit":
            h = -h
        n += 1
        t += h
        c = o["meta"]["channel"]
        e = ch.get(c)
        if e is None:
            ch[c] = [1, h]
        else:
            e[0] += 1
            e[1] += h
        a = o["account"]
        acc[a] = acc.get(a, 0) + h
    return n, t


def main():
    path = sys.argv[1]
    rates = json.loads(open(path, "rb").readline())["rates"]
    ch = {}  # channel -> [count, net]
    acc = {}  # account -> net
    n = 0
    t = 0
    f = open(path, "rb")
    f.readline()  # rates line
    tail = b""
    read = f.read
    while True:
        block = read(1 << 23)
        if not block:
            break
        lines = (tail + block).split(b"\n")
        tail = lines.pop()
        dn, dt = process(lines, rates, ch, acc)
        n += dn
        t += dt
    if tail:
        dn, dt = process([tail], rates, ch, acc)
        n += dn
        t += dt
    out = ["counted %d" % n, "net %d" % t]
    for name in sorted(ch):
        c, net = ch[name]
        out.append("channel %s %d %d" % (name, c, net))
    top = sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for name, net in top:
        out.append("account %s %d" % (name, net))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


main()
