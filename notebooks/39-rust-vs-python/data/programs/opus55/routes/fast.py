import sys

import numpy as np

# Width of the distance window relaxed per round. Small enough that nodes are rarely
# relaxed twice, large enough that each round handles a big batch of nodes at once.
DELTA = 40


def build_csr(n, u, v, w):
    """Adjacency of the undirected graph in CSR form: (indptr, target, weight)."""
    keep = u != v
    u, v, w = u[keep], v[keep], w[keep]
    fr = np.concatenate((u, v))
    to = np.concatenate((v, u))
    ww = np.concatenate((w, w))
    deg = np.bincount(fr, minlength=n)
    indptr = np.zeros(n + 1, np.int64)
    np.cumsum(deg, out=indptr[1:])
    nb = max(n - 1, 1).bit_length()
    if 2 * nb + 10 <= 63:
        # Sorting one packed key (source, target, weight) is much faster than argsort.
        key = (fr << (nb + 10)) | (to << 10) | ww
        key.sort()
        to = (key >> 10) & ((1 << nb) - 1)
        ww = key & 1023
    else:
        order = np.argsort(fr)
        to = to[order]
        ww = ww[order]
    return indptr, deg, to, ww


def main():
    with open(sys.argv[1], "rb") as f:
        a = np.array(f.read().split(), dtype=np.int64)
    n, m, q = int(a[0]), int(a[1]), int(a[2])
    e = a[3:3 + 3 * m].reshape(m, 3)
    sources = a[3 + 3 * m:3 + 3 * m + q]
    indptr, deg, to, ww = build_csr(n, e[:, 0], e[:, 1], e[:, 2])
    del a, e

    # All sources run together on q stacked copies of the graph: node k*n + v is node v in
    # the copy searched from source k. Each round takes the pending nodes whose distance is
    # within DELTA of the smallest pending distance and relaxes all their edges at once.
    # Distances are at most (n - 1) * 1000, so int32 is enough for all but huge graphs.
    dt = np.int32 if n * 1000 < 2**30 else np.int64
    inf = np.iinfo(dt).max // 2
    ww = ww.astype(dt)
    total_nodes = q * n
    dist = np.full(total_nodes, inf, dt)
    pending = np.zeros(total_nodes, bool)
    stamp = np.empty(total_nodes, np.int64)
    start = sources + np.arange(q, dtype=np.int64) * n
    dist[start] = 0
    pending[start] = True
    active = np.unique(start)
    while active.size:
        da = dist[active]
        sel = da < da.min() + DELTA
        f = active[sel]
        active = active[~sel]
        pending[f] = False
        base = f % n
        cnt = deg[base]
        nz = cnt > 0
        if not nz.all():
            f, base, cnt = f[nz], base[nz], cnt[nz]
            if f.size == 0:
                continue
        # Edge ids of all frontier nodes: runs indptr[b] .. indptr[b] + cnt, built as a
        # cumulative sum of ones with a jump at the start of each run.
        st = indptr[base]
        cs = np.cumsum(cnt)
        step = np.ones(int(cs[-1]), np.int64)
        step[0] = st[0]
        step[cs[:-1]] = st[1:] - st[:-1] - cnt[:-1] + 1
        eidx = np.cumsum(step)
        tg = to[eidx]
        tg += np.repeat(f - base, cnt)
        cand = ww[eidx]
        cand += np.repeat(dist[f], cnt)
        better = cand < dist[tg]
        tg = tg[better]
        np.minimum.at(dist, tg, cand[better])
        # Queue improved nodes that are not pending yet, once each (last write wins).
        tg = tg[~pending[tg]]
        ids = np.arange(tg.size)
        stamp[tg] = ids
        tg = tg[stamp[tg] == ids]
        pending[tg] = True
        active = np.concatenate((active, tg))

    out = []
    for k, row in enumerate(dist.reshape(q, n)):
        reach = row < inf
        r = row[reach]
        far = int(r.max())
        out.append(f"{int(sources[k])} {r.size} {int(r.sum(dtype=np.int64))} {far} {int(np.argmax(row == far))}\n")
    sys.stdout.buffer.write("".join(out).encode())


main()
