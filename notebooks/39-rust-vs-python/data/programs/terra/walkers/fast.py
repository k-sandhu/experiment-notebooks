import multiprocessing as mp
import sys

import numpy as np

MASK = (1 << 64) - 1
GAMMA = 0x9E3779B97F4A7C15
BLOCK = 4096


def run_walks(task):
    start, end, steps, bound, seed = task
    spread = bumps = returns = 0
    best_j, best_d = -1, -1
    increments = np.arange(1, min(BLOCK, steps) + 1, dtype=np.uint64)
    increments *= np.uint64(GAMMA)
    for j in range(start, end):
        state = (seed + j) & MASK
        x = y = 0
        for offset in range(0, steps, BLOCK):
            n = min(BLOCK, steps - offset)
            z = increments[:n] + np.uint64(state)
            state = (state + n * GAMMA) & MASK
            z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
            z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
            directions = ((z ^ (z >> np.uint64(31))) >> np.uint64(62)).astype(np.uint8)
            dx = (directions == 0).astype(np.int8) - (directions == 1)
            dy = (directions == 2).astype(np.int8) - (directions == 3)
            xs = np.cumsum(dx, dtype=np.int64) + x
            ys = np.cumsum(dy, dtype=np.int64) + y
            if (xs.min() >= -bound and xs.max() <= bound and
                    ys.min() >= -bound and ys.max() <= bound):
                returns += int(np.count_nonzero((xs == 0) & (ys == 0)))
                x, y = int(xs[-1]), int(ys[-1])
            else:
                for direction in directions.tolist():
                    if direction == 0:
                        if x < bound: x += 1
                        else:
                            bumps += 1
                            continue
                    elif direction == 1:
                        if x > -bound: x -= 1
                        else:
                            bumps += 1
                            continue
                    elif direction == 2:
                        if y < bound: y += 1
                        else:
                            bumps += 1
                            continue
                    else:
                        if y > -bound: y -= 1
                        else:
                            bumps += 1
                            continue
                    returns += x == 0 and y == 0
        spread += x * x + y * y
        distance = abs(x) + abs(y)
        if distance > best_d:
            best_j, best_d = j, distance
    return spread, bumps, returns, best_j, best_d


def main():
    with open(sys.argv[1]) as f:
        walkers, steps, bound, seed = map(int, f.read().split())
    bound = min(bound, steps)
    workers = int(sys.argv[2])
    tasks = [(walkers * w // workers, walkers * (w + 1) // workers,
              steps, bound, seed) for w in range(workers)]
    if workers == 1:
        results = [run_walks(tasks[0])]
    else:
        with mp.Pool(workers) as pool:
            results = pool.map(run_walks, tasks)
    spread = sum(r[0] for r in results)
    bumps = sum(r[1] for r in results)
    returns = sum(r[2] for r in results)
    best = min(results, key=lambda r: (-r[4], r[3]))
    print(f"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {best[3]} {best[4]}")


if __name__ == '__main__':
    main()
