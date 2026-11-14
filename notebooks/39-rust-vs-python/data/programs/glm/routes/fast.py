import sys
from heapq import heappush, heappop

import numpy as np

SHIFT = 8  # bucket width: light edges have w <= 2**SHIFT


class _Abort(Exception):
    """Raised when the bucket scheme degenerates for a source."""


def dijkstra_heap(n, s, indptr_l, targets_l, weights_l, nb):
    """Plain heap Dijkstra on Python-list CSR; used for degenerate sources."""
    mask = (1 << nb) - 1
    inf = 1 << 62
    dist = [inf] * n
    dist[s] = 0
    heap = [s]  # packed (d << nb) | v with d == 0
    while heap:
        key = heappop(heap)
        v = key & mask
        d = key >> nb
        if d != dist[v]:
            continue  # stale entry
        for u, w in zip(targets_l[indptr_l[v]:indptr_l[v + 1]],
                        weights_l[indptr_l[v]:indptr_l[v + 1]]):
            nd = d + w
            if nd < dist[u]:
                dist[u] = nd
                heappush(heap, (nd << nb) | u)
    total = 0
    cnt = 0
    far = 0
    for x in dist:
        if x != inf:
            cnt += 1
            total += x
            if x > far:
                far = x
    return cnt, total, far, dist.index(far)


def bucket_dijkstra(n, s, dist, l_indptr, l_targets, l_weights, h_indptr,
                    h_targets, h_weights, l_indptr_l, nb, wave_limit,
                    visit_limit):
    """Delta-stepping: bucket-ordered label-correcting with vectorized waves.

    Light edges (w <= 2**SHIFT) are re-relaxed on every improvement inside a
    bucket; heavy edges are relaxed exactly once per bucket, after it
    converges, using the final distances of the nodes settled in it.
    """
    INF = np.int64(1 << 62)
    DMASK = (1 << 32) - 1   # distances are < 2^32 (N * 1000)
    THRESH = 24             # waves smaller than this use the scalar path
    future = {}             # bucket id -> list of pending node arrays
    pend = []               # packed cross-bucket improvements of current bucket
    waves = 0
    scalar_visits = 0
    k = 0
    W = np.array([s], dtype=np.int64)
    settled = []            # node arrays settled into the current bucket
    while True:
        # --- light cascade: converge bucket k ---
        while W.size:
            waves += 1
            if waves > wave_limit or scalar_visits > visit_limit:
                raise _Abort
            if W.size >= THRESH:
                start = l_indptr[W]
                deg = l_indptr[W + 1] - start
                nl = int(deg.sum())
                settled.append(W)
                if nl:
                    csum = np.cumsum(deg)
                    idx = np.repeat(start - (csum - deg), deg) + \
                        np.arange(nl, dtype=np.int64)
                    tgt = l_targets[idx]
                    cand = np.repeat(dist[W], deg) + l_weights[idx]
                    imp = cand < dist[tgt]
                    t = tgt[imp]
                    c = cand[imp]
                    if t.size:
                        # min-reduce per target: pack, sort, first per node
                        key = (t << 32) | c
                        key.sort()
                        t = key >> 32
                        c = key & DMASK
                        first = np.empty(t.size, dtype=bool)
                        first[0] = True
                        if t.size > 1:
                            np.not_equal(t[1:], t[:-1], out=first[1:])
                        t = t[first]
                        c = c[first]
                        dist[t] = c
                        b = c >> SHIFT
                        same_m = b == k
                        W = t[same_m]
                        rest = t[~same_m]
                        if rest.size:
                            pend.append((b[~same_m] << nb) | rest)
                    else:
                        W = W[:0]
                else:
                    W = W[:0]
            else:
                # scalar path for small waves (light edges only)
                scalar_visits += W.size
                settled.append(W)
                nxt = []
                fset = future.setdefault
                for u in W.tolist():
                    p = l_indptr_l[u]
                    pe = l_indptr_l[u + 1]
                    du = int(dist[u])
                    tl = l_targets[p:pe].tolist()
                    wl = l_weights[p:pe].tolist()
                    for j in range(pe - p):
                        v = tl[j]
                        nd = du + wl[j]
                        if nd < dist[v]:
                            dist[v] = nd
                            b = nd >> SHIFT
                            if b == k:
                                nxt.append(v)
                            else:
                                fset(b, []).append(
                                    np.array([v], dtype=np.int64))
                W = np.array(nxt, dtype=np.int64)
        # --- bucket converged: relax heavy edges once, with final dists ---
        if settled:
            S = np.unique(np.concatenate(settled)) if len(settled) > 1 \
                else settled[0]
            settled = []
            start = h_indptr[S]
            deg = h_indptr[S + 1] - start
            nl = int(deg.sum())
            if nl:
                csum = np.cumsum(deg)
                idx = np.repeat(start - (csum - deg), deg) + \
                    np.arange(nl, dtype=np.int64)
                tgt = h_targets[idx]
                cand = np.repeat(dist[S], deg) + h_weights[idx]
                imp = cand < dist[tgt]
                t = tgt[imp]
                c = cand[imp]
                if t.size:
                    key = (t << 32) | c
                    key.sort()
                    t = key >> 32
                    c = key & DMASK
                    first = np.empty(t.size, dtype=bool)
                    first[0] = True
                    if t.size > 1:
                        np.not_equal(t[1:], t[:-1], out=first[1:])
                    t = t[first]
                    c = c[first]
                    dist[t] = c
                    pend.append(((c >> SHIFT) << nb) | t)
        # --- distribute cross-bucket improvements to future buckets ---
        if pend:
            keys = np.concatenate(pend)
            pend.clear()
            keys.sort()
            t = keys & ((1 << nb) - 1)
            rb = keys >> nb
            change = np.flatnonzero(rb[1:] != rb[:-1])
            bs = np.concatenate(([0], change + 1))
            be = np.concatenate((change + 1, [rb.size]))
            for a, e in zip(bs.tolist(), be.tolist()):
                future.setdefault(int(rb[a]), []).append(t[a:e])
        if future:
            k = min(future)
            fl = future.pop(k)
            W = np.concatenate(fl) if len(fl) > 1 else fl[0]
        else:
            break

    reach = dist != INF
    dm = dist[reach]
    total = int(dm.sum())
    far = int(dm.max())
    node = int(np.flatnonzero(dist == far)[0])
    return int(dm.size), total, far, node


def main():
    buf = open(sys.argv[1], 'rb').read()
    toks = buf.split()
    arr = np.array(toks, dtype=np.int64)
    del toks, buf
    n, m, q = int(arr[0]), int(arr[1]), int(arr[2])
    sources = arr[3 + 3 * m: 3 + 3 * m + q].tolist()

    # CSR adjacency (both directions), built with vectorized ops.
    eu = arr[3:3 + 3 * m:3]
    ev = arr[4:4 + 3 * m:3]
    ew = arr[5:5 + 3 * m:3]
    src = np.concatenate((eu, ev))
    dst = np.concatenate((ev, eu))
    wts = np.concatenate((ew, ew))
    order = np.argsort(src.astype(np.int32))  # quicksort: group order irrelevant
    targets = dst[order]
    weights = wts[order]
    counts = np.bincount(src, minlength=n)
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(counts, out=indptr[1:])
    del arr, src, dst, wts, order, counts, eu, ev, ew

    # Split into light (w <= DELTA) and heavy CSR.
    DELTA = 1 << SHIFT
    light_m = weights <= DELTA
    src_sorted = np.repeat(np.arange(n, dtype=np.int64), np.diff(indptr))
    l_indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(np.bincount(src_sorted[light_m], minlength=n), out=l_indptr[1:])
    l_targets = targets[light_m]
    l_weights = weights[light_m]
    h_indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(np.bincount(src_sorted[~light_m], minlength=n), out=h_indptr[1:])
    h_targets = targets[~light_m]
    h_weights = weights[~light_m]
    l_indptr_l = l_indptr.tolist()  # for the scalar path on small waves
    del light_m, src_sorted

    nb = max(1, (n - 1).bit_length())  # bits for a node id
    wave_limit = max(500, n >> 4)
    visit_limit = max(2000, n >> 4)

    out = []
    fb = None  # lazily built Python CSR lists for the fallback Dijkstra
    for s in sources:
        dist = np.full(n, np.int64(1 << 62), dtype=np.int64)
        dist[s] = 0
        try:
            cnt, total, far, node = bucket_dijkstra(
                n, s, dist, l_indptr, l_targets, l_weights, h_indptr,
                h_targets, h_weights, l_indptr_l, nb, wave_limit, visit_limit)
        except _Abort:
            if fb is None:
                fb = (indptr.tolist(), targets.tolist(), weights.tolist())
            cnt, total, far, node = dijkstra_heap(n, s, fb[0], fb[1], fb[2], nb)
        out.append('%d %d %d %d %d' % (s, cnt, total, far, node))

    sys.stdout.buffer.write(('\n'.join(out) + '\n').encode())


main()
