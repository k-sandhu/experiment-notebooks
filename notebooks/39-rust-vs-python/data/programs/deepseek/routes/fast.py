import sys

import numpy as np


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()

    vals = list(map(int, data.split()))
    del data
    n = vals[0]
    m = vals[1]
    q = vals[2]

    if m:
        edges = np.array(vals[3:3 + 3 * m], dtype=np.int64).reshape(m, 3)
        srcs = edges[:, 0]
        dsts = edges[:, 1]
        wts = edges[:, 2]
        maxw = int(wts.max())
    else:
        srcs = np.empty(0, dtype=np.int64)
        dsts = np.empty(0, dtype=np.int64)
        wts = np.empty(0, dtype=np.int64)
        maxw = 0
    sources = vals[3 + 3 * m:3 + 3 * m + q]
    del vals

    # Build a CSR layout of the undirected graph, sorted by edge source.
    all_src = np.concatenate((srcs, dsts))
    all_dst = np.concatenate((dsts, srcs))
    all_w = np.concatenate((wts, wts))
    order = np.argsort(all_src, kind="stable")
    all_dst = all_dst[order]
    all_w = all_w[order]
    off = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(np.bincount(all_src, minlength=n), out=off[1:])
    del all_src, order

    # Dial's algorithm: every road is at most maxw long, so all queued
    # distances lie in a window of maxw + 1 consecutive values.  B circular
    # buckets plus a bitset let us jump to the next non-empty distance.
    B = 1 << maxw.bit_length()
    BM = B - 1
    one = [1 << i for i in range(B)]
    allbits = (1 << B) - 1
    shift_w = maxw.bit_length()

    nbr = all_dst
    wt = all_w

    # Encoded adjacency for the rare scalar (single-node bucket) path.
    enc = (all_dst << shift_w) | all_w
    off_list = off.tolist()
    adj = [enc[a:b].tolist() for a, b in zip(off_list, off_list[1:])]
    del enc, all_dst, all_w
    INF = 1 << 62
    OUT = []

    for s in sources:
        distn = np.full(n, INF, dtype=np.int64)
        distl = [INF] * n
        distn[s] = 0
        distl[s] = 0
        buckets = [None] * B
        buckets[0] = [s]
        bits = 1
        cur = 0
        pos = 0
        reach = 0
        total = 0
        far = 0
        node = s

        while bits:
            U = buckets[pos]
            if U is not None:
                buckets[pos] = None
                bits ^= one[pos]
                if len(U) == 1:
                    u = U[0]
                    if distl[u] != cur:
                        continue
                    reach += 1
                    total += cur
                    if cur > far:
                        far = cur
                        node = u
                    elif cur == far and u < node:
                        node = u
                    for e in adj[u]:
                        v = e >> shift_w
                        nd = cur + (e & BM)
                        if nd < distl[v]:
                            distl[v] = nd
                            distn[v] = nd
                            p2 = nd & BM
                            bb = buckets[p2]
                            if bb is None:
                                buckets[p2] = [v]
                            else:
                                bb.append(v)
                            bits |= one[p2]
                else:
                    Ua = np.array(U, dtype=np.int64)
                    Ua = Ua[distn[Ua] == cur]
                    if Ua.size:
                        k = int(Ua.size)
                        reach += k
                        total += cur * k
                        mn = int(Ua.min())
                        if cur > far:
                            far = cur
                            node = mn
                        elif cur == far and mn < node:
                            node = mn
                        e0 = off[Ua]
                        cnt = off[Ua + 1] - e0
                        tot = int(cnt.sum())
                        if tot:
                            csum = np.cumsum(cnt)
                            idx = np.repeat(e0, cnt) + (
                                np.arange(tot, dtype=np.int64)
                                - np.repeat(csum - cnt, cnt)
                            )
                            dd = nbr[idx]
                            nd = cur + wt[idx]
                            old = distn[dd]
                            np.minimum.at(distn, dd, nd)
                            new = distn[dd]
                            ch = new < old
                            if ch.any():
                                cv = dd[ch]
                                ucv = np.unique(cv)
                                cd = distn[ucv]
                                for vv, dv in zip(ucv.tolist(), cd.tolist()):
                                    distl[vv] = dv
                                    p2 = dv & BM
                                    bb = buckets[p2]
                                    if bb is None:
                                        buckets[p2] = [vv]
                                    else:
                                        bb.append(vv)
                                    bits |= one[p2]
            else:
                nxt = pos + 1
                if nxt == B:
                    nxt = 0
                if nxt:
                    rot = ((bits >> nxt) | (bits << (B - nxt))) & allbits
                else:
                    rot = bits
                inc = (rot & -rot).bit_length()
                cur += inc
                pos = (pos + inc) & BM

        OUT.append("%d %d %d %d %d" % (s, reach, total, far, node))

    if OUT:
        sys.stdout.buffer.write(("\n".join(OUT) + "\n").encode())


main()
