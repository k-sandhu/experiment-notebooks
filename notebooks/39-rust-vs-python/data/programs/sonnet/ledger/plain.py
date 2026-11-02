import sys
import gc
import json

CHUNK = 4 << 20


def main():
    gc.disable()
    path = sys.argv[1]
    loads = json.loads
    rates = None
    count = 0
    net = 0
    channels = {}
    accounts = {}
    acc_get = accounts.get
    chan_get = channels.get
    sign = {"credit": 1, "refund": 1, "debit": -1}
    sign_get = sign.get

    with open(path, "rb") as f:
        tail = b""
        eof = False
        while not eof:
            data = f.read(CHUNK)
            if not data:
                eof = True
                block = tail
                tail = b""
            else:
                data = tail + data
                cut = data.rfind(b"\n")
                if cut < 0:
                    tail = data
                    continue
                block = data[:cut]
                tail = data[cut + 1:]
            block = block.strip()
            if not block:
                continue
            if rates is None:
                nl = block.find(b"\n")
                if nl < 0:
                    first, block = block, b""
                else:
                    first, block = block[:nl], block[nl + 1:]
                rates = loads(first)["rates"]
                if not block:
                    continue
            objs = loads(b"[" + block.replace(b"\n", b",") + b"]")
            for d in objs:
                s = sign_get(d["type"])
                if s is None or "test" in d["tags"]:
                    continue
                a = d["amount"]
                i = a.find(".")
                if i < 0:
                    h = int(a) * 100
                else:
                    n = len(a) - i - 1
                    h = int(a[:i] + a[i + 1:])
                    if n == 1:
                        h *= 10
                    elif n == 0:
                        h *= 100
                v = h * rates[d["currency"]] // 1000000
                if s < 0:
                    v = -v
                count += 1
                net += v
                acc = d["account"]
                accounts[acc] = acc_get(acc, 0) + v
                ch = d["meta"]["channel"]
                e = chan_get(ch)
                if e is None:
                    channels[ch] = [1, v]
                else:
                    e[0] += 1
                    e[1] += v

    out = ["counted %d" % count, "net %d" % net]
    for name in sorted(channels, key=lambda s: s.encode("utf-8")):
        c, v = channels[name]
        out.append("channel %s %d %d" % (name, c, v))
    top = sorted(accounts.items(), key=lambda kv: (-kv[1], kv[0].encode("utf-8")))[:10]
    for name, v in top:
        out.append("account %s %d" % (name, v))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))


main()
