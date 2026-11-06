import sys
import threading
import multiprocessing as mp

M64 = 0xFFFFFFFFFFFFFFFF
GOLDEN = 0x9E3779B97F4A7C15
MIX1 = 0xBF58476D1CE4E5B9
MIX2 = 0x94D049BB133111EB

# SplitMix64 is evaluated for BATCH consecutive steps at once, "SIMD style": one big
# integer holds BATCH lanes of 128 bits, each lane carrying a 64-bit value in its low
# half. A 64x64-bit product fits in a lane, so a whole batch costs a handful of
# big-integer operations instead of ten per step.
BATCH = 4096
LANE_BYTES = 16
LANE_BITS = 8 * LANE_BYTES


def packed(value):
    """`value` (< 2**128) repeated in every lane."""
    return int.from_bytes(value.to_bytes(LANE_BYTES, "little") * BATCH, "little")


LANE_MASK = packed(M64)
# The direction is bits 62-63 of the output; the final z ^ (z >> 31) leaves them alone.
# Byte 7 of each lane holds bits 56-63, so the direction is that byte >> 6.
TOP_TO_DIR = bytes(v >> 6 for v in range(256))

# Below this many safe steps, a stretch is walked step by step.
MIN_SKIP = 12
SLOW_STEPS = 16


def directions(state):
    """Yield, batch by batch, bytes with the direction (0..3) of each step."""
    advance = packed(BATCH * GOLDEN & M64)
    s = int.from_bytes(
        b"".join(((state + (k + 1) * GOLDEN) & M64).to_bytes(LANE_BYTES, "little") for k in range(BATCH)),
        "little",
    )
    nbytes = BATCH * LANE_BYTES
    mask = LANE_MASK
    while True:
        z = (s ^ (s >> 30)) & mask
        z = (z * MIX1) & mask
        z = ((z ^ (z >> 27)) & mask) * MIX2
        # only the low 64 bits of every lane matter; higher bits stay inside the lane
        yield z.to_bytes(nbytes, "little")[7:nbytes:LANE_BYTES].translate(TOP_TO_DIR)
        s = (s + advance) & mask


def walk(seed, steps, b):
    """Run one walker; return (x, y, bumps, returns)."""
    x = y = 0
    bumps = returns = 0
    nb = -b
    gen = directions(seed)
    left = steps
    while left > 0:
        ds = next(gen)
        n = BATCH if left > BATCH else left
        left -= n
        i = 0
        while i < n:
            ax = x if x >= 0 else -x
            ay = y if y >= 0 else -y
            # Steps the walker surely takes without touching a wall or the origin.
            m = b - (ax if ax > ay else ay)
            o = ax + ay - 1
            if o < m:
                m = o
            if m >= MIN_SKIP:
                e = i + m
                if e > n:
                    e = n
                x += ds.count(0, i, e) - ds.count(1, i, e)
                y += ds.count(2, i, e) - ds.count(3, i, e)
                i = e
                continue
            e = i + SLOW_STEPS
            if e > n:
                e = n
            for d in ds[i:e]:
                if d == 0:
                    if x < b:
                        x += 1
                        if not x and not y:
                            returns += 1
                    else:
                        bumps += 1
                elif d == 1:
                    if x > nb:
                        x -= 1
                        if not x and not y:
                            returns += 1
                    else:
                        bumps += 1
                elif d == 2:
                    if y < b:
                        y += 1
                        if not x and not y:
                            returns += 1
                    else:
                        bumps += 1
                elif y > nb:
                    y -= 1
                    if not x and not y:
                        returns += 1
                else:
                    bumps += 1
            i = e
    return x, y, bumps, returns


def claim(counter, owner, me, total):
    """Yield walker numbers taken from the shared counter, recording `me` as their owner."""
    lock = counter.get_lock()
    while True:
        with lock:
            k = counter.value
            if k >= total:
                return
            counter.value = k + 1
            owner[k] = me
        yield k


def worker(me, counter, owner, conn, seed, total, steps, b):
    conn.send([(k, walk((seed + k) & M64, steps, b)) for k in claim(counter, owner, me, total)])
    conn.close()


def start_workers(count, counter, owner, conns, args):
    for me in range(1, count + 1):
        if counter.value >= len(owner):
            break
        recv_end, send_end = mp.Pipe(False)
        conns[me] = recv_end
        mp.Process(target=worker, args=(me, counter, owner, send_end) + args, daemon=True).start()
    sys.setswitchinterval(0.005)


def main():
    with open(sys.argv[1]) as f:
        j, steps, b, seed = map(int, f.read().split()[:4])
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    workers = max(1, min(workers, j))

    if workers == 1:
        results = [walk((seed + k) & M64, steps, b) for k in range(j)]
    else:
        # Walkers are handed out one at a time from a shared counter. This process walks
        # too while a helper thread starts the other workers, so their start-up time
        # (hundreds of milliseconds on Windows) is not spent idle. Workers that only come up
        # after every walker is taken have nothing to report and are terminated at exit.
        counter = mp.Value("q", 0)
        owner = mp.Array("i", j, lock=False)
        conns = {}
        starter = threading.Thread(
            target=start_workers, args=(workers - 1, counter, owner, conns, (seed, j, steps, b))
        )
        # Hand the GIL over often while the helper thread is still starting workers.
        sys.setswitchinterval(0.0002)
        starter.start()
        results = [None] * j
        for k in claim(counter, owner, 0, j):
            results[k] = walk((seed + k) & M64, steps, b)
        starter.join()
        for me in set(owner):
            if me:
                for k, r in conns[me].recv():
                    results[k] = r

    spread = bumps = returns = 0
    best_j, best_d = 0, -1
    for w, (x, y, bu, re) in enumerate(results):
        spread += x * x + y * y
        bumps += bu
        returns += re
        d = abs(x) + abs(y)
        if d > best_d:
            best_d, best_j = d, w
    if best_d < 0:
        best_d = 0
    sys.stdout.buffer.write(
        f"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {best_j} {best_d}\n".encode()
    )


if __name__ == "__main__":
    main()
