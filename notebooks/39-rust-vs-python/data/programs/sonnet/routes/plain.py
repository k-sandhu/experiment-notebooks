import sys
from heapq import heappush, heappop


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read().split()
    n = int(data[0])
    m = int(data[1])
    q = int(data[2])
    vals = list(map(int, data[3:3 + 3 * m]))
    us = vals[0::3]
    vs = vals[1::3]
    ws = vals[2::3]
    sources = list(map(int, data[3 + 3 * m:3 + 3 * m + q]))
    del data, vals

    # adjacency lists of packed (w << shift | v)
    shift = max(n, 1).bit_length()
    mask = (1 << shift) - 1
    adj = [[] for _ in range(n)]
    for u, v, w in zip(us, vs, ws):
        if u != v:
            adj[u].append(w << shift | v)
            adj[v].append(w << shift | u)
    del us, vs, ws

    out = []
    cache = {}
    inf = float("inf")
    for s in sources:
        line = cache.get(s)
        if line is None:
            dist = [-1] * n
            best = [inf] * n
            best[s] = 0
            heap = [s]
            r = 0
            total = 0
            far = 0
            node = s
            while heap:
                key = heappop(heap)
                u = key & mask
                if dist[u] >= 0:
                    continue
                d = key >> shift
                dist[u] = d
                r += 1
                total += d
                if d > far or (d == far and u < node):
                    far = d
                    node = u
                for e in adj[u]:
                    v = e & mask
                    if dist[v] < 0:
                        nd = d + (e >> shift)
                        if nd < best[v]:
                            best[v] = nd
                            heappush(heap, nd << shift | v)
            line = "%d %d %d %d %d" % (s, r, total, far, node)
            cache[s] = line
        out.append(line)
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
