import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np


MASK = (1 << 64) - 1
GAMMA = 0x9E3779B97F4A7C15
G64 = np.uint64(GAMMA)
M1 = np.uint64(0xBF58476D1CE4E5B9)
M2 = np.uint64(0x94D049BB133111EB)


def directions(state, n):
    z = np.arange(n, dtype=np.uint64)
    z *= G64
    z += np.uint64((state + GAMMA) & MASK)
    z ^= z >> 30
    z *= M1
    z ^= z >> 27
    z *= M2
    z ^= z >> 31
    z >>= 62
    return z.astype(np.uint8), (state + n * GAMMA) & MASK


def reflect(p, bound):
    outside = (p > bound) | (p < -bound)
    start = int(outside.argmax())
    if not outside[start]:
        return 0

    upper = bool(p[start] > bound)
    bumps = 0

    while True:
        v = p[start:]

        if upper:
            correction = np.maximum.accumulate(v)
            np.maximum(correction, bound, out=correction)
            correction -= bound
            adjusted = v - correction
            opposite = adjusted < -bound
        else:
            correction = np.minimum.accumulate(v)
            np.minimum(correction, -bound, out=correction)
            correction += bound
            adjusted = v - correction
            opposite = adjusted > bound

        k = int(opposite.argmax())
        if not opposite[k]:
            v[:] = adjusted
            bumps += abs(int(correction[-1]))
            return bumps

        amount = int(correction[k])
        bumps += abs(amount)
        v[:k] = adjusted[:k]
        v[k:] -= amount
        start += k
        upper = not upper


def scalar_walk(state, steps, bound):
    x = y = bumps = returns = 0
    remaining = steps

    while remaining:
        n = min(65536, remaining)
        ds, state = directions(state, n)

        for d in ds.tobytes():
            if d == 0:
                if x < bound:
                    x += 1
                else:
                    bumps += 1
            elif d == 1:
                if x > -bound:
                    x -= 1
                else:
                    bumps += 1
            elif d == 2:
                if y < bound:
                    y += 1
                else:
                    bumps += 1
            else:
                if y > -bound:
                    y -= 1
                else:
                    bumps += 1

            if x == 0 and y == 0:
                returns += 1

        remaining -= n

    return x, y, bumps, returns


def vector_walk(state, steps, bound, dtype, block):
    x = y = bumps = returns = 0
    remaining = steps

    while remaining:
        n = min(block, remaining)
        ds, state = directions(state, n)

        px = (ds == 0).astype(dtype)
        px -= ds == 1
        np.cumsum(px, dtype=dtype, out=px)
        px += x
        bumps += reflect(px, bound)

        py = (ds == 2).astype(dtype)
        py -= ds == 3
        np.cumsum(py, dtype=dtype, out=py)
        py += y
        bumps += reflect(py, bound)

        returns += int(np.count_nonzero((px == 0) & (py == 0)))
        x = int(px[-1])
        y = int(py[-1])
        remaining -= n

    return x, y, bumps, returns


def run_group(first, last, steps, bound, seed):
    spread = bumps = returns = 0
    farthest_j = first
    farthest_d = -1
    dtype = np.int32 if steps <= 2147483647 else np.int64
    block = 65536 if bound >= 182 else max(1024, 2 * bound * bound)

    for j in range(first, last):
        state = (seed + j) & MASK

        if bound < 24:
            x, y, b, r = scalar_walk(state, steps, bound)
        else:
            x, y, b, r = vector_walk(
                state, steps, bound, dtype, block
            )

        spread += x * x + y * y
        bumps += b
        returns += r
        distance = abs(x) + abs(y)

        if distance > farthest_d:
            farthest_d = distance
            farthest_j = j

    return spread, bumps, returns, farthest_j, farthest_d


def main():
    with open(sys.argv[1], "rb") as f:
        walkers, steps, bound, seed = map(int, f.read().split())

    workers = int(sys.argv[2])
    bound = min(bound, steps)

    if workers == 1:
        results = [run_group(0, walkers, steps, bound, seed)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    run_group,
                    walkers * w // workers,
                    walkers * (w + 1) // workers,
                    steps,
                    bound,
                    seed,
                )
                for w in range(workers)
            ]
            results = [future.result() for future in futures]

    spread = bumps = returns = 0
    farthest_j = 0
    farthest_d = -1

    for s, b, r, j, d in results:
        spread += s
        bumps += b
        returns += r
        if d > farthest_d or (d == farthest_d and j < farthest_j):
            farthest_j = j
            farthest_d = d

    sys.stdout.write(
        f"spread {spread}\n"
        f"bumps {bumps}\n"
        f"returns {returns}\n"
        f"farthest {farthest_j} {farthest_d}\n"
    )


if __name__ == "__main__":
    main()
