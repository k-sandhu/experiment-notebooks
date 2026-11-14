"""Single-pass access-log summary, using only the standard library."""

import heapq
import re
import sys
from collections import defaultdict


LINE = re.compile(
    rb'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z '
    rb'[a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) '
    rb'(/[A-Za-z0-9_/-]*)(?:\?[^ ]*)? ([0-9])[0-9]{2} [0-9]+B '
    rb'([0-9]+)\.([0-9])ms "[^"]*"\n\Z'
)
IDS = re.compile(rb'/[0-9]+(?=/|$)')


def main(filename):
    # The grammar puts no bound on the number of latency digits.
    sys.set_int_max_str_digits(0)
    match = LINE.match
    normalize = IDS.sub
    paths = defaultdict(list)
    statuses = [0] * 10
    lines = malformed = 0
    with open(filename, 'rb', buffering=1024 * 1024) as source:
        for line in source:
            lines += 1
            record = match(line)
            if record is None:
                malformed += 1
                continue
            path, status, whole, fraction = record.groups()
            statuses[status[0] - 48] += 1
            template = normalize(b'/{id}', path)
            paths[template].append(int(whole) * 10 + fraction[0] - 48)

    output = [f'lines {lines}', f'malformed {malformed}']
    output.extend(f'status {i}xx {n}' for i, n in enumerate(statuses) if n)
    busiest = heapq.nsmallest(10, paths.items(), key=lambda item: (-len(item[1]), item[0]))
    for path, values in busiest:
        values.sort()
        n = len(values)
        p50 = values[(n - 1) // 2]
        p95 = values[n - n // 20 - 1]
        maximum = values[-1]
        output.append(
            f'path {path.decode("ascii")} {n} '
            f'{p50 // 10}.{p50 % 10} {p95 // 10}.{p95 % 10} '
            f'{maximum // 10}.{maximum % 10}'
        )
    sys.stdout.buffer.write(('\n'.join(output) + '\n').encode('ascii'))


if __name__ == '__main__':
    main(sys.argv[1])
