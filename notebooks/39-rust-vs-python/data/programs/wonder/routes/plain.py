import sys


def main():
    if len(sys.argv) < 2:
        return
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    if not data:
        return
    a = list(map(int, data.split()))
    if len(a) < 3:
        return
    n, m, q = a[0], a[1], a[2]

    adj = [[] for _ in range(n)]
    maxw = 0
    # Pack (neighbour, weight) into one int: neighbour << 10 | weight (weight <= 1000 < 1024).
    base = 3
    for i in range(base, base + 3 * m, 3):
        u = a[i]
        v = a[i + 1]
        w = a[i + 2]
        if u == v:
            continue
        if w > maxw:
            maxw = w
        adj[u].append((v << 10) | w)
        adj[v].append((u << 10) | w)
    sources = a[base + 3 * m: base + 3 * m + q]
    del a, data

    b_size = maxw + 1
    inf = 1 << 62
    out_lines = []

    for s in sources:
        dist = [inf] * n
        visited = bytearray(n)
        buckets = [[] for _ in range(b_size)]
        dist[s] = 0
        buckets[0].append(s)
        mask = 1
        idx = 0
        cur = 0
        reached = 0
        total = 0
        far = 0
        far_node = s

        while mask:
            # Jump to the next non-empty bucket using the occupancy bitmask.
            shifted = mask >> idx
            if shifted:
                off = (shifted & -shifted).bit_length() - 1
            else:
                off = (b_size - idx) + ((mask & -mask).bit_length() - 1)
            if off:
                cur += off
                idx += off
                if idx >= b_size:
                    idx -= b_size

            bucket = buckets[idx]
            while bucket:
                v = bucket.pop()
                if visited[v]:
                    continue
                visited[v] = 1
                reached += 1
                total += cur
                if cur > far:
                    far = cur
                    far_node = v
                elif cur == far and v < far_node:
                    far_node = v
                d = cur
                for code in adj[v]:
                    wgt = code & 1023
                    to = code >> 10
                    nd = d + wgt
                    if nd < dist[to]:
                        dist[to] = nd
                        b = idx + wgt
                        if b >= b_size:
                            b -= b_size
                        bk = buckets[b]
                        bk.append(to)
                        if len(bk) == 1:
                            mask |= 1 << b
            mask &= ~(1 << idx)

        out_lines.append(f"{s} {reached} {total} {far} {far_node}")

    if out_lines:
        sys.stdout.buffer.write(("\n".join(out_lines) + "\n").encode())


if __name__ == "__main__":
    main()
