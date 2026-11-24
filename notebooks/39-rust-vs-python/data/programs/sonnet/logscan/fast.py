import re
import sys

import numpy as np

LINE = re.compile(
    rb'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ (?:GET|POST|PUT|DELETE|PATCH) '
    rb'(/[A-Za-z0-9_/-]*)(?:\?[^ \n]*)? (\d)\d{2} \d+B (\d+\.\d)ms "[^"\n]*"$',
    re.M,
)
IDSEG = re.compile(rb'/\d+(?=[/\n]|\Z)')
BLOCK = 1 << 18


class IdMap(dict):
    def __init__(self):
        super().__init__()
        self.names = []

    def __missing__(self, key):
        i = len(self.names)
        self.names.append(key)
        self[key] = i
        return i


def fmt(t):
    return "%d.%d" % divmod(int(t), 10)


def main():
    lines = 0
    status = np.zeros(256, dtype=np.int64)
    idmap = IdMap()
    getid = idmap.__getitem__
    id_parts = []
    lat_parts = []
    findall = LINE.findall
    sub = IDSEG.sub

    def process(buf):
        res = findall(buf)
        n = len(res)
        if not n:
            return
        paths, sts, lats = zip(*res)
        status[:] += np.bincount(np.frombuffer(b''.join(sts), dtype=np.uint8), minlength=256)
        ts = sub(b'/{id}', b'\n'.join(paths)).split(b'\n')
        id_parts.append(np.fromiter(map(getid, ts), dtype=np.int32, count=n))
        lat_parts.append(np.fromstring(b' '.join(lats).replace(b'.', b''), dtype=np.int64, sep=' '))

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

    good = int(status.sum())
    out = ["lines %d" % lines, "malformed %d" % (lines - good)]
    for d in np.nonzero(status)[0]:
        out.append("status %cxx %d" % (int(d), status[d]))
    if good:
        ids = np.concatenate(id_parts)
        lats = np.concatenate(lat_parts)
        counts = np.bincount(ids, minlength=len(idmap.names))
        names = idmap.names
        order = sorted(range(len(names)), key=lambda k: (-int(counts[k]), names[k]))[:10]
        for k in order:
            v = np.sort(lats[ids == k])
            n = len(v)
            out.append("path %s %d %s %s %s" % (
                names[k].decode(), n, fmt(v[(50 * n + 99) // 100 - 1]),
                fmt(v[(95 * n + 99) // 100 - 1]), fmt(v[-1])))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
