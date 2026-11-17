import sys
from heapq import heappop, heappush


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read().split()
    n, m, q = int(data[0]), int(data[1]), int(data[2])

    # Each adjacency entry packs (neighbour << 10) | weight; weights are at most 1000.
    adj = [[] for _ in range(n)]
    it = map(int, data[3 : 3 + 3 * m])
    for u, v, w in zip(it, it, it):
        if u != v:  # self-loops never shorten a path
            adj[u].append((v << 10) | w)
            adj[v].append((u << 10) | w)
    sources = list(map(int, data[3 + 3 * m : 3 + 3 * m + q]))

    # Heap entries pack (distance << 20) | node; nodes are below 2**20.
    SHIFT = 20
    MASK = (1 << SHIFT) - 1
    INF = 1 << 62

    out = []
    for s in sources:
        dist = [INF] * n
        dist[s] = 0
        heap = [s]
        reach = 0
        total = 0
        far = 0
        far_node = s
        while heap:
            key = heappop(heap)
            d = key >> SHIFT
            v = key & MASK
            if d != dist[v]:  # stale entry
                continue
            reach += 1
            total += d
            if d > far:
                far = d
                far_node = v
            elif d == far and v < far_node:
                far_node = v
            for c in adj[v]:
                nd = d + (c & 1023)
                t = c >> 10
                if nd < dist[t]:
                    dist[t] = nd
                    heappush(heap, (nd << SHIFT) | t)
        out.append(f"{s} {reach} {total} {far} {far_node}\n")
    sys.stdout.buffer.write("".join(out).encode())


if __name__ == "__main__":
    main()
