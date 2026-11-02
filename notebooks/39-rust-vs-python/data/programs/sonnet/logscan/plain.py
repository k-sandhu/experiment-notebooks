import re
import sys
from collections import Counter, defaultdict

LINE = re.compile(
    rb'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ (?:GET|POST|PUT|DELETE|PATCH) '
    rb'(/[A-Za-z0-9_/-]*)(?:\?[^ \n]*)? (\d)\d{2} \d+B (\d+\.\d)ms "[^"\n]*"$',
    re.M,
)
IDSEG = re.compile(rb'/\d+(?=[/\n]|\Z)')
BLOCK = 1 << 18


def fmt(t):
    return "%d.%d" % divmod(t, 10)


def main():
    lines = 0
    good = 0
    status = Counter()
    groups = defaultdict(list)
    findall = LINE.findall
    sub = IDSEG.sub

    def process(buf):
        nonlocal good
        res = findall(buf)
        if not res:
            return
        good += len(res)
        paths, sts, lats = zip(*res)
        status.update(b''.join(sts))
        ts = sub(b'/{id}', b'\n'.join(paths)).split(b'\n')
        vals = list(map(int, b' '.join(lats).replace(b'.', b'').split()))
        for t, v in zip(ts, vals):
            groups[t].append(v)

    with open(sys.argv[1], 'rb') as f:
        tail = b''
        while True:
            block = f.read(BLOCK)
            if not block:
                break
            block = tail + block if tail else block
            cut = block.rfind(b'\n') + 1
            if cut == 0:
                tail = block
                continue
            tail = block[cut:]
            chunk = block[:cut]
            del block
            lines += chunk.count(b'\n')
            process(chunk)
        if tail:
            lines += 1
            process(tail)

    out = ["lines %d" % lines, "malformed %d" % (lines - good)]
    for d in sorted(status):
        out.append("status %cxx %d" % (d, status[d]))
    top = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:10]
    for t, v in top:
        v.sort()
        n = len(v)
        out.append("path %s %d %s %s %s" % (
            t.decode(), n, fmt(v[(50 * n + 99) // 100 - 1]),
            fmt(v[(95 * n + 99) // 100 - 1]), fmt(v[-1])))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
