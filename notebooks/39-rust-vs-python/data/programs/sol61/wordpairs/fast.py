"""Count word pairs with compact NumPy arrays and an in-place numeric sort."""

import itertools
import os
import re
import sys

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np


TABLE = bytes(
    c + 32 if 65 <= c <= 90 else c if 97 <= c <= 122
    else 46 if c in (46, 33, 63) else 32
    for c in range(256)
)
TOKENS = re.compile(rb"[a-z]+|\.")
BLOCK = 4 * 1024 * 1024
MASK = (1 << 32) - 1
PACKED_LIMIT = 1 << 32
WIDE_PAIR = np.dtype([("first", np.uint64), ("second", np.uint64)])


def dictionary_ids(block, vocabulary):
    tokens = TOKENS.findall(block)
    fresh = set(tokens).difference(vocabulary)
    vocabulary.update(zip(fresh, itertools.count(len(vocabulary))))
    return np.fromiter(map(vocabulary.get, tokens), dtype=np.uint64, count=len(tokens))


def token_ids(block, vocabulary):
    """Factor words in C, looking up only the chunk's distinct spellings in Python."""
    if not block:
        return np.empty(0, dtype=np.uint64)
    if len(block) < 4096:
        return dictionary_ids(block, vocabulary)
    data = np.frombuffer(block, dtype=np.uint8)
    letters = data >= 97
    stops = data == 46
    flags = letters.copy()
    flags[1:] &= ~letters[:-1]
    flags |= stops
    starts = np.flatnonzero(flags)
    if not starts.size:
        return np.empty(0, dtype=np.uint64)
    flags[:] = letters
    flags[:-1] &= ~letters[1:]
    flags |= stops
    sizes = np.flatnonzero(flags) - starts + 1
    width = max(8, int(sizes.max()))
    intern = vocabulary.setdefault
    if width > 32:
        # Avoid padding every short word to the width of an unusually long word.
        return dictionary_ids(block, vocabulary)

    padded = block + b"\0" * (width - 1)
    words = np.ndarray((len(block),), dtype=f"S{width}", buffer=padded, strides=(1,))[starts]
    words.view(np.uint8).reshape(-1, width)[
        np.arange(width)[None, :] >= sizes[:, None]
    ] = 0
    if width == 8:
        unique, inverse = np.unique(words.view(np.uint64), return_inverse=True)
        unique = unique.view("S8")
    else:
        unique, inverse = np.unique(words, return_inverse=True)
    mapping = np.fromiter(
        (intern(word, len(vocabulary)) for word in unique.tolist()), dtype=np.uint64,
        count=unique.size,
    )
    return mapping[inverse]


def main(path):
    vocabulary = {b".": 0}
    chunks = []
    wide = False
    previous = 0
    word_count = 0
    carry = b""
    with open(path, "rb") as source:
        while True:
            raw = source.read(BLOCK)
            if raw:
                block = carry + raw.translate(TABLE)
                end = max(block.rfind(b" "), block.rfind(b".")) + 1
                carry = block[end:]
                block = block[:end]
            else:
                block = carry
            tokens = token_ids(block, vocabulary)
            ids = np.empty(tokens.size + 1, dtype=np.uint64)
            ids[0] = previous
            ids[1:] = tokens
            if len(vocabulary) > PACKED_LIMIT and not wide:
                # Widen existing keys rather than imposing a vocabulary limit.
                for index, chunk in enumerate(chunks):
                    converted = np.empty(chunk.size, dtype=WIDE_PAIR)
                    converted["first"] = chunk >> 32
                    converted["second"] = chunk & MASK
                    chunks[index] = converted
                wide = True
            word_count += int(np.count_nonzero(ids[1:]))
            previous = int(ids[-1])
            valid = (ids[:-1] != 0) & (ids[1:] != 0)
            if wide:
                keys = np.empty(int(np.count_nonzero(valid)), dtype=WIDE_PAIR)
                keys["first"] = ids[:-1][valid]
                keys["second"] = ids[1:][valid]
            else:
                keys = (ids[:-1][valid] << 32) | ids[1:][valid]
            if keys.size:
                chunks.append(keys)
            if not raw:
                break
    del ids, keys, valid, raw, block, carry, tokens

    pairs = np.concatenate(chunks) if chunks else np.empty(0, dtype=np.uint64)
    del chunks
    total = pairs.size
    best = []
    distinct = 0
    if total:
        pairs.sort(kind="quicksort")
        if wide:
            changed = (pairs["first"][1:] != pairs["first"][:-1]) | (
                pairs["second"][1:] != pairs["second"][:-1])
        else:
            changed = pairs[1:] != pairs[:-1]
        starts = np.flatnonzero(np.concatenate(([True], changed)))
        del changed
        counts = np.diff(np.append(starts, total))
        distinct = starts.size
        number = min(20, distinct)
        maximum = int(counts.max())
        if maximum <= max(256, distinct):
            histogram = np.bincount(counts)
            cutoff = histogram.size - 1 - int(np.searchsorted(
                np.cumsum(histogram[::-1]), number))
        else:
            cutoff = int(np.partition(counts, distinct - number)[distinct - number])

        names = list(vocabulary)
        for index in np.flatnonzero(counts > cutoff):
            key = pairs[starts[index]]
            if wide:
                first, second = int(key["first"]), int(key["second"])
            else:
                first, second = int(key) >> 32, int(key) & MASK
            best.append((-int(counts[index]), names[first], names[second]))

        needed = number - len(best)
        tied = pairs[starts[counts == cutoff]]
        # Resolve a potentially huge cutoff tie with numeric partition.
        ordered_names = sorted(vocabulary)
        rank = np.empty(len(names), dtype=np.uint64)
        for lexical_id, word in enumerate(ordered_names):
            rank[vocabulary[word]] = lexical_id
        if wide:
            lexical = np.empty(tied.size, dtype=WIDE_PAIR)
            lexical["first"] = rank[tied["first"]]
            lexical["second"] = rank[tied["second"]]
        else:
            lexical = (rank[tied >> 32] << 32) | rank[tied & MASK]
        lexical.partition(needed - 1)
        for key in lexical[:needed]:
            if wide:
                first, second = int(key["first"]), int(key["second"])
            else:
                first, second = int(key) >> 32, int(key) & MASK
            best.append((-cutoff, ordered_names[first], ordered_names[second]))
    best.sort()
    lines = [f"words {word_count}", f"pairs {total}", f"distinct {distinct}"]
    lines.extend(f"{-count} {a.decode('ascii')} {b.decode('ascii')}" for count, a, b in best)
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("ascii"))


if __name__ == "__main__":
    main(sys.argv[1])
