import sys
from collections import Counter
from itertools import islice


def main():
    data = open(sys.argv[1], "rb").read()

    # Translate bytes: A-Z -> a-z, '.' '!' '?' -> '\n' (sentence end),
    # every other byte -> ' ' (separator, incl. original newlines).
    table = bytearray(b" " * 256)
    for c in range(65, 91):
        table[c] = c + 32
    for c in range(97, 123):
        table[c] = c
    table[ord(".")] = ord("\n")
    table[ord("!")] = ord("\n")
    table[ord("?")] = ord("\n")
    t = data.translate(bytes(table))
    del data

    counts = Counter()
    total_words = 0
    total_pairs = 0
    update = counts.update
    for sent in t.split(b"\n"):
        ws = sent.split()
        n = len(ws)
        if n > 1:
            total_words += n
            total_pairs += n - 1
            update(zip(ws, islice(ws, 1, None)))
        else:
            total_words += n

    distinct = len(counts)
    out = sys.stdout.buffer

    def emit(items):
        parts = [b"words %d\npairs %d\ndistinct %d\n" % (total_words, total_pairs, distinct)]
        for (a, b), c in items:
            parts.append(b"%d %s %s\n" % (c, a, b))
        out.write(b"".join(parts))

    if distinct <= 20:
        emit(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1])))
        return

    # 20th largest count; only pairs with count >= it can be in the top 20.
    import heapq

    threshold = heapq.nlargest(20, counts.values())[-1]
    cand = [(c, a, b) for (a, b), c in counts.items() if c >= threshold]
    # count desc, then first word asc, then second word asc
    cand.sort(key=lambda x: (-x[0], x[1], x[2]))
    emit([((a, b), c) for c, a, b in cand[:20]])


main()
