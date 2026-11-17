import sys
import gc
import json
import re
from collections import defaultdict
from heapq import nsmallest

CHUNK = 1 << 18


def main():
    gc.disable()
    path = sys.argv[1]
    scan = json.JSONDecoder().scan_once
    skip_ws = re.compile(r"[ \t\r\n]*").match

    acc = defaultdict(int)
    ccount = defaultdict(int)
    cnet = defaultdict(int)

    with open(path, "rb") as f:
        readline = f.readline
        read = f.read

        first = readline()
        while first and not first.strip():
            first = readline()
        if first:
            rates = json.loads(first)["rates"]
        else:
            rates = {}

        while True:
            block = read(CHUNK)
            if not block:
                break
            tail = readline()
            if tail:
                block += tail
            text = block.decode("utf-8")
            n = len(text)
            idx = 0
            while idx < n:
                try:
                    d, idx = scan(text, idx)
                except StopIteration:
                    idx = skip_ws(text, idx).end()
                    if idx >= n:
                        break
                    d, idx = scan(text, idx)
                idx += 1

                t = d["type"]
                if t == "void" or "test" in d["tags"]:
                    continue

                a = d["amount"]
                h = int(a.replace(".", ""))
                if a[-3:-2] != ".":
                    if a[-2:-1] == ".":
                        h *= 10
                    else:
                        h *= 100

                v = h * rates[d["currency"]] // 1000000
                if t == "debit":
                    v = -v

                c = d["meta"]["channel"]
                ccount[c] += 1
                cnet[c] += v
                acc[d["account"]] += v

    out = []
    out.append("counted %d" % sum(ccount.values()))
    out.append("net %d" % sum(cnet.values()))
    for name in sorted(ccount):
        out.append("channel %s %d %d" % (name, ccount[name], cnet[name]))
    top = nsmallest(10, acc.items(), key=lambda kv: (-kv[1], kv[0]))
    for name, net in top:
        out.append("account %s %d" % (name, net))
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
