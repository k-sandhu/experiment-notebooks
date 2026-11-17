import re
import sys
from collections import Counter

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

_MASKS = np.array(
    [(1 << (8 * i)) - 1 if i < 8 else (1 << 64) - 1 for i in range(9)],
    dtype=np.uint64,
)
_C1 = np.uint64(0x9E3779B185EBCA87)
_C2 = np.uint64(0xFF51AFD7ED558CCD)


def _solve_plain(data: bytes) -> bytes:
    """Fallback for very long words (rare); same algorithm as plain.py."""
    data = data.translate(bytes.maketrans(b".!?", b"..."))
    tokens = re.findall(rb"[a-z]+|\.", data)
    total_words = len(tokens) - data.count(b".") if tokens else 0
    counter: Counter = Counter()
    if len(tokens) >= 2:
        counter.update(zip(tokens, tokens[1:]))
    dot = b"."
    for k in [k for k in counter if k[0] == dot or k[1] == dot]:
        del counter[k]
    lines = [
        b"words " + str(total_words).encode(),
        b"pairs " + str(sum(counter.values())).encode(),
        b"distinct " + str(len(counter)).encode(),
    ]
    ranked = sorted((-c, w1, w2) for (w1, w2), c in counter.items())
    for negc, w1, w2 in ranked[:20]:
        lines.append(str(-negc).encode() + b" " + w1 + b" " + w2)
    return b"\n".join(lines) + b"\n"


def main() -> None:
    if len(sys.argv) < 2:
        return
    with open(sys.argv[1], "rb") as f:
        raw = f.read()
    lower = raw.lower()
    arr = np.frombuffer(lower, dtype=np.uint8)
    n = arr.size
    if n == 0:
        sys.stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return

    is_letter = (arr >= 97) & (arr <= 122)
    padded = np.zeros(n + 2, dtype=np.int8)
    padded[1:-1] = is_letter
    del is_letter
    d = np.diff(padded)
    del padded
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    del d
    total_words = int(starts.size)
    if total_words == 0:
        sys.stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return
    lengths = ends - starts
    maxlen = int(lengths.max())
    if maxlen > 24:
        sys.stdout.buffer.write(_solve_plain(lower))
        return
    chunks = (maxlen + 7) // 8

    # Pack each word into `chunks` uint64s (exact byte representation).
    arr_pad = np.concatenate([arr, np.zeros(chunks * 8, dtype=np.uint8)])
    win = sliding_window_view(arr_pad, 8)
    packs = []
    for ci in range(chunks):
        off = ci * 8
        pack = win[starts + off].view(np.uint64).reshape(-1).copy()
        pack &= _MASKS[np.clip(lengths - off, 0, 8)]
        packs.append(pack)
    del arr_pad, win

    # Hash packs to one uint64 and intern via sort + searchsorted.
    h = lengths.astype(np.uint64) * _C1
    for p in packs:
        h = (h ^ p) * _C2
        h ^= h >> np.uint64(29)

    sorted_h = np.sort(h)
    new_mask = np.empty(sorted_h.size, dtype=bool)
    new_mask[0] = True
    np.not_equal(sorted_h[1:], sorted_h[:-1], out=new_mask[1:])
    uniq_h = sorted_h[new_mask]
    del sorted_h, new_mask
    vocab = int(uniq_h.size)
    ids = np.searchsorted(uniq_h, h)
    del h, uniq_h
    ids64 = ids.astype(np.int64, copy=False)
    del ids

    # First occurrence of each word id, and collision check on the packs.
    first_occ = np.full(vocab, total_words, dtype=np.int64)
    np.minimum.at(first_occ, ids64, np.arange(total_words, dtype=np.int64))
    collision = False
    for p in packs:
        if not np.array_equal(p, p[first_occ][ids64]):
            collision = True
            break
    if collision:
        sys.stdout.buffer.write(_solve_plain(lower))
        return

    # Lexicographic rank of each (hash) word id: sorting only the vocab.
    # Representative packed bytes, in hash-id order.
    rep_stacked = np.empty((vocab, chunks), dtype=np.uint64)
    for ci, p in enumerate(packs):
        rep_stacked[:, ci] = p[first_occ]
    del packs
    void_rep = rep_stacked.view(dtype=f"V{chunks * 8}").reshape(-1)
    del rep_stacked
    order = np.argsort(void_rep)
    del void_rep
    lex_rank = np.empty(vocab, dtype=np.int64)
    lex_rank[order] = np.arange(vocab, dtype=np.int64)
    rep_lex = np.empty(vocab, dtype=np.int64)
    rep_lex[lex_rank] = first_occ
    del order, first_occ

    # Pair counting via sorting pair keys.
    total_pairs = 0
    distinct = 0
    uniq_pairs = None
    counts = None
    if total_words >= 2:
        sent_pos = np.flatnonzero((arr == 46) | (arr == 33) | (arr == 63))
        valid = np.ones(total_words - 1, dtype=bool)
        if sent_pos.size:
            nxt = np.searchsorted(starts, sent_pos)
            nxt = nxt[(nxt >= 1) & (nxt <= total_words - 1)]
            if nxt.size:
                valid[nxt - 1] = False
        del sent_pos
        pair_keys = ids64[:-1][valid] * np.int64(vocab) + ids64[1:][valid]
        del valid, ids64
        total_pairs = int(pair_keys.size)
        if total_pairs:
            sp = np.sort(pair_keys)
            del pair_keys
            pmask = np.empty(sp.size, dtype=bool)
            pmask[0] = True
            np.not_equal(sp[1:], sp[:-1], out=pmask[1:])
            uniq_pairs = sp[pmask]
            bounds = np.flatnonzero(pmask)
            counts = np.diff(np.append(bounds, sp.size))
            del sp, pmask, bounds
            distinct = int(uniq_pairs.size)

    lines = [
        b"words " + str(total_words).encode(),
        b"pairs " + str(total_pairs).encode(),
        b"distinct " + str(distinct).encode(),
    ]

    if distinct:
        # Chosen entries as (count, lex_first, lex_second).
        if distinct <= 20:
            chosen_pos = np.arange(distinct)
            cand_counts = counts
            cand_pairs = uniq_pairs
        else:
            thr = int(np.partition(counts, distinct - 20)[distinct - 20])
            greater_pos = np.flatnonzero(counts > thr)
            need = 20 - int(greater_pos.size)
            tie_pos = np.flatnonzero(counts == thr)
            if need == 0:
                tie_pos = tie_pos[:0]
            elif tie_pos.size > need:
                # Lexicographically smallest `need` ties.
                tf = lex_rank[uniq_pairs[tie_pos] // vocab]
                ts = lex_rank[uniq_pairs[tie_pos] % vocab]
                lex_key = tf * np.int64(vocab) + ts
                sel = np.argpartition(lex_key, need - 1)[:need]
                tie_pos = tie_pos[sel]
            chosen_pos = np.concatenate([greater_pos, tie_pos])
            cand_counts = counts
            cand_pairs = uniq_pairs
        chosen = []
        for pos in chosen_pos.tolist():
            pid = int(cand_pairs[pos])
            f_hash, s_hash = pid // vocab, pid % vocab
            chosen.append(
                (int(cand_counts[pos]), int(lex_rank[f_hash]), int(lex_rank[s_hash]))
            )
        chosen.sort(key=lambda t: (-t[0], t[1], t[2]))
        for c, lf, ls in chosen:
            wf = lower[starts[rep_lex[lf]] : ends[rep_lex[lf]]]
            ws = lower[starts[rep_lex[ls]] : ends[rep_lex[ls]]]
            lines.append(str(c).encode() + b" " + wf + b" " + ws)

    sys.stdout.buffer.write(b"\n".join(lines) + b"\n")


if __name__ == "__main__":
    main()
