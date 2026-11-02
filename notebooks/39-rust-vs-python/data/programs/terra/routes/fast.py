import sys
from heapq import heappop, heappush
import numpy as np


def main():
    with open(sys.argv[1], 'rb') as f:
        n, m, q = map(int, f.readline().split())
        data = np.fromstring(f.read(), dtype=np.int64, sep=' ')
    edges = data[:3*m].reshape(m, 3)
    # Convert once to native integers so the graph traversal avoids NumPy scalar overhead.
    us = edges[:, 0].tolist()
    vs = edges[:, 1].tolist()
    ws = edges[:, 2].tolist()
    sources = data[3*m:3*m+q].tolist()
    del edges, data
    adj = [[] for _ in range(n)]
    for u, v, w in zip(us, vs, ws):
        adj[u].append((v, w))
        adj[v].append((u, w))
    del us, vs, ws

    inf = 1 << 63
    results = {}
    output = []
    for source in sources:
        if source not in results:
            dist = [inf] * n
            dist[source] = 0
            heap = [(0, source)]
            count = total = far = 0
            far_node = source
            while heap:
                d, u = heappop(heap)
                if d != dist[u]:
                    continue
                count += 1
                total += d
                if d > far or (d == far and u < far_node):
                    far, far_node = d, u
                for v, w in adj[u]:
                    nd = d + w
                    if nd < dist[v]:
                        dist[v] = nd
                        heappush(heap, (nd, v))
            results[source] = f'{source} {count} {total} {far} {far_node}'
        output.append(results[source])
    if output:
        sys.stdout.write('\n'.join(output) + '\n')


if __name__ == '__main__':
    main()
