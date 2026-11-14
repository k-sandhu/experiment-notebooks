import sys
import os
import numpy as np

BITS = 20
NB = 1 << BITS
SH = np.uint64(64 - BITS)
TAB = np.empty(NB, np.uint64)
MULTS = [np.uint64(x) for x in (
    0x9E3779B97F4A7C15, 0xC2B2AE3D27D4EB4F, 0x165667B19E3779F9, 0xD6E8FEB86659FD93,
    0xFF51AFD7ED558CCD, 0xC4CEB9FE1A85EC53, 0x2545F4914F6CDD1D, 0x9FB21C651E98DF25)]
MASKS = np.array([(1 << (8 * i)) - 1 for i in range(9)], dtype=np.uint64)

_t = bytearray(256)
_t2 = bytearray(b' ' * 256)
for _c in range(65, 91):
    _t[_c] = _c + 32
    _t[_c + 32] = _c + 32
    _t2[_c] = _c + 32
    _t2[_c + 32] = _c + 32
for _c in b'.!?':
    _t[_c] = 1
    _t2[_c] = 46
TAB1 = bytes(_t)
TAB2 = bytes(_t2)


def ident(keys):
    """Map each distinct uint64 key to a distinct integer id (exact)."""
    h = keys * MULTS[0]
    h >>= SH
    h = h.view(np.intp)
    TAB[h] = keys
    rem = np.flatnonzero(TAB[h] != keys)
    if rem.size == 0:
        return h, NB
    ids = h
    r = 1
    while rem.size:
        if r >= 1024:
            raise OverflowError
        cur = keys[rem]
        h = cur * MULTS[r & 7]
        h >>= SH
        h = h.view(np.intp)
        TAB[h] = cur
        ok = TAB[h] == cur
        h += r << BITS
        ids[rem] = h
        rem = rem[~ok]
        r += 1
    return ids, r << BITS


def fast(buf):
    low = buf.translate(TAB1)
    L = len(low)
    arr = np.frombuffer(low, dtype=np.uint8)
    m = arr >= 97
    b = np.flatnonzero(m[1:] != m[:-1])
    del m
    nw = b.size >> 1
    if nw == 0:
        return "words 0\npairs 0\ndistinct 0\n"
    starts = np.ascontiguousarray(b[0::2])
    lens = b[1::2] - starts
    del b
    maxlen = int(lens.max())
    if maxlen > 64:
        raise OverflowError

    tpos = np.flatnonzero(arr == 1)
    brk = np.zeros(nw + 1, np.bool_)
    if tpos.size:
        brk[np.searchsorted(starts, tpos)] = True
    del tpos

    v = np.ndarray((L - 8,), dtype=np.uint64, buffer=low, offset=1, strides=(1,))
    k0 = v[starts]
    k0 &= MASKS[np.minimum(lens, 8)]
    ids, space = ident(k0)
    del k0

    if maxlen > 8:
        sub = np.flatnonzero(lens > 8)
        pid = ids[sub]
        st = starts[sub]
        ln = lens[sub]
        while True:
            if space >= (1 << 31):
                raise OverflowError
            st += 8
            ln -= 8
            c = v[st]
            c &= MASKS[np.minimum(ln, 8)]
            cid, _ = ident(c)
            comb = (pid << 32) | cid
            nid, nk = ident(comb.view(np.uint64))
            nid += space
            space += nk
            ids[sub] = nid
            more = np.flatnonzero(ln > 8)
            if more.size == 0:
                break
            sub = sub[more]
            pid = nid[more]
            st = st[more]
            ln = ln[more]
        del sub, pid, st, ln, c, cid, comb, nid

    mark = np.zeros(space, np.bool_)
    mark[ids] = True
    used = np.flatnonzero(mark)
    del mark
    V = int(used.size)
    rep = np.empty(space, np.intp)
    rep[ids] = np.arange(nw, dtype=np.intp)
    repw = rep[used]
    del rep
    sa = starts[repw]
    sa += 1
    se = sa + lens[repw]
    words = [low[a:e].decode('ascii') for a, e in zip(sa.tolist(), se.tolist())]
    order = sorted(range(V), key=words.__getitem__)
    sw = [words[i] for i in order]

    if V * V < (1 << 32):
        dt = np.uint32
        sent = 0xFFFFFFFF
    else:
        dt = np.uint64
        sent = 0xFFFFFFFFFFFFFFFF
    rank = np.empty(V, dt)
    rank[np.array(order, dtype=np.intp)] = np.arange(V, dtype=dt)
    cmap = np.empty(space, dt)
    cmap[used] = rank
    wid = cmap[ids]
    del cmap, ids, used

    lines = ["words %d" % nw]
    T = 0
    D = 0
    pair_lines = []
    if nw >= 2:
        key = wid[:-1] * dt(V)
        key += wid[1:]
        inv = brk[1:nw]
        ninv = int(np.count_nonzero(inv))
        if ninv:
            np.putmask(key, inv, dt(sent))
        key.sort()
        T = nw - 1 - ninv
        if T > 0:
            pk = key[:T]
            chg = np.flatnonzero(pk[1:] != pk[:-1])
            D = int(chg.size) + 1
            rs = np.empty(D + 1, np.intp)
            rs[0] = 0
            if D > 1:
                rs[1:D] = chg
                rs[1:D] += 1
            rs[D] = T
            counts = np.diff(rs)
            if D > 20:
                c20 = np.partition(counts, D - 20)[D - 20]
                gt = np.flatnonzero(counts > c20)
                if gt.size:
                    gt = gt[np.argsort(-counts[gt], kind='stable')]
                eq = np.flatnonzero(counts == c20)[:20 - gt.size]
                sel = np.concatenate((gt, eq))
            else:
                sel = np.argsort(-counts, kind='stable')
            for i in sel.tolist():
                c = int(counts[i])
                k = int(pk[rs[i]])
                a, bb = divmod(k, V)
                pair_lines.append("%d %s %s" % (c, sw[a], sw[bb]))
    lines.append("pairs %d" % T)
    lines.append("distinct %d" % D)
    lines.extend(pair_lines)
    return "\n".join(lines) + "\n"


def slow(buf):
    from collections import Counter
    import heapq
    t = bytes(buf).translate(TAB2)
    cnt = Counter()
    W = 0
    for s in t.split(b'.'):
        ws = s.split()
        k = len(ws)
        W += k
        if k > 1:
            cnt.update(zip(ws, ws[1:]))
    T = sum(cnt.values())
    D = len(cnt)
    top = heapq.nsmallest(20, cnt.items(), key=lambda kv: (-kv[1], kv[0]))
    lines = ["words %d" % W, "pairs %d" % T, "distinct %d" % D]
    for (a, b), c in top:
        lines.append("%d %s %s" % (c, a.decode('ascii'), b.decode('ascii')))
    return "\n".join(lines) + "\n"


def main():
    path = sys.argv[1]
    with open(path, 'rb', buffering=0) as f:
        n = os.fstat(f.fileno()).st_size
        buf = bytearray(n + 16)
        mv = memoryview(buf)
        pos = 1
        end = n + 1
        while pos < end:
            k = f.readinto(mv[pos:end])
            if not k:
                break
            pos += k
        mv.release()
    try:
        out = fast(buf)
    except Exception:
        out = slow(buf)
    sys.stdout.write(out)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
