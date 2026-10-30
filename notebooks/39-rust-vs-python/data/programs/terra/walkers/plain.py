import multiprocessing as mp
import sys

MASK = (1 << 64) - 1


def run_walks(task):
    start, end, steps, bound, seed = task
    spread = bumps = returns = 0
    best_j, best_d = -1, -1
    for j in range(start, end):
        state = (seed + j) & MASK
        x = y = 0
        for _ in range(steps):
            state = (state + 0x9E3779B97F4A7C15) & MASK
            z = ((state ^ (state >> 30)) * 0xBF58476D1CE4E5B9) & MASK
            z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
            d = (z ^ (z >> 31)) >> 62
            if d == 0:
                if x < bound: x += 1
                else:
                    bumps += 1
                    continue
            elif d == 1:
                if x > -bound: x -= 1
                else:
                    bumps += 1
                    continue
            elif d == 2:
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
