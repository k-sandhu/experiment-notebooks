import sys
import json


def main():
    path = sys.argv[1]
    loads = json.loads
    counted = 0
    net = 0
    chan_count = {}
    chan_net = {}
    accounts = {}
    with open(path, "rb") as f:
        first = f.readline()
        if not first:
            sys.stdout.write("counted 0\nnet 0\n")
            return
        rates = loads(first)["rates"]
        for line in f:
            if not line.strip():
                continue
            d = loads(line)
            t = d["type"]
            if t == "void":
                continue
            if "test" in d["tags"]:
                continue
            s = d["amount"]
            dot = s.find(".")
            if dot < 0:
                hundredths = int(s) * 100
            elif dot == len(s) - 2:  # one fractional digit
                hundredths = int(s[:dot]) * 100 + int(s[dot + 1:]) * 10
            else:  # two fractional digits
                hundredths = int(s[:dot]) * 100 + int(s[dot + 1:])
            usd = (hundredths * rates[d["currency"]]) // 1000000
            if t == "debit":
                usd = -usd
            counted += 1
            net += usd
            ch = d["meta"]["channel"]
            chan_count[ch] = chan_count.get(ch, 0) + 1
            chan_net[ch] = chan_net.get(ch, 0) + usd
            acc = d["account"]
            accounts[acc] = accounts.get(acc, 0) + usd

    out = [f"counted {counted}", f"net {net}"]
    for ch in sorted(chan_count, key=lambda s: s.encode("utf-8", "surrogatepass")):
        out.append(f"channel {ch} {chan_count[ch]} {chan_net[ch]}")
    top = sorted(
        accounts.items(),
        key=lambda kv: (-kv[1], kv[0].encode("utf-8", "surrogatepass")),
    )[:10]
    for acc, v in top:
        out.append(f"account {acc} {v}")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
