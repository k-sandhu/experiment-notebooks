"""NumPy batches the generator and resolves reflecting boundaries with scans."""

import os
import sys
from multiprocessing import Pool

# Worker processes provide the parallelism; NumPy kernels need no BLAS pool.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import numpy as np


MASK = (1 << 64) - 1
GAMMA = 0x9E3779B97F4A7C15
BATCH = 65536


def narrow_path(increments, start, bound):
    """Scan compositions of clipped translations in a balanced binary tree.

    A segment maps x to clip(x + delta, low, high). This representation is
    closed under composition, so an upsweep builds segment maps and a
    downsweep finds every starting position in linear total array work.
    """
    size = increments.size
    padded = 1 << (size - 1).bit_length()
    delta = np.zeros(padded, dtype=np.int32)
    delta[:size] = increments
    low = np.maximum(delta, 0) - bound
    high = np.minimum(delta, 0) + bound
    levels = []
    while delta.size > 1:
        levels.append((delta, low, high))
        right_delta = delta[1::2]
        new_low = np.clip(low[::2] + right_delta, low[1::2], high[1::2])
        high = np.clip(high[::2] + right_delta, low[1::2], high[1::2])
        low = new_low
        delta = delta[::2] + right_delta
    starts = np.array([start], dtype=np.int32)
    for delta, low, high in reversed(levels):
        children = np.empty(delta.size, dtype=np.int32)
        children[::2] = starts
        children[1::2] = np.clip(starts + delta[::2], low[::2], high[::2])
        starts = children
    attempted = starts[:size] + increments
    path = np.clip(attempted, -bound, bound)
    return path, int(np.count_nonzero(attempted != path))


def bounded_path(increments, start, bound):
    """Return all positions and the bump count for a single coordinate.

    Between switches of the active wall, the blocked steps are precisely the
    new extrema of the unconstrained prefix sum. Each scan handles that whole
    interval at once.
    """
    if bound < 64:
        return narrow_path(increments, start, bound)
    dtype = np.int32 if bound <= 2147483647 - BATCH else np.int64
    path = np.cumsum(increments, dtype=dtype)
    path += start
    outside = (path > bound) | (path < -bound)
    if not outside.any():
        return path, 0
    bumps = 0
    offset = 0
    first = int(outside.argmax())
    upper = int(path[first]) > bound
    size = path.size
    phases = 0
    while first < size:
        # Keep adversarial paths linear as well: too many wall switches make
        # a composition scan cheaper than repeatedly scanning the suffix.
        if phases == 8:
            return narrow_path(increments, start, bound)
        phases += 1
        tail = path[first:]
        if upper:
            extrema = np.maximum.accumulate(tail)
            crossed = extrema - tail > 2 * bound
            stop = int(crossed.argmax()) if crossed.any() else tail.size
            last_offset = int(extrema[stop - 1]) - bound
            bumps += last_offset - offset
            tail[:stop] -= extrema[:stop] - bound
        else:
            extrema = np.minimum.accumulate(tail)
            crossed = tail - extrema > 2 * bound
            stop = int(crossed.argmax()) if crossed.any() else tail.size
            last_offset = int(extrema[stop - 1]) + bound
            bumps += offset - last_offset
            tail[:stop] -= extrema[:stop] + bound
        offset = last_offset
        first += stop
        upper = not upper
    return path, bumps


def simulate(task):
    first, end, steps, bound, seed = task
    spread = bumps = returns = best_distance = 0
    best_walker = first
    if steps == 0 or first == end:
        return 0, 0, 0, first, 0
    # Modular arithmetic on arrays deliberately uses uint64 wraparound.
    base = np.arange(1, min(steps, BATCH) + 1, dtype=np.uint64)
    base *= np.uint64(GAMMA)
    scratch = np.empty_like(base)
    for walker in range(first, end):
        state = (seed + walker) & MASK
        x = y = 0
        remaining = steps
        while remaining:
            count = min(remaining, BATCH)
            z = base[:count] + np.uint64(state)
            temp = scratch[:count]
            np.right_shift(z, 30, out=temp)
            np.bitwise_xor(z, temp, out=z)
            z *= np.uint64(0xBF58476D1CE4E5B9)
            np.right_shift(z, 27, out=temp)
            np.bitwise_xor(z, temp, out=z)
            z *= np.uint64(0x94D049BB133111EB)
            # Only the top two bits are used, unaffected by the final xor.
            np.right_shift(z, 62, out=z)
            direction = z.astype(np.int8)
            sign = 1 - 2 * (direction & 1)
            xs, bx = bounded_path(sign * (direction < 2), x, bound)
            ys, by = bounded_path(sign * (direction >= 2), y, bound)
            bumps += bx + by
            # A bump cannot occur at the origin (B >= 1).
            returns += int(np.count_nonzero((xs == 0) & (ys == 0)))
            x, y = int(xs[-1]), int(ys[-1])
            state = (state + count * GAMMA) & MASK
            remaining -= count
        spread += x * x + y * y
        distance = abs(x) + abs(y)
        if distance > best_distance:
            best_distance = distance
            best_walker = walker
    return spread, bumps, returns, best_walker, best_distance


def main():
    with open(sys.argv[1], "rb") as source:
        walkers, steps, bound, seed = map(int, source.read().split())
    # A bound beyond L is unreachable; this also keeps array arithmetic small.
    bound = min(bound, steps)
    workers = int(sys.argv[2])
    tasks = []
    first = 0
    for worker in range(workers):
        end = first + walkers // workers + (worker < walkers % workers)
        tasks.append((first, end, steps, bound, seed))
        first = end
    if workers == 1:
        results = [simulate(tasks[0])]
    else:
        with Pool(workers) as pool:
            results = pool.map(simulate, tasks, chunksize=1)
    best = max(results, key=lambda result: (result[4], -result[3]))
    output = (f"spread {sum(r[0] for r in results)}\n"
              f"bumps {sum(r[1] for r in results)}\n"
              f"returns {sum(r[2] for r in results)}\n"
              f"farthest {best[3]} {best[4]}\n")
    sys.stdout.buffer.write(output.encode("ascii"))


if __name__ == "__main__":
    main()
