import re
import sys
from collections import defaultdict

sys.set_int_max_str_digits(0)
LINE = re.compile(rb'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z [a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(?:\?[^ ]*)? ([0-9])[0-9]{2} [0-9]+B ([0-9]+)\.([0-9])ms "[^"]*"')
SEGMENT = re.compile(rb'(?<=/)[0-9]+(?=/|$)')

def main():
    paths = defaultdict(list)
    statuses = [0] * 10
    lines = malformed = 0
    match = LINE.fullmatch
    substitute = SEGMENT.sub
    with open(sys.argv[1], 'rb', buffering=1024 * 1024) as source:
        for line in source:
            lines += 1
            m = match(line[:-1])
            if m is None:
                malformed += 1
                continue
            path, status, whole, fraction = m.groups()
            statuses[status[0] - 48] += 1
            paths[substitute(b'{id}', path)].append(int(whole + fraction))
    out = [f'lines {lines}', f'malformed {malformed}']
    out.extend(f'status {i}xx {n}' for i, n in enumerate(statuses) if n)
    top = sorted(paths.items(), key=lambda item: (-len(item[1]), item[0]))[:10]
    for path, values in top:
        values.sort()
        n = len(values)
        selected = (values[(n + 1) // 2 - 1], values[(95 * n + 99) // 100 - 1], values[-1])
        formatted = ' '.join(f'{v // 10}.{v % 10}' for v in selected)
        out.append(f'path {path.decode("ascii")} {n} {formatted}')
    sys.stdout.buffer.write(('\n'.join(out) + '\n').encode('ascii'))

if __name__ == '__main__':
    main()
