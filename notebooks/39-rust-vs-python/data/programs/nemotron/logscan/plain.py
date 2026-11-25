"""Log scan summariser -- plain Python 3.13, standard library only."""

import re
import sys

_LINE_RE = re.compile(
    rb"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ "
    rb"(GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(\?[^ ]*)? "
    rb"(\d{3}) \d+B (\d+)\.(\d)ms \"[^\"]*\"$",
    re.MULTILINE,
)

_TOP = 10


def template(path: bytes) -> bytes:
    # Split on '/', replace non-empty all-digit segments with '{id}', rejoin.
    return b"/".join(b"{id}" if seg.isdigit() else seg for seg in path.split(b"/"))


def nearest_rank(pct: int, n: int) -> int:
    # 0-based index of the element at 1-based position ceil(pct * n / 100).
    return -(-pct * n // 100) - 1


def fmt_ms(tenths: int) -> str:
    return f"{tenths // 10}.{tenths % 10}"


def main() -> None:
    data = open(sys.argv[1], "rb").read()
    # Every line ends in '\n', so the number of lines equals the count of '\n'.
    total_lines = data.count(b"\n")

    status = [0] * 10
    templates: dict[bytes, list] = {}
    matched = 0

    for m in _LINE_RE.finditer(data):
        matched += 1
        status[m.group(4)[0] - 48] += 1
        lat = int(m.group(5)) * 10 + int(m.group(6))
        key = template(m.group(2))
        entry = templates.get(key)
        if entry is None:
            templates[key] = [1, [lat]]
        else:
            entry[0] += 1
            entry[1].append(lat)

    out = [f"lines {total_lines}", f"malformed {total_lines - matched}"]
    for cls in range(10):
        cnt = status[cls]
        if cnt:
            out.append(f"status {cls}xx {cnt}")
    items = sorted(templates.items(), key=lambda kv: (-kv[1][0], kv[0]))
    for key, (cnt, lats) in items[:_TOP]:
        lats.sort()
        n = len(lats)
        out.append(
            "path {} {} {} {} {}".format(
                key.decode("ascii"),
                cnt,
                fmt_ms(lats[nearest_rank(50, n)]),
                fmt_ms(lats[nearest_rank(95, n)]),
                fmt_ms(lats[-1]),
            )
        )
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
