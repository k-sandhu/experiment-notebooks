"""NumPy CSR graph and batched, integer delta-stepping shortest paths."""
import sys
import os

# Keep NumPy's native runtime single-threaded as well.
for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'BLIS_NUM_THREADS'):
    os.environ[variable] = '1'
import numpy as np


def parse_numbers(data, dtype):
    # Decode all positive decimal integers with vectorized digit gathers.
    # No Python object per token, and no locale-sensitive text conversions.
    raw = np.frombuffer(b' ' * 20 + data + b' ', dtype=np.uint8)
    digit = raw > 32
    positions = np.flatnonzero(digit[:-1] & ~digit[1:])
    values = np.zeros(positions.size, dtype=dtype)
    active = np.ones(positions.size, dtype=bool)
    factor = 1
    while True:
        digits = raw[positions]
        active &= digits > 32
        if not np.any(active):
            return values
        contribution = digits.astype(dtype) - 48
        contribution[~active] = 0
        values += contribution * factor
        positions -= 1
        factor *= 10


def read_graph(path):
    with open(path, 'rb') as file:
        n, m, q = map(int, file.readline().split())
        dtype = np.int32 if n <= 2**31 else np.int64
        values = parse_numbers(file.read(), dtype)
    sources = values[3 * m:3 * m + q].tolist()
    roads = values[:3 * m].reshape(m, 3)
    roads = roads[roads[:, 0] != roads[:, 1]]
    del values
    if n > 2**21:
        roads = roads.astype(np.int64)
    u, v, w = roads.T
    origins = np.concatenate((u, v))
    packed = np.concatenate(((v << 10) | w, (u << 10) | w))
    del roads, u, v, w
    offsets = np.empty(n + 1, dtype=np.int64)
    offsets[0] = 0
    np.cumsum(np.bincount(origins, minlength=n), out=offsets[1:])
    order = np.argsort(origins, kind='stable')
    return offsets, packed[order], sources


def shortest_paths(offsets, edges, source):
    n = len(offsets) - 1
    infinity = 1000 * n + 1
    distances = np.full(n, infinity, dtype=np.int64)
    distances[source] = 0
    # Width 32, 64 circular buckets: a relaxation moves at most 32 buckets.
    small = [[] for _ in range(64)]
    large = [[] for _ in range(64)]
    small[0].append(source)
    occupied = 1
    current = 0
    bits = [1 << i for i in range(64)]
    offset_view = memoryview(offsets)
    edge_view = memoryview(edges)
    distance_view = memoryview(distances)

    while occupied:
        start = current & 63
        later = occupied >> start
        if later:
            current += (later & -later).bit_length() - 1
        else:
            current += 64 - start + (occupied & -occupied).bit_length() - 1
        index = current & 63
        scalar_nodes = small[index]
        chunks = large[index]
        small[index] = []
        large[index] = []
        occupied ^= bits[index]

        if not chunks and len(scalar_nodes) < 128:
            # Scalar work avoids NumPy dispatch/allocation costs on narrow
            # frontiers, isolated nodes, and long, thin components.
            steps = 0
            while scalar_nodes and steps < 128:
                node = scalar_nodes.pop()
                distance = distance_view[node]
                if distance >> 5 != current:
                    continue
                steps += 1
                begin = offset_view[node]
                end = offset_view[node + 1]
                if end - begin >= 256:
                    # A small frontier may still contain a very large hub.
                    scalar_nodes.append(node)
                    large[index].append(np.asarray(scalar_nodes, dtype=np.int64))
                    scalar_nodes = []
                    occupied |= bits[index]
                    break
                for j in range(begin, end):
                    edge = edge_view[j]
                    neighbor = edge >> 10
                    candidate = distance + (edge & 1023)
                    if candidate < distance_view[neighbor]:
                        distance_view[neighbor] = candidate
                        target_index = (candidate >> 5) & 63
                        if target_index == index:
                            scalar_nodes.append(neighbor)
                        else:
                            small[target_index].append(neighbor)
                            occupied |= bits[target_index]
            if scalar_nodes:
                small[index] = scalar_nodes
                occupied |= bits[index]
            continue

        if scalar_nodes:
            chunks.append(np.asarray(scalar_nodes, dtype=np.int64))
        active = np.unique(chunks[0] if len(chunks) == 1 else np.concatenate(chunks))
        labels = distances[active]
        valid = (labels >> 5) == current
        active = active[valid]
        labels = labels[valid]
        if not active.size:
            continue
        starts = offsets[active]
        counts = offsets[active + 1] - starts
        ends = np.cumsum(counts)
        if not ends[-1]:
            continue
        # Expand variable-length CSR rows entirely in native NumPy loops.
        positions = np.arange(ends[-1], dtype=np.int64)
        positions += np.repeat(starts - (ends - counts), counts)
        packed = edges[positions]
        targets = packed >> 10
        candidates = np.repeat(labels, counts) + (packed & 1023)
        improve = candidates < distances[targets]
        targets = targets[improve]
        candidates = candidates[improve]
        if not targets.size:
            continue
        # Repeated endpoints must reduce by minimum, never overwrite in
        # advanced-index assignment order (parallel roads are legal).
        np.minimum.at(distances, targets, candidates)
        valid = candidates == distances[targets]
        targets = targets[valid]
        keys = candidates[valid] >> 5
        order = np.argsort(keys, kind='stable')
        targets = targets[order]
        keys = keys[order]
        boundaries = np.flatnonzero(keys[1:] != keys[:-1]) + 1
        begin = 0
        for end in boundaries:
            target_index = int(keys[begin]) & 63
            large[target_index].append(targets[begin:end])
            occupied |= bits[target_index]
            begin = int(end)
        target_index = int(keys[begin]) & 63
        large[target_index].append(targets[begin:])
        occupied |= bits[target_index]

    reached = distances != infinity
    reachable = int(np.count_nonzero(reached))
    total = int(np.sum(distances, where=reached, dtype=np.int64))
    far = int(np.max(distances, where=reached, initial=0))
    far_node = int(np.argmax(distances == far))
    return reachable, total, far, far_node


def main():
    offsets, edges, sources = read_graph(sys.argv[1])
    cache = {}
    output = []
    for source in sources:
        result = cache.get(source)
        if result is None:
            result = shortest_paths(offsets, edges, source)
            cache[source] = result
        output.append(f'{source} {result[0]} {result[1]} {result[2]} {result[3]}')
    if output:
        sys.stdout.write('\n'.join(output) + '\n')


if __name__ == '__main__':
    main()
