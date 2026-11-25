import sys


def read_graph(path):
    import numpy as np

    with open(path, "rb") as f:
        n, m, q = map(int, f.readline().split())
        data = np.fromstring(f.read(), dtype=np.int64, sep=" ")

    sources = data[3 * m:3 * m + q].tolist()
    if m == 0 or q == 0:
        return n, None, sources

    edges = data[:3 * m].reshape(m, 3)
    owners = np.concatenate((edges[:, 0], edges[:, 1]))
    packed = np.concatenate((
        (edges[:, 1] << 10) | edges[:, 2],
        (edges[:, 0] << 10) | edges[:, 2],
    ))

    offsets = np.empty(n + 1, dtype=np.int64)
    offsets[0] = 0
    np.cumsum(np.bincount(owners, minlength=n), out=offsets[1:])

    order = np.argsort(owners, kind="stable")
    flat = packed[order].tolist()
    offsets = offsets.tolist()
    graph = [flat[offsets[i]:offsets[i + 1]] for i in range(n)]

    return n, graph, sources


def shortest_summary(graph, n, source):
    infinity = 1000 * n + 1
    dist = [infinity] * n
    dist[source] = 0

    buckets = [[] for _ in range(1024)]
    buckets[0].append(source)
    occupied = 1
    position = 0
    distance = 0
    farthest = 0

    while occupied:
        ahead = occupied >> position
        if ahead:
            step = (ahead & -ahead).bit_length() - 1
        else:
            step = (
                1024 - position
                + (occupied & -occupied).bit_length() - 1
            )

        distance += step
        position = (position + step) & 1023
        bucket = buckets[position]
        occupied ^= 1 << position

        for u in bucket:
            if dist[u] != distance:
                continue

            farthest = distance
            for edge in graph[u]:
                v = edge >> 10
                candidate = distance + (edge & 1023)
                if candidate < dist[v]:
                    dist[v] = candidate
                    index = candidate & 1023
                    target = buckets[index]
                    if not target:
                        occupied |= 1 << index
                    target.append(v)

        bucket.clear()

    unreachable = dist.count(infinity)
    reachable = n - unreachable
    total = sum(dist) - unreachable * infinity
    far_node = dist.index(farthest)
    return f"{source} {reachable} {total} {farthest} {far_node}"


def main():
    n, graph, sources = read_graph(sys.argv[1])
    if not sources:
        return

    if graph is None:
        sys.stdout.write(
            "".join(f"{s} 1 0 0 {s}\n" for s in sources)
        )
        return

    cache = {}
    output = []
    for source in sources:
        line = cache.get(source)
        if line is None:
            line = shortest_summary(graph, n, source)
            cache[source] = line
        output.append(line)

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
