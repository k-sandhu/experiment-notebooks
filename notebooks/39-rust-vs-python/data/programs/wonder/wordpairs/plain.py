import re
import sys
from collections import Counter

_TOKEN_RE = re.compile(rb"[a-z]+|\.")
_TRANS = bytes.maketrans(b".!?", b"...")
_DOT = b"."


def main() -> None:
    if len(sys.argv) < 2:
        return
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    data = data.lower().translate(_TRANS)

    tokens = _TOKEN_RE.findall(data)
    total_words = len(tokens) - data.count(b".") if tokens else 0
    # data.count counts terminators (all mapped to '.'); but '.' in original also.
    # tokens include one token per terminator, so words = tokens - terminators.

    counter: Counter = Counter()
    if len(tokens) >= 2:
        counter.update(zip(tokens, tokens[1:]))

    # Remove pairs involving a sentence terminator.
    if counter:
        bad = [k for k in counter if k[0] is _DOT or k[1] is _DOT or k[0] == _DOT or k[1] == _DOT]
        # `is` fast path: findall may intern '.' tokens; equality covers all.
        for k in bad:
            del counter[k]

    distinct = len(counter)
    total_pairs = 0
    for c in counter.values():
        total_pairs += c

    out_lines = [
        b"words " + str(total_words).encode(),
        b"pairs " + str(total_pairs).encode(),
        b"distinct " + str(distinct).encode(),
    ]

    if distinct:
        if distinct <= 20:
            ranked = sorted((-c, w1, w2) for (w1, w2), c in counter.items())
            chosen = ranked[:20]
            for negc, w1, w2 in chosen:
                out_lines.append(str(-negc).encode() + b" " + w1 + b" " + w2)
        else:
            # Bucket by count to find the top-20 threshold without sorting all pairs.
            freq = Counter(counter.values())
            # distinct count values, sorted descending
            threshold = None
            above = 0  # pairs with count > current value
            cumulative = 0
            for cnt in sorted(freq, reverse=True):
                cumulative += freq[cnt]
                if cumulative >= 20:
                    threshold = cnt
                    above = cumulative - freq[cnt]
                    break
            greater = []  # (count, w1, w2) with count > threshold
            ties = []  # (w1, w2) with count == threshold
            for (w1, w2), c in counter.items():
                if c > threshold:
                    greater.append((c, w1, w2))
                elif c == threshold:
                    ties.append((w1, w2))
            need = 20 - len(greater)
            if need < len(ties):
                ties.sort()
                del ties[need:]
            ranked = [(-c, w1, w2) for c, w1, w2 in greater]
            ranked.extend(( -threshold, w1, w2) for w1, w2 in ties)
            ranked.sort()
            for negc, w1, w2 in ranked:
                out_lines.append(str(-negc).encode() + b" " + w1 + b" " + w2)

    sys.stdout.buffer.write(b"\n".join(out_lines) + b"\n")


if __name__ == "__main__":
    main()
