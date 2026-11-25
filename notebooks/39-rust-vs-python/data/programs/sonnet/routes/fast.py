import sys
import numpy as np

INF = np.int64(1) << 60


def parse_ints(raw):
    b = np.frombuffer(raw, dtype=np.uint8)
    d = b - np.uint8(48)
    isd = d < 10
    flag = np.empty(b.size + 2, dtype=np.int8)
    flag[0] = 0
    flag[-1] = 0
    flag[1:-1] = isd
    edge = np.diff(flag)
    starts = np.flatnonzero(edge == 1)
    lens = np.flatnonzero(edge == -1) - starts
    val = np.zeros(starts.size, dtype=np.int64)
    k = 0
    maxlen = int(lens.max()) if lens.size else 0
    while k < maxlen:
        if k == 0:
            val = d[starts].astype(np.int64)
        else:
            sel = np.flatnonzero(lens > k)
            val[sel] = val[sel] * 10 + d[starts[sel] + k]
        k += 1
    return val


def main():
    with open(sys.argv[1], "rb") as f:
        raw = f.read()
    a = parse_ints(raw)
    del raw
    n, m, q = int(a[0]), int(a[1]), int(a[2])
    e = a[3:3 + 3 * m].reshape(m, 3)
    sources = a[3 + 3 * m:3 + 3 * m + q].tolist()
    u = e[:, 0]
    v = e[:, 1]
    w = e[:, 2]
    keep = u != v
    if not keep.all():
        u, v, w = u[keep], v[keep], w[keep]
    src = np.concatenate((u, v))
    dst = np.concatenate((v, u))
    wt = np.concatenate((w, w))
    maxw = int(wt.max()) if wt.size else 1
    bw = max(maxw, 1).bit_length()
    bn = max(n, 1).bit_length()
    if 2 * bn + bw <= 62:
        key = (src << (bn + bw)) | (dst << bw) | wt
        key.sort()
        adj = (key >> bw) & ((1 << bn) - 1)
        wts = key & ((1 << bw) - 1)
        del key
    else:
        order = np.argsort(src)
        adj = dst[order]
        wts = wt[order]
    deg = np.bincount(src, minlength=n)
    start = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(deg, out=start[1:])
    del src, dst, wt, a, e, u, v, w
    st = start[:-1]
    delta = max(maxw // 2, 1)

    minimum_at = np.minimum.at
    out = []
    cache = {}
    for s in sources:
        line = cache.get(s)
        if line is None:
            dist = np.full(n, INF, dtype=np.int64)
            dist[s] = 0
            relaxed = np.full(n, -1, dtype=np.int64)
            stamp = np.zeros(n, dtype=np.int64)
            pending = np.array([s], dtype=np.int64)
            while pending.size:
                pd = dist[pending]
                lo = pd.min()
                sel = pd < lo + delta
                if sel.all():
                    act = pending
                    pending = pending[:0]
                else:
                    act = pending[sel]
                    pending = pending[~sel]
                # drop duplicates and nodes already relaxed at their current distance
                da = dist[act]
                ok = relaxed[act] != da
                if not ok.all():
                    act = act[ok]
                    da = da[ok]
                if act.size > 1:
                    ar = np.arange(act.size)
                    stamp[act] = ar
                    ok = stamp[act] == ar
                    if not ok.all():
                        act = act[ok]
                        da = da[ok]
                relaxed[act] = da
                cnt = deg[act]
                tot = int(cnt.sum())
                if tot == 0:
                    continue
                cs = np.cumsum(cnt)
                idx = np.arange(tot) + np.repeat(st[act] - (cs - cnt), cnt)
                nv = adj[idx]
                nd = wts[idx] + np.repeat(da, cnt)
                old = dist[nv]
                better = nd < old
                if not better.any():
                    continue
                nv = nv[better]
                nd = nd[better]
                old = old[better]
                minimum_at(dist, nv, nd)
                ch = dist[nv] < old
                new = nv[ch]
                if new.size:
                    pending = np.concatenate((pending, new)) if pending.size else new
            reach = dist < INF
            r = int(reach.sum())
            total = int(dist[reach].sum())
            far = int(dist[reach].max())
            node = int(np.argmax(dist == far))
            line = "%d %d %d %d %d" % (s, r, total, far, node)
            cache[s] = line
        out.append(line)
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
