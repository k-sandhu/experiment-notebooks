"""Straightforward standard-library solutions, also usable as standalone programs."""

import collections
import heapq
import json
import multiprocessing
import re
import sys
from pathlib import Path

MASK = (1 << 64) - 1
LOG_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ (GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(\?[^ ]*)? (\d{3}) \d+B (\d+)\.(\d)ms "[^"]*"$', re.ASCII)


def springs(path, workers=1):
    with open(path, encoding="ascii") as f:
        n_text, steps, dt_text, circumference = f.readline().split()
        n, steps, dt, circumference = int(n_text), int(steps), float(dt_text), float(circumference)
        x, v, mass, k, rest, damping = map(list, zip(*(map(float, line.split()) for line in f)))
    force = [0.0] * n
    for _ in range(steps):
        for i in range(n - 1):
            force[i] = k[i] * ((x[i + 1] - x[i]) - rest[i])
        force[-1] = k[-1] * (((x[0] + circumference) - x[-1]) - rest[-1])
        for i in range(n):
            net = (force[i] - force[i - 1]) - damping[i] * v[i]
            v[i] = v[i] + dt * (net / mass[i])
            x[i] = x[i] + dt * v[i]
    kinetic = sum(((.5 * mass[i]) * v[i]) * v[i] for i in range(n))
    potential = 0.0
    for i in range(n):
        stretch = ((x[i + 1] - x[i]) if i + 1 < n else ((x[0] + circumference) - x[i])) - rest[i]
        potential += ((.5 * k[i]) * stretch) * stretch
    fastest = max(range(n), key=lambda i: abs(v[i]))
    return f"kinetic {kinetic:.16e}\npotential {potential:.16e}\nposition {sum(x):.16e}\nfastest {fastest}\n"


def wordpairs(path, workers=1):
    counts = collections.Counter()
    words = pairs = 0
    previous = None
    with open(path, encoding="ascii") as f:
        for line in f:
            for match in re.finditer(r"[A-Za-z]+|[.!?]", line):
                token = match[0].lower()
                if token in (".", "!", "?"):
                    previous = None
                    continue
                words += 1
                if previous is not None:
                    counts[previous, token] += 1
                    pairs += 1
                previous = token
    result = [f"words {words}", f"pairs {pairs}", f"distinct {len(counts)}"]
    for (a, b), count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:20]:
        result.append(f"{count} {a} {b}")
    return "\n".join(result) + "\n"


def ledger(path, workers=1):
    counted = total = 0
    channels, accounts = {}, collections.defaultdict(int)
    with open(path, encoding="utf-8") as f:
        rates = json.loads(next(f))["rates"]
        for line in f:
            tx = json.loads(line)
            if tx["type"] == "void" or "test" in tx["tags"]:
                continue
            whole, _, fraction = tx["amount"].partition(".")
            hundredths = int(whole) * 100 + int((fraction + "00")[:2])
            value = hundredths * rates[tx["currency"]] // 1000000
            if tx["type"] == "debit":
                value = -value
            counted += 1
            total += value
            channel = tx["meta"]["channel"]
            if channel not in channels:
                channels[channel] = [0, 0]
            channels[channel][0] += 1
            channels[channel][1] += value
            accounts[tx["account"]] += value
    lines = [f"counted {counted}", f"net {total}"]
    lines += [f"channel {key} {values[0]} {values[1]}" for key, values in sorted(channels.items())]
    lines += [f"account {key} {value}" for key, value in sorted(accounts.items(), key=lambda item: (-item[1], item[0]))[:10]]
    return "\n".join(lines) + "\n"


def logscan(path, workers=1):
    statuses = collections.Counter()
    paths = collections.defaultdict(list)
    lines = malformed = 0
    with open(path, encoding="ascii") as f:
        for line in f:
            lines += 1
            match = LOG_PATTERN.fullmatch(line.removesuffix("\n"))
            if match is None:
                malformed += 1
                continue
            _, path_text, _, status, whole, tenth = match.groups()
            statuses[status[0] + "xx"] += 1
            template = "/".join("{id}" if part.isdigit() else part for part in path_text.split("/"))
            paths[template].append(int(whole) * 10 + int(tenth))
    result = [f"lines {lines}", f"malformed {malformed}"]
    result += [f"status {status} {count}" for status, count in sorted(statuses.items())]
    for template in sorted(paths, key=lambda key: (-len(paths[key]), key))[:10]:
        values = sorted(paths[template])
        n = len(values)
        p50, p95, maximum = (values[(percent * n + 99) // 100 - 1] for percent in (50, 95, 100))
        result.append(f"path {template} {n} {p50//10}.{p50%10} {p95//10}.{p95%10} {maximum//10}.{maximum%10}")
    return "\n".join(result) + "\n"


def routes(path, workers=1):
    with open(path, encoding="ascii") as f:
        n, m, q = map(int, next(f).split())
        graph = [[] for _ in range(n)]
        for _ in range(m):
            u, v, weight = map(int, next(f).split())
            graph[u].append((v, weight))
            graph[v].append((u, weight))
        sources = list(map(int, next(f).split()))
    result = []
    for source in sources:
        distance = [None] * n
        distance[source] = 0
        queue = [(0, source)]
        while queue:
            cost, u = heapq.heappop(queue)
            if cost != distance[u]:
                continue
            for v, weight in graph[u]:
                candidate = cost + weight
                if distance[v] is None or candidate < distance[v]:
                    distance[v] = candidate
                    heapq.heappush(queue, (candidate, v))
        reachable = [d for d in distance if d is not None]
        far = max(reachable)
        result.append(f"{source} {len(reachable)} {sum(reachable)} {far} {distance.index(far)}")
    return "\n".join(result) + "\n"


def align(path, workers=1):
    result = []
    with open(path, encoding="ascii") as f:
        alphabet = next(f).strip()
        index = {letter: i for i, letter in enumerate(alphabet)}
        ins, delete = [list(map(int, next(f).split())) for _ in range(2)]
        sub = [list(map(int, next(f).split())) for _ in alphabet]
        pairs = int(next(f))
        for _ in range(pairs):
            s_text, t_text = next(f).split()
            s, t = [index[c] for c in s_text], [index[c] for c in t_text]
            previous = [0]
            for letter in t:
                previous.append(previous[-1] + ins[letter])
            for left in s:
                current = [previous[0] + delete[left]]
                for j, right in enumerate(t, 1):
                    current.append(min(previous[j] + delete[left], current[j - 1] + ins[right],
                                       previous[j - 1] + sub[left][right]))
                previous = current
            result.append(previous[-1])
    return "\n".join(map(str, result)) + f"\ntotal {sum(result)}\n"


def heat(path, workers=1):
    with open(path, encoding="ascii") as f:
        h, w, steps = map(int, next(f).split())
        grid = [next(f).strip() for _ in range(h)]
    values = [[int(c) * 1000 if c.isdigit() else 0 for c in row] for row in grid]
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == "."]
    for _ in range(steps):
        new = [row.copy() for row in values]
        for r, c in cells:
            old = values[r][c]
            up = values[r - 1][c] if r and grid[r - 1][c] != "#" else old
            down = values[r + 1][c] if r + 1 < h and grid[r + 1][c] != "#" else old
            left = values[r][c - 1] if c and grid[r][c - 1] != "#" else old
            right = values[r][c + 1] if c + 1 < w and grid[r][c + 1] != "#" else old
            new[r][c] = (4 * old + up + down + left + right) // 8
        values = new
    maximum = max(values[r][c] for r, c in cells)
    r_max, c_max = next((r, c) for r, c in cells if values[r][c] == maximum)
    total = sum(values[r][c] for r, c in cells)
    checksum = sum(values[r][c] * (r * w + c + 1) for r, c in cells)
    return f"sum {total}\nmax {maximum} {r_max} {c_max}\nchecksum {checksum}\n"


def one_walk(args):
    j, length, bound, seed = args
    state = (seed + j) & MASK
    x = y = bumps = returns = 0
    for _ in range(length):
        state = (state + 0x9E3779B97F4A7C15) & MASK
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        direction = (z ^ (z >> 31)) >> 62
        nx, ny = x, y
        if direction == 0:
            nx += 1
        elif direction == 1:
            nx -= 1
        elif direction == 2:
            ny += 1
        else:
            ny -= 1
        if abs(nx) > bound or abs(ny) > bound:
            bumps += 1
        else:
            x, y = nx, ny
            if x == y == 0:
                returns += 1
    return x * x + y * y, bumps, returns, j, abs(x) + abs(y)


def walkers(path, workers=1):
    j, length, bound, seed = map(int, Path(path).read_text().split())
    jobs = [(i, length, bound, seed) for i in range(j)]
    if workers > 1:
        with multiprocessing.Pool(workers) as pool:
            result = pool.map(one_walk, jobs)
    else:
        result = list(map(one_walk, jobs))
    winner = min(result, key=lambda row: (-row[4], row[3]))
    return (f"spread {sum(row[0] for row in result)}\nbumps {sum(row[1] for row in result)}\n"
            f"returns {sum(row[2] for row in result)}\nfarthest {winner[3]} {winner[4]}\n")


SOLVERS = {name: globals()[name] for name in ("springs", "wordpairs", "ledger", "logscan", "routes", "align", "heat", "walkers")}


def solve(task, path, workers=1):
    return SOLVERS[task](path, workers)


if __name__ == "__main__":
    output = solve('routes', sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    print(output, end="")
