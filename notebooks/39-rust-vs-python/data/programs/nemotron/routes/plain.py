"""Plain Python 3.13 solution: multi-source Dijkstra with a binary heap.

Standard library only. Reads one input file, prints one result line per source.
"""
import sys
import re
import heapq


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

    # Compressed-sparse-rows graph (undirected: 2M directed arcs).
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

    INF = 1 << 62
    hpush = heapq.heappush
    hpop = heapq.heappop
    write = sys.stdout.buffer.write

    for s in sources:
        dist = [INF] * n
        dist[s] = 0
        heap = [(0, s)]
        while heap:
            d, u = hpop(heap)
            if d > dist[u]:
                continue
            start = head[u]
            end = head[u + 1]
            for i in range(start, end):
                v = to[i]
                nd = d + wt[i]
                if nd < dist[v]:
                    dist[v] = nd
                    hpush(heap, (nd, v))

        reach = 0
        total = 0
        far = 0
        node = s
        for u in range(n):
            d = dist[u]
            if d < INF:
                reach += 1
                total += d
                if d > far:
                    far = d
                    node = u
        write(f"{s} {reach} {total} {far} {node}\n".encode())


if __name__ == "__main__":
    main()
