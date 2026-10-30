"""Deterministic input generation. Run: python -m bench.generate [--tasks ...]."""

import argparse
import json
import math
import random
import string
from pathlib import Path

import numpy as np

from bench import config as C
from bench.common import read_json, sha256, write_json


def springs(rng, p, out):
    n = p["N"]
    p["P"] = n
    out.write(f'{n} {p["S"]} {p["dt"]} {n}\n')
    for i in range(n):
        x = i + rng.uniform(-0.01, 0.01)
        v, m, k = rng.uniform(-0.03, 0.03), rng.uniform(1, 3), rng.uniform(0.3, 2)
        if i == n // 2:
            v, m, k = 2.0, 50.0, 0.02
        rest = rng.uniform(.98, 1.02)
        rest = p.get("rest_length", rest)
        out.write(f'{x:.15g} {v:.15g} {m:.15g} {k:.15g} {rest:.15g} 0.0001\n')


def vocabulary(rng, count):
    words = set()
    while len(words) < count:
        length = rng.choices(range(1, 15), weights=[3, 8, 22, 30, 18, 8, 4, 2, 1, 1, 1, 1, 1, 1])[0]
        word = "".join(rng.choices(string.ascii_lowercase, k=length))
        if not word.startswith("zz"):
            words.add(word)
    return sorted(words)  # Never depend on Python's randomised set iteration order.


def wordpairs(rng, p, out):
    words = vocabulary(rng, p["vocabulary"])
    remaining = p["words"]
    # Reserved, sentence-isolated pairs guarantee ties within the top 20 and at 20/21.
    unit = max(1, remaining // 300)
    buffer = ""
    width = rng.randint(60, 80)

    def emit(text):
        nonlocal buffer, width
        buffer += text
        while len(buffer) > 80:
            # A newline may split a sentence, never a word. Keep punctuation intact.
            candidates = [i for i in range(60, 81)
                          if not buffer[i - 1].isalpha() or not buffer[i].isalpha()]
            split = min(candidates, key=lambda i: (abs(i - width), i))
            out.write(buffer[:split] + "\n")
            buffer = buffer[split:].lstrip(" ")
            width = rng.randint(60, 80)

    for i in range(21):
        count = unit + (3 - i // 6 if i < 18 else 0)
        # Tiny inputs need at least 21 distinct anchored pairs as well as punctuation cases.
        if p["words"] < 1000:
            count = 2 if i < 18 else 1
        count = min(count, remaining // 2)
        if not count:
            break
        a, b = "zz" + chr(97 + i) + "a", "zz" + chr(97 + i) + "b"
        emit((f"{a} {b}. " * count))
        remaining -= 2 * count
    # Every special construct contributes two words. Empty sentences contribute none.
    specials = ["don't", "abc123def", "red,fox", "RED;FOX", '"red" (fox)',
                "red-fox", "MiXeD UPPER", "Title lower"]
    for piece in specials * (3 if p["words"] >= 1000 else 1):
        if remaining >= 2:
            emit(piece + ". ?! ... !! ")
            remaining -= 2
    weights = np.arange(1, len(words) + 1, dtype=float) ** -0.85
    weights /= weights.sum()
    nrng = np.random.default_rng(rng.getrandbits(64))
    separators = [" ", ", ", "; ", "-", "'", "123", ' (', '") ']
    while remaining:
        size = min(remaining, 40_000)
        indices = nrng.choice(len(words), size=size, p=weights)
        for index in indices:
            word = words[int(index)]
            case = rng.randrange(8)
            if case == 0:
                word = word.upper()
            elif case == 1:
                word = word.title()
            elif case == 2:
                word = "".join(c.upper() if j % 2 else c for j, c in enumerate(word))
            remaining -= 1
            ending = ". " if remaining and rng.randrange(12) == 0 else rng.choice(separators)
            emit(word + ending)
    out.write(buffer.rstrip() + "\n")  # The final sentence deliberately has no terminator.


def ledger(rng, p, out):
    rates = dict(list({"USD": 1000000, "EUR": 1083250, "JPY": 6612, "GBP": 1295000,
                      "CAD": 724500, "AUD": 658000, "CHF": 1144000, "INR": 11910,
                      "SEK": 94300, "NZD": 604000}.items())[:p["currencies"]])
    out.write(json.dumps({"rates": rates}) + "\n")
    currencies = list(rates)
    channels = ["branch", "mobile", "web", "atm", "api", "phone", "wire", "batch", "card", "desk", "agent", "mail"][:p["channels"]]
    notes = ['rent "October"', "folder \\ archive", "path /receipt", "line\nnext", "caf\u00e9", "na\u00efve raw UTF-8", "emoji \U0001f600"]
    for i in range(p["transactions"]):
        # Power-law account activity with a long tail of quiet accounts.
        account = min(p["accounts"] - 1, int(rng.random() ** 3 * p["accounts"]))
        kind = rng.choices(["credit", "debit", "refund"], [48, 45, 4])[0]
        tags = [rng.choice(["payroll", "rent", "testing", "Test"])] if rng.random() < .1 else []
        cents = rng.randrange(0, 400000)
        amount = [str(cents // 100), f"{cents // 100}.{cents % 10}", f"{cents // 100}.{cents % 100:02d}"][i % 3]
        if i % 53 == 0:
            amount = "0"
        transaction = dict(id=i, account=f"AC-{account:05d}", type=kind, amount=amount,
                           currency=rng.choice(currencies), tags=tags,
                           meta=dict(channel=channels[i % len(channels)], ts="2026-10-30T14:22:05Z", note=notes[i % len(notes)]))
        if i < 12 and p["transactions"] < 100:
            transaction.update(account=f"AC-{i:05d}", amount="1", currency="USD", type="credit", tags=[])
        elif p["transactions"] < 100:
            transaction["amount"] = "0"  # Preserve equal account nets in the tiny sample.
        # Guaranteed skip/non-skip examples, including escaped notes, repeated in larger inputs.
        if i % 100 in (20, 24, 25):
            transaction["type"] = "void"
        if i % 100 in (21, 26):
            transaction["tags"] = ["test"]
        if i % 100 in (22, 23):
            transaction["tags"] = ["testing" if i % 100 == 22 else "Test"]
        nested = {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, None, True]}
        transaction["extra"] = nested
        transaction["meta"]["extra"] = nested
        items = list(transaction.items())
        rng.shuffle(items)
        transaction = dict(items)
        text = json.dumps(transaction, ensure_ascii=(i % 7 != 5),
                          separators=[(",", ":"), (", ", ": "), (",  ", " :  ")][i % 3])
        if i % 7 == 2:
            text = text.replace("/receipt", r"\/receipt")
        out.write(text + "\n")


def logscan(rng, p, out):
    # Oversample malformed forms in the small sample so each of the 13 forms occurs >=3 times.
    period = 5 if p["lines"] <= 100 else max(1, p["lines"] // max(C.LOG_MIN_MALFORMED, p["lines"] // 100))
    p["malformed_period"] = period
    templates = ["/api/v2/items/{id}", "/users/{id}/orders/", "/x//{id}/12a", "/health", "/{id}/{id}/{id}"]
    templates += [f"/service/{i}a/v2/" + "/".join(["{id}"] * (i % 4)) + ("/" if i % 7 == 0 else "")
                  for i in range(p["templates"] - len(templates))]
    weights = [1 / (i + 1) ** .9 for i in range(len(templates))]
    for i in range(p["lines"]):
        template = templates[(i // 2) % len(templates)] if p["lines"] <= 100 else rng.choices(templates, weights)[0]
        path = template
        while "{id}" in path:
            path = path.replace("{id}", str(rng.randrange(100000)), 1)
        if rng.random() < .3:
            path += "?ref=abc&item=12"
        status = rng.choices([101, 200, 201, 204, 301, 404, 500, 503], [1, 62, 9, 9, 7, 7, 4, 1])[0]
        latency = 7 if i % 17 == 0 else min(999999, int(rng.lognormvariate(5, 1.5)))
        line = f'2026-10-30T14:22:05.123Z web-17 GET {path} {status} 1834B {latency // 10}.{latency % 10}ms "Mozilla/5.0 (X11; Linux x86_64)"'
        # A complete rotation of malformed forms; avoid accidentally valid mutations.
        if i % period == 0:
            form = (i // period) % 13
            line = [line[:35], "    at handler (server.js:1)", "Traceback:", line.replace("GET", "get"),
                    line.replace(f"{latency // 10}.{latency % 10}ms", "45ms"),
                    line.replace(f"{latency // 10}.{latency % 10}ms", "45.25ms"), line[:-1], line + " extra",
                    line.replace("Z web", "Z\tweb"), line.replace(f" {status} ", " 2000 "),
                    line.replace("2026-10-30T", "2026/10/30T"), line.replace("web-17", "web"), ""][form]
        out.write(line + "\n")


def routes(rng, p, out):
    n, m = p["N"], p["M"]
    if n < 12:
        raise ValueError("Routes requires N >= 12 for its six sources and island cases")
    edges = []
    if n == 12:
        edges = [(0, 1, 5), (0, 2, 5), (3, 4, 2), (4, 5, 2), (6, 7, 1), (8, 9, 3), (0, 0, 1)]
        while len(edges) < m:
            u, v, w = edges[rng.randrange(6)]
            edges.append((u, v, w + rng.randrange(0, 9)))
        sources = [0, 3, 6, 8, 10, 11]
    else:
        island_start = n - max(6, n // 100)
        width = max(2, math.isqrt(island_start))
        for u in range(island_start):
            for v in (u + 1 if (u + 1) % width else island_start, u + width):
                if v < island_start and rng.random() > .12:
                    edges.append((u, v, rng.randint(1, 65)))
        for u in range(island_start, n - 2):
            if u + 1 < n - 2:
                edges.append((u, u + 1, rng.randint(1, 30)))
        while len(edges) < m:
            u = rng.randrange(island_start)
            draw = rng.random()
            v = u if draw < .02 else (min(island_start - 1, u + 1) if draw < .2 else rng.randrange(island_start))
            edges.append((u, v, rng.randint(1, 1000) if draw >= .2 else rng.randint(1, 50)))
        sources = [0, island_start // 3, island_start // 2, island_start, n - 2, n - 1]
    out.write(f'{n} {m} {p["Q"]}\n')
    for u, v, w in edges[:m]:
        out.write(f"{u} {v} {w}\n")
    out.write(" ".join(map(str, sources)) + "\n")


def align(rng, p, out):
    alphabet = string.ascii_uppercase[:p["alphabet"]]
    a = len(alphabet)
    ins, delete = [rng.randrange(1, 500) for _ in alphabet], [rng.randrange(1, 500) for _ in alphabet]
    ins[0], delete[1] = 0, 0
    sub = [[0 if i == j else rng.randrange(1001) for j in range(a)] for i in range(a)]
    sub[0][1] = 1000  # Deletion plus insertion is cheaper.
    sub[2][3] = 0
    out.write(alphabet + "\n")
    for row in (ins, delete, *sub):
        out.write(" ".join(map(str, row)) + "\n")
    out.write(f'{p["P"]}\n')
    for i in range(p["P"]):
        low, high = p["min_length"], p["max_length"]
        n = int(rng.triangular(low, high, min(high, low + 150)))
        m = int(rng.triangular(low, high, min(high, low + 150)))
        if high <= 12:
            n, m = [(1, 1), (1, 12), (12, 1), (5, 5), (8, 9), (3, 10)][i % 6]
        elif i % 30 == 0:
            n, m = low, high
        s, t = "".join(rng.choices(alphabet, k=n)), "".join(rng.choices(alphabet, k=m))
        if i % 30 == 3:
            t = s
        out.write(f"{s} {t}\n")


def heat(rng, p, out):
    h, w = p["H"], p["W"]
    if min(h, w) < 3:
        raise ValueError("Heat floor plan requires H,W >= 3")
    grid = [["."] * w for _ in range(h)]
    for r in range(5, h, 9):
        for c in range(w):
            grid[r][c] = "#" if c % 11 not in (2, 3) else "."
    for c in range(6, w, 11):
        for r in range(h):
            grid[r][c] = "#" if r % 9 not in (1, 2) else "."
    for _ in range(max(3, h * w // 90)):
        grid[rng.randrange(h)][rng.randrange(w)] = str(rng.randint(1, 9))
    grid[0][0], grid[0][1], grid[0][2] = "#", "9", "."
    grid[-1][-1], grid[-1][-2], grid[-1][-3] = "#", "1", "."
    if h == 7 and w == 9:
        # Two symmetric open cells have the same maximum, plus an insulated room.
        grid = [list(row) for row in ["#9.9.9#.#", "#####.#..", "..1..#...", ".....#...", "##.###...", ".....#...", ".#2..#..3"]]
    out.write(f'{h} {w} {p["S"]}\n')
    out.write("\n".join("".join(row) for row in grid) + "\n")


def walkers(rng, p, out):
    seed = (1 << 64) - rng.randint(1, max(2, p["J"] // 2))
    out.write(f'{p["J"]} {p["L"]} {p["B"]} {seed}\n')
    p["SEED"] = seed


GENERATORS = {task: globals()[task] for task in C.TASKS}


def generate(task, scale, seed, path, *, parameters=None):
    """Write one input; return the actual parameters. Optional overrides support tiny fixtures."""
    path = Path(path)
    p = C.parameters(task, scale, path.stem) if parameters is None else parameters.copy()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as out:
        GENERATORS[task](random.Random(seed), p, out)
    return p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", nargs="+", choices=C.TASKS, default=C.TASKS)
    parser.add_argument("--replace", action="store_true", help="Explicitly replace existing frozen inputs")
    args = parser.parse_args()
    manifest_path = C.DATA / "inputs_manifest.json"
    old = read_json(manifest_path) if manifest_path.exists() else {"inputs": []}
    entries = {(row["task"], row["name"]): row for row in old["inputs"]}
    for task in args.tasks:
        for name, (scale, seed) in C.input_sets(task).items():
            path = C.input_path(task, name)
            key = task, name
            if path.exists() and key in entries and not args.replace:
                if sha256(path) != entries[key]["sha256"]:
                    raise ValueError(f"Frozen input changed: {path}")
                print(task, name, "cached", flush=True)
                continue
            p = generate(task, scale, seed, path)
            entries[key] = dict(task=task, name=name, scale=scale, seed=seed, parameters=p,
                                bytes=path.stat().st_size, sha256=sha256(path), generator_version=C.GENERATOR_VERSION)
            write_json(manifest_path, dict(generator_version=C.GENERATOR_VERSION, inputs=list(entries.values())))
            print(task, name, path.stat().st_size, p, flush=True)


if __name__ == "__main__":
    main()
