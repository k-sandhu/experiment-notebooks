import gc
import re
import sys
from collections import Counter

# Each well-formed line is matched together with the newline before it, so the
# search can jump between newlines; the input is prefixed with b'\n'.
LINE = re.compile(
    rb'\n\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z [a-z]+-\d+ (?:GET|POST|PUT|DELETE|PATCH) '
    rb'(/[A-Za-z0-9_/-]*)(?:\?[^ \n]*)? (\d)\d\d \d+B (\d+\.\d)ms "[^"\n]*"(?=\n)'
)
# Paths are joined with b'/\n', so every segment is followed by '/'. A
# digit-only segment becomes the single byte \x00, which no path contains.
ID_SEGMENT = re.compile(rb'/\d+(?=/)')

CHUNK = 1 << 25


def fmt(v):
    return f'{v // 10}.{v % 10}'


def main():
    gc.disable()
    total_lines = 0
    matched = 0
    status = Counter()
    groups = {}
    findall = LINE.findall
    sub = ID_SEGMENT.sub

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
            total_lines += data.count(b'\n') - 1
            res = findall(data)
            del data
            if not res:
                continue
            matched += len(res)
            paths, codes, lats = zip(*res)
            del res
            status.update(codes)
            blob = sub(b'/\x00', b'/\n'.join(paths) + b'/\n')
            del paths
            templates = blob.split(b'/\n')
            templates.pop()
            del blob
            for t in set(templates).difference(groups):
                groups[t] = []
            list(map(list.append, map(groups.__getitem__, templates), lats))
            del templates, lats

    out = [f'lines {total_lines}', f'malformed {total_lines - matched}']
    for c in sorted(status):
        out.append(f'status {c.decode()}xx {status[c]}')

    def template_name(t):
        return t.replace(b'\x00', b'{id}')

    ranked = sorted(groups, key=lambda t: (-len(groups[t]), template_name(t)))[:10]
    for t in ranked:
        name = template_name(t)
        vals = sorted(map(int, b' '.join(groups[t]).replace(b'.', b'').split()))
        n = len(vals)
        p50 = vals[(50 * n + 99) // 100 - 1]
        p95 = vals[(95 * n + 99) // 100 - 1]
        out.append(f'path {name.decode()} {n} {fmt(p50)} {fmt(p95)} {fmt(vals[-1])}')
    sys.stdout.buffer.write(('\n'.join(out) + '\n').encode())


main()
