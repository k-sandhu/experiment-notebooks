import re
import sys

import numpy as np

TOP = 20
PACKED_MAX = 64  # longer words use the exact path; packing costs one pass per byte
WORD = re.compile(rb"[a-z]+")


def word_ids_packed(data, low, starts, lengths):
    """Give each word a group id using its bytes, packed 8 per uint64 column.

    Returns (group id per word, representative bytes per group), or None if the
    hash-based grouping is found to be wrong (then the caller falls back).
    """
    n = starts.size
    last = low.size - 1
    maxlen = int(lengths.max())
    cols = []
    for c0 in range(0, maxlen, 8):
        col = np.zeros(n, dtype=np.uint64)
        for k in range(c0, min(c0 + 8, maxlen)):
            byte = low[np.minimum(starts + k, last)].astype(np.uint64)
            byte[lengths <= k] = 0
            byte <<= np.uint64(8 * (k - c0))
            col |= byte
        cols.append(col)
    del byte

    h = np.zeros(n, dtype=np.uint64)
    for col in cols:
        h = h * np.uint64(0x9E3779B97F4A7C15) + col
    uniq, inv = np.unique(h, return_inverse=True)
    del h
    inv = inv.reshape(-1).astype(np.int32)
    first = np.empty(uniq.size, dtype=np.intp)
    first[inv] = np.arange(n, dtype=np.intp)

    # Hash equality is not word equality, so check every word against its
    # group's representative. A collision sends the caller to the exact path.
    for col in cols:
        if not np.array_equal(col[first][inv], col):
            return None

    rep_starts = starts[first].tolist()
    rep_ends = (starts[first] + lengths[first]).tolist()
    vocab = [data[s:e].lower() for s, e in zip(rep_starts, rep_ends)]
    return inv, vocab


def word_ids_by_bytes(data):
    """Exact fallback for words longer than PACKED_MAX."""
    ids = {}
    words = WORD.findall(data.lower())
    wid = np.fromiter(
        (ids.setdefault(w, len(ids)) for w in words), dtype=np.int32, count=len(words)
    )
    return wid, list(ids)


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()

    arr = np.frombuffer(data, dtype=np.uint8)
    # Letters fold to lower case with bit 0x20; for printable ASCII this maps
    # exactly A-Z and a-z onto 97..122.
    low = arr | np.uint8(0x20)
    is_letter = (low - np.uint8(97)) < np.uint8(26)

    # Word = maximal run of letters: find run starts and ends (exclusive).
    padded = np.zeros(arr.size + 2, dtype=bool)
    padded[1:-1] = is_letter
    del is_letter
    edges = np.diff(padded.view(np.int8))
    del padded
    starts = np.flatnonzero(edges == 1).astype(np.int32)
    ends = np.flatnonzero(edges == -1).astype(np.int32)
    del edges
    n = starts.size
    if n == 0:
        sys.stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return
    lengths = ends - starts
    del ends

    # Sentence ends. Words never contain punctuation, so a word's sentence index
    # is the number of sentence ends before its first letter. Two neighbouring
    # words share a sentence exactly when those counts are equal.
    punct = np.flatnonzero((arr == 46) | (arr == 33) | (arr == 63))  # . ! ?
    if punct.size:
        sentence = np.searchsorted(punct, starts)
        same = sentence[1:] == sentence[:-1]
        del sentence
    else:
        same = None

    found = word_ids_packed(data, low, starts, lengths) if lengths.max() <= PACKED_MAX else None
    if found is None:
        found = word_ids_by_bytes(data)
    wid, vocab = found
    del low, starts, lengths
    groups = len(vocab)

    # Rank groups in byte order, so a pair key of (rank, rank) sorts exactly as
    # the output requires.
    order = sorted(range(groups), key=vocab.__getitem__)
    rank = np.empty(groups, dtype=np.uint32)
    rank[np.array(order, dtype=np.intp)] = np.arange(groups, dtype=np.uint32)
    sorted_vocab = [vocab[g] for g in order]

    kd = np.uint32 if groups * groups <= 0xFFFFFFFF else np.uint64
    wr = rank.astype(kd)[wid]
    del wid
    a = wr[:-1]
    b = wr[1:]
    if same is not None:
        a = a[same]
        b = b[same]
    keys = a * kd(groups) + b
    del a, b, wr
    pairs = keys.size

    keys.sort()
    flag = np.ones(pairs, dtype=bool)
    flag[1:] = keys[1:] != keys[:-1]
    run_start = np.flatnonzero(flag)
    del flag
    counts = np.diff(np.append(run_start, pairs))
    uk = keys[run_start]
    del keys, run_start
    distinct = uk.size

    # Top 20 by count, then by key. Ties at the 20th count are kept whole so the
    # key order can break them.
    if distinct > TOP:
        threshold = np.partition(counts, distinct - TOP)[distinct - TOP]
        cand = np.flatnonzero(counts >= threshold)
    else:
        cand = np.arange(distinct)
    chosen = cand[np.lexsort((uk[cand], -counts[cand]))[:TOP]]

    out = [f"words {n}", f"pairs {pairs}", f"distinct {distinct}"]
    for i in chosen.tolist():
        first_rank, second_rank = divmod(int(uk[i]), groups)
        out.append(
            f"{int(counts[i])} {sorted_vocab[first_rank].decode()} {sorted_vocab[second_rank].decode()}"
        )
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


if __name__ == "__main__":
    main()
