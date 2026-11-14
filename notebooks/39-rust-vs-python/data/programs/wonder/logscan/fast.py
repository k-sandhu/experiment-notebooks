import re
import sys

import numpy as np

# Same C-level regex scan as the plain version (it validates in C and
# yields only well-formed lines); NumPy is used for the percentiles,
# where partitioning beats a full sort of each top template's latencies.
PAT = re.compile(
    rb'(?m)^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ '
    rb'(?:GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(?:\?[^ \n]*)? '
    rb'(\d)\d{2} \d+B (\d+)\.(\d)ms "[^"\n]*"$'
)
ID = b"{id}"


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    if not data:
        total = 0
    else:
        total = data.count(b"\n") + (0 if data.endswith(b"\n") else 1)

    status = [0] * 10
    agg = {}
    ok = 0
    finditer = PAT.finditer
    for m in finditer(data):
        ok += 1
        path, sdig, whole, frac = m.groups()
        status[sdig[0] - 48] += 1
        templ = b"/".join([ID if seg.isdigit() else seg
                            for seg in path.split(b"/")])
        lat = int(whole) * 10 + (frac[0] - 48)
        try:
            agg[templ].append(lat)
        except KeyError:
            agg[templ] = [lat]

    out = [b"lines " + str(total).encode(),
           b"malformed " + str(total - ok).encode()]
    for d in range(10):
        c = status[d]
        if c:
            out.append(b"status %dxx %d" % (d, c))
    top = sorted(agg.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:10]
    for templ, lats in top:
        n = len(lats)
        arr = np.array(lats, dtype=np.int64)
        mx = int(arr.max())
        k50 = (50 * n + 99) // 100 - 1
        k95 = (95 * n + 99) // 100 - 1
        if k50 == k95:
            part = np.partition(arr, k50)
            p50 = p95 = int(part[k50])
        else:
            part = np.partition(arr, (k50, k95))
            p50 = int(part[k50])
            p95 = int(part[k95])
        out.append(b"path %s %d %d.%d %d.%d %d.%d" % (
            templ, n,
            p50 // 10, p50 % 10,
            p95 // 10, p95 % 10,
            mx // 10, mx % 10))
    sys.stdout.buffer.write(b"\n".join(out) + b"\n")


if __name__ == "__main__":
    main()
