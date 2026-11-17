import json
import sys


def main() -> None:
    with open(sys.argv[1], "rb") as f:
        lines = f.read().decode("utf-8").split("\n")

    rates = json.loads(lines[0])["rates"]
    loads = json.loads

    counted = 0
    net = 0
    channels = {}  # name -> [count, net]
    accounts = {}  # account -> net

    for line in lines[1:]:
        if not line:
            continue
        tx = loads(line)
        kind = tx["type"]
        if kind == "void" or "test" in tx["tags"]:
            continue

        amount = tx["amount"]
        dot = amount.find(".")
        if dot < 0:
            hundredths = int(amount) * 100
        else:
            frac = amount[dot + 1:]
            hundredths = int(amount[:dot]) * 100 + int(frac) * (10 if len(frac) == 1 else 1)

        usd = hundredths * rates[tx["currency"]] // 1_000_000
        if kind == "debit":
            usd = -usd

        counted += 1
        net += usd

        channel = tx["meta"]["channel"]
        entry = channels.get(channel)
        if entry is None:
            channels[channel] = [1, usd]
        else:
            entry[0] += 1
            entry[1] += usd

        account = tx["account"]
        accounts[account] = accounts.get(account, 0) + usd

    out = [f"counted {counted}", f"net {net}"]
    for name in sorted(channels):
        count, total = channels[name]
        out.append(f"channel {name} {count} {total}")
    top = sorted(accounts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for account, total in top:
        out.append(f"account {account} {total}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


if __name__ == "__main__":
    main()
