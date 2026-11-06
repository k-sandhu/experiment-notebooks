import sys
from array import array
from itertools import accumulate


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    if not data:
        return
    nums = array("i", map(int, data.split()))
    del data
    if len(nums) < 3:
        return
    n = nums[0]
    m = nums[1]
    q = nums[2]
    edge_end = 3 + 3 * m
    sources = list(nums[edge_end:edge_end + q])

    deg = [0] * n
    max_w = 0
    for i in range(3, edge_end, 3):
        u = nums[i]
        v = nums[i + 1]
        if u == v:
            continue
        w = nums[i + 2]
        deg[u] += 1
        deg[v] += 1
        if w > max_w:
            max_w = w

    start = list(accumulate(deg, initial=0))
    del deg
    shift = max_w.bit_length() if max_w else 1
    wmask = (1 << shift) - 1
    edges = [0] * start[-1]
    cursor = start[:-1]
    # accumulate returns list copy semantics: start[:-1] is a fresh list.
    for i in range(3, edge_end, 3):
        u = nums[i]
        v = nums[i + 1]
        if u == v:
            continue
        w = nums[i + 2]
        p = cursor[u]
        edges[p] = (v << shift) | w
        cursor[u] = p + 1
        p = cursor[v]
        edges[p] = (u << shift) | w
        cursor[v] = p + 1
    del nums, cursor

    bsize = max_w + 1 if max_w else 1
    buckets = [[] for _ in range(bsize)]
    bits = [1 << i for i in range(bsize)]
    inf = 1 << 62

    out = []
    cache = {}
    for s in sources:
        hit = cache.get(s)
        if hit is not None:
            out.append(hit)
            continue

        dist = [inf] * n
        done = bytearray(n)
        dist[s] = 0
        buckets[0].append(s)
        mask = 1
        cur = 0
        idx = 0
        reach = 0
        total = 0
        far = 0
        far_node = s

        # Local aliases for the hot loop.
        st = start
        ed = edges
        di = dist
        dn = done
        bk_all = buckets
        bt = bits
        bsz = bsize
        sh = shift
        wm = wmask

        while mask:
            shifted = mask >> idx
            if shifted:
                offset = (shifted & -shifted).bit_length() - 1
            else:
                offset = bsz - idx + ((mask & -mask).bit_length() - 1)
            if offset:
                cur += offset
                idx += offset
                if idx >= bsz:
                    idx -= bsz
            stack = bk_all[idx]
            mask &= ~bt[idx]
            bucket_min = -1
            while stack:
                u = stack.pop()
                if dn[u] or di[u] != cur:
                    continue
                dn[u] = 1
                reach += 1
                total += cur
                if bucket_min < 0 or u < bucket_min:
                    bucket_min = u
                for e in ed[st[u]:st[u + 1]]:
                    v = e >> sh
                    if dn[v]:
                        continue
                    w = e & wm
                    nd = cur + w
                    if nd < di[v]:
                        di[v] = nd
                        nb = idx + w
                        if nb >= bsz:
                            nb -= bsz
                        bk = bk_all[nb]
                        if not bk:
                            mask |= bt[nb]
                        bk.append(v)
            if bucket_min >= 0:
                far = cur
                far_node = bucket_min

        line = f"{s} {reach} {total} {far} {far_node}"
        cache[s] = line
        out.append(line)

    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()
