import re
import sys

import numpy as np

CHUNK = 1 << 20
SLOT_BITS = 20
SLOT_MASK_SHIFT = np.uint64(64 - SLOT_BITS)
MAX_ROUNDS = 8
MULTS = [0x9E3779B97F4A7C15, 0xC2B2AE3D27D4EB4F, 0x165667B19E3779F9, 0xD6E8FEB86659FD93,
         0xFF51AFD7ED558CCD, 0xC4CEB9FE1A85EC53, 0x94D049BB133111EB, 0xBF58476D1CE4E5B9]


def chunk_bounds(data, n):
    bounds = []
    pos = 0
    while pos < n:
        end = pos + CHUNK
        if end >= n:
            end = n
        else:
            # move to a byte that is not a letter so no word is split
            while end < n and (97 <= (data[end] | 32) <= 122):
                end += 1
        bounds.append((pos, end))
        pos = end
    return bounds


def power_tables(base, size):
    """P[i] = base**i and Q[i] = base**-i modulo 2**64, for i < size."""
    P = np.full(size, base, dtype=np.uint64)
    Q = np.full(size, pow(base, -1, 1 << 64), dtype=np.uint64)
    np.cumprod(P, out=P)
    np.cumprod(Q, out=Q)
    # shift by one so that index 0 holds 1
    P[1:] = P[:-1]
    Q[1:] = Q[:-1]
    P[:1] = 1
    Q[:1] = 1
    return P, Q


# byte -> 1..26 for a letter (either case), 0 otherwise; byte -> 1 for a sentence end, 0 otherwise
LETTER_VALUE = bytes(((c | 32) - 96 if 97 <= (c | 32) <= 122 else 0) for c in range(256))
IS_END = bytes(1 if c in b".!?" else 0 for c in range(256))
EXACT_LEN = 13  # 27**13 < 2**62, so a word of up to 13 letters gets an exact base-27 value
LONG_BASE = 0x9E3779B97F4A7C15 | 1
SMALL_POWERS = np.array([pow(LONG_BASE, k, 1 << 64) for k in range(2048)], dtype=np.uint64)


def tokenize(data, bounds):
    """Hash every word, and number its sentence.

    Words of up to 13 letters hash to their exact base-27 value. Longer ones use a second
    polynomial hash with bit 63 set, which keeps them apart from the exact values.
    Returns (hashes, sentence-break flags, word start offsets)."""
    longest_chunk = max((e - s for s, e in bounds), default=0)
    P, Q = power_tables(27, longest_chunk)
    P2 = Q2 = None

    hs, bs, ps = [], [], []
    pending = False  # a sentence end lies between the last word seen and the current position
    wbuf = np.empty(longest_chunk, dtype=np.uint64)
    for s, e in bounds:
        L = e - s
        raw = data[s:e]
        t = np.frombuffer(raw.translate(LETTER_VALUE), dtype=np.uint8)
        isl = t != 0
        edges = np.flatnonzero(isl[1:] != isl[:-1]) + 1
        if isl[0]:
            edges = np.concatenate((np.zeros(1, dtype=edges.dtype), edges))
        if isl[-1]:
            edges = np.concatenate((edges, np.full(1, L, dtype=edges.dtype)))
        epos = np.flatnonzero(np.frombuffer(raw.translate(IS_END), dtype=np.uint8).view(np.bool_))
        if edges.size == 0:
            pending = pending or epos.size > 0
            continue
        starts = edges[0::2]
        ends = edges[1::2]
        nw = starts.size
        lens = ends - starts
        w = wbuf[:L]
        np.copyto(w, t, casting="unsafe")
        long_idx = np.flatnonzero(lens > EXACT_LEN) if int(lens.max()) > EXACT_LEN else None
        w2 = None
        if long_idx is not None:
            m = int(lens[long_idx].max())
            if m <= len(SMALL_POWERS) and long_idx.size * m <= 4 * L:
                w2 = False  # few long words: hash them from a gathered matrix of their letters
            else:
                if P2 is None:
                    P2, Q2 = power_tables(LONG_BASE, longest_chunk)
                w2 = w * P2[:L]
        w *= P[:L]
        # bytes between words weigh zero, so the segment sums are the word sums
        h = np.add.reduceat(w, starts) * Q[starts]
        if w2 is False:
            ll = lens[long_idx]
            cols = np.arange(m)
            pos = starts[long_idx][:, None] + cols
            pos = np.minimum(pos, L - 1)
            letters = t[pos] * (cols < ll[:, None])
            h2 = (letters.astype(np.uint64) * SMALL_POWERS[:m]).sum(axis=1, dtype=np.uint64)
            h[long_idx] = h2 | np.uint64(1 << 63)
        elif w2 is not None:
            ls = starts[long_idx]
            h[long_idx] = (np.add.reduceat(w2, starts)[long_idx] * Q2[ls]) | np.uint64(1 << 63)
        # brk[k]: a sentence end lies between word k-1 and word k
        gaps = np.bincount(np.searchsorted(starts, epos), minlength=nw + 1)
        brk = gaps[:nw] > 0
        if pending:
            brk[0] = True
        pending = bool(gaps[nw])
        hs.append(h)
        bs.append(brk)
        ps.append((starts + s).astype(np.uint32))
    if not hs:
        return np.empty(0, np.uint64), np.empty(0, np.bool_), np.empty(0, np.uint32)
    return np.concatenate(hs), np.concatenate(bs), np.concatenate(ps)


def assign_ids(H):
    """Dense-enough integer id per distinct hash. Returns (ids uint32, id space size)."""
    n = H.size
    ids = np.empty(n, dtype=np.uint32)
    M = 1 << SLOT_BITS
    idx = None  # None means every word
    cur = H
    space = 0
    for r in range(MAX_ROUNDS):
        slot = ((cur * np.uint64(MULTS[r])) >> SLOT_MASK_SHIFT).astype(np.intp)
        table = np.zeros(M, dtype=np.uint64)
        table[slot] = cur
        ok = table[slot] == cur
        won = np.flatnonzero(ok)
        if idx is None:
            ids[won] = slot[won] + space
        else:
            ids[idx[won]] = slot[won] + space
        space += M
        lost = np.flatnonzero(~ok)
        if lost.size == 0:
            return ids, space
        idx = lost if idx is None else idx[lost]
        cur = H[idx]
    u, inv = np.unique(cur, return_inverse=True)
    ids[idx] = inv.astype(np.uint32) + space
    return ids, space + u.size


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()
    n = len(data)
    bounds = chunk_bounds(data, n)
    H, BRK, POS = tokenize(data, bounds)
    words = H.size
    if words == 0:
        sys.stdout.buffer.write(b"words 0\npairs 0\ndistinct 0\n")
        return

    ids, space = assign_ids(H)
    del H

    valid = ~BRK[1:]
    del BRK
    keys = (ids[:-1].astype(np.uint64) << np.uint64(32))[valid]
    keys |= ids[1:][valid]
    total = keys.size
    out = ["words %d" % words, "pairs %d" % total]
    if total == 0:
        out.append("distinct 0")
        sys.stdout.buffer.write(("\n".join(out) + "\n").encode())
        return
    keys.sort()
    firsts = np.flatnonzero(keys[1:] != keys[:-1]) + 1
    firsts = np.concatenate((np.zeros(1, dtype=firsts.dtype), firsts))
    counts = np.diff(np.append(firsts, total))
    distinct = firsts.size
    out.append("distinct %d" % distinct)

    if distinct > 20:
        thr = np.partition(counts, distinct - 20)[distinct - 20]
        cand = np.flatnonzero(counts >= thr)
    else:
        cand = np.arange(distinct)
    ck = keys[firsts[cand]]
    ca = (ck >> np.uint64(32)).astype(np.intp)
    cb = (ck & np.uint64(0xFFFFFFFF)).astype(np.intp)
    cc = counts[cand]

    # word text for every id used by a candidate, ranked in byte order
    used = np.unique(np.concatenate((ca, cb)))
    rep = np.zeros(space, dtype=np.int64)
    rep[ids] = np.arange(words)
    word_re = re.compile(rb"[A-Za-z]+")
    text = {}
    for i in used.tolist():
        off = int(POS[rep[i]])
        text[i] = word_re.match(data, off).group().lower()
    rank = np.zeros(space, dtype=np.int64)
    for r, i in enumerate(sorted(text, key=text.__getitem__)):
        rank[i] = r
    order = np.lexsort((rank[cb], rank[ca], -cc))[:20]
    for j in order.tolist():
        out.append("%d %s %s" % (cc[j], text[int(ca[j])].decode(), text[int(cb[j])].decode()))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
