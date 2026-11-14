import re
import sys

import numpy as np

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
    names = []
    ids = {}
    gids = []
    lats = []
    valid = 0

    finditer = LINE_RE.finditer
    getid = ids.get
    names_append = names.append
    gids_append = gids.append
    lats_append = lats.append

    for m in finditer(data):
        valid += 1
        status[m.group(2)[0] - 48] += 1

        path = m.group(1)
        tpl = b"/".join([ID if seg.isdigit() else seg for seg in path.split(b"/")])
        g = getid(tpl)
        if g is None:
            g = len(names)
            ids[tpl] = g
            names_append(tpl)
        gids_append(g)
        lats_append(int(m.group(3)) * 10 + m.group(4)[0] - 48)

    gids_arr = np.fromiter(gids, np.int32, len(gids))
    try:
        lats_arr = np.fromiter(lats, np.int64, len(lats))
    except OverflowError:
        lats_arr = None  # pathological latencies: keep exact Python integers
    counts = np.bincount(gids_arr, minlength=len(names))

    order = sorted(range(len(names)), key=lambda i: (-int(counts[i]), names[i]))[:10]

    out = ["lines %d" % total, "malformed %d" % (total - valid)]
    for c in range(10):
        if status[c]:
            out.append("status %dxx %d" % (c, status[c]))
    for gi in order:
        if lats_arr is not None:
            v = np.sort(lats_arr[gids_arr == gi])
            n = v.size
            p50 = int(v[(50 * n + 99) // 100 - 1])
            p95 = int(v[(95 * n + 99) // 100 - 1])
            mx = int(v[n - 1])
        else:
            v = sorted(lats[i] for i in range(len(gids)) if gids[i] == gi)
            n = len(v)
            p50 = v[(50 * n + 99) // 100 - 1]
            p95 = v[(95 * n + 99) // 100 - 1]
            mx = v[n - 1]
        out.append(
            "path %s %d %d.%d %d.%d %d.%d"
            % (
                names[gi].decode(),
                n,
                p50 // 10,
                p50 % 10,
                p95 // 10,
                p95 % 10,
                mx // 10,
                mx % 10,
            )
        )
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
