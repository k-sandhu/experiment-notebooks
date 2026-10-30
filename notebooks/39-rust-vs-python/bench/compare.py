"""Strict output grammars; parse failures are distinct from incorrect answers."""

import math
import re

class Unreadable(ValueError):
    pass


def normalise(text):
    text = text.replace("\r\n", "\n")
    lines = [line.rstrip(" ") for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def integer(text):
    if not re.fullmatch(r"-?[0-9]+", text):
        raise Unreadable(f"expected integer, got {text[:40]!r}")
    return int(text)


def parse(task, text):
    """Return rows of typed fields, retaining keywords for useful mismatch messages."""
    lines = normalise(text)
    rows = []

    def row(i, keyword, types):
        if i >= len(lines):
            raise Unreadable(f"line {i + 1}: missing {keyword or 'data'}")
        fields = lines[i].split(" ")
        if any(not value for value in fields):
            raise Unreadable(f"line {i + 1}: fields must use single spaces")
        if keyword:
            if fields.pop(0) != keyword:
                raise Unreadable(f"line {i + 1}: expected {keyword}")
        if len(fields) != len(types):
            raise Unreadable(f"line {i + 1}: expected {len(types)} fields after {keyword or 'start'}")
        values = [keyword] if keyword else []
        for value, kind in zip(fields, types):
            try:
                if kind == "int":
                    parsed = integer(value)
                elif kind == "float":
                    parsed = float(value)
                    if not math.isfinite(parsed):
                        raise ValueError("non-finite float")
                else:
                    if not re.fullmatch(kind, value, flags=re.ASCII):
                        raise ValueError(f"invalid field {value[:40]!r}")
                    parsed = value
            except (ValueError, OverflowError) as exc:
                raise Unreadable(f"line {i + 1}, field {len(values) + 1}: {exc}") from exc
            values.append(parsed)
        rows.append(tuple(values))

    def exact_count(n):
        if len(lines) != n:
            raise Unreadable(f"expected {n} lines, got {len(lines)}")

    if task == "springs":
        exact_count(4)
        for i, key in enumerate(("kinetic", "potential", "position", "fastest")):
            row(i, key, ["int" if key == "fastest" else "float"])
    elif task == "heat":
        exact_count(3)
        row(0, "sum", ["int"])
        row(1, "max", ["int"] * 3)
        row(2, "checksum", ["int"])
    elif task == "walkers":
        exact_count(4)
        for i, key in enumerate(("spread", "bumps", "returns", "farthest")):
            row(i, key, ["int"] * (2 if i == 3 else 1))
    elif task == "routes":
        if not lines:
            raise Unreadable("expected source rows")
        for i in range(len(lines)):
            row(i, None, ["int"] * 5)
    elif task == "align":
        if len(lines) < 2:
            raise Unreadable("expected pair costs and total")
        for i in range(len(lines) - 1):
            row(i, None, ["int"])
        row(len(lines) - 1, "total", ["int"])
    elif task == "wordpairs":
        if not 3 <= len(lines) <= 23:
            raise Unreadable("expected 3 to 23 lines")
        for i, key in enumerate(("words", "pairs", "distinct")):
            row(i, key, ["int"])
        for i in range(3, len(lines)):
            row(i, None, ["int", "[a-z]+", "[a-z]+"])
        expected_lines = 3 + min(20, max(0, rows[2][1]))
        exact_count(expected_lines)
    elif task in ("ledger", "logscan"):
        first, second = ("counted", "net") if task == "ledger" else ("lines", "malformed")
        row(0, first, ["int"])
        row(1, second, ["int"])
        phase = 0
        count_last = 0
        for i in range(2, len(lines)):
            key = lines[i].split(" ")[0]
            keys = ("channel", "account") if task == "ledger" else ("status", "path")
            if key not in keys or (phase and key == keys[0]):
                raise Unreadable(f"line {i + 1}: invalid row keyword/order")
            if key == keys[1]:
                phase = 1
                count_last += 1
            if key == "channel":
                row(i, key, [r"[!-~]+", "int", "int"])
            elif key == "account":
                row(i, key, [r"[!-~]+", "int"])
            elif key == "status":
                row(i, key, [r"[0-9]xx", "int"])
            else:
                row(i, key, [r"/[A-Za-z0-9_/{}/-]*", "int"] + [r"[0-9]+\.[0-9]"] * 3)
        if count_last > 10:
            raise Unreadable("more than 10 ranked rows")
    else:
        raise ValueError(task)
    return rows


def compare(task, got_text, expected_text):
    expected = parse(task, expected_text)
    try:
        got = parse(task, got_text)
    except Unreadable as exc:
        return "unreadable", str(exc)
    for i, (actual, wanted) in enumerate(zip(got, expected), 1):
        if actual[:1] != wanted[:1] and isinstance(wanted[0], str):
            return "wrong", f"line {i}: got a {actual[0]!r} row, expected a {wanted[0]!r} row"
        for j, (a, b) in enumerate(zip(actual, wanted), 1):
            equal = abs(a - b) <= 1e-9 * max(abs(a), abs(b)) if task == "springs" and isinstance(b, float) else a == b
            if not equal:
                return "wrong", f"line {i}, field {j}: got {a!r}, expected {b!r}"
    # A well-formed output with missing or extra rows (a channel, a status class, a source) is a wrong answer.
    if len(got) != len(expected):
        return "wrong", f"expected {len(expected)} rows, got {len(got)}"
    return "correct", ""
