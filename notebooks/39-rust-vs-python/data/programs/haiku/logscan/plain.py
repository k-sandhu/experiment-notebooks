"""Web access log summary (standard library only).

Reads the file as bytes, one line at a time, and validates each line with a
single compiled regex. Usage: python plain.py INPUT_PATH
"""

import re
import sys

# Groups: 1 = path without query, 2 = status first digit, 3 = latency integer
# part, 4 = latency tenths digit. Names and fields not needed are non-capturing.
LINE = re.compile(
    rb'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z'
    rb' [a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(?:\?[^ ]*)?'
    rb' ([0-9])[0-9]{2} [0-9]+B ([0-9]+)\.([0-9])ms "[^"]*"'
)


def template(path):
    """Replaces every all-digit, non-empty segment with {id}."""
    return b"/".join([b"{id}" if seg.isdigit() else seg for seg in path.split(b"/")])


def tenths_text(value):
    return f"{value // 10}.{value % 10}"


def main():
    total = 0
    malformed = 0
    status = [0] * 10
    latencies = {}  # template -> list of latencies in tenths of a ms

    with open(sys.argv[1], "rb") as f:
        for raw in f:
            total += 1
            m = LINE.fullmatch(raw.rstrip(b"\n"))
            if m is None:
                malformed += 1
                continue
            path, code, whole, frac = m.group(1, 2, 3, 4)
            status[int(code)] += 1
            key = template(path)
            value = int(whole) * 10 + int(frac)
            bucket = latencies.get(key)
            if bucket is None:
                latencies[key] = [value]
            else:
                bucket.append(value)

    out = [f"lines {total}", f"malformed {malformed}"]
    for cls, count in enumerate(status):
        if count:
            out.append(f"status {cls}xx {count}")

    ranked = sorted(latencies.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for key, values in ranked[:10]:
        values.sort()
        n = len(values)
        p50 = values[(50 * n + 99) // 100 - 1]
        p95 = values[(95 * n + 99) // 100 - 1]
        out.append(
            f"path {key.decode('ascii')} {n} {tenths_text(p50)} "
            f"{tenths_text(p95)} {tenths_text(values[-1])}"
        )

    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
