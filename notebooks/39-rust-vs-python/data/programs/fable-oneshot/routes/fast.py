import sys
import numpy as np
from heapq import heapify, heappop, heappush


def distribute(buckets, t, kb):
    lo = int(kb.min())
    hi = int(kb.max())
    if lo == hi:
        lst = buckets.get(lo)
        if lst is None:
            buckets[lo] = [t]
        else:
            lst.append(t)
        return
    off = kb - lo
    r = hi - lo
    if r < 65536:
        if r < 256:
            order = np.argsort(off.astype(np.uint8), kind='stable')
        else:
            order = np.argsort(off.astype(np.uint16), kind='stable')
        ts = t[order]
        p = 0
        j = lo
        for cn in np.bincount(off).tolist():
            if cn:
                q = p + cn
                lst = buckets.get(j)
                if lst is None:
                    buckets[j] = [ts[p:q]]
                else:
                    lst.append(ts[p:q])
                p = q
            j += 1
    else:
        order = np.argsort(off, kind='stable')
        ts = t[order]
        ks = off[order]
        cut = (np.flatnonzero(ks[1:] != ks[:-1]) + 1).tolist()
        st = [0] + cut
        en = cut + [int(ts.size)]
        keys = ks[st].tolist()
        for i in range(len(st)):
            j = lo + keys[i]
            lst = buckets.get(j)
            if lst is None:
                buckets[j] = [ts[st[i]:en[i]]]
            else:
                lst.append(ts[st[i]:en[i]])


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
    n = len(data)
    if n == 0:
        return
    buf = np.frombuffer(data, dtype=np.uint8)
    dg = buf - np.uint8(48)
    isd = dg < 10
    bnd = np.flatnonzero(isd[1:] != isd[:-1]) + 1
    if isd[0]:
        bnd = np.concatenate((np.zeros(1, dtype=np.int64), bnd))
    if isd[-1]:
        bnd = np.concatenate((bnd, np.array([n], dtype=np.int64)))
    starts = bnd[0::2]
    stops = bnd[1::2]
    if starts.size < 3:
        return
    lens = stops - starts
    ends = stops - 1
    vals = dg[ends].astype(np.int64)
    act = np.flatnonzero(lens > 1)
    if act.size:
        e = ends[act]
        l = lens[act]
        k = 1
        mult = 10
        while True:
            vals[act] += dg[e - k].astype(np.int64) * mult
            k += 1
            mult *= 10
            m = l > k
            if not m.any():
                break
            act = act[m]
            e = e[m]
            l = l[m]

    N = int(vals[0])
    M = int(vals[1])
    Q = int(vals[2])
    E = vals[3:3 + 3 * M]
    eu = E[0::3]
    ev = E[1::3]
    ew = E[2::3]
    srcs_all = vals[3 + 3 * M:3 + 3 * M + Q].tolist()
    Q = len(srcs_all)
    if Q == 0 or N <= 0:
        return

    maxw = int(ew.max()) if ew.size > 0 else 1
    if maxw < 1:
        maxw = 1
    wb = maxw.bit_length()
    nbits = max(1, (N - 1).bit_length())
    ne = eu != ev
    uu = eu[ne]
    vv = ev[ne]
    ww = ew[ne]
    k = int(uu.size)
    if k > 0 and 2 * nbits + wb <= 62:
        hi = nbits + wb
        key = np.empty(2 * k, dtype=np.int64)
        key[:k] = (uu << hi) | (vv << wb) | ww
        key[k:] = (vv << hi) | (uu << wb) | ww
        key.sort()
        p = key >> wb
        keep = np.empty(2 * k, dtype=bool)
        keep[0] = True
        np.not_equal(p[1:], p[:-1], out=keep[1:])
        key = key[keep]
        p = p[keep]
        wt = key & ((1 << wb) - 1)
        adj = p & ((1 << nbits) - 1)
        deg = np.bincount(p >> nbits, minlength=N)
    else:
        src = np.concatenate((uu, vv))
        dst = np.concatenate((vv, uu))
        w2 = np.concatenate((ww, ww))
        order = np.argsort(src, kind='stable')
        adj = dst[order]
        wt = w2[order]
        deg = np.bincount(src, minlength=N)
    deg = deg.astype(np.int64, copy=False)
    indptr = np.zeros(N + 1, dtype=np.int64)
    np.cumsum(deg, out=indptr[1:])
    ip0 = indptr[:-1]

    INF = 1 << 60
    minshift = max(0, wb - 6)
    maxshift = wb
    W = 16
    LOWN = 256 * W
    HIGHN = 4096 * W
    FALLN = 32 * W

    QB = max(1, min(Q, 4000000 // N))
    nbl = None
    wll = None
    out = []

    for cs in range(0, Q, QB):
        srcs = srcs_all[cs:cs + QB]
        nq = len(srcs)
        S = nq * N
        multi = nq > 1
        dist = np.full(S, INF, dtype=np.int64)
        c0 = np.array([q * N + s for q, s in enumerate(srcs)], dtype=np.int64)
        dist[c0] = 0
        buckets = {0: [c0]}
        shift = min(maxshift, minshift + 1)
        lowd = 0
        win_steps = 0
        win_nodes = 0
        lowcount = 0
        fallback = False

        while buckets:
            if win_steps >= W:
                ns = shift
                if win_nodes < LOWN:
                    if shift < maxshift:
                        ns = shift + 1
                        lowcount = 0
                    else:
                        lowcount += 1
                        if lowcount >= 4 and win_nodes < FALLN:
                            fallback = True
                            break
                else:
                    lowcount = 0
                    if win_nodes > HIGHN and shift > minshift:
                        ns = shift - 1
                win_steps = 0
                win_nodes = 0
                if ns != shift:
                    arrs = [x for lst in buckets.values() for x in lst]
                    allc = np.concatenate(arrs)
                    ad = dist[allc]
                    m = ad >= lowd
                    allc = allc[m]
                    ad = ad[m]
                    buckets = {}
                    shift = ns
                    if allc.size:
                        distribute(buckets, allc, ad >> shift)
                    continue

            b = min(buckets)
            chunks = buckets.pop(b)
            lowd = b << shift
            if len(chunks) == 1:
                c = np.sort(chunks[0])
            else:
                c = np.concatenate(chunks)
                c.sort()
            d = dist[c]
            m = (d >> shift) == b
            m[1:] &= c[1:] != c[:-1]
            c = c[m]
            cn = int(c.size)
            win_steps += 1
            if cn == 0:
                continue
            win_nodes += cn
            d = d[m]
            if multi:
                v = c % N
                offs = c - v
            else:
                v = c
            cnt = deg[v]
            ce = np.cumsum(cnt)
            tot = int(ce[-1])
            if tot == 0:
                continue
            idx = np.repeat(ip0[v] - ce + cnt, cnt)
            idx += np.arange(tot, dtype=np.int64)
            t = adj[idx]
            if multi:
                t += np.repeat(offs, cnt)
            nd = wt[idx]
            nd += np.repeat(d, cnt)
            m = nd < dist[t]
            t = t[m]
            if t.size == 0:
                continue
            nd = nd[m]
            np.minimum.at(dist, t, nd)
            m = nd == dist[t]
            t = t[m]
            nd = nd[m]
            distribute(buckets, t, nd >> shift)

        if fallback:
            arrs = [x for lst in buckets.values() for x in lst]
            pend = np.unique(np.concatenate(arrs))
            pdv = dist[pend]
            m = pdv >= lowd
            pend = pend[m]
            pdv = pdv[m]
            distl = dist.tolist()
            heap = [dd * S + cc for dd, cc in zip(pdv.tolist(), pend.tolist())]
            heapify(heap)
            if nbl is None:
                ipl = indptr.tolist()
                adjl = adj.tolist()
                wtl = wt.tolist()
                nbl = [adjl[ipl[i]:ipl[i + 1]] for i in range(N)]
                wll = [wtl[ipl[i]:ipl[i + 1]] for i in range(N)]
            pop = heappop
            push = heappush
            while heap:
                hk = pop(heap)
                dd, cc = divmod(hk, S)
                if dd > distl[cc]:
                    continue
                vx = cc % N
                ofx = cc - vx
                for tt, wx in zip(nbl[vx], wll[vx]):
                    x = dd + wx
                    tt += ofx
                    if x < distl[tt]:
                        distl[tt] = x
                        push(heap, x * S + tt)
            dist = np.array(distl, dtype=np.int64)

        for q, s in enumerate(srcs):
            dq = dist[q * N:(q + 1) * N]
            reach = dq < INF
            R = int(np.count_nonzero(reach))
            dz = np.where(reach, dq, -1)
            far = int(dz.max())
            node = int(dz.argmax())
            total = int(dz.sum()) + (N - R)
            out.append("%d %d %d %d %d\n" % (s, R, total, far, node))

    sys.stdout.write(''.join(out))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
