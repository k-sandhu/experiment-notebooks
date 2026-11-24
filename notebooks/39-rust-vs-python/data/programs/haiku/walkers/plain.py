import sys
from concurrent.futures import ProcessPoolExecutor

MASK = (1 << 64) - 1
GAMMA = 0x9E3779B97F4A7C15


def walk_range(task):
    """Walk walkers lo..hi-1 and return (spread, bumps, returns, best_dist, best_walker)."""
    lo, hi, steps, bound, seed = task
    neg_bound = -bound
    spread = bumps = returns = 0
    best_dist, best_walker = -1, 0
    for walker in range(lo, hi):
        state = (seed + walker) & MASK
        x = y = 0
        for _ in range(steps):
            state = (state + GAMMA) & MASK
            z = ((state ^ (state >> 30)) * 0xBF58476D1CE4E5B9) & MASK
            z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
            d = (z ^ (z >> 31)) >> 62
            if d < 2:
                nx = x + 1 if d == 0 else x - 1
                ny = y
            else:
                nx = x
                ny = y + 1 if d == 2 else y - 1
            if neg_bound <= nx <= bound and neg_bound <= ny <= bound:
                x = nx
                y = ny
                if not (x or y):
                    returns += 1
            else:
                bumps += 1
        dist = abs(x) + abs(y)
        spread += x * x + y * y
        if dist > best_dist:
            best_dist, best_walker = dist, walker
    return spread, bumps, returns, best_dist, best_walker


def main():
    path = sys.argv[1]
    workers = int(sys.argv[2])
    with open(path) as f:
        walkers, steps, bound, seed = map(int, f.read().split())
    workers = max(1, min(workers, walkers))
    tasks = [
        (walkers * w // workers, walkers * (w + 1) // workers, steps, bound, seed)
        for w in range(workers)
    ]
    if workers == 1:
        parts = [walk_range(tasks[0])]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parts = list(pool.map(walk_range, tasks))

    spread = bumps = returns = 0
    best_dist, best_walker = -1, 0
    for p_spread, p_bumps, p_returns, p_dist, p_walker in parts:
        spread += p_spread
        bumps += p_bumps
        returns += p_returns
        if p_dist > best_dist or (p_dist == best_dist and p_walker < best_walker):
            best_dist, best_walker = p_dist, p_walker
    if best_dist < 0:
        best_dist = 0

    report = (
        f"spread {spread}\n"
        f"bumps {bumps}\n"
        f"returns {returns}\n"
        f"farthest {best_walker} {best_dist}\n"
    )
    sys.stdout.buffer.write(report.encode())


if __name__ == "__main__":
    main()
