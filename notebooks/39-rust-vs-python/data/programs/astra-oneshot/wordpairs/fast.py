import sys
import re
import heapq
from collections import Counter, defaultdict
from itertools import count


def emit(word_count, pair_count, distinct_count, rows):
    lines = [
        f"words {word_count}",
        f"pairs {pair_count}",
        f"distinct {distinct_count}",
    ]
    lines.extend(
        f"{frequency} {first.decode('ascii')} {second.decode('ascii')}"
        for frequency, first, second in rows
    )
    sys.stdout.write("\n".join(lines) + "\n")


def main():
    translation = bytes(
        c + 32 if 65 <= c <= 90
        else c if 97 <= c <= 122
        else 46 if c in (33, 46, 63)
        else 32
        for c in range(256)
    )

    with open(sys.argv[1], "rb") as source:
        data = source.read().translate(translation)

    if len(data) <= 131072:
        tokens = data.replace(b".", b" . ").split()
        word_count = len(tokens) - tokens.count(b".")
        frequencies = Counter(
            (first, second)
            for first, second in zip(tokens, tokens[1:])
            if first != b"." and second != b"."
        )
        best = heapq.nsmallest(
            20,
            frequencies.items(),
            key=lambda item: (-item[1], item[0]),
        )
        emit(
            word_count,
            sum(frequencies.values()),
            len(frequencies),
            [(frequency, pair[0], pair[1]) for pair, frequency in best],
        )
        return

    import numpy as np

    vocabulary = defaultdict(count(1).__next__)
    vocabulary[b"."] = 0
    get_id = vocabulary.__getitem__
    find_separator = re.compile(rb"[ .]").search

    chunks = []
    word_count = 0
    position = 0
    size = len(data)
    block_size = 4 * 1024 * 1024

    while position < size:
        end = min(position + block_size, size)
        if end < size:
            match = find_separator(data, end)
            end = match.end() if match is not None else size

        tokens = data[position:end].replace(b".", b" . ").split()
        block_ids = np.fromiter(
            map(get_id, tokens),
            dtype=np.uint32,
            count=len(tokens),
        )
        word_count += int(np.count_nonzero(block_ids))
        chunks.append(block_ids)
        del tokens, block_ids
        position = end

    del data, get_id

    if word_count < 2:
        emit(word_count, 0, 0, [])
        return

    ids = np.concatenate(chunks)
    del chunks

    if word_count == ids.size:
        valid = None
        pair_count = ids.size - 1
    else:
        valid = ids[:-1] != 0
        valid &= ids[1:] != 0
        pair_count = int(np.count_nonzero(valid))
        if pair_count == 0:
            emit(word_count, 0, 0, [])
            return

    names = sorted(vocabulary)
    ranks = np.empty(len(names), dtype=np.uint32)
    for rank, word in enumerate(names):
        ranks[vocabulary[word]] = rank
    del vocabulary

    ids = ranks[ids]
    del ranks

    if valid is None:
        keys = ids[:-1].astype(np.uint64)
        keys <<= 32
        keys |= ids[1:]
    else:
        keys = ids[:-1][valid].astype(np.uint64)
        keys <<= 32
        keys |= ids[1:][valid]

    del ids, valid
    keys.sort()

    boundaries = np.empty(pair_count + 1, dtype=np.bool_)
    boundaries[0] = True
    boundaries[-1] = True
    np.not_equal(keys[1:], keys[:-1], out=boundaries[1:-1])
    starts = np.flatnonzero(boundaries)
    del boundaries

    frequencies = np.diff(starts)
    distinct_count = frequencies.size

    if distinct_count <= 20:
        selected = list(range(distinct_count))
    else:
        cutoff_index = distinct_count - 20
        cutoff = int(np.partition(frequencies, cutoff_index)[cutoff_index])
        selected = np.flatnonzero(frequencies > cutoff).tolist()
        needed = 20 - len(selected)

        for begin in range(0, distinct_count, 262144):
            matches = np.flatnonzero(
                frequencies[begin:begin + 262144] == cutoff
            )[:needed]
            selected.extend((matches + begin).tolist())
            needed -= matches.size
            if needed == 0:
                break

    selected.sort(
        key=lambda index: (
            -int(frequencies[index]),
            int(keys[starts[index]]),
        )
    )

    rows = []
    for index in selected:
        key = int(keys[starts[index]])
        rows.append((
            int(frequencies[index]),
            names[key >> 32],
            names[key & 0xFFFFFFFF],
        ))

    emit(word_count, pair_count, distinct_count, rows)


if __name__ == "__main__":
    main()
