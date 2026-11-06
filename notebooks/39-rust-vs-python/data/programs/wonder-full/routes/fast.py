import sys

import numpy as np

DELTA = 1000
INF = 1 << 60


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    if not data:
        return
    a = np.array(data.split(), dtype=np.int64)
    del data
    if a.size < 3:
        return
    n = int(a[0])
    m = int(a[1])
    q = int(a[2])
    if q == 0 or n == 0:
        return
    edge_end = 3 + 3 * m
    sources = a[edge_end:edge_end + q].astype(np.int64, copy=False)
    uniq_sources, inv = np.unique(sources, return_inverse=True)
    qc = int(uniq_sources.size)

    # ---- CSR adjacency (vectorized counting sort by source) ----
    if m:
        e = a[3:edge_end].reshape(m, 3)
        max_w = int(e[:, 2].max())
        u = e[:, 0]
        v = e[:, 1]
        w = e[:, 2]
        keep = u != v
        u = u[keep]
        v = v[keep]
        w = w[keep]
        src = np.concatenate([u, v])
        dst = np.concatenate([v, u])
        ww = np.concatenate([w, w])
        del e, u, v, w, keep
        deg = np.bincount(src, minlength=n).astype(np.int64, copy=False)
        start = np.empty(n + 1, dtype=np.int64)
        start[0] = 0
        np.cumsum(deg, out=start[1:])
        order = np.argsort(src)
        del src
        dst = dst[order]
        ww = ww[order]
        del order
    else:
        max_w = 0
        deg = np.zeros(n, dtype=np.int64)
        start = np.zeros(n + 1, dtype=np.int64)
        dst = np.empty(0, dtype=np.int64)
        ww = np.empty(0, dtype=np.int64)
    del a

    def dial_results():
        """Scalar Dial's algorithm per source (used if the batched
        frontier turns out too narrow for NumPy to be efficient)."""
        st = start.tolist()
        sh = max_w.bit_length() if max_w else 1
        wm = (1 << sh) - 1
        ed = [(int(v) << sh) | int(w) for v, w in zip(dst.tolist(), ww.tolist())]
        bsz = max_w + 1 if max_w else 1
        bk_all = [[] for _ in range(bsz)]
        bt = [1 << i for i in range(bsz)]
        inf = 1 << 62
        res = []
        for s0 in uniq_sources.tolist():
            s = int(s0)
            di = [inf] * n
            dn = bytearray(n)
            di[s] = 0
            bk_all[0].append(s)
            mask = 1
            cur = 0
            idx = 0
            reach = 0
            total = 0
            far = 0
            far_node = s
            while mask:
                shifted = mask >> idx
                if shifted:
                    offset = (shifted & -shifted).bit_length() - 1
                else:
                    offset = bsz - idx + ((mask & -mask).bit_length() - 1)
                if offset:
                    cur += offset
                    idx += offset
                    if idx >= bsz:
                        idx -= bsz
                stack = bk_all[idx]
                mask &= ~bt[idx]
                bucket_min = -1
                while stack:
                    u = stack.pop()
                    if dn[u] or di[u] != cur:
                        continue
                    dn[u] = 1
                    reach += 1
                    total += cur
                    if bucket_min < 0 or u < bucket_min:
                        bucket_min = u
                    for e in ed[st[u]:st[u + 1]]:
                        v = e >> sh
                        if dn[v]:
                            continue
                        w = e & wm
                        nd = cur + w
                        if nd < di[v]:
                            di[v] = nd
                            nb = idx + w
                            if nb >= bsz:
                                nb -= bsz
                            bk = bk_all[nb]
                            if not bk:
                                mask |= bt[nb]
                            bk.append(v)
                if bucket_min >= 0:
                    far = cur
                    far_node = bucket_min
            res.append(f"{s} {reach} {total} {far} {far_node}")
        return res

    # ---- Delta-stepping, all sources batched together ----
    # A state is encoded as pair_id = q_index * n + node.
    stats = [0, 0, 0]  # relax calls, states processed, fallback flag
    total_states = qc * n
    dist = np.full(total_states, INF, dtype=np.int64)
    init_ids = (np.arange(qc, dtype=np.int64) * n + uniq_sources).astype(np.int64)
    dist[init_ids] = 0
    buckets = {0: [init_ids]}

    def relax(ids, light):
        """Relax light (w <= DELTA) or heavy edges out of `ids`.

        Returns (updated_ids, their_new_distances), ids deduplicated.
        """
        if ids.size == 0:
            return ids, ids
        stats[0] += 1
        stats[1] += int(ids.size)
        if stats[0] > 2000 and stats[1] < 64 * stats[0]:
            stats[2] = 1
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
        nodes = ids % n
        counts = deg[nodes]
        nz = counts > 0
        if not nz.any():
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
        if not nz.all():
            ids = ids[nz]
            nodes = nodes[nz]
            counts = counts[nz]
        starts = start[nodes]
        tot = int(counts.sum())
        # Expand CSR ranges [starts[i], starts[i]+counts[i]) into one array.
        eidx = np.ones(tot, dtype=np.int64)
        eidx[0] = starts[0]
        if ids.size > 1:
            pos = np.cumsum(counts)[:-1]
            eidx[pos] = starts[1:] - starts[:-1] - counts[:-1] + 1
        np.cumsum(eidx, out=eidx)

        weights = ww[eidx]
        if light and DELTA >= max_w:
            sel = None
        elif light:
            sel = weights <= DELTA
        else:
            sel = weights > DELTA
        if sel is not None and not sel.any():
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)

        src_rep = np.repeat(ids, counts)
        base_rep = np.repeat(ids - nodes, counts)
        if sel is not None and not sel.all():
            src_rep = src_rep[sel]
            base_rep = base_rep[sel]
            eidx = eidx[sel]
            weights = weights[sel]
        targets = base_rep + dst[eidx]
        cand = dist[src_rep] + weights
        del src_rep, base_rep, eidx, weights

        sel = cand < dist[targets]
        if not sel.any():
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
        if not sel.all():
            targets = targets[sel]
            cand = cand[sel]
        np.minimum.at(dist, targets, cand)
        sel = dist[targets] == cand
        if not sel.all():
            targets = targets[sel]
        if targets.size == 0:
            return targets, targets
        targets = np.unique(targets)
        return targets, dist[targets]

    def insert(ids, ds):
        if ids.size == 0:
            return
        b = ds // DELTA
        bmin = int(b.min())
        bmax = int(b.max())
        if bmax - bmin <= 32:
            # Few distinct bucket numbers: grouping by mask beats a sort.
            for bv in range(bmin, bmax + 1):
                chunk = ids[b == bv]
                if chunk.size:
                    lst = buckets.get(bv)
                    if lst is None:
                        buckets[bv] = [chunk]
                    else:
                        lst.append(chunk)
            return
        order = np.argsort(b, kind="stable")
        b_sorted = b[order]
        ids_sorted = ids[order]
        uniq_b, cnts = np.unique(b_sorted, return_counts=True)
        pos = 0
        for bv, c in zip(uniq_b.tolist(), cnts.tolist()):
            chunk = ids_sorted[pos:pos + c]
            pos += c
            lst = buckets.get(bv)
            if lst is None:
                buckets[bv] = [chunk]
            else:
                lst.append(chunk)

    while buckets and not stats[2]:
        i = min(buckets)
        s_chunks = []
        # Light edges: keep processing bucket i until it stays empty.
        while i in buckets and not stats[2]:
            chunks = buckets.pop(i)
            r = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
            if r.size == 0:
                continue
            r = np.unique(r)
            # Drop stale entries whose distance has since moved to a
            # lower bucket (they were re-inserted there on improvement).
            sel = dist[r] // DELTA == i
            if not sel.all():
                r = r[sel]
            if r.size == 0:
                continue
            s_chunks.append(r)
            upd_ids, upd_ds = relax(r, True)
            insert(upd_ids, upd_ds)
        if stats[2]:
            break
        if not s_chunks:
            continue
        if DELTA >= max_w:
            continue  # no heavy edges exist
        s_all = s_chunks[0] if len(s_chunks) == 1 else np.unique(np.concatenate(s_chunks))
        upd_ids, upd_ds = relax(s_all, False)
        insert(upd_ids, upd_ds)

    if stats[2]:
        results = dial_results()
        out = [results[int(inv[k])] for k in range(q)]
        sys.stdout.write("\n".join(out) + "\n")
        return

    # ---- Per-source statistics ----
    dmat = dist.reshape(qc, n)
    results = []
    for qi in range(qc):
        row = dmat[qi]
        reach_mask = row != INF
        reach = int(reach_mask.sum())
        vals = row[reach_mask]
        total = int(vals.sum())
        far = int(vals.max())
        node = int(np.argmax(row == far))
        results.append(f"{int(uniq_sources[qi])} {reach} {total} {far} {node}")

    out = [results[int(inv[k])] for k in range(q)]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
