import sys
import os
import gc
from collections import deque


def main():
    gc.disable()
    with open(sys.argv[1], 'rb') as f:
        data = f.read().split()
    N = int(data[0])
    M = int(data[1])
    Q = int(data[2])
    end = 3 + 3 * M

    # Canonical (contiguously allocated) int objects for node ids -> better cache locality
    ids = list(range(N))
    getid = ids.__getitem__
    U = list(map(getid, map(int, data[3:end:3])))
    V = list(map(getid, map(int, data[4:end:3])))
    W = list(map(int, data[5:end:3]))
    sources = list(map(int, data[end:end + Q]))
    del data

    maxw = max(W, default=1)
    if maxw < 1:
        maxw = 1
    wtab = list(range(maxw + 1))
    W = list(map(wtab.__getitem__, W))

    adjv = [[] for _ in range(N)]
    adjw = [[] for _ in range(N)]
    app = list.append
    drain = deque(maxlen=0).extend
    gv = adjv.__getitem__
    gw = adjw.__getitem__
    drain(map(app, map(gv, U), V))
    drain(map(app, map(gv, V), U))
    drain(map(app, map(gw, U), W))
    drain(map(app, map(gw, V), W))
    del U, V, W
    adjv = list(map(tuple, adjv))
    adjw = list(map(tuple, adjw))

    # Dial's algorithm with a circular bucket array (size > max weight)
    NB = 1 << maxw.bit_length()
    MASK = NB - 1
    buckets = [[] for _ in range(NB)]
    flags = bytearray(NB)
    find = flags.find
    INF = N * maxw + 1

    out = []
    for s in sources:
        dist = [INF] * N
        dist[s] = 0
        d = 0
        c = 0
        far = 0
        cur = buckets[0]
        cur.append(s)
        while True:
            for u in cur:
                if dist[u] == d:
                    far = d
                    for v, w in zip(adjv[u], adjw[u]):
                        nd = d + w
                        if nd < dist[v]:
                            dist[v] = nd
                            i = nd & MASK
                            buckets[i].append(v)
                            flags[i] = 1
            cur.clear()
            flags[c] = 0
            j = find(1, c + 1)
            if j < 0:
                j = find(1, 0, c)
                if j < 0:
                    break
                d += j + NB - c
            else:
                d += j - c
            c = j
            cur = buckets[j]

        ninf = dist.count(INF)
        R = N - ninf
        total = sum(dist) - INF * ninf
        node = dist.index(far)
        out.append("%d %d %d %d %d" % (s, R, total, far, node))

    if out:
        sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()
    os._exit(0)


main()
