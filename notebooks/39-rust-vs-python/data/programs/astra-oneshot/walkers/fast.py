import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np


MASK64 = (1 << 64) - 1
STEP = 0x9E3779B97F4A7C15
MUL1 = np.uint64(0xBF58476D1CE4E5B9)
MUL2 = np.uint64(0x94D049BB133111EB)


def reflect(path, bound, extremes, adjusted, flags):
    low = int(path.min())
    high = int(path.max())

    if low >= -bound and high <= bound:
        return 0

    if low >= -bound:
        np.greater(path, bound, out=flags)
        start = int(flags.argmax())
        upper = True
    elif high <= bound:
        np.less(path, -bound, out=flags)
        start = int(flags.argmax())
        upper = False
    else:
        np.greater(path, bound, out=flags)
        first_upper = int(flags.argmax())
        np.less(path, -bound, out=flags)
        first_lower = int(flags.argmax())
        upper = first_upper < first_lower
        start = first_upper if upper else first_lower

    size = path.size
    shift = 0
    bumps = 0

    while start < size:
        remaining = size - start
        source = path[start:]
        extreme = extremes[:remaining]
        result = adjusted[:remaining]
        bad = flags[:remaining]

        if upper:
            np.maximum.accumulate(source, out=extreme)
            np.subtract(source, extreme, out=result)
            np.add(result, bound, out=result)
            np.less(result, -bound, out=bad)
            target = bound
        else:
            np.minimum.accumulate(source, out=extreme)
            np.subtract(source, extreme, out=result)
            np.subtract(result, bound, out=result)
            np.greater(result, bound, out=bad)
            target = -bound

        count = int(bad.argmax())
        # The first adjusted position is on the active boundary,
        # so an argmax of zero means there is no opposite violation.
        if count == 0:
            count = remaining

        new_shift = target - int(extreme[count - 1])
        bumps += abs(new_shift - shift)
        path[start:start + count] = result[:count]

        shift = new_shift
        start += count
        upper = not upper

    return bumps


def main():
    with open(sys.argv[1], "rb") as source:
        walkers, steps, bound, seed = map(int, source.read().split())
    workers = int(sys.argv[2])

    bound = min(bound, steps)
    scalar = bound < 16 or steps < 256

    if scalar:
        block_size = min(steps, 65536)
    else:
        block_size = min(steps, 65536, max(1024, 8 * bound * bound))

    offsets = np.arange(1, block_size + 1, dtype=np.uint64)
    np.multiply(offsets, np.uint64(STEP), out=offsets)

    def run_group(group):
        first, last = group
        if first == last:
            return 0, 0, 0, walkers, -1

        bits = np.empty(block_size, dtype=np.uint64)
        scratch = np.empty(block_size, dtype=np.uint64)

        if not scalar:
            x_buffer = np.empty(block_size, dtype=np.int64)
            y_buffer = np.empty(block_size, dtype=np.int64)
            flag_buffer = np.empty(block_size, dtype=np.bool_)
            other_flags = np.empty(block_size, dtype=np.bool_)
            extreme_buffer = scratch.view(np.int64)
            adjusted_buffer = bits.view(np.int64)

        total_spread = 0
        total_bumps = 0
        total_returns = 0
        best_id = first
        best_distance = -1

        for walker in range(first, last):
            state = (seed + walker) & MASK64
            x = 0
            y = 0
            remaining = steps

            while remaining:
                count = min(remaining, block_size)
                z = bits[:count]
                temp = scratch[:count]

                np.add(offsets[:count], np.uint64(state), out=z)
                state = (state + count * STEP) & MASK64

                np.right_shift(z, 30, out=temp)
                np.bitwise_xor(z, temp, out=z)
                np.multiply(z, MUL1, out=z)

                np.right_shift(z, 27, out=temp)
                np.bitwise_xor(z, temp, out=z)
                np.multiply(z, MUL2, out=z)

                np.right_shift(z, 31, out=temp)
                np.bitwise_xor(z, temp, out=z)
                np.right_shift(z, 62, out=z)

                if scalar:
                    for direction in z.astype(np.uint8).tobytes():
                        if direction == 0:
                            if x == bound:
                                total_bumps += 1
                            else:
                                x += 1
                        elif direction == 1:
                            if x == -bound:
                                total_bumps += 1
                            else:
                                x -= 1
                        elif direction == 2:
                            if y == bound:
                                total_bumps += 1
                            else:
                                y += 1
                        else:
                            if y == -bound:
                                total_bumps += 1
                            else:
                                y -= 1

                        if x == 0 and y == 0:
                            total_returns += 1
                else:
                    xp = x_buffer[:count]
                    yp = y_buffer[:count]
                    flags = flag_buffer[:count]

                    np.equal(z, 0, out=xp)
                    np.equal(z, 1, out=flags)
                    np.subtract(xp, flags, out=xp)
                    np.cumsum(xp, out=xp)
                    np.add(xp, x, out=xp)

                    np.equal(z, 2, out=yp)
                    np.equal(z, 3, out=flags)
                    np.subtract(yp, flags, out=yp)
                    np.cumsum(yp, out=yp)
                    np.add(yp, y, out=yp)

                    extremes = extreme_buffer[:count]
                    adjusted = adjusted_buffer[:count]

                    total_bumps += reflect(
                        xp, bound, extremes, adjusted, flags
                    )
                    total_bumps += reflect(
                        yp, bound, extremes, adjusted, flags
                    )

                    zeros_y = other_flags[:count]
                    np.equal(xp, 0, out=flags)
                    np.equal(yp, 0, out=zeros_y)
                    np.logical_and(flags, zeros_y, out=flags)
                    total_returns += int(np.count_nonzero(flags))

                    x = int(xp[-1])
                    y = int(yp[-1])

                remaining -= count

            total_spread += x * x + y * y
            distance = abs(x) + abs(y)
            if distance > best_distance:
                best_distance = distance
                best_id = walker

        return (
            total_spread,
            total_bumps,
            total_returns,
            best_id,
            best_distance,
        )

    groups = [
        (i * walkers // workers, (i + 1) * walkers // workers)
        for i in range(workers)
    ]

    if workers == 1:
        results = [run_group(groups[0])]
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(run_group, groups))

    spread = 0
    bumps = 0
    returns = 0
    farthest_id = walkers
    farthest_distance = -1

    for group_spread, group_bumps, group_returns, index, distance in results:
        spread += group_spread
        bumps += group_bumps
        returns += group_returns
        if distance > farthest_distance or (
            distance == farthest_distance and index < farthest_id
        ):
            farthest_id = index
            farthest_distance = distance

    sys.stdout.write(
        f"spread {spread}\n"
        f"bumps {bumps}\n"
        f"returns {returns}\n"
        f"farthest {farthest_id} {farthest_distance}\n"
    )


if __name__ == "__main__":
    main()
