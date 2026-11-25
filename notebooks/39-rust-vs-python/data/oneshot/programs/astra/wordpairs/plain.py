import sys
import re
from bisect import insort


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read().lower()

    tokenize = re.compile(rb"[a-z]+|[.!?]+").findall
    find_separator = re.compile(rb"[^a-z]").search

    word_ids = {}
    get_id = word_ids.get
    vocabulary = []
    counts = []

    previous = None
    total_words = 0
    nonempty_sentences = 0

    size = len(data)
    start = 0
    chunk_size = 4 * 1024 * 1024

    while start < size:
        end = min(start + chunk_size, size)
        if end < size:
            separator = find_separator(data, end)
            end = separator.start() if separator is not None else size

        tokens = tokenize(data, start, end)
        total_words += len(tokens)

        for token in tokens:
            if token[0] < 97:
                total_words -= 1
                previous = None
                continue

            word_id = get_id(token)
            if word_id is None:
                word_id = len(vocabulary)
                word_ids[token] = word_id
                vocabulary.append(token)
                counts.append({})

            if previous is None:
                nonempty_sentences += 1
            else:
                previous[word_id] = previous.get(word_id, 0) + 1

            previous = counts[word_id]

        del tokens
        start = end

    del data
    del get_id
    del word_ids

    total_pairs = total_words - nonempty_sentences
    distinct_pairs = sum(map(len, counts))

    best = []
    cutoff = 0
    worst_first = b""

    for first_id, following in enumerate(counts):
        first = vocabulary[first_id]
        for second_id, count in following.items():
            if count < cutoff:
                continue
            if count == cutoff and first > worst_first:
                continue

            candidate = (-count, first, vocabulary[second_id])

            if len(best) < 20:
                insort(best, candidate)
                if len(best) == 20:
                    cutoff = -best[-1][0]
                    worst_first = best[-1][1]
            elif candidate < best[-1]:
                insort(best, candidate)
                best.pop()
                cutoff = -best[-1][0]
                worst_first = best[-1][1]

    output = [
        b"words %d\n" % total_words,
        b"pairs %d\n" % total_pairs,
        b"distinct %d\n" % distinct_pairs,
    ]
    for negative_count, first, second in best:
        output.append(b"%d %s %s\n" % (-negative_count, first, second))

    sys.stdout.buffer.write(b"".join(output))


if __name__ == "__main__":
    main()
