"""Packed-integer SplitMix64 batches, with scalar walks in worker processes."""

import sys
from multiprocessing import Pool


def simulate(task):
    first, end, steps, bound, seed = task
    mask = (1 << 64) - 1
    gamma = 0x9E3779B97F4A7C15
    mul1 = 0xBF58476D1CE4E5B9
    mul2 = 0x94D049BB133111EB
    if steps == 0 or first == end:
        return 0, 0, 0, first, 0
    batch = min(steps, 8192)
    # Each 128-bit lane holds a uint64 value and 64 guard bits. Multiplication
    # by a uint64 constant fits within a lane, so Python's large-integer C
    # loops can evaluate thousands of independent generators at once. Masks
    # clear the guard bits after shifts and enforce modulo 2**64 arithmetic.
    ones = ((1 << (128 * batch)) - 1) // ((1 << 128) - 1)
    lanes_mask = ones * mask
    directions_mask = ones * 3
    base = int.from_bytes(b"".join(
        ((i * gamma) & mask).to_bytes(16, "little")
        for i in range(1, batch + 1)
    ), "little")
    low = -bound
    spread = bumps = returns = best_distance = 0
    best_walker = first
    for walker in range(first, end):
        state = (seed + walker) & mask
        x = y = 0
        for offset in range(0, steps, batch):
            count = min(batch, steps - offset)
            z = (base + ones * state) & lanes_mask
            z = (((z ^ (z >> 30)) & lanes_mask) * mul1) & lanes_mask
            z = ((z ^ (z >> 27)) & lanes_mask) * mul2
            # Only bits 62 and 63 matter; the final xor cannot affect them.
            directions = ((z >> 62) & directions_mask).to_bytes(16 * batch, "little")
            state = (state + count * gamma) & mask
            for direction in memoryview(directions)[:16 * count:16]:
                if direction == 0:
                    if x == bound:
                        bumps += 1
                        continue
                    x += 1
                elif direction == 1:
                    if x == low:
                        bumps += 1
                        continue
                    x -= 1
                elif direction == 2:
                    if y == bound:
                        bumps += 1
                        continue
                    y += 1
                else:
                    if y == low:
                        bumps += 1
                        continue
                    y -= 1
                if x == 0 and y == 0:
                    returns += 1
        spread += x * x + y * y
        distance = abs(x) + abs(y)
        if distance > best_distance:
            best_distance = distance
            best_walker = walker
    return spread, bumps, returns, best_walker, best_distance


def main():
    with open(sys.argv[1], "rb") as source:
        walkers, steps, bound, seed = map(int, source.read().split())
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
