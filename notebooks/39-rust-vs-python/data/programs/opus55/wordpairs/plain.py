import sys
from collections import Counter
from heapq import nlargest
from itertools import compress, islice, repeat
from operator import and_, ne

CHUNK = 1 << 22


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()

    # Lower-case the letters, turn every sentence end into "." and every other
    # character into a space, so that str.split() yields words and "." tokens.
    table = bytearray(b" " * 256)
    for c in range(ord("a"), ord("z") + 1):
        table[c] = c
        table[c - 32] = c
    for c in b".!?":
        table[c] = ord(".")
    data = data.translate(table)
    sentences = data.count(b".")
    text = data.replace(b".", b" . ").decode("ascii")
    del data

    counts = Counter()
    update = counts.update
    n = len(text)
    ntokens = 0
    prev = None
    pos = 0
    # Work in chunks cut at a space, so the token lists stay small.
    while pos < n:
        end = text.find(" ", pos + CHUNK)
        if end < 0:
            end = n
        toks = text[pos:end].split()
        if toks:
            ntokens += len(toks)
            # Only count pairs where neither token is a sentence end.
            ok = list(map(ne, toks, repeat(".")))
            update(compress(zip(toks, islice(toks, 1, None)), map(and_, ok, islice(ok, 1, None))))
            if prev is not None and prev != "." and toks[0] != ".":
                counts[prev, toks[0]] += 1
            prev = toks[-1]
        pos = end

    out = [
        f"words {ntokens - sentences}",
        f"pairs {sum(counts.values())}",
        f"distinct {len(counts)}",
    ]
    if counts:
        threshold = nlargest(20, counts.values())[-1]
        top = [(-c, a, b) for (a, b), c in counts.items() if c >= threshold]
        top.sort()
        out.extend(f"{-c} {a} {b}" for c, a, b in top[:20])
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
