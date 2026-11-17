import re
import sys
from heapq import _heapify_max, _heapreplace_max


def main():
    with open(sys.argv[1], "rb") as source:
        sentences = re.split(rb"[.!?]+", source.read().lower())

    find_words = re.compile(rb"[a-z]+").findall
    entries = {}
    get_entry = entries.get
    word_count = 0
    pair_count = 0

    for sentence in sentences:
        tokens = find_words(sentence)
        size = len(tokens)
        if not size:
            continue

        word_count += size
        pair_count += size - 1

        token_iter = iter(tokens)
        token = next(token_iter)
        entry = get_entry(token)
        if entry is None:
            entry = (token, {})
            entries[token] = entry
        previous = entry[1]

        for token in token_iter:
            entry = get_entry(token)
            if entry is None:
                entry = (token, {})
                entries[token] = entry

            word, following = entry
            previous[word] = previous.get(word, 0) + 1
            previous = following

    del sentences, tokens

    distinct = 0
    best = []
    cutoff = 0

    for first, successors in entries.values():
        distinct += len(successors)
        for second, count in successors.items():
            if count < cutoff:
                continue

            candidate = (-count, first, second)
            if len(best) < 20:
                best.append(candidate)
                if len(best) == 20:
                    _heapify_max(best)
                    cutoff = -best[0][0]
            elif candidate < best[0]:
                _heapreplace_max(best, candidate)
                cutoff = -best[0][0]

    best.sort()
    output = [
        f"words {word_count}",
        f"pairs {pair_count}",
        f"distinct {distinct}",
    ]
    output.extend(
        f"{-negative_count} {first.decode('ascii')} {second.decode('ascii')}"
        for negative_count, first, second in best
    )
    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
