import sys


MASK64 = (1 << 64) - 1
GAMMA = 0x9E3779B97F4A7C15
MUL1 = 0xBF58476D1CE4E5B9
MUL2 = 0x94D049BB133111EB


def scalar_walks(start, stop, steps, bound, seed):
    spread = bumps = returns = 0
    best_j = start
    best_d = -1
    lower = -bound

    mask = MASK64
    gamma = GAMMA
    mul1 = MUL1
    mul2 = MUL2

    for j in range(start, stop):
        state = (seed + j) & mask
        x = y = 0

        for _ in range(steps):
            state = (state + gamma) & mask
            z = ((state ^ (state >> 30)) * mul1) & mask

            # The final XOR cannot change the top two bits.
            direction = (((z ^ (z >> 27)) * mul2) >> 62) & 3

            if direction == 0:
                if x != bound:
                    x += 1
                else:
                    bumps += 1
            elif direction == 1:
                if x != lower:
                    x -= 1
                else:
                    bumps += 1
            elif direction == 2:
                if y != bound:
                    y += 1
                else:
                    bumps += 1
            else:
                if y != lower:
                    y -= 1
                else:
                    bumps += 1

            if not x and not y:
                returns += 1

        spread += x * x + y * y
        distance = abs(x) + abs(y)
        if distance > best_d:
            best_j = j
            best_d = distance

    return spread, bumps, returns, best_j, best_d


def packed_walks(start, stop, steps, bound, seed):
    # Independent walkers occupy widely separated integer fields.
    count = stop - start
    bounded = bound < steps
    bound = min(bound, steps)
    twice_bound = bound * 2
    coordinate_bits = twice_bound.bit_length()
    half = max(64, coordinate_bits + 1, steps.bit_length() + 1)
    stride = half * 2

    ones = ((1 << (stride * count)) - 1) // ((1 << stride) - 1)
    both = ones | (ones << half)
    state_mask = ones * MASK64
    increment = ones * GAMMA
    bias = both * bound
    position = bias
    padding = both * ((1 << coordinate_bits) - 1)
    return_padding = ones * ((1 << coordinate_bits) - 1)

    state = 0
    for i, j in enumerate(range(start, stop)):
        state |= ((seed + j) & MASK64) << (stride * i)

    bump_counts = return_counts = 0
    mul1 = MUL1
    mul2 = MUL2

    if bounded:
        for _ in range(steps):
            state = (state + increment) & state_mask
            z = (
                (state ^ ((state >> 30) & state_mask)) * mul1
            ) & state_mask
            z = (z ^ ((z >> 27) & state_mask)) * mul2

            low = (z >> 62) & ones
            high = (z >> 63) & ones

            active = (ones ^ high) | (high << half)
            negative = low | (low << half)

            target = (ones ^ low) * twice_bound
            target |= target << half

            at_boundary = (
                (~((position ^ target) + padding)) >> coordinate_bits
            ) & both
            blocked = active & at_boundary
            allowed = active ^ blocked

            position += allowed - ((allowed & negative) << 1)
            bump_counts += (blocked | (blocked >> half)) & ones

            difference = position ^ bias
            difference |= difference >> half
            return_counts += (
                (~(difference + return_padding)) >> coordinate_bits
            ) & ones
    else:
        for _ in range(steps):
            state = (state + increment) & state_mask
            z = (
                (state ^ ((state >> 30) & state_mask)) * mul1
            ) & state_mask
            z = (z ^ ((z >> 27) & state_mask)) * mul2

            low = (z >> 62) & ones
            high = (z >> 63) & ones
            active = (ones ^ high) | (high << half)
            negative = low | (low << half)

            position += active - ((active & negative) << 1)

            difference = position ^ bias
            difference |= difference >> half
            return_counts += (
                (~(difference + return_padding)) >> coordinate_bits
            ) & ones

    coordinate_mask = (1 << half) - 1
    counter_mask = (1 << stride) - 1
    spread = bumps = returns = 0
    best_j = start
    best_d = -1

    for j in range(start, stop):
        x = (position & coordinate_mask) - bound
        y = ((position >> half) & coordinate_mask) - bound
        spread += x * x + y * y
        bumps += bump_counts & counter_mask
        returns += return_counts & counter_mask

        distance = abs(x) + abs(y)
        if distance > best_d:
            best_j = j
            best_d = distance

        position >>= stride
        bump_counts >>= stride
        return_counts >>= stride

    return spread, bumps, returns, best_j, best_d


def work(arguments):
    start, stop, steps, bound, seed = arguments
    if stop - start >= 16:
        return packed_walks(start, stop, steps, bound, seed)
    return scalar_walks(start, stop, steps, bound, seed)


def main():
    with open(sys.argv[1], "rb") as source:
        walkers, steps, bound, seed = map(int, source.read().split())

    workers = int(sys.argv[2])
    jobs = [
        (
            i * walkers // workers,
            (i + 1) * walkers // workers,
            steps,
            bound,
            seed,
        )
        for i in range(workers)
    ]

    if workers == 1:
        results = [work(jobs[0])]
    else:
        import multiprocessing

        with multiprocessing.Pool(processes=workers) as pool:
            results = pool.map(work, jobs, chunksize=1)

    spread = bumps = returns = 0
    best_j = 0
    best_d = -1

    for part_spread, part_bumps, part_returns, j, distance in results:
        spread += part_spread
        bumps += part_bumps
        returns += part_returns
        if distance > best_d or (distance == best_d and j < best_j):
            best_j = j
            best_d = distance

    sys.stdout.write(
        f"spread {spread}\n"
        f"bumps {bumps}\n"
        f"returns {returns}\n"
        f"farthest {best_j} {best_d}\n"
    )


if __name__ == "__main__":
    main()
