"""Shortest paths using a circular, bitmap-indexed Dial queue."""
import sys
from array import array


def shortest_paths(graph, source, bits):
    n = len(graph)
    distances = [1000 * n + 1] * n
    distances[source] = 0
    buckets = [[] for _ in range(1024)]
    buckets[0].append(source)
    occupied = 1
    current = reachable = total = far = 0
    far_node = source
    while occupied:
        start = current & 1023
        later = occupied >> start
        if later:
            current += (later & -later).bit_length() - 1
        else:
            current += 1024 - start + (occupied & -occupied).bit_length() - 1
        index = current & 1023
        bucket = buckets[index]
        occupied ^= bits[index]
        while bucket:
            node = bucket.pop()
            if distances[node] != current:
                continue
            reachable += 1
            total += current
            if current > far:
                far = current
                far_node = node
            elif current == far and node < far_node:
                far_node = node
            row = iter(graph[node])
            for neighbor in row:
                candidate = current + next(row)
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    target_index = candidate & 1023
                    target = buckets[target_index]
                    if not target:
                        occupied |= bits[target_index]
                    target.append(neighbor)
    return reachable, total, far, far_node


def main():
    with open(sys.argv[1], 'rb') as file:
        n, m, q = map(int, file.readline().split())
        # Flat native arrays avoid a Python tuple and integer references for
        # every directed edge. Each row alternates neighbor, weight.
        code = 'I' if n <= 2**32 else 'Q'
        graph = [array(code) for _ in range(n)]
        for _ in range(m):
            u, v, w = map(int, file.readline().split())
            if u != v:
                graph[u].extend((v, w))
                graph[v].extend((u, w))
        sources = list(map(int, file.read().split()))
    bits = [1 << i for i in range(1024)]
    cache = {}
    output = []
    for source in sources[:q]:
        result = cache.get(source)
        if result is None:
            result = shortest_paths(graph, source, bits)
            cache[source] = result
        output.append(f'{source} {result[0]} {result[1]} {result[2]} {result[3]}')
    if output:
        sys.stdout.write('\n'.join(output) + '\n')


if __name__ == '__main__':
    main()
