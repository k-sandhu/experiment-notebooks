import sys

import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        # Lowercase at C speed; buf doubles as the source of output word bytes.
        buf = bytearray(f.read().translate(bytes.maketrans(
            bytes(range(65, 91)), bytes(range(97, 123)))))
    d = np.frombuffer(buf, dtype=np.uint8)

    n = d.size
    is_l = ((d >= 97) & (d <= 122)) if n else np.zeros(0, bool)
    is_s = (d == 46) | (d == 33) | (d == 63) if n else np.zeros(0, bool)

    # Word spans [starts[i], ends[i]).
    if n:
        prev_l = np.empty(n, bool)
        prev_l[0] = False
        prev_l[1:] = is_l[:-1]
        starts = np.nonzero(is_l & ~prev_l)[0]
        next_l = np.empty(n, bool)
        next_l[-1] = False
        next_l[:-1] = is_l[1:]
        ends = np.nonzero(is_l & ~next_l)[0] + 1
    else:
        starts = np.zeros(0, np.int64)
        ends = np.zeros(0, np.int64)
    nw = starts.size
    if nw == 0:
        sys.stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return
    lens = (ends - starts).astype(np.int64)

    # Adjacent words form a pair iff no sentence-end byte lies between them.
    if nw > 1:
        send_pos = np.nonzero(is_s)[0]
        sb = np.searchsorted(send_pos, starts)
        adj = sb[1:] == sb[:-1]
        del send_pos, sb
    else:
        adj = np.zeros(0, bool)

    # Exact word encoding: base-256 little-endian value of the word's letters,
    # split into 64-bit limbs (letters are >= 97 so the encoding is injective).
    # Limbs are paired into one uint64 each via an odd multiplier (a bijection
    # on Z/2^64), giving one uint64 per <=16-byte word, else a tuple of uint64s.
    letts = d[is_l] if n else np.zeros(0, np.uint8)
    nlet = letts.size
    maxlen = int(lens.max()) if nw else 0
    nlimbs = max(1, (maxlen + 7) // 8)
    cl = np.zeros(nw + 1, np.int64)
    np.cumsum(lens, out=cl[1:])
    starts_l = cl[:-1]

    pw32 = np.array([1, 256, 65536, 16777216], dtype=np.uint32)
    starts32 = starts_l.astype(np.int32)
    lens32 = lens.astype(np.int32)
    Z32 = np.uint32(0)
    limbs = []
    for j in range(nlimbs):
        base = 8 * j
        if not (lens32 > base).any():
            break
        lo = np.zeros(nw, np.uint32)
        hi = np.zeros(nw, np.uint32)
        for half, acc in ((0, lo), (4, hi)):
            for k in range(4):
                p = base + half + k
                vi = np.nonzero(lens32 > p)[0]
                if vi.size == 0:
                    continue
                # selected words all have a letter at position p: no bounds clamp
                g = letts[starts32[vi] + np.int32(p)].astype(np.uint32) * pw32[k]
                if vi.size == nw:
                    acc += g
                else:
                    acc[vi] += g
        limbs.append(lo.astype(np.uint64) + np.uint64(4294967296) * hi.astype(np.uint64))

    ODD = np.uint64(0x9E3779B97F4A7C15)
    zero = np.zeros(nw, np.uint64)
    comps = []
    for j in range(0, nlimbs, 2):
        a = limbs[j]
        b = limbs[j + 1] if j + 1 < nlimbs else zero
        comps.append(a * ODD + b)
    m = len(comps)
    del limbs

    # Sort words once; derive unique ids, inverse mapping and first occurrences.
    sorted_fields = []
    if m == 1:
        order = np.argsort(comps[0])
        sorted_fields.append(comps[0][order])
    else:
        dt = np.dtype([(f"f{i}", np.uint64) for i in range(m)])
        rec = np.empty(nw, dt)
        for i, c in enumerate(comps):
            rec[f"f{i}"] = c
        order = np.argsort(rec)
        for i in range(m):
            sorted_fields.append(rec[f"f{i}"][order])
    newg = np.empty(nw, bool)
    newg[0] = True
    diff = np.zeros(nw - 1, bool)
    for sf in sorted_fields:
        diff |= sf[1:] != sf[:-1]
    newg[1:] = diff
    inv = np.empty(nw, np.int64)
    inv[order] = np.cumsum(newg) - 1
    grp = np.nonzero(newg)[0]
    first = order[grp]
    V = grp.size
    del comps, order, sorted_fields, newg, grp, diff

    # Representative word bytes per unique word id.
    strs = [bytes(buf[starts[i]:ends[i]]) for i in first]

    total_words = int(nw)
    if nw > 1:
        k1 = inv[:-1][adj]
        k2 = inv[1:][adj]
        total_pairs = int(adj.sum())
    else:
        k1 = np.zeros(0, np.int64)
        k2 = np.zeros(0, np.int64)
        total_pairs = 0

    if total_pairs:
        K = np.uint64(V)
        pk = k1.astype(np.uint64) * K + k2.astype(np.uint64)
        ukp, cnt = np.unique(pk, return_counts=True)
        distinct = int(ukp.size)
    else:
        ukp = np.zeros(0, np.uint64)
        cnt = np.zeros(0, np.uint64)
        distinct = 0

    # Lexicographic rank of each word id.
    order = sorted(range(V), key=strs.__getitem__)
    lexrank = np.empty(V, np.int64)
    lexrank[np.asarray(order, np.int64)] = np.arange(V, dtype=np.int64)

    if distinct > 20:
        th = np.partition(cnt, distinct - 20)[distinct - 20]
        cand = np.nonzero(cnt >= th)[0]
    else:
        cand = np.arange(distinct)
    c1 = (ukp[cand] // np.uint64(V)).astype(np.int64)
    c2 = (ukp[cand] % np.uint64(V)).astype(np.int64)
    o = np.lexsort((lexrank[c2], lexrank[c1], -cnt[cand].astype(np.int64)))
    take = o[:20]

    out = [b"words %d\npairs %d\ndistinct %d\n" % (total_words, total_pairs, distinct)]
    for t in take:
        out.append(b"%d %s %s\n" % (int(cnt[cand][t]), strs[c1[t]], strs[c2[t]]))
    sys.stdout.buffer.write(b"".join(out))


main()
