import json
import sys


def main():
    path = sys.argv[1]
    scan = json.JSONDecoder().scan_once  # C scanner; skips json.loads' regex/whitespace overhead
    loads = json.loads

    with open(path, encoding="utf-8", newline="\n", buffering=1 << 20) as f:
        rates = loads(f.readline())["rates"]
        accounts = {}
        chan_count = {}
        chan_net = {}
        counted = 0
        net = 0
        acc_get = accounts.get
        cnt_get = chan_count.get
        cnet_get = chan_net.get

        for line in f:
            try:
                d = scan(line, 0)[0]
            except StopIteration:
                d = loads(line)  # leading whitespace
            t = d["type"]
            if t == "void" or "test" in d["tags"]:
                continue
            a = d["amount"]
            dot = a.find(".")
            if dot < 0:
                h = int(a) * 100
            elif dot == len(a) - 2:
                h = int(a[:dot] + a[dot + 1:]) * 10
            else:
                h = int(a[:dot] + a[dot + 1:])
            v = h * rates[d["currency"]] // 1000000
            if t == "debit":
                v = -v
            counted += 1
            net += v
            acct = d["account"]
            accounts[acct] = acc_get(acct, 0) + v
            ch = d["meta"]["channel"]
            chan_count[ch] = cnt_get(ch, 0) + 1
            chan_net[ch] = cnet_get(ch, 0) + v

    out = [f"counted {counted}", f"net {net}"]
    for ch in sorted(chan_count, key=lambda s: s.encode()):
        out.append(f"channel {ch} {chan_count[ch]} {chan_net[ch]}")
    top = sorted(accounts.items(), key=lambda kv: (-kv[1], kv[0].encode()))[:10]
    for acct, v in top:
        out.append(f"account {acct} {v}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
