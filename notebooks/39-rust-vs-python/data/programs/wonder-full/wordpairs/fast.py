import sys

import numpy as np

# Byte translation: A-Z -> a-z, . ! ? -> '.', every other non-letter -> space.
_tbl = bytearray(256)
for _i in range(256):
    if 65 <= _i <= 90:
        _tbl[_i] = _i + 32
    elif 97 <= _i <= 122:
        _tbl[_i] = _i
    elif _i in (46, 33, 63):
        _tbl[_i] = 46
    else:
        _tbl[_i] = 32
TABLE = bytes(_tbl)
SENT = b"\x01"


def main():
    data = open(sys.argv[1], "rb").read()
    t = data.translate(TABLE)
    del data
    nsent = t.count(b".")
    if nsent:
        # Each sentence end becomes a standalone sentinel token.
        t = t.replace(b".", b" \x01 ")
    toks = t.split()
    del t

    words = len(toks) - nsent
    if words == 0:
        sys.stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return

    # Intern tokens with a dict (C-level set/map loops). The vocabulary
    # is sorted, so a word id *is* its lexicographic rank, and the pair
    # key id1 * V + id2 is monotonic in (word1, word2) byte order.
    vocab = sorted(set(toks))
    id_of = {w: i for i, w in enumerate(vocab)}
    sent_id = id_of.get(SENT, -1)
    ids = np.fromiter(
        map(id_of.__getitem__, toks), dtype=np.int64, count=len(toks)
    )
    del toks, id_of
    vocab_size = len(vocab)

    if ids.size < 2:
        sys.stdout.buffer.write(f"words {words}\npairs 0\ndistinct 0\n".encode())
        return

    a = ids[:-1]
    b = ids[1:]
    del ids
    if sent_id >= 0:
        keep = (a != sent_id) & (b != sent_id)
        a = a[keep]
        b = b[keep]
        del keep

    keys = a * vocab_size + b
    del a, b
    total_pairs = int(keys.size)
    if total_pairs == 0:
        sys.stdout.buffer.write(f"words {words}\npairs 0\ndistinct 0\n".encode())
        return

    # Sorting the integer pair keys counts every distinct pair.
    pair_keys, counts = np.unique(keys, return_counts=True)
    del keys
    distinct = int(pair_keys.size)

    if distinct <= 20:
        sel = np.arange(distinct)
    else:
        # 20th largest count, from a histogram of counts. pair_keys is
        # sorted ascending, so among pairs tied at the threshold the
        # lexicographically smallest come first.
        hist = np.bincount(counts)
        pos = int(np.searchsorted(np.cumsum(hist[::-1]), 20))
        thr = len(hist) - 1 - pos
        del hist
        gt = np.flatnonzero(counts > thr)
        need = 20 - gt.size
        eq = np.flatnonzero(counts == thr)[:need]
        sel = np.concatenate((gt, eq))

    chosen = [(int(counts[i]), int(pair_keys[i])) for i in sel]
    chosen.sort(key=lambda x: (-x[0], x[1]))

    out = [f"words {words}\n", f"pairs {total_pairs}\n", f"distinct {distinct}\n"]
    for c, key in chosen:
        w1 = vocab[key // vocab_size].decode()
        w2 = vocab[key % vocab_size].decode()
        out.append(f"{c} {w1} {w2}\n")
    sys.stdout.buffer.write("".join(out).encode())


main()
