import gc
import sys
from heapq import heappop, heappush


def main():
    gc.disable()  # millions of small containers, none of them cyclic
    with open(sys.argv[1], "rb") as f:
        data = f.read().split()
    n, m, q = int(data[0]), int(data[1]), int(data[2])
    end = 3 + 3 * m
    us = list(map(int, data[3:end:3]))
    vs = list(map(int, data[4:end:3]))
    ws = list(map(int, data[5:end:3]))
    sources = list(map(int, data[end:end + q]))
    del data

    adj = [[] for _ in range(n)]
    # The (neighbour, weight) tuples are built by zip in C. Self-loops are kept: relaxing
    # one never improves a distance.
    for u, v, fwd, back in zip(us, vs, zip(vs, ws), zip(us, ws)):
        adj[u].append(fwd)
        adj[v].append(back)
    del us, vs, ws

    inf = 1 << 62
    out = []
    for s in sources:
        # Dijkstra over distinct distances: each pending distance maps to the list of nodes
        # reached at it, and the heap only holds the distances themselves. Edge weights are
        # small, so many nodes share a distance and the heap stays small.
        dist = [inf] * n
        dist[s] = 0
        buckets = {0: [s]}
        keys = [0]
        while keys:
            d = heappop(keys)
            for v in buckets.pop(d):
                if dist[v] != d:
                    continue
                for u, w in adj[v]:
                    nd = d + w
                    if nd < dist[u]:
                        dist[u] = nd
                        b = buckets.get(nd)
                        if b is None:
                            buckets[nd] = [u]
                            heappush(keys, nd)
                        else:
                            b.append(u)
        far = max(filter(inf.__gt__, dist))
        unreached = dist.count(inf)
        reached = n - unreached
        total = sum(dist) - unreached * inf
        out.append(f"{s} {reached} {total} {far} {dist.index(far)}\n")
    sys.stdout.buffer.write("".join(out).encode())


main()
