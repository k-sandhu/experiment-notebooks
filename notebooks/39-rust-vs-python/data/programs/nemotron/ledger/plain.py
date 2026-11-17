"""Ledger totaler: plain Python 3.13, standard library only."""

import json
import sys


def to_hundredths(amount: str) -> int:
    """Convert '12', '12.5', '12.05' to integer hundredths."""
    parts = amount.split(".")
    ip = int(parts[0])
    if len(parts) == 1:
        return ip * 100
    fp = parts[1]
    if len(fp) == 1:
        return ip * 100 + int(fp) * 10
    return ip * 100 + int(fp)


def main() -> None:
    path = sys.argv[1]
    with open(path, "rb") as f:
        rates = json.loads(f.readline())["rates"]
        loads = json.loads

        count = 0
        net = 0
        channels: dict[str, list[int]] = {}
        accounts: dict[str, int] = {}

        for line in f:
            if not line or line == b"\n":
                continue
            tx = loads(line)
            t = tx["type"]
            if t == "void":
                continue
            if "test" in tx["tags"]:
                continue

            rate = rates[tx["currency"]]
            usd = to_hundredths(tx["amount"]) * rate // 1_000_000
            signed = -usd if t == "debit" else usd

            count += 1
            net += signed

            name = tx["meta"]["channel"]
            ch = channels.get(name)
            if ch is None:
                channels[name] = [1, signed]
            else:
                ch[0] += 1
                ch[1] += signed

            aid = tx["account"]
            accounts[aid] = accounts.get(aid, 0) + signed

    out: list[str] = []
    out.append("counted %d" % count)
    out.append("net %d" % net)

    for name in sorted(channels):
        c, n = channels[name]
        out.append("channel %s %d %d" % (name, c, n))

    top = sorted(accounts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for aid, n in top:
        out.append("account %s %d" % (aid, n))

    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
