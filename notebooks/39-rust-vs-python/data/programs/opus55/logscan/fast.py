import gc
import re
import sys

import numpy as np

# Each well-formed line is matched together with the newline before it, so the
# search can jump between newlines; every chunk is prefixed with b'\n'.
LINE = re.compile(
    rb'\n\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z [a-z]+-\d+ (?:GET|POST|PUT|DELETE|PATCH) '
    rb'(/[A-Za-z0-9_/-]*)(?:\?[^ \n]*)? (\d)\d\d \d+B (\d+\.\d)ms "[^"\n]*"(?=\n)'
)
# Paths are joined with b'/\n', so every segment is followed by '/'. A
# digit-only segment becomes the single byte \x00, which no path contains.
ID_SEGMENT = re.compile(rb'/\d+(?=/)')

CHUNK = 1 << 25
BIG = 1 << 62
# Latency strings up to this many bytes convert exactly through float64.
FLOAT_EXACT = 15


def fmt(v):
    v = int(v)
    return f'{v // 10}.{v % 10}'


def main():
    gc.disable()
    total = 0
    status_counts = np.zeros(10, dtype=np.int64)
    tid = {}
    id_parts, lat_parts = [], []
    big_vals = {}
    findall = LINE.findall
    sub = ID_SEGMENT.sub

    def consume(data):
        res = findall(data)
        if not res:
            return
        paths, codes, lats = zip(*res)
        del res
        status_counts[:] += np.bincount(np.frombuffer(b''.join(codes), dtype=np.uint8) - 48, minlength=10)
        blob = sub(b'/\x00', b'/\n'.join(paths) + b'/\n')
        del paths
        templates = blob.split(b'/\n')
        templates.pop()
        del blob
        for t in set(templates).difference(tid):
            tid[t] = len(tid)
        ids = np.fromiter(map(tid.__getitem__, templates), np.int32, len(templates))
        raw = np.array(lats)
        if raw.dtype.itemsize <= FLOAT_EXACT:
            tenths = np.rint(raw.astype(np.float64) * 10).astype(np.int64)
        else:
            # Very long latencies: exact integer arithmetic in Python.
            vals = [int(x.replace(b'.', b'')) for x in lats]
            small = np.array([v < BIG for v in vals], dtype=bool)
            for t, v, s in zip(templates, vals, small):
                if not s:
                    big_vals.setdefault(tid[t], []).append(v)
            ids = ids[small]
            tenths = np.array([v for v in vals if v < BIG], dtype=np.int64)
        id_parts.append(ids)
        lat_parts.append(tenths)

    with open(sys.argv[1], 'rb') as f:
        carry = b'\n'
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            cut = block.rfind(b'\n') + 1
            if cut == 0:
                carry += block
                continue
            data = carry + block[:cut]
            carry = b'\n' + block[cut:]
            total += data.count(b'\n') - 1
            consume(data)
            del data

    ids = np.concatenate(id_parts) if id_parts else np.zeros(0, np.int32)
    lats = np.concatenate(lat_parts) if lat_parts else np.zeros(0, np.int64)
    del id_parts, lat_parts
    counts = np.bincount(ids, minlength=len(tid)).tolist()
    for i, v in big_vals.items():
        counts[i] += len(v)

    out = [f'lines {total}', f'malformed {total - sum(counts)}']
    for c in range(10):
        if status_counts[c]:
            out.append(f'status {c}xx {status_counts[c]}')

    shown = [(t.replace(b'\x00', b'{id}'), i) for t, i in tid.items()]
    shown.sort(key=lambda x: (-counts[x[1]], x[0]))
    for name, i in shown[:10]:
        small = np.sort(lats[ids == i])
        big = sorted(big_vals.get(i, ()))
        n = counts[i]
        parts = []
        for k in ((50 * n + 99) // 100 - 1, (95 * n + 99) // 100 - 1, n - 1):
            parts.append(fmt(small[k]) if k < len(small) else fmt(big[k - len(small)]))
        out.append(f'path {name.decode()} {n} {" ".join(parts)}')
    sys.stdout.buffer.write(('\n'.join(out) + '\n').encode())


main()
