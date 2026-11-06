import sys

MASK = (1 << 64) - 1
GOLD = 0x9E3779B97F4A7C15
M1 = 0xBF58476D1CE4E5B9
M2 = 0x94D049BB133111EB


def run_chunk(args):
    start, end, L, B, seed = args
    spread = 0
    bumps_t = 0
    returns_t = 0
    best_j = start
    best_d = -1
    mask = MASK
    gold = GOLD
    m1 = M1
    m2 = M2
    nB = -B
    for j in range(start, end):
        state = (seed + j) & mask
        x = 0
        y = 0
        bumps = 0
        returns = 0
        for _ in range(L):
            state = (state + gold) & mask
            z = state
            z = ((z ^ (z >> 30)) * m1) & mask
            z = ((z ^ (z >> 27)) * m2) & mask
            d = z >> 62
            if d == 0:
                if x == B:
                    bumps += 1
                else:
                    x += 1
                    if x == 0 and y == 0:
                        returns += 1
            elif d == 1:
                if x == nB:
                    bumps += 1
                else:
                    x -= 1
                    if x == 0 and y == 0:
                        returns += 1
            elif d == 2:
                if y == B:
                    bumps += 1
                else:
                    y += 1
                    if x == 0 and y == 0:
                        returns += 1
            else:
                if y == nB:
                    bumps += 1
                else:
                    y -= 1
                    if x == 0 and y == 0:
                        returns += 1
        spread += x * x + y * y
        bumps_t += bumps
        returns_t += returns
        dist = x if x >= 0 else -x
        dist += y if y >= 0 else -y
        if dist > best_d:
            best_d = dist
            best_j = j
    return (spread, bumps_t, returns_t, best_j, best_d)


def main():
    argv = sys.argv
    with open(argv[1], "r") as f:
        parts = f.read().split()
    J = int(parts[0]); L = int(parts[1]); B = int(parts[2]); seed = int(parts[3])
    workers = int(argv[2]) if len(argv) > 2 else 1
    if workers < 1:
        workers = 1
    elif workers > 32:
        workers = 32

    if J == 0:
        sys.stdout.buffer.write(b"spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n")
        return

    if workers == 1 or J == 1:
        chunks = [(0, J, L, B, seed)]
        results = [run_chunk(chunks[0])]
    else:
        w = workers if workers < J else J
        # One chunk per worker: all walkers cost the same.
        chunk = (J + w - 1) // w
        chunks = []
        s = 0
        while s < J:
            e = s + chunk
            if e > J:
                e = J
            chunks.append((s, e, L, B, seed))
            s = e
        if len(chunks) == 1:
            results = [run_chunk(chunks[0])]
        else:
            import multiprocessing as mp
            with mp.Pool(processes=len(chunks)) as pool:
                results = pool.map(run_chunk, chunks)

    spread = 0; bumps = 0; returns = 0; best_j = 0; best_d = -1
    for sp, bu, re_, bj, bd in results:
        spread += sp; bumps += bu; returns += re_
        if bd > best_d:
            best_d = bd; best_j = bj
    if best_d < 0:
        best_d = 0
    sys.stdout.buffer.write(f"spread {spread}\nbumps {bumps}\nreturns {returns}\nfarthest {best_j} {best_d}\n".encode())


if __name__ == "__main__":
    main()
