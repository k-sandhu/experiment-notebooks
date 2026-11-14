"""Access-log summary with compact latency buffers and NumPy rank selection."""

import heapq
import re
import sys
from array import array
from collections import defaultdict

import numpy as np


LINE = re.compile(
    rb'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z '
    rb'[a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) '
    rb'(/[A-Za-z0-9_/-]*)(?:\?[^ ]*)? ([0-9])[0-9]{2} [0-9]+B '
    rb'([0-9]+)\.([0-9])ms "[^"]*"\n\Z'
)
IDS = re.compile(rb'/[0-9]+(?=/|$)')
U64_MAX = (1 << 64) - 1


def main(filename):
    sys.set_int_max_str_digits(0)
    match = LINE.match
    normalize = IDS.sub
    paths = defaultdict(lambda: array('Q'))
    # Preserve arbitrary-size integers without making ordinary values objects.
    big = defaultdict(list)
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
            value = int(whole) * 10 + fraction[0] - 48
            values = paths[template]
            if value <= U64_MAX:
                values.append(value)
            else:
                big[template].append(value)

    output = [f'lines {lines}', f'malformed {malformed}']
    output.extend(f'status {i}xx {n}' for i, n in enumerate(statuses) if n)
    busiest = heapq.nsmallest(
        10, paths.items(),
        key=lambda item: (-(len(item[1]) + len(big.get(item[0], ()))), item[0]),
    )
    for path, buffer in busiest:
        large = big.get(path, ())
        small = np.frombuffer(buffer, dtype=np.uint64)
        k = len(small)
        n = k + len(large)
        ranks = ((n - 1) // 2, n - n // 20 - 1)
        needed = [rank for rank in ranks if rank < k]
        maximum = max(large) if large else int(small.max())
        if needed:
            small.partition(needed)
        if large:
            large.sort()
        p50, p95 = (int(small[r]) if r < k else large[r - k] for r in ranks)
        output.append(
            f'path {path.decode("ascii")} {n} '
            f'{p50 // 10}.{p50 % 10} {p95 // 10}.{p95 % 10} '
            f'{maximum // 10}.{maximum % 10}'
        )
    sys.stdout.buffer.write(('\n'.join(output) + '\n').encode('ascii'))


if __name__ == '__main__':
    main(sys.argv[1])
