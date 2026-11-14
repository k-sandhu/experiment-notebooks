import sys
import heapq

import numpy as np

DELTA = 256


def relax_edges(frontier, starts, nbr, wt, dist, settled, want_light):
    """Relax light (or heavy) edges out of `frontier`; return unique improved nodes."""
    if frontier.size == 0:
        return frontier
    cnt = starts[frontier + 1] - starts[frontier]
    total = int(cnt.sum())
    if total == 0:
        return np.empty(0, dtype=np.int64)
    cum = np.cumsum(cnt)
    edge_idx = (
        np.arange(total, dtype=np.int64)
        - np.repeat(cum - cnt, cnt)
        + np.repeat(starts[frontier], cnt)
    )
    src_e = np.repeat(frontier, cnt)
    dst_e = nbr[edge_idx]
    w_e = wt[edge_idx]
    if want_light:
        mask = w_e <= DELTA
    else:
        mask = w_e > DELTA
    if not bool(mask.any()):
        return np.empty(0, dtype=np.int64)
    dst_e = dst_e[mask]
    cand = dist[src_e[mask]] + w_e[mask]
    keep = (cand < dist[dst_e]) & ~settled[dst_e]
    if not bool(keep.any()):
        return np.empty(0, dtype=np.int64)
    dst_i = dst_e[keep]
    np.minimum.at(dist, dst_i, cand[keep])
    return np.unique(dst_i)


def add_pending(pending, heap, inheap, nodes, dist):
    buckets = (dist[nodes] // DELTA).astype(int)
    for b in np.unique(buckets):
        sel = nodes[buckets == b]
        pending.setdefault(int(b), []).append(sel.copy())
        if int(b) not in inheap:
            heapq.heappush(heap, int(b))
            inheap.add(int(b))


def delta_source(s, n, starts, nbr, wt):
    inf = np.int64(1 << 60)
    dist = np.full(n, inf, dtype=np.int64)
    dist[s] = 0
    settled = np.zeros(n, dtype=bool)
    pending = {0: [np.array([s], dtype=np.int64)]}
    heap = [0]
    inheap = {0}
    reached = 0
    total = 0
    far = 0
    far_node = s

    while heap:
        k = heapq.heappop(heap)
        inheap.discard(k)
        arrays = pending.pop(k, None)
        if arrays is None:
            continue
        low = k * DELTA
        high = low + DELTA
        cand_nodes = np.concatenate(arrays) if len(arrays) > 1 else arrays[0]
        cand_nodes = np.unique(cand_nodes)
        dvals = dist[cand_nodes]
        frontier = cand_nodes[(dvals >= low) & (dvals < high) & ~settled[cand_nodes]]

        processed = []
        while frontier.size:
            processed.append(frontier)
            improved = relax_edges(frontier, starts, nbr, wt, dist, settled, True)
            if improved.size == 0:
                break
            dvals = dist[improved]
            fut = improved[dvals >= high]
            if fut.size:
                add_pending(pending, heap, inheap, fut, dist)
            inb = improved[dvals < high]
            frontier = np.unique(inb) if inb.size else np.empty(0, dtype=np.int64)

        if not processed:
            continue
        req = np.unique(np.concatenate(processed))
        settled[req] = True
        for node in req.tolist():
            dv = int(dist[node])
            reached += 1
            total += dv
            if dv > far:
                far = dv
                far_node = node
            elif dv == far and node < far_node:
                far_node = node
        improved = relax_edges(req, starts, nbr, wt, dist, settled, False)
        if improved.size:
            add_pending(pending, heap, inheap, improved, dist)

    return reached, total, far, far_node


def dial_source(s, adj, b_size, n):
    inf = 1 << 62
    dist = [inf] * n
    visited = bytearray(n)
    buckets = [[] for _ in range(b_size)]
    dist[s] = 0
    buckets[0].append(s)
    mask = 1
    idx = 0
    cur = 0
    reached = 0
    total = 0
    far = 0
    far_node = s
    while mask:
        shifted = mask >> idx
        if shifted:
            off = (shifted & -shifted).bit_length() - 1
        else:
            off = (b_size - idx) + ((mask & -mask).bit_length() - 1)
        if off:
            cur += off
            idx += off
            if idx >= b_size:
                idx -= b_size
        bucket = buckets[idx]
        while bucket:
            v = bucket.pop()
            if visited[v]:
                continue
            visited[v] = 1
            reached += 1
            total += cur
            if cur > far:
                far = cur
                far_node = v
            elif cur == far and v < far_node:
                far_node = v
            d = cur
            for code in adj[v]:
                wgt = code & 1023
                to = code >> 10
                nd = d + wgt
                if nd < dist[to]:
                    dist[to] = nd
                    b = idx + wgt
                    if b >= b_size:
                        b -= b_size
                    bk = buckets[b]
                    bk.append(to)
                    if len(bk) == 1:
                        mask |= 1 << b
        mask &= ~(1 << idx)
    return reached, total, far, far_node


def main():
    if len(sys.argv) < 2:
        return
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    if not data:
        return
    # map(int, ...) in CPython is far faster than np.fromstring(sep=...) here.
    a = np.array(list(map(int, data.split())), dtype=np.int64)
    del data
    if a.size < 3:
        return
    n, m, q = int(a[0]), int(a[1]), int(a[2])
    edge_end = 3 + 3 * m
    u = a[3:edge_end:3]
    v = a[4:edge_end:3]
    w = a[5:edge_end:3]
    sources = a[edge_end:edge_end + q].tolist()

    if m:
        keep = u != v
        if not bool(keep.all()):
            u = u[keep]
            v = v[keep]
            w = w[keep]
    maxw = int(w.max()) if w.size else 0

    out_lines = []

    # Dense enough graphs: vectorised delta-stepping. Very sparse (chain-like)
    # graphs: the pure-Python Dial loop has less per-step overhead.
    use_delta = w.size >= 2 * max(n, 1)

    if use_delta:
        src = np.concatenate((u, v))
        dst = np.concatenate((v, u))
        ww = np.concatenate((w, w))
        order = np.argsort(src, kind="stable")
        nbr = dst[order]
        wt = ww[order]
        counts = np.bincount(src, minlength=n)
        starts = np.empty(n + 1, dtype=np.int64)
        starts[0] = 0
        np.cumsum(counts, out=starts[1:])
        del a, src, dst, ww, order, counts
        for s in sources:
            r, tot, far, fn = delta_source(s, n, starts, nbr, wt)
            out_lines.append(f"{s} {r} {tot} {far} {fn}")
    else:
        adj = [[] for _ in range(n)]
        for uu, vv, ww_ in zip(u.tolist(), v.tolist(), w.tolist()):
            adj[uu].append((vv << 10) | ww_)
            adj[vv].append((uu << 10) | ww_)
        del a
        b_size = maxw + 1
        for s in sources:
            r, tot, far, fn = dial_source(s, adj, b_size, n)
            out_lines.append(f"{s} {r} {tot} {far} {fn}")

    if out_lines:
        sys.stdout.buffer.write(("\n".join(out_lines) + "\n").encode())


if __name__ == "__main__":
    main()
