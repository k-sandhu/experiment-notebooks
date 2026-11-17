import sys
import heapq
from collections import Counter
from itertools import islice

# Byte translation: A-Z -> a-z, . ! ? -> '.', every other non-letter -> space.
_tbl = bytearray(256)
for _i in range(256):
    if 65 <= _i <= 90:
        _tbl[_i] = _i + 32
    elif 97 <= _i <= 122:
        _tbl[_i] = _i
    elif _i in (46, 33, 63):
        _tbl[_i] = 46
    else:
        _tbl[_i] = 32
TABLE = bytes(_tbl)
SENT = b"\x01"


def main():
    data = open(sys.argv[1], "rb").read()
    t = data.translate(TABLE)
    del data
    nsent = t.count(b".")
    if nsent:
        # Turn each sentence end into a standalone sentinel token, so that
        # adjacent-token pairs never cross a sentence boundary.
        t = t.replace(b".", b" \x01 ")
    toks = t.split()
    del t

    words = len(toks) - nsent
    if words == 0:
        sys.stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return

    # Counter.update uses the C _count_elements accelerator.
    ntoks = len(toks)
    counter = Counter(zip(toks, islice(toks, 1, None)))

    removed = 0
    if nsent:
        # Drop every pair touching the sentinel. Those keys are exactly
        # (SENT, w) and (w, SENT) for w in the vocabulary.
        pop = counter.pop
        removed += pop((SENT, SENT), 0)
        for w in set(toks):
            removed += pop((SENT, w), 0)
            removed += pop((w, SENT), 0)
    del toks

    # The Counter was fed ntoks - 1 adjacent pairs in total.
    total_pairs = ntoks - 1 - removed
    distinct = len(counter)

    out = [f"words {words}\n", f"pairs {total_pairs}\n", f"distinct {distinct}\n"]
    if distinct:
        if distinct <= 20:
            chosen = sorted(
                ((c, k) for k, c in counter.items()),
                key=lambda x: (-x[0], x[1]),
            )
        else:
            thr = heapq.nlargest(20, counter.values())[-1]
            gt = [(c, k) for k, c in counter.items() if c > thr]
            eq = [k for k, c in counter.items() if c == thr]
            need = 20 - len(gt)
            chosen = gt + [(thr, k) for k in heapq.nsmallest(need, eq)]
            chosen.sort(key=lambda x: (-x[0], x[1]))
        for c, (w1, w2) in chosen:
            out.append(f"{c} {w1.decode()} {w2.decode()}\n")
    sys.stdout.buffer.write("".join(out).encode())


main()
