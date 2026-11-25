"""Log scan summariser -- fast Python 3.13, standard library only.

The heavy lifting (full-line validation against the spec's regex) is done by
the C regex engine over the whole file at once via findall, which returns the
captured groups directly as tuples and avoids per-match match-object calls.
Per-line work is kept to a minimum: bytes keys, an inlined template rewrite,
C-level int parsing via int(), and tenths-of-ms extracted as `tenth[0] - 48`.
Per-template latency lists are sorted in place (Timsort, C) for the nearest-rank
percentiles. No external dependencies (NumPy dropped: list.sort won on the small
per-template arrays).
"""

import re
import sys

_LINE_RE = re.compile(
    rb"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ "
    rb"(GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(\?[^ ]*)? "
    rb"(\d{3}) \d+B (\d+)\.(\d)ms \"[^\"]*\"$",
    re.MULTILINE,
)

_TOP = 10


def main() -> None:
    data = open(sys.argv[1], "rb").read()
    # Every line ends in '\n', so the number of lines equals the count of '\n'.
    total_lines = data.count(b"\n")

    status = [0] * 10
    templates: dict[bytes, list] = {}
    matched = 0
    get = templates.get

    # findall lets the C engine find all matches and returns the captured
    # groups directly as tuples, avoiding per-match match-object method calls.
    for _method, path, _query, status_code, int_part, tenth in _LINE_RE.findall(data):
        matched += 1
        status[status_code[0] - 48] += 1
        lat = int(int_part) * 10 + (tenth[0] - 48)

        # Path template, inlined: digit-only non-empty segments -> {id}.
        segs = path.split(b"/")
        key = b"/".join([b"{id}" if seg.isdigit() else seg for seg in segs])

        entry = get(key)
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
        r50 = -(-50 * n // 100) - 1
        r95 = -(-95 * n // 100) - 1
        out.append(
            "path {} {} {} {} {}".format(
                key.decode("ascii"),
                cnt,
                f"{lats[r50] // 10}.{lats[r50] % 10}",
                f"{lats[r95] // 10}.{lats[r95] % 10}",
                f"{lats[-1] // 10}.{lats[-1] % 10}",
            )
        )
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
