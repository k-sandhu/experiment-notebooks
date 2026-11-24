import heapq
import json
import sys


def main():
    loads = json.loads
    with open(sys.argv[1], encoding="utf-8") as f:
        rates = loads(f.readline())["rates"]

        count = 0
        net = 0
        channels = {}  # name -> [count, sum]
        accounts = {}  # id -> sum

        for line in f:
            t = loads(line)
            kind = t["type"]
            if kind == "void" or "test" in t["tags"]:
                continue

            amount = t["amount"]
            whole, _, frac = amount.partition(".")
            hundredths = int(whole) * 100 + (int(frac.ljust(2, "0")) if frac else 0)
            usd = hundredths * rates[t["currency"]] // 1000000
            value = -usd if kind == "debit" else usd

            count += 1
            net += value

            name = t["meta"]["channel"]
            entry = channels.get(name)
            if entry is None:
                channels[name] = [1, value]
            else:
                entry[0] += 1
                entry[1] += value

            account = t["account"]
            accounts[account] = accounts.get(account, 0) + value

    out = [f"counted {count}", f"net {net}"]
    for name in sorted(channels):
        c, s = channels[name]
        out.append(f"channel {name} {c} {s}")
    for account, s in heapq.nsmallest(10, accounts.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(f"account {account} {s}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
