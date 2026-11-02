import re
import sys
from collections import Counter, defaultdict
from itertools import count, repeat
from operator import add, mul

CHUNK = 1 << 22
SHIFT = 32


def chunk_end(data, pos, n):
    end = pos + CHUNK
    if end >= n:
        return n
    cut = max(data.rfind(b".", pos, end), data.rfind(b"!", pos, end), data.rfind(b"?", pos, end))
    if cut >= 0:
        return cut + 1
    cuts = [c for c in (data.find(b".", end), data.find(b"!", end), data.find(b"?", end)) if c >= 0]
    return min(cuts) + 1 if cuts else n


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    n = len(data)
    tokens = re.compile(rb"[a-z]+|[.!?]").findall
    ids = defaultdict(count().__next__)
    for p in (b".", b"!", b"?"):
        ids[p]
    get = ids.__getitem__
    counts = Counter()
    update = counts.update
    mult = repeat(1 << SHIFT)
    pos = 0
    ntok = 0
    while pos < n:
        end = chunk_end(data, pos, n)
        toks = list(map(get, tokens(data[pos:end].lower())))
        pos = end
        ntok += len(toks)
        update(map(add, map(mul, toks, mult), toks[1:]))
    ends = (b".", b"!", b"?")
    words = ntok - sum(data.count(c) for c in ends)
    nw = len(ids)
    pop = counts.pop
    for e in range(3):
        base = e << SHIFT
        for w in range(nw):
            pop(base | w, None)
            pop((w << SHIFT) | e, None)
    total = sum(counts.values())
    distinct = len(counts)
    hist = Counter(counts.values())
    thr = 1
    seen = 0
    for c in sorted(hist, reverse=True):
        seen += hist[c]
        if seen >= 20:
            thr = c
            break
    names = list(ids)
    mask = (1 << SHIFT) - 1
    top = [(-c, names[k >> SHIFT], names[k & mask]) for k, c in counts.items() if c >= thr]
    top.sort()
    out = ["words %d" % words, "pairs %d" % total, "distinct %d" % distinct]
    for c, a, b in top[:20]:
        out.append("%d %s %s" % (-c, a.decode(), b.decode()))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
