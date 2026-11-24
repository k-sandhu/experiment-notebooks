import re
import sys
from collections import Counter
from itertools import islice

TOP = 20
WORD = re.compile(rb"[a-z]+")
SENTENCE_END = re.compile(rb"[.!?]")


def main():
    with open(sys.argv[1], "rb") as f:
        # bytes.lower() only touches A-Z, which is all the word rule needs.
        data = f.read().lower()

    words_total = 0
    pairs_total = 0
    counts = Counter()
    findall = WORD.findall
    for sentence in SENTENCE_END.split(data):
        ws = findall(sentence)
        n = len(ws)
        if n > 1:
            pairs_total += n - 1
            counts.update(zip(ws, islice(ws, 1, None)))
        words_total += n
    del data

    # Only the pairs whose count can reach the top 20 need sorting.
    best = counts.most_common(TOP)
    if len(best) == TOP:
        threshold = best[-1][1]
        candidates = [(c, k) for k, c in counts.items() if c >= threshold]
    else:
        candidates = [(c, k) for k, c in counts.items()]
    candidates.sort(key=lambda p: (-p[0], p[1]))

    out = [b"words %d\npairs %d\ndistinct %d\n" % (words_total, pairs_total, len(counts))]
    for c, (first, second) in candidates[:TOP]:
        out.append(b"%d %s %s\n" % (c, first, second))
    sys.stdout.buffer.write(b"".join(out))


if __name__ == "__main__":
    main()
