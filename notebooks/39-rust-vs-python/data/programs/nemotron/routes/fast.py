"""NumPy-accelerated Python 3.13 solution: multi-source Dijkstra.

Uses Dial's bucket queue (edge weights are in 1..1000, so modulo-1001 buckets
give O(1) decrease-key) with NumPy vectorised arc relaxation for the settled
nodes of each distance level. Standard library plus NumPy only.
"""
import sys
import re
import heapq
import numpy as np

W = 1001  # one more than the maximum edge weight
INF = 1 << 62
VECTOR_BATCH = 16  # vectorise relaxation when a distance bucket is this big


def dijkstra(n, head, to, wt, s):
    dist = np.full(n, INF, dtype=np.int64)
    buckets = [[] for _ in range(W)]
    heap = []  # (distance, bucket class)
    dist[s] = 0
    buckets[0].append(s)
    heapq.heappush(heap, (0, 0))

    while heap:
        d, c = heapq.heappop(heap)
        bucket = buckets[c]
        if not bucket:
            continue
        buckets[c] = []

        d = int(d)
        settle = []
        t_list = []
        w_list = []
        # All live entries in this bucket have distance exactly d; stale ones
        # (node improved after being enqueued) are skipped.
        for u in bucket:
            if dist[u] != d:
                continue
            settle.append(u)
            st = head[u]
            en = head[u + 1]
            t_list.extend(to[st:en])
            w_list.extend(wt[st:en])
        if not settle:
            continue

        if len(settle) >= VECTOR_BATCH:
            t = np.array(t_list, dtype=np.int64)
            cand = d + np.array(w_list, dtype=np.int64)
            old = dist[t].copy()
            upd = cand < old
            if upd.any():
                np.minimum.at(dist, t, cand)
                v = t[upd]
                nd = cand[upd]
                for vi, ndi in zip(v.tolist(), nd.tolist()):
                    ndi = int(ndi)
                    b = buckets[ndi % W]
                    if not b:
                        heapq.heappush(heap, (ndi, ndi % W))
                    b.append(int(vi))
        else:
            for u in settle:
                st = head[u]
                en = head[u + 1]
                du = d
                for i in range(st, en):
                    v = to[i]
                    nd = du + wt[i]
                    if nd < dist[v]:
                        dist[v] = nd
                        b = buckets[nd % W]
                        if not b:
                            heapq.heappush(heap, (nd, nd % W))
                        b.append(v)
    return dist


def stats(dist):
    reachable = dist < INF
    reach = int(np.count_nonzero(reachable))
    total = int(np.sum(dist[reachable]))
    far = int(np.max(dist[reachable]))
    node = int(np.flatnonzero(dist == far)[0])
    return reach, total, far, node


def main() -> None:
    data = open(sys.argv[1], "rb").read()

    tokens = re.finditer(rb"\d+", data)
    next_t = lambda: int(next(tokens).group())  # noqa: E731

    n = next_t()
    m = next_t()
    q = next_t()

    eu = [0] * m
    ev = [0] * m
    ew = [0] * m
    for i in range(m):
        eu[i] = next_t()
        ev[i] = next_t()
        ew[i] = next_t()
    sources = [0] * q
    for i in range(q):
        sources[i] = next_t()

    deg = [0] * n
    for i in range(m):
        deg[eu[i]] += 1
        deg[ev[i]] += 1
    head = [0] * (n + 1)
    for i in range(n):
        head[i + 1] = head[i] + deg[i]
    cur = head[:]
    size = 2 * m
    to = [0] * size
    wt = [0] * size
    for i in range(m):
        u = eu[i]
        v = ev[i]
        w = ew[i]
        p = cur[u]
        to[p] = v
        wt[p] = w
        cur[u] = p + 1
        p = cur[v]
        to[p] = u
        wt[p] = w
        cur[v] = p + 1

    write = sys.stdout.buffer.write
    for s in sources:
        dist = dijkstra(n, head, to, wt, s)
        reach, total, far, node = stats(dist)
        write(f"{s} {reach} {total} {far} {node}\n".encode())


if __name__ == "__main__":
    main()
