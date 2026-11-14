import gc
import heapq
import sys


def shortest_routes(graph, source, infinity):
    distances = [infinity] * len(graph)
    distances[source] = 0

    # Pending distances span at most 1000, so circular buckets cannot collide.
    buckets = [[] for _ in range(1001)]
    buckets[0].append(source)
    queue = [0]

    push = heapq.heappush
    pop = heapq.heappop

    reachable = 0
    total = 0
    farthest = 0
    farthest_node = source
    node_count = len(graph)

    while queue:
        current = pop(queue)
        index = current % 1001
        nodes = buckets[index]
        buckets[index] = []

        count = 0
        smallest = node_count

        for u in nodes:
            if distances[u] != current:
                continue

            count += 1
            if u < smallest:
                smallest = u

            for v, weight in graph[u]:
                candidate = current + weight
                if candidate < distances[v]:
                    distances[v] = candidate
                    bucket = buckets[candidate % 1001]
                    if not bucket:
                        push(queue, candidate)
                    bucket.append(v)

        if count:
            reachable += count
            total += current * count
            farthest = current
            farthest_node = smallest

    return reachable, total, farthest, farthest_node


def main():
    gc.disable()

    with open(sys.argv[1], "rb") as input_file:
        readline = input_file.readline
        n, m, q = map(int, readline().split())
        graph = [[] for _ in range(n)]

        for _ in range(m):
            u, v, weight = map(int, readline().split())
            if u != v:
                graph[u].append((v, weight))
                graph[v].append((u, weight))

        sources = list(map(int, readline().split()))

    infinity = n * 1000 + 1
    results = {}
    output = []

    for source in sources:
        result = results.get(source)
        if result is None:
            if graph[source]:
                result = shortest_routes(graph, source, infinity)
            else:
                result = (1, 0, 0, source)
            results[source] = result

        reachable, total, farthest, node = result
        output.append(f"{source} {reachable} {total} {farthest} {node}")

    if output:
        sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
