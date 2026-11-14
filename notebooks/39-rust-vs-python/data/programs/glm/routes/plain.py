import sys
from heapq import heappush, heappop


def main():
    vals = list(map(int, open(sys.argv[1], 'rb').read().split()))
    n, m, q = vals[0], vals[1], vals[2]

    # Sources are the last q tokens.
    srcs = vals[3 + 3 * m: 3 + 3 * m + q]

    # Adjacency: per node, a list of packed ints (w << NB) | other_node.
    # n <= 2^20 for benchmark sizes; distances stay far below 2^42.
    NB = 20
    NMASK = (1 << NB) - 1
    adj = [[] for _ in range(n)]
    us = vals[3:3 + 3 * m:3]
    vs = vals[4:4 + 3 * m:3]
    ws = vals[5:5 + 3 * m:3]
    for u, v, w in zip(us, vs, ws):
        e = (w << NB) | v
        adj[u].append(e)
        e = (w << NB) | u
        adj[v].append(e)
    del us, vs, ws, vals

    out = []
    push = heappush
    pop = heappop
    INF = 1 << 62

    for s in srcs:
        dist = [INF] * n
        dist[s] = 0
        heap = [s]  # packed (d << NB) | v with d == 0
        while heap:
            key = pop(heap)
            v = key & NMASK
            d = key >> NB
            if d != dist[v]:
                continue  # stale entry
            for e in adj[v]:
                u = e & NMASK
                nd = d + (e >> NB)
                if nd < dist[u]:
                    dist[u] = nd
                    push(heap, (nd << NB) | u)
        total = 0
        cnt = 0
        far = 0
        for x in dist:
            if x != INF:
                cnt += 1
                total += x
                if x > far:
                    far = x
        node = dist.index(far)
        out.append('%d %d %d %d %d' % (s, cnt, total, far, node))
    sys.stdout.buffer.write(('\n'.join(out) + '\n').encode())


main()
