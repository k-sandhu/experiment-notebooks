import sys


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()

    vals = list(map(int, data.split()))
    del data
    n = vals[0]
    m = vals[1]
    q = vals[2]

    adj = [[] for _ in range(n)]
    k = 3
    maxw = 0
    for _ in range(m):
        u = vals[k]
        v = vals[k + 1]
        w = vals[k + 2]
        k += 3
        adj[u].append((v << 10) | w)
        adj[v].append((u << 10) | w)
        if w > maxw:
            maxw = w

    sources = vals[k:k + q]
    del vals

    # Dial's algorithm with a circular bucket array.  Every road is at most
    # maxw long, so all distances waiting in the queue lie in a window of
    # maxw + 1 consecutive values and fit in B circular buckets.  A bitset
    # lets us jump straight to the next non-empty distance instead of
    # scanning the (possibly huge) distance range.
    B = 1 << maxw.bit_length()
    BM = B - 1
    one = [1 << i for i in range(B)]
    allbits = (1 << B) - 1
    INF = 1 << 62

    out = []
    for s in sources:
        dist = [INF] * n
        dist[s] = 0
        buckets = [[] for _ in range(B)]
        buckets[0].append(s)
        bits = 1
        cur = 0
        pos = 0
        reach = 0
        total = 0
        far = 0
        node = s

        while bits:
            b = buckets[pos]
            if b:
                u = b.pop()
                if not b:
                    bits ^= one[pos]
                if dist[u] != cur:
                    continue
                reach += 1
                total += cur
                if cur > far:
                    far = cur
                    node = u
                elif cur == far and u < node:
                    node = u
                for e in adj[u]:
                    v = e >> 10
                    nd = cur + (e & 1023)
                    if nd < dist[v]:
                        dist[v] = nd
                        p2 = nd & BM
                        buckets[p2].append(v)
                        bits |= one[p2]
            else:
                shift = pos + 1
                if shift == B:
                    shift = 0
                if shift:
                    rot = ((bits >> shift) | (bits << (B - shift))) & allbits
                else:
                    rot = bits
                inc = (rot & -rot).bit_length()
                cur += inc
                pos = (pos + inc) & BM

        out.append("%d %d %d %d %d" % (s, reach, total, far, node))

    if out:
        sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
