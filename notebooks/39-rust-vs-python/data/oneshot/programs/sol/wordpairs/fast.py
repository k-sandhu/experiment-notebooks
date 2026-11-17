import sys
import re
import heapq


TOKEN_RE = re.compile(rb"[a-z]+|[.!?]+")
SEPARATOR_RE = re.compile(rb"[^a-z]")


class WordIds(dict):
    def __missing__(self, word):
        if word[0] < 97:
            return 0
        value = len(self) - 2
        self[word] = value
        return value


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read().lower()

    if len(data) < 262144:
        frequencies = {}
        previous = None
        word_count = 0
        pair_count = 0

        for token in TOKEN_RE.findall(data):
            if token[0] < 97:
                previous = None
                continue

            word_count += 1
            if previous is not None:
                pair = (previous, token)
                frequencies[pair] = frequencies.get(pair, 0) + 1
                pair_count += 1
            previous = token

        top = heapq.nsmallest(
            20,
            frequencies.items(),
            key=lambda item: (-item[1], item[0]),
        )
        lines = [
            f"words {word_count}",
            f"pairs {pair_count}",
            f"distinct {len(frequencies)}",
        ]
        lines.extend(
            f"{count} {first.decode('ascii')} {second.decode('ascii')}"
            for (first, second), count in top
        )
        sys.stdout.write("\n".join(lines) + "\n")
        return

    import numpy as np

    size = len(data)
    dtype = np.uint32 if size < 4294967296 else np.uint64
    vocabulary = WordIds({b".": 0, b"!": 0, b"?": 0})
    lookup = vocabulary.__getitem__
    parts = []
    begin = 0

    while begin < size:
        end = min(begin + 1048576, size)
        if end < size:
            boundary = SEPARATOR_RE.search(data, end)
            end = boundary.start() if boundary is not None else size

        tokens = TOKEN_RE.findall(data, begin, end)
        parts.append(
            np.fromiter(map(lookup, tokens), dtype=dtype, count=len(tokens))
        )
        del tokens
        begin = end

    del data, lookup

    ids = np.concatenate(parts)
    del parts

    word_count = int(np.count_nonzero(ids))
    valid = (ids[:-1] != 0) & (ids[1:] != 0)
    pair_count = int(np.count_nonzero(valid))

    if pair_count == 0:
        sys.stdout.write(f"words {word_count}\npairs 0\ndistinct 0\n")
        return

    words = sorted(vocabulary)[3:]
    base = len(words) + 1
    ranks = np.empty(base, dtype=dtype)
    ranks[0] = 0

    for rank, word in enumerate(words, 1):
        ranks[vocabulary[word]] = rank

    ids = ranks[ids]
    del ranks, vocabulary

    keys = ids[:-1][valid].astype(np.uint64)
    keys *= base
    keys += ids[1:][valid]
    del ids, valid

    keys.sort()

    changes = np.empty(pair_count, dtype=np.bool_)
    changes[0] = True
    np.not_equal(keys[1:], keys[:-1], out=changes[1:])
    starts = np.flatnonzero(changes)
    del changes

    counts = np.diff(starts, append=pair_count)
    distinct = len(starts)

    if distinct <= 20:
        selected = list(range(distinct))
    else:
        threshold = int(np.partition(counts, distinct - 20)[distinct - 20])
        selected = np.flatnonzero(counts > threshold).tolist()

        for begin in range(0, distinct, 65536):
            tied = np.flatnonzero(counts[begin:begin + 65536] == threshold)
            needed = 20 - len(selected)
            selected.extend((tied[:needed] + begin).tolist())
            if len(selected) == 20:
                break

    selected.sort(
        key=lambda index: (-int(counts[index]), int(keys[starts[index]]))
    )

    lines = [
        f"words {word_count}",
        f"pairs {pair_count}",
        f"distinct {distinct}",
    ]
    for index in selected:
        first, second = divmod(int(keys[starts[index]]), base)
        lines.append(
            f"{int(counts[index])} "
            f"{words[first - 1].decode('ascii')} "
            f"{words[second - 1].decode('ascii')}"
        )

    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
