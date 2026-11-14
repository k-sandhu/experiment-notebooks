"""Log scan, tuned Python 3 (standard library + NumPy).

Reads the file in binary chunks, validates/extracts every line with one
multiline bytes-regex findall over the whole chunk (C-speed matching), and
aggregates in a tight loop.  Latency percentiles are computed with NumPy.
"""

import re
import sys

# Multiline scan over raw bytes.  Character classes exclude '\n' where the
# SPEC pattern allows any non-space/non-quote byte, so a match can never
# straddle a physical line even when scanning a whole chunk.
PAT = re.compile(
    rb"(?m)^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d++"
    rb" (?:GET|PUT|POST|PATCH|DELETE)"
    rb" (/[A-Za-z0-9_/-]*+)(?:\?[^\n ]*+)?+"
    rb" (\d)\d\d \d+B (\d++)\.(\d)ms \"[^\n\"]*+\"$",
    re.ASCII,
)

CHUNK = 1 << 23  # 8 MiB


def main() -> None:
    sys.stdout.reconfigure(newline="\n")
    classes = [0] * 10
    paths: dict[bytes, list[int]] = {}
    lines = ok = 0
    findall = PAT.findall
    paths_get = paths.get
    carry = b""
    with open(sys.argv[1], "rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            lines += chunk.count(b"\n")
            if carry:
                chunk = carry + chunk
            nl = chunk.rfind(b"\n")
            if nl < 0:
                carry = chunk
                continue
            carry = chunk[nl + 1 :]
            for pth, s1, li, dec in findall(chunk, 0, nl + 1):
                ok += 1
                classes[s1[0] - 48] += 1
                tpl = b"/".join(
                    [b"{id}" if seg.isdigit() else seg for seg in pth.split(b"/")]
                )
                lats = paths_get(tpl)
                if lats is None:
                    paths[tpl] = [int(li) * 10 + (dec[0] - 48)]
                else:
                    lats.append(int(li) * 10 + (dec[0] - 48))
    if carry:  # spec says every line ends in '\n'; just be safe
        lines += 1
        m = PAT.fullmatch(carry)
        if m is not None:
            ok += 1
            s1 = m.group(2)
            classes[int(s1)] += 1
            pth = m.group(1)
            tpl = b"/".join(b"{id}" if seg.isdigit() else seg for seg in pth.split(b"/"))
            li, dec = m.group(3), m.group(4)
            paths.setdefault(tpl, []).append(int(li) * 10 + (dec[0] - 48))

    # Percentiles via NumPy (import deferred; only needed for the top 10).
    import numpy as np

    top = sorted(paths.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:10]
    out = [f"lines {lines}", f"malformed {lines - ok}"]
    for c, cnt in enumerate(classes):
        if cnt:
            out.append(f"status {c}xx {cnt}")
    for tpl, lats in top:
        n = len(lats)
        i50 = (50 * n + 99) // 100 - 1
        i95 = (95 * n + 99) // 100 - 1
        try:
            arr = np.fromiter(lats, dtype=np.int64, count=n)
            arr.sort()
            p50, p95, mx = int(arr[i50]), int(arr[i95]), int(arr[n - 1])
        except OverflowError:  # latency too large for int64: use exact big ints
            s = sorted(lats)
            p50, p95, mx = s[i50], s[i95], s[-1]
        out.append(
            f"path {tpl.decode()} {n} {p50 // 10}.{p50 % 10}"
            f" {p95 // 10}.{p95 % 10} {mx // 10}.{mx % 10}"
        )
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
