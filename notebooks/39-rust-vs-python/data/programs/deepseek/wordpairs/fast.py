import sys


def main():
    import numpy as np

    np.seterr(over="ignore")

    with open(sys.argv[1], "rb") as f:
        raw = f.read()
    b = np.frombuffer(raw, dtype=np.uint8)
    n = b.size
    stdout = sys.stdout
    if n == 0:
        stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return

    alpha_tab = np.zeros(256, dtype=np.bool_)
    alpha_tab[65:91] = True
    alpha_tab[97:123] = True
    is_alpha = alpha_tab[b]

    # Run boundaries: d[j] = +1 where a word starts at j, -1 where it ends.
    ia = is_alpha.view(np.int8)
    d = np.empty(n + 1, dtype=np.int8)
    d[0] = ia[0]
    np.subtract(ia[1:], ia[:-1], out=d[1:n])
    d[n] = -ia[n - 1]
    starts = np.flatnonzero(d == 1).astype(np.int32)
    ends = np.flatnonzero(d == -1).astype(np.int32)
    nw = starts.size
    if nw == 0:
        stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return
    del d, ia
    lens = ends - starts
    del ends

    # Letters, lowercased, in order of appearance (ASCII | 0x20 lowercases).
    vals = b[is_alpha]
    vals |= np.uint8(32)
    n_letters = vals.size
    del is_alpha

    punct_tab = np.zeros(256, dtype=np.bool_)
    punct_tab[33] = True
    punct_tab[46] = True
    punct_tab[63] = True
    punct_pos = np.flatnonzero(punct_tab[b]).astype(np.int32)
    del b, raw

    # Start offset of each word inside the letter array.
    wl_start = np.empty(nw, dtype=np.int32)
    wl_start[0] = 0
    if nw > 1:
        np.cumsum(lens[:-1], dtype=np.int32, out=wl_start[1:])

    # Position of each letter inside its word: propagate the start offset
    # of the containing word forward, then subtract the letter's own index.
    starts_at = np.zeros(n_letters, dtype=np.int32)
    starts_at[wl_start] = wl_start
    np.maximum.accumulate(starts_at, out=starts_at)
    k = np.arange(n_letters, dtype=np.int32)
    k -= starts_at
    del starts_at

    # Polynomial hash of every word (wrapping uint64).
    max_len = int(lens.max())
    powv = np.empty(max_len, dtype=np.uint64)
    powv[0] = np.uint64(1)
    if max_len > 1:
        p = np.uint64(0x9E3779B185EBCA87)
        for i in range(1, max_len):
            powv[i] = powv[i - 1] * p

    contrib = vals.astype(np.uint64)
    contrib += np.uint64(1)
    contrib *= powv[k]
    del powv
    cs = np.empty(n_letters + 1, dtype=np.uint64)
    cs[0] = 0
    np.cumsum(contrib, out=cs[1:])
    del contrib
    hs = cs[wl_start]
    hashes = cs[wl_start + lens]
    hashes -= hs
    del hs, cs

    # Distinct word hashes, with an id for each token.
    srt = np.sort(hashes)
    flag = np.empty(nw, dtype=np.bool_)
    flag[0] = True
    np.not_equal(srt[1:], srt[:-1], out=flag[1:])
    uniq = srt[flag]
    del srt
    U = uniq.size
    if U <= 2_000_000:
        # Small vocabulary: map hashes to ids through a bucket table.
        M = 1 << 12
        while M < 16 * U and M < (1 << 24):
            M <<= 1
        bmask = np.uint64(M - 1)
        lut = np.full(M, -1, dtype=np.int32)
        lut[(uniq & bmask).astype(np.intp)] = np.arange(U, dtype=np.int32)
        inv = lut[(hashes & bmask).astype(np.intp)]
        del lut
        if not np.array_equal(uniq[inv], hashes):
            miss = np.flatnonzero(uniq[inv] != hashes)
            inv[miss] = np.searchsorted(uniq, hashes[miss])
            del miss
    else:
        inv = np.searchsorted(uniq, hashes).astype(np.int32)
    del uniq, hashes

    # An arbitrary (first) token index for each id.
    first = np.empty(U, dtype=np.int64)
    first[inv[::-1]] = np.arange(nw - 1, -1, -1, dtype=np.int64)
    first = first.astype(np.int32)

    fs = wl_start[first]
    fl = lens[first]
    rep_words = []
    ap = rep_words.append
    for s, l in zip(fs.tolist(), fl.tolist()):
        ap(vals[s:s + l].tobytes())
    del fs, fl

    # Exact verification: an id may only merge byte-identical words.
    rep_lens = lens[first]
    ok = bool(np.array_equal(lens, rep_lens[inv]))
    if ok:
        rep_start = np.empty(U, dtype=np.int32)
        rep_start[0] = 0
        if U > 1:
            np.cumsum(rep_lens[:-1], dtype=np.int32, out=rep_start[1:])
        rep_flat = np.frombuffer(b"".join(rep_words), dtype=np.uint8)
        p0 = rep_start[inv]
        if max_len <= 4096:
            # Compare the k-th letter of every long-enough word.
            for kk in range(max_len):
                act = lens > kk
                v = vals[wl_start[act] + kk]
                e = rep_flat[p0[act] + kk]
                if not np.array_equal(v, e):
                    ok = False
                    break
        else:
            inv_letter = np.repeat(inv, lens)
            idx = rep_start[inv_letter]
            idx += k
            ok = bool(np.array_equal(rep_flat[idx], vals))
            del inv_letter, idx
        del p0, rep_flat, rep_start
    del rep_lens, first, k

    if not ok:
        # Extremely unlikely fallback: intern tokens exactly, one by one.
        ids = {}
        inv = np.empty(nw, dtype=np.int32)
        wl = wl_start.tolist()
        ln = lens.tolist()
        for i in range(nw):
            s = wl[i]
            w = vals[s:s + ln[i]].tobytes()
            j = ids.get(w)
            if j is None:
                j = len(ids)
                ids[w] = j
            inv[i] = j
        rep_words = list(ids.keys())
        U = len(rep_words)

    del vals, wl_start, lens

    # Lexicographic rank of every word.
    order = sorted(range(U), key=rep_words.__getitem__)
    rank = np.empty(U, dtype=np.int32)
    rank[np.asarray(order, dtype=np.int64)] = np.arange(U, dtype=np.int32)
    del order

    # Sentence id of each word = number of sentence punctuation bytes before it.
    q = np.searchsorted(starts, punct_pos, side="right")
    del punct_pos
    cnt = np.bincount(q, minlength=nw + 1)
    del q
    sent_id = cnt[:nw]
    np.cumsum(sent_id, out=sent_id)
    same = sent_id[:-1] == sent_id[1:]
    del sent_id, cnt
    total_pairs = int(np.count_nonzero(same))

    id1 = inv[:-1][same]
    id2 = inv[1:][same]
    del same, inv, starts
    keys = (id1.astype(np.uint64) << np.uint64(32)) | id2.astype(np.uint64)
    del id1, id2

    ukeys, counts = np.unique(keys, return_counts=True)
    del keys
    D = int(ukeys.size)

    if D == 0:
        sel = np.empty(0, dtype=np.int64)
    elif D <= 20:
        sel = np.arange(D)
    else:
        kth = D - 20
        thresh = np.partition(counts, kth)[kth]
        above = np.flatnonzero(counts > thresh)
        need = 20 - above.size
        tie = np.flatnonzero(counts == thresh)
        if tie.size > need:
            kk = ukeys[tie]
            a1 = (kk >> np.uint64(32)).astype(np.int64)
            a2 = (kk & np.uint64(0xFFFFFFFF)).astype(np.int64)
            comp = rank[a1].astype(np.uint64) * np.uint64(U) + rank[a2].astype(
                np.uint64
            )
            part = np.argpartition(comp, need - 1)[:need]
            tie = tie[part]
        sel = np.concatenate((above, tie))

    items = []
    for i in sel.tolist():
        key = int(ukeys[i])
        items.append(
            (int(counts[i]), rep_words[key >> 32], rep_words[key & 0xFFFFFFFF])
        )
    items.sort(key=lambda t: (-t[0], t[1], t[2]))
    items = items[:20]

    parts = [
        b"words %d\n" % nw,
        b"pairs %d\n" % total_pairs,
        b"distinct %d\n" % D,
    ]
    for c, a, b2 in items:
        parts.append(b"%d %s %s\n" % (c, a, b2))
    stdout.buffer.write(b"".join(parts))


if __name__ == "__main__":
    main()
