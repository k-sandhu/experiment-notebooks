import sys
from heapq import heappop, heappush


def main():
    with open(sys.argv[1], "rb") as f:
        readline = f.readline
        n, m, q = map(int, readline().split())
        graph = [[] for _ in range(n)]

        for _ in range(m):
            u, v, w = map(int, readline().split())
            if u != v:
                graph[u].append((v << 10) | w)
                graph[v].append((u << 10) | w)

        sources = list(map(int, readline().split()))

    infinity = 1 << 63
    push = heappush
    pop = heappop
    cache = {}
    output = []

    for source in sources:
        result = cache.get(source)

        if result is None:
            if not graph[source]:
                result = (1, 0, 0, source)
            else:
                distances = [infinity] * n
                distances[source] = 0

                buckets = [[] for _ in range(1024)]
                buckets[0].append(source)
                pending = [0]

                reachable = 0
                total = 0
                farthest = 0

                while pending:
                    distance = pop(pending)
                    batch = buckets[distance & 1023]
                    count = len(batch)

                    for u in batch:
                        if distances[u] != distance:
                            count -= 1
                            continue

                        for edge in graph[u]:
                            v = edge >> 10
                            candidate = distance + (edge & 1023)

                            if candidate < distances[v]:
                                distances[v] = candidate
                                target = buckets[candidate & 1023]
                                if not target:
                                    push(pending, candidate)
                                target.append(v)

                    batch.clear()

                    if count:
                        reachable += count
                        total += distance * count
                        farthest = distance

                result = (
                    reachable,
                    total,
                    farthest,
                    distances.index(farthest),
                )

            cache[source] = result

        reachable, total, farthest, node = result
        output.append(f"{source} {reachable} {total} {farthest} {node}")

    if output:
        sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
