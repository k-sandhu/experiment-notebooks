import multiprocessing as mp
import sys


def simulate(start, stop, length, bound, seed):
    mask = (1 << 64) - 1
    increment = 0x9E3779B97F4A7C15
    multiplier1 = 0xBF58476D1CE4E5B9
    multiplier2 = 0x94D049BB133111EB
    negative_bound = -bound
    steps = range(length)

    spread = 0
    bumps = 0
    returns = 0
    best_walker = start
    best_distance = -1

    for walker in range(start, stop):
        state = (seed + walker) & mask
        x = 0
        y = 0

        for _ in steps:
            state = (state + increment) & mask
            z = ((state ^ (state >> 30)) * multiplier1) & mask

            # The final XOR with z >> 31 cannot change the top two bits.
            direction = (((z ^ (z >> 27)) * multiplier2) >> 62) & 3

            if direction == 0:
                if x != bound:
                    x += 1
                else:
                    bumps += 1
            elif direction == 1:
                if x != negative_bound:
                    x -= 1
                else:
                    bumps += 1
            elif direction == 2:
                if y != bound:
                    y += 1
                else:
                    bumps += 1
            else:
                if y != negative_bound:
                    y -= 1
                else:
                    bumps += 1

            # Since bound >= 1, a bump cannot occur at the origin.
            if not x and not y:
                returns += 1

        spread += x * x + y * y
        distance = abs(x) + abs(y)
        if distance > best_distance:
            best_distance = distance
            best_walker = walker

    return spread, bumps, returns, best_walker, best_distance


def worker(connection, start, stop, length, bound, seed):
    try:
        connection.send(simulate(start, stop, length, bound, seed))
    finally:
        connection.close()


def main():
    with open(sys.argv[1], "rb") as input_file:
        walkers, length, bound, seed = map(int, input_file.read().split())

    workers = int(sys.argv[2])
    children = []

    if workers > 1:
        context = mp.get_context("spawn")
        for index in range(1, workers):
            start = walkers * index // workers
            stop = walkers * (index + 1) // workers
            receiver, sender = context.Pipe(duplex=False)
            process = context.Process(
                target=worker,
                args=(sender, start, stop, length, bound, seed),
            )
            process.start()
            sender.close()
            children.append((process, receiver))

    # The main process is also a worker, giving exactly WORKERS processes.
    spread, bumps, returns, best_walker, best_distance = simulate(
        0, walkers // workers, length, bound, seed
    )

    for process, receiver in children:
        part_spread, part_bumps, part_returns, walker, distance = receiver.recv()
        receiver.close()
        process.join()

        spread += part_spread
        bumps += part_bumps
        returns += part_returns
        if distance > best_distance or (
            distance == best_distance and walker < best_walker
        ):
            best_walker = walker
            best_distance = distance

    sys.stdout.write(
        f"spread {spread}\n"
        f"bumps {bumps}\n"
        f"returns {returns}\n"
        f"farthest {best_walker} {best_distance}\n"
    )


if __name__ == "__main__":
    main()
