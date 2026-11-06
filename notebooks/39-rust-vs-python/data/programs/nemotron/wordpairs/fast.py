"""Word pair counter: Python 3.13 with NumPy.

Segmentation (sentence splitting, word spans, pair validity) is done with
vectorised NumPy operations over the raw bytes; word interning and output stay
in Python.
"""

import sys

import numpy as np


def main() -> None:
    data = np.fromfile(sys.argv[1], dtype=np.uint8)
    n = int(data.size)

    if n == 0:
        sys.stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return

    # Lowercase in place (input is pure ASCII).
    data[(data >= 65) & (data <= 90)] += 32

    # Bytes copy on top of which memoryview slices are immutable (hence hashable)
    # and O(1): no per-word allocation while interning.
    mv = memoryview(data.tobytes())

    letter = (data >= 97) & (data <= 122)
    ender = (data == 0x2E) | (data == 0x21) | (data == 0x3F)  # . ! ?

    # Word spans: a word starts at a letter preceded by a non-letter (or the
    # start of the file) and ends at a letter followed by a non-letter (or EOF).
    prev_letter = np.empty(n, dtype=bool)
    prev_letter[0] = False
    prev_letter[1:] = letter[:-1]
    starts = np.flatnonzero(letter & ~prev_letter)

    next_letter = np.empty(n, dtype=bool)
    next_letter[n - 1] = False
    next_letter[: n - 1] = letter[1:]
    ends = np.flatnonzero(letter & ~next_letter)

    word_count = int(starts.size)

    # Intern words in order of first appearance. memoryview slices are O(1) and
    # hash by content, just like bytes.
    word_index: dict = {}
    words_list: list = []
    ids = np.empty(word_count, dtype=np.int32)
    for k in range(word_count):
        word = mv[int(starts[k]) : int(ends[k]) + 1]
        word_id = word_index.get(word)
        if word_id is None:
            word_id = len(words_list)
            word_index[word] = word_id
            words_list.append(word)
        ids[k] = word_id

    # Remap ids so that id order matches lexicographic word order; then sorting
    # by id is the same as sorting by word bytes.
    vocab = len(words_list)
    order = sorted(range(vocab), key=lambda k: words_list[k].tobytes())
    order_arr = np.array(order, dtype=np.int32)
    remap = np.empty(vocab, dtype=np.int32)
    remap[order_arr] = np.arange(vocab, dtype=np.int32)
    ids = remap[ids]

    pair_count = 0
    if word_count > 1:
        ender_positions = np.flatnonzero(ender)
        # The gap between word k and word k+1 is valid iff no sentence ender lies
        # strictly between them: ends[k] < pos < starts[k+1].
        after = ends[:-1] + 1
        if ender_positions.size:
            idx = ender_positions.searchsorted(after)
            take = np.minimum(idx, ender_positions.size - 1)
            valid = (idx == ender_positions.size) | (
                ender_positions[take] >= starts[1:]
            )
        else:
            valid = np.ones(word_count - 1, dtype=bool)

        pair_count = int(valid.sum())

        first = ids[:-1][valid]
        second = ids[1:][valid]
        keys = (first.astype(np.uint64) << 32) | second.astype(np.uint64)
        uniq, counts = np.unique(keys, return_counts=True)
        # uniq is sorted by (first, second) ascending; a stable sort by
        # descending count therefore yields count desc, then first word, then
        # second word, ascending.
        order = np.argsort(-counts, kind="stable")
        top = order[: min(20, order.size)]

        out = [
            f"words {word_count}",
            f"pairs {pair_count}",
            f"distinct {uniq.size}",
        ]
        for t in top.tolist():
            key = int(uniq[t])
            first_id = key >> 32
            second_id = key & 0xFFFFFFFF
            out.append(
                "{} {} {}".format(
                    counts[t],
                    bytes(words_list[order_arr[first_id]]).decode("ascii"),
                    bytes(words_list[order_arr[second_id]]).decode("ascii"),
                )
            )
        sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))
        return

    sys.stdout.buffer.write(f"words {word_count}\npairs 0\ndistinct 0\n".encode("ascii"))


if __name__ == "__main__":
    main()
