import re
import sys

# Groups: 1 = path, 2 = status, 3 = latency integer part, 4 = latency tenths digit.
LINE_RE = re.compile(
    rb"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ "
    rb"(?:GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(?:\?[^ ]*)? "
    rb"(\d{3}) \d+B (\d+)\.(\d)ms \"[^\"]*\"$",
    re.MULTILINE,
)

ID = b"{id}"


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()

    total = data.count(b"\n")
    status = [0] * 10
    stats = {}  # template -> [count, [latencies]]
    valid = 0

    finditer = LINE_RE.finditer
    for m in finditer(data):
        valid += 1
        status[m.group(2)[0] - 48] += 1

        path = m.group(1)
        tpl = b"/".join([ID if seg.isdigit() else seg for seg in path.split(b"/")])
        s = stats.get(tpl)
        if s is None:
            stats[tpl] = [1, [int(m.group(3)) * 10 + m.group(4)[0] - 48]]
        else:
            s[0] += 1
            s[1].append(int(m.group(3)) * 10 + m.group(4)[0] - 48)

    out = ["lines %d" % total, "malformed %d" % (total - valid)]
    for c in range(10):
        if status[c]:
            out.append("status %dxx %d" % (c, status[c]))

    top = sorted(stats.items(), key=lambda kv: (-kv[1][0], kv[0]))[:10]
    for tpl, (count, lats) in top:
        lats.sort()
        n = len(lats)
        p50 = lats[(50 * n + 99) // 100 - 1]
        p95 = lats[(95 * n + 99) // 100 - 1]
        out.append(
            "path %s %d %d.%d %d.%d %d.%d"
            % (
                tpl.decode(),
                count,
                p50 // 10,
                p50 % 10,
                p95 // 10,
                p95 % 10,
                lats[-1] // 10,
                lats[-1] % 10,
            )
        )

    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
