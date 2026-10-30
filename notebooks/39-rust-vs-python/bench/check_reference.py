"""Independent algorithms. Every saved input is checked, with a per-input deadline."""

import collections
import functools
import json
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np


def springs(path):
    with open(path) as f:
        n, steps, dt, circumference = next(f).split()
        n, steps, dt, circumference = int(n), int(steps), float(dt), float(circumference)
        x, v, mass, k, rest, damping = np.loadtxt(f, ndmin=2).T.copy()
    for _ in range(steps):
        next_x = np.roll(x, -1)
        next_x[-1] += circumference
        force = k * ((next_x - x) - rest)
        v = v + dt * (((force - np.roll(force, 1)) - damping * v) / mass)
        x = x + dt * v
    next_x = np.roll(x, -1)
    next_x[-1] += circumference
    stretch = (next_x - x) - rest
    kinetic = np.sum(((.5 * mass) * v) * v)
    potential = np.sum(((.5 * k) * stretch) * stretch)
    return f"kinetic {kinetic:.16e}\npotential {potential:.16e}\nposition {x.sum():.16e}\nfastest {np.argmax(np.abs(v))}\n"


def wordpairs(path):
    # Byte state machine, no regular expressions or sentence splitting.
    counts = collections.defaultdict(int)
    words = pairs = 0
    previous, word = None, bytearray()
    with open(path, "rb") as f:
        while block := f.read(1024 * 1024):
            for byte in block:
                if 65 <= byte <= 90 or 97 <= byte <= 122:
                    word.append(byte + 32 if byte <= 90 else byte)
                    continue
                if word:
                    token = bytes(word)
                    words += 1
                    if previous is not None:
                        counts[previous, token] += 1
                        pairs += 1
                    previous, word = token, bytearray()
                if byte in (33, 46, 63):
                    previous = None
    if word:
        token = bytes(word)
        words += 1
        if previous is not None:
            counts[previous, token] += 1
            pairs += 1
    ranked = sorted((-count, a, b) for (a, b), count in counts.items())[:20]
    rows = [f"words {words}", f"pairs {pairs}", f"distinct {len(counts)}"]
    rows += [f"{-count} {a.decode()} {b.decode()}" for count, a, b in ranked]
    return "\n".join(rows) + "\n"


def ledger(path):
    # Decimal conversion and per-channel/per-account lists, then aggregation.
    accounts, channels = collections.defaultdict(list), collections.defaultdict(list)
    with open(path, encoding="utf-8") as f:
        rates = json.loads(next(f))["rates"]
        for line in f:
            tx = json.loads(line)
            if tx["type"] != "void" and all(tag != "test" for tag in tx["tags"]):
                cents = int(Decimal(tx["amount"]) * 100)
                usd = (cents * rates[tx["currency"]]) // 1000000
                signed = usd * (-1 if tx["type"] == "debit" else 1)
                accounts[tx["account"]].append(signed)
                channels[tx["meta"]["channel"]].append(signed)
    rows = [f"counted {sum(map(len, channels.values()))}", f"net {sum(map(sum, accounts.values()))}"]
    rows += [f"channel {key} {len(channels[key])} {sum(channels[key])}" for key in sorted(channels)]
    ranked = sorted(((-sum(values), key) for key, values in accounts.items()))[:10]
    rows += [f"account {key} {-negative}" for negative, key in ranked]
    return "\n".join(rows) + "\n"


def ascii_digits(text):
    return bool(text) and all("0" <= c <= "9" for c in text)


def parse_log(line):
    fields = line.split(" ", 7)
    if len(fields) != 8 or any(not value for value in fields):
        return None
    stamp, host, method, target, status, size, latency, agent = fields
    model = "0000-00-00T00:00:00.000Z"
    if len(stamp) != len(model) or any(not ("0" <= a <= "9") if b == "0" else a != b for a, b in zip(stamp, model)):
        return None
    host_name, dash, host_number = host.rpartition("-")
    if not dash or not host_name or not all("a" <= c <= "z" for c in host_name) or not ascii_digits(host_number):
        return None
    if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
        return None
    path = target.partition("?")[0]
    if not path.startswith("/") or not all(c.isascii() and (c.isalnum() or c in "_/-") for c in path):
        return None
    if len(status) != 3 or not ascii_digits(status) or not size.endswith("B") or not ascii_digits(size[:-1]):
        return None
    if not latency.endswith("ms"):
        return None
    whole, dot, tenth = latency[:-2].partition(".")
    if not dot or not ascii_digits(whole) or len(tenth) != 1 or not ascii_digits(tenth):
        return None
    if len(agent) < 2 or agent[0] != '"' or agent[-1] != '"' or '"' in agent[1:-1]:
        return None
    template = "/".join("{id}" if ascii_digits(segment) else segment for segment in path.split("/"))
    return status[0] + "xx", template, int(whole) * 10 + int(tenth)


def logscan(path):
    statuses, paths = collections.Counter(), collections.defaultdict(collections.Counter)
    lines = bad = 0
    with open(path, encoding="ascii") as f:
        for line in f:
            lines += 1
            parsed = parse_log(line.removesuffix("\n"))
            if parsed is None:
                bad += 1
            else:
                status, template, latency = parsed
                statuses[status] += 1
                paths[template][latency] += 1
    rows = [f"lines {lines}", f"malformed {bad}"]
    rows += [f"status {status} {count}" for status, count in sorted(statuses.items())]
    for template in sorted(paths, key=lambda key: (-sum(paths[key].values()), key))[:10]:
        frequencies = paths[template]
        n = sum(frequencies.values())
        quantiles = []
        for percentile in (50, 95, 100):
            rank, running = (percentile * n + 99) // 100, 0
            for value, count in sorted(frequencies.items()):
                running += count
                if running >= rank:
                    quantiles.append(f"{value//10}.{value%10}")
                    break
        rows.append(f"path {template} {n} " + " ".join(quantiles))
    return "\n".join(rows) + "\n"


def routes(path):
    # Dial's circular buckets, independent of heap-based Dijkstra.
    with open(path) as f:
        n, m, q = map(int, next(f).split())
        graph = [dict() for _ in range(n)]
        for _ in range(m):
            a, b, w = map(int, next(f).split())
            graph[a][b] = min(graph[a].get(b, 1001), w)
            graph[b][a] = min(graph[b].get(a, 1001), w)
        sources = list(map(int, next(f).split()))
    result = []
    for source in sources:
        buckets = [collections.deque() for _ in range(1001)]
        buckets[0].append((source, 0))
        distances = {source: 0}
        pending, cursor = 1, 0
        while pending:
            while not buckets[cursor % 1001]:
                cursor += 1
            u, d = buckets[cursor % 1001].popleft()
            pending -= 1
            if distances[u] != d:
                continue
            for v, weight in graph[u].items():
                cost = d + weight
                if cost < distances.get(v, 1 << 63):
                    distances[v] = cost
                    buckets[cost % 1001].append((v, cost))
                    pending += 1
        far = max(distances.values())
        node = min(v for v, d in distances.items() if d == far)
        result.append(f"{source} {len(distances)} {sum(distances.values())} {far} {node}")
    return "\n".join(result) + "\n"


def align(path):
    rows = []
    with open(path) as f:
        alphabet = next(f).strip()
        index = {c: i for i, c in enumerate(alphabet)}
        ins, delete = [np.array(list(map(int, next(f).split())), dtype=np.int64) for _ in range(2)]
        sub = np.array([list(map(int, next(f).split())) for _ in alphabet], dtype=np.int64)
        for _ in range(int(next(f))):
            left, right = next(f).split()
            s, t = np.array([index[c] for c in left]), np.array([index[c] for c in right])
            n, m = len(s), len(t)
            if n + m < 120:
                @functools.cache
                def cost(i, j):
                    if i == 0:
                        return sum(int(ins[c]) for c in t[:j])
                    if j == 0:
                        return sum(int(delete[c]) for c in s[:i])
                    return min(cost(i-1, j) + int(delete[s[i-1]]), cost(i, j-1) + int(ins[t[j-1]]),
                               cost(i-1, j-1) + int(sub[s[i-1], t[j-1]]))
                value = cost(n, m)
            else:
                table = np.zeros((n + 1, m + 1), dtype=np.int64)
                table[1:, 0], table[0, 1:] = np.cumsum(delete[s]), np.cumsum(ins[t])
                for diagonal in range(2, n + m + 1):
                    i = np.arange(max(1, diagonal-m), min(n, diagonal-1) + 1)
                    j = diagonal - i
                    table[i, j] = np.minimum(np.minimum(table[i-1, j] + delete[s[i-1]],
                                                       table[i, j-1] + ins[t[j-1]]),
                                             table[i-1, j-1] + sub[s[i-1], t[j-1]])
                value = int(table[n, m])
            rows.append(value)
    return "\n".join(map(str, rows)) + f"\ntotal {sum(rows)}\n"


def heat(path):
    with open(path) as f:
        h, w, steps = map(int, next(f).split())
        chars = np.array([list(next(f).strip()) for _ in range(h)])
    walls, open_cells = chars == "#", chars == "."
    values = np.zeros((h, w), dtype=np.int64)
    for digit in "123456789":
        values[chars == digit] = int(digit) * 1000
    for _ in range(steps):
        padded = np.pad(values, 1, mode="edge")
        padded_walls = np.pad(walls, 1, constant_values=True)
        new = 4 * values
        for dr, dc in ((0, 1), (2, 1), (1, 0), (1, 2)):
            new += np.where(padded_walls[dr:dr+h, dc:dc+w], values, padded[dr:dr+h, dc:dc+w])
        values[open_cells] = (new // 8)[open_cells]
    flat = np.where(open_cells, values, -1).ravel()
    winner = int(flat.argmax())
    weights = np.arange(1, h*w + 1).reshape(h, w)
    return (f"sum {values[open_cells].sum()}\nmax {flat[winner]} {winner//w} {winner%w}\n"
            f"checksum {(values * weights)[open_cells].sum()}\n")


def walkers(path):
    j, length, bound, seed = map(int, Path(path).read_text().split())
    state = np.array([(seed + i) % (1 << 64) for i in range(j)], dtype=np.uint64)
    x, y = np.zeros(j, dtype=np.int64), np.zeros(j, dtype=np.int64)
    bumps = returns = 0
    with np.errstate(over="ignore"):
        for _ in range(length):
            state += np.uint64(0x9E3779B97F4A7C15)
            z = (state ^ (state >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
            z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
            d = (z ^ (z >> np.uint64(31))) >> np.uint64(62)
            nx, ny = x + (d == 0) - (d == 1), y + (d == 2) - (d == 3)
            valid = (np.abs(nx) <= bound) & (np.abs(ny) <= bound)
            bumps += int((~valid).sum())
            x[valid], y[valid] = nx[valid], ny[valid]
            returns += int((valid & (x == 0) & (y == 0)).sum())
    distance = np.abs(x) + np.abs(y)
    winner = int(distance.argmax())
    return (f"spread {(x*x + y*y).sum()}\nbumps {bumps}\nreturns {returns}\n"
            f"farthest {winner} {distance[winner]}\n")


def main():
    import argparse
    from bench import config as C
    from bench.common import append_csv, manifest
    from bench.compare import compare
    from bench.winjob import run
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", choices=C.TASKS, default=C.TASKS)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    csv_path = C.DATA / "reference_agreements.csv"
    failures = []
    print("task       input       status       seconds", flush=True)
    for entry in manifest():
        task, name = entry["task"], entry["name"]
        if task not in args.tasks:
            continue
        scratch = C.RUNS / "check_reference" / task / name
        out, err = scratch / "stdout.txt", scratch / "stderr.txt"
        command = [str(C.PYTHON), "-X", "utf8", "-m", "bench.check_reference", "_solve", task, str(C.input_path(task, name))]
        result = run(command, C.ROOT, out, err, C.CHECK_TIMEOUT)
        expected = (C.DATA / "expected" / task / f"{name}.out").read_text()
        if result["timed_out"] or result["exit_code"]:
            status, detail = "timeout" if result["timed_out"] else "crashed", err.read_text()[:500]
        else:
            status, detail = compare(task, out.read_text(), expected)
        append_csv(csv_path, dict(task=task, name=name, status=status, wall_seconds=result["wall_seconds"], detail=detail),
                   ["task", "name", "status", "wall_seconds", "detail"])
        print(f'{task:10} {name:11} {status:12} {result["wall_seconds"]:.3f}', flush=True)
        if status != "correct":
            failures.append((task, name, status, detail))
    if failures:
        raise SystemExit(str(failures))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "_solve":
        print(globals()[sys.argv[2]](sys.argv[3]), end="")
    else:
        main()
