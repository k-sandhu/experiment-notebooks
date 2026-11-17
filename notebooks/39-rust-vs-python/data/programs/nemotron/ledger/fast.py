"""Ledger totaler: fast Python 3.13.

NumPy is allowed but does not help here: the bottleneck is the per-line stateful
JSON parse (keys appear in any order with nested decoys), which json.loads does
in C.  This version minimizes interpreter overhead instead: one big read, local
bindings, inlined amount conversion, and fewer dict lookups.
"""

import json
import sys


def main() -> None:
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()

    loads = json.loads
    header, rest = data.split(b"\n", 1)
    rates = loads(header)["rates"]

    count = 0
    net = 0
    channels: dict = {}
    accounts: dict = {}

    for line in rest.split(b"\n"):
        if not line:
            continue
        tx = loads(line)
        t = tx["type"]
        if t == "void" or "test" in tx["tags"]:
            continue

        rate = rates[tx["currency"]]
        amount = tx["amount"]
        dot = amount.find(".")
        if dot == -1:
            usd = int(amount) * 100 * rate // 1_000_000
        else:
            ip = int(amount[:dot])
            fp = amount[dot + 1:]
            h = ip * 100 + (int(fp) * 10 if len(fp) == 1 else int(fp))
            usd = h * rate // 1_000_000
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
        prev = accounts.get(aid)
        if prev is None:
            accounts[aid] = signed
        else:
            accounts[aid] = prev + signed

    out = ["counted %d" % count, "net %d" % net]
    for name in sorted(channels):
        c, n = channels[name]
        out.append("channel %s %d %d" % (name, c, n))
    top = sorted(accounts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for aid, n in top:
        out.append("account %s %d" % (aid, n))

    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
