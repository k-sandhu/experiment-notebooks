import re
import sys

# One C-level scan over the whole file finds every well-formed line.
# [^ \n] / [^"\n] keep a match from ever spanning a newline, so this is
# exactly equivalent to a per-line fullmatch. Only status class (first
# digit), path, and the two latency groups are captured.
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
    for m in PAT.finditer(data):
        ok += 1
        path, sdig, whole, frac = m.groups()
        status[sdig[0] - 48] += 1
        # Template: replace digit-only '/'-separated segments with {id}.
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
        lats.sort()
        n = len(lats)
        p50 = lats[(50 * n + 99) // 100 - 1]
        p95 = lats[(95 * n + 99) // 100 - 1]
        mx = lats[-1]
        out.append(b"path %s %d %d.%d %d.%d %d.%d" % (
            templ, n,
            p50 // 10, p50 % 10,
            p95 // 10, p95 % 10,
            mx // 10, mx % 10))
    sys.stdout.buffer.write(b"\n".join(out) + b"\n")


if __name__ == "__main__":
    main()
