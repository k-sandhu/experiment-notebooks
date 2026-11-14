import sys
from heapq import heappop, heappush

import numpy as np

# Bucket width for delta-stepping. Arcs of weight <= DELTA are "light" and are
# relaxed repeatedly inside a bucket; heavier arcs are relaxed once per bucket.
DELTA = 256
INF = np.int64(1 << 62)


def build_csr(tail, head, wt, n):
    # Arcs leaving u are at indptr[u]:indptr[u + 1].
    order = np.argsort(tail, kind="stable")
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(np.bincount(tail, minlength=n), out=indptr[1:])
    return indptr, head[order], wt[order]


def gather(nodes, csr, dist):
    # All arcs leaving `nodes`, as (target, candidate distance) arrays.
    indptr, head, wt = csr
    starts = indptr[nodes]
    counts = indptr[nodes + 1] - starts
    total = int(counts.sum())
    offs = np.cumsum(counts) - counts
    pos = np.arange(total, dtype=np.int64) + np.repeat(starts - offs, counts)
    return head[pos], np.repeat(dist[nodes], counts) + wt[pos]


def shortest_paths(s, n, light, heavy):
    dist = np.full(n, INF, dtype=np.int64)
    dist[s] = 0
    buckets = {0: [np.array([s], dtype=np.int64)]}
    heap = [0]

    def push(nodes):
        # Queue nodes (with current distances) into their buckets.
        keys = dist[nodes] // DELTA
        for k in np.unique(keys).tolist():
            part = nodes[keys == k]
            if k in buckets:
                buckets[k].append(part)
            else:
                buckets[k] = [part]
                heappush(heap, k)

    while heap:
        b = heappop(heap)
        lo = b * DELTA
        hi = lo + DELTA
        # Entries can be stale: the node may have moved to an earlier bucket.
        frontier = np.unique(np.concatenate(buckets.pop(b)))
        frontier = frontier[(dist[frontier] >= lo) & (dist[frontier] < hi)]
        settled = []
        while frontier.size:
            settled.append(frontier)
            tgt, cand = gather(frontier, light, dist)
            better = cand < dist[tgt]
            if not better.any():
                break
            tgt = tgt[better]
            np.minimum.at(dist, tgt, cand[better])
            uniq = np.unique(tgt)
            inside = dist[uniq] < hi
            frontier = uniq[inside]
            push(uniq[~inside])
        if settled:
            done = np.unique(np.concatenate(settled))
            tgt, cand = gather(done, heavy, dist)
            better = cand < dist[tgt]
            if better.any():
                tgt = tgt[better]
                np.minimum.at(dist, tgt, cand[better])
                push(np.unique(tgt))
    return dist


def main():
    with open(sys.argv[1], "rb") as f:
        raw = f.read()
    arr = np.array(raw.split(), dtype=np.int64)
    n, m, q = int(arr[0]), int(arr[1]), int(arr[2])
    edges = arr[3 : 3 + 3 * m].reshape(m, 3)
    sources = arr[3 + 3 * m : 3 + 3 * m + q].tolist()

    # Self-loops never shorten a path, so they are dropped.
    eu, ev, ew = edges[:, 0], edges[:, 1], edges[:, 2]
    keep = eu != ev
    eu, ev, ew = eu[keep], ev[keep], ew[keep]
    tail = np.concatenate((eu, ev))
    head = np.concatenate((ev, eu))
    wt = np.concatenate((ew, ew))
    is_light = wt <= DELTA
    light = build_csr(tail[is_light], head[is_light], wt[is_light], n)
    heavy = build_csr(tail[~is_light], head[~is_light], wt[~is_light], n)

    out = []
    for s in sources:
        dist = shortest_paths(s, n, light, heavy)
        reached = dist[dist < INF]
        far = int(reached.max())
        far_node = int(np.flatnonzero(dist == far)[0])
        out.append(f"{s} {reached.size} {int(reached.sum())} {far} {far_node}\n")
    sys.stdout.buffer.write("".join(out).encode())


if __name__ == "__main__":
    main()
