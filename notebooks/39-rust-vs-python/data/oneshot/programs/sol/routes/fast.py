import sys
import numpy as np


def shortest(source, graph, n, buckets, bits, infinity):
    if not graph[source]:
        return f"{source} 1 0 0 {source}"

    distances = [infinity] * n
    distances[source] = 0
    buckets[0].append(source)

    active = 1
    position = 0
    distance = 0
    farthest = 0

    while active:
        tail = active >> position
        if tail:
            index = position + (tail & -tail).bit_length() - 1
        else:
            index = (active & -active).bit_length() - 1

        distance += (index - position) & 1023
        position = index
        active ^= bits[index]
        current = buckets[index]

        for u in current:
            if distances[u] != distance:
                continue

            farthest = distance
            for edge in graph[u]:
                v = edge >> 10
                candidate = distance + (edge & 1023)
                if candidate < distances[v]:
                    distances[v] = candidate
                    slot = candidate & 1023
                    bucket = buckets[slot]
                    if not bucket:
                        active |= bits[slot]
                    bucket.append(v)

        current.clear()

    unreachable = distances.count(infinity)
    reachable = n - unreachable
    total = sum(distances) - unreachable * infinity
    node = distances.index(farthest)
    return f"{source} {reachable} {total} {farthest} {node}"


def main():
    with open(sys.argv[1], "rb") as file:
        data = np.fromstring(file.read(), dtype=np.int64, sep=" ")

    n, m, q = map(int, data[:3])
    source_start = 3 + 3 * m
    sources = data[source_start:source_start + q].tolist()

    if not q:
        return

    if not m:
        sys.stdout.write(
            "\n".join(f"{s} 1 0 0 {s}" for s in sources) + "\n"
        )
        return

    edges = data[3:source_start].reshape(m, 3)
    shift = (n - 1).bit_length() + 10

    packed = np.empty(2 * m, dtype=np.int64)
    packed[:m] = (
        (edges[:, 0] << shift)
        | (edges[:, 1] << 10)
        | edges[:, 2]
    )
    packed[m:] = (
        (edges[:, 1] << shift)
        | (edges[:, 0] << 10)
        | edges[:, 2]
    )
    del edges, data

    packed.sort()

    # Sorting also places the shortest parallel road first.
    pairs = packed >> 10
    keep = np.empty(packed.size, dtype=np.bool_)
    keep[0] = True
    np.not_equal(pairs[1:], pairs[:-1], out=keep[1:])
    packed = packed[keep]
    del pairs, keep

    counts = np.bincount(packed >> shift, minlength=n)
    ends = np.cumsum(counts).tolist()
    values = (packed & ((1 << shift) - 1)).tolist()
    del packed, counts

    graph = []
    start = 0
    for end in ends:
        graph.append(values[start:end])
        start = end
    del ends, values

    # Every edge weight is smaller than the circular queue's period.
    buckets = [[] for _ in range(1024)]
    bits = [1 << i for i in range(1024)]
    infinity = n * 1000

    cache = {}
    output = []
    for source in sources:
        answer = cache.get(source)
        if answer is None:
            answer = shortest(
                source, graph, n, buckets, bits, infinity
            )
            cache[source] = answer
        output.append(answer)

    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
