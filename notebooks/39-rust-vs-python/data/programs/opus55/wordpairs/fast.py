import sys

import numpy as np
from numpy.lib.stride_tricks import as_strided

U64 = np.uint64
M8 = U64(0x00FF00FF00FF00FF)
M16 = U64(0x0000FFFF0000FFFF)
M32 = U64(0xFFFFFFFF)
HASH = U64(0x9E3779B97F4A7C15)
MAX_LEVELS = 4


def pack5(x, t, steps):
    """Packs in place the 5-bit codes held in the bytes of x, first byte most
    significant. `t` is scratch space; 2 steps pack 4 bytes, 3 steps 8 bytes."""
    for mask, sh in ((M8, 8), (M16, 16), (M32, 32))[:steps]:
        np.right_shift(x, U64(sh), out=t)
        if sh != 32:
            t &= mask
        t <<= U64(sh * 5 // 8)
        x &= mask
        x |= t


def word_ids(keys):
    """Maps every key to its rank among the distinct keys, using a hash table
    probed in bulk. Returns (ids, number of distinct keys)."""
    uk = np.sort(keys)
    if len(uk):
        uk = uk[np.concatenate(([True], uk[1:] != uk[:-1]))]
    nv = len(uk)
    bits = max((4 * nv).bit_length(), 4)
    mask = (1 << bits) - 1
    shift = U64(64 - bits)
    tkey = np.zeros(1 << bits, U64)
    tval = np.zeros(1 << bits, np.int32)

    h = ((uk * HASH) >> shift).view(np.int64)
    pend = np.arange(nv)
    while len(pend):
        hp = h[pend]
        free = tkey[hp] == 0
        tkey[hp[free]] = uk[pend[free]]
        won = tkey[hp] == uk[pend]
        tval[hp[won]] = pend[won]
        pend = pend[~won]
        h[pend] = (h[pend] + 1) & mask

    h = keys * HASH
    h >>= shift
    h = h.view(np.int64)
    ids = tval[h]
    bad = np.flatnonzero(tkey[h] != keys)
    while len(bad):
        hb = (h[bad] + 1) & mask
        h[bad] = hb
        ids[bad] = tval[hb]
        bad = bad[tkey[hb] != keys[bad]]
    return ids, nv


# Shifts that clear the bytes past the end of a word, by its length (capped at 12).
SH8 = np.array([8 * max(8 - k, 0) for k in range(13)], U64)
SH4 = np.array([8 * min(max(12 - k, 0), 4) for k in range(13)], U64)


def chunk_keys(codes, n, pos, rem):
    """Keys of the 12 letters at `pos` (fewer if `rem` < 12) as 5-bit codes,
    a=1 .. z=26 and zero padded, so keys compare like the letter strings."""
    x = as_strided(codes, shape=(n + 8, 8), strides=(1, 1))[pos].view(">u8").ravel().astype(U64)
    y = as_strided(codes[8:], shape=(n + 4, 4), strides=(1, 1))[pos].view(">u4").ravel().astype(U64)
    r = np.minimum(rem, 12)
    sh = SH8[r]
    x >>= sh
    x <<= sh
    sh = SH4[r]
    y >>= sh
    y <<= sh
    del sh, r
    pack5(x, np.empty_like(x), 3)
    pack5(y, np.empty_like(y), 2)
    x <<= U64(20)
    x |= y
    return x


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    n = len(data)
    buf = np.zeros(n + 16, np.uint8)
    buf[:n] = np.frombuffer(data, np.uint8)

    isl = ((buf | 0x20) - 97) < 26
    edges = np.flatnonzero(isl[1:] != isl[:-1]) + 1
    if isl[0]:
        edges = np.concatenate(([0], edges))
    starts = edges[0::2]
    ends = edges[1::2]
    del edges
    nwords = len(starts)
    lens = ends - starts

    codes = (buf & 31) * isl
    del isl
    k12 = chunk_keys(codes, n, starts, lens)
    wid, nvocab = word_ids(k12)

    # Longer words: refine the id with each further 12 letters, so words get
    # new ids in a fresh range at every level. Very long words use a dict.
    lvl = np.flatnonzero(lens > 12)
    very = lvl[lens[lvl] > 12 * MAX_LEVELS]
    lvl = lvl[lens[lvl] <= 12 * MAX_LEVELS]
    off = 12
    while len(lvl):
        sub, nsub = word_ids(chunk_keys(codes, n, starts[lvl] + off, lens[lvl] - off))
        comp = wid[lvl].astype(np.int64) * nsub + sub
        comp += 1
        cid, nc = word_ids(comp.view(U64))
        wid[lvl] = cid + nvocab
        nvocab += nc
        off += 12
        lvl = lvl[lens[lvl] > off]
    del codes
    if len(very):
        lower = data.lower()
        strs = [lower[s:e] for s, e in zip(starts[very].tolist(), ends[very].tolist())]
        ids = dict.fromkeys(strs)
        for i, w in enumerate(ids):
            ids[w] = i
        wid[very] = np.array(list(map(ids.__getitem__, strs)), np.int64) + nvocab
        nvocab += len(ids)
        del strs, ids, lower

    # One occurrence of each word (ids that no word ended up with stay unset).
    rep = np.empty(nvocab, np.int64)
    rep[wid] = np.arange(nwords)

    # Pair i joins words i and i+1 unless a sentence end lies between them.
    isterm = buf == 46
    isterm |= buf == 33
    isterm |= buf == 63
    if nwords:
        # Each segment runs from a word start to the next word start.
        valid = ~np.logical_or.reduceat(isterm, starts)[:-1]
    else:
        valid = np.zeros(0, bool)
    del isterm
    pk = wid[:-1][valid].astype(np.int64)
    pk *= nvocab
    pk += wid[1:][valid]
    del wid, valid
    npairs = len(pk)
    pk.sort()

    out = [f"words {nwords}", f"pairs {npairs}"]
    if npairs == 0:
        out.append("distinct 0")
    else:
        runs = np.flatnonzero(np.concatenate(([True], pk[1:] != pk[:-1])))
        counts = np.diff(np.append(runs, npairs))
        upk = pk[runs]
        del pk, runs
        distinct = len(upk)
        out.append(f"distinct {distinct}")

        if distinct <= 20:
            sel = np.arange(distinct)
        else:
            thr = np.partition(counts, distinct - 20)[distinct - 20]
            above = np.flatnonzero(counts > thr)
            tied = np.flatnonzero(counts == thr)
            need = 20 - len(above)
            if len(tied) > need:
                # Keep the tied pairs that can still make the cut by their
                # 12-letter prefixes; exact strings settle the rest below.
                wa = upk[tied] // nvocab
                ka = k12[rep[wa]]
                kb = k12[rep[upk[tied] % nvocab]]
                o = np.lexsort((kb, ka))
                ba, bb = ka[o[need - 1]], kb[o[need - 1]]
                same = ka == ba
                # The second words only decide if the first words are equal.
                if (wa[same] == wa[same][0]).all():
                    same &= kb <= bb
                tied = tied[(ka < ba) | same]
            sel = np.concatenate((above, tied))

        def word(i):
            p = rep[i]
            return data[starts[p] : ends[p]].lower().decode()

        top = []
        for c, k in zip(counts[sel].tolist(), upk[sel].tolist()):
            a, b = divmod(k, nvocab)
            top.append((-c, word(a), word(b)))
        top.sort()
        out.extend(f"{-c} {a} {b}" for c, a, b in top[:20])

    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
