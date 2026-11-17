import gc
import re
import sys
from collections import defaultdict
from heapq import nsmallest
from itertools import count

import numpy as np

CHUNK = 1 << 23  # bytes of input handled per batch


def main():
    gc.disable()
    try:
        sys.set_int_max_str_digits(0)
    except AttributeError:
        pass

    with open(sys.argv[1], 'rb') as fh:
        data = fh.read()
    size = len(data)
    total = data.count(b'\n')

    # Whole-buffer matching: every match is exactly one full line (including
    # its '\n').  The two "anything but X" classes are written as positive
    # ranges that also exclude '\n' (so a match can never span lines):
    #   [\x00-\t\x0b-\x1f!-\xff]  == [^ \n]
    #   [\x00-\t\x0b-!#-\xff]     == [^"\n]
    line_re = re.compile(
        rb'^[0-9]{4}-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.[0-9]{3}Z '
        rb'[a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) '
        rb'(/[A-Za-z0-9_/-]*)(?:\?[\x00-\t\x0b-\x1f!-\xff]*)? '
        rb'([0-9])[0-9][0-9] [0-9]+B ([0-9]+\.[0-9])ms '
        rb'"[\x00-\t\x0b-!#-\xff]*"\n',
        re.MULTILINE,
    )
    findall = line_re.findall

    tid = defaultdict(count().__next__)   # template (with '{' marker) -> id
    getid = tid.__getitem__

    fromiter = np.fromiter
    frombuffer = np.frombuffer
    flatnonzero = np.flatnonzero
    bincount = np.bincount
    u8 = np.uint8

    status = np.zeros(58, dtype=np.int64)
    id_parts = []
    lat_parts = []
    good = 0

    pos = 0
    while pos < size:
        end = pos + CHUNK
        if end >= size:
            end = size
        else:
            end = data.rfind(b'\n', pos, end) + 1
            if end == 0:
                end = data.find(b'\n', pos + CHUNK) + 1
                if end == 0:
                    end = size
        rows = findall(data, pos, end)
        pos = end
        if not rows:
            continue
        n = len(rows)
        good += n
        paths, sds, lats = zip(*rows)
        del rows

        # status classes
        status += bincount(frombuffer(b''.join(sds), dtype=u8), minlength=58)

        # latencies in tenths of a millisecond
        f64 = fromiter(map(float, lats), dtype=np.float64, count=n)
        if f64.max() < 1e14:
            f64 *= 10.0
            lat = np.rint(f64).astype(np.int64)
        else:
            # exact fallback for absurdly large values
            lat = np.array(
                [int(s[:-2]) * 10 + (s[-1] - 48) for s in lats], dtype=object
            )
        lat_parts.append(lat)

        # path templates: collapse every all-digit segment to a single '{'
        blob = b'\n'.join(paths) + b'\n'
        a = frombuffer(blob, dtype=u8)
        isd = (a >= 48) & (a <= 57)
        cp = flatnonzero(isd[1:] != isd[:-1])
        if cp.size:
            cp += 1
            starts = cp[0::2]          # first digit of each digit run
            ends = cp[1::2]            # first byte after each digit run
            ae = a[ends]
            ok = (a[starts - 1] == 47) & ((ae == 47) | (ae == 10))
            gs = starts[ok]
            if gs.size:
                ge = ends[ok]
                out = a.copy()
                out[gs] = 123          # '{'
                delta = np.zeros(a.size, dtype=np.int8)
                delta[gs + 1] = 1
                delta[ge] -= 1
                keep = np.cumsum(delta, dtype=np.int8) == 0
                blob = out[keep].tobytes()
        tpl = blob.split(b'\n')
        tpl.pop()
        id_parts.append(fromiter(map(getid, tpl), dtype=np.int32, count=n))

    out_lines = ['lines %d' % total, 'malformed %d' % (total - good)]
    for d in range(10):
        c = int(status[48 + d])
        if c:
            out_lines.append('status %dxx %d' % (d, c))

    if good:
        ids = np.concatenate(id_parts)
        lat = np.concatenate(lat_parts)
        names = [k.replace(b'{', b'{id}') for k in tid]
        counts = bincount(ids, minlength=len(names)).tolist()
        top = nsmallest(
            10, range(len(names)), key=lambda i: (-counts[i], names[i])
        )
        for i in top:
            c = counts[i]
            v = lat[ids == i]
            v.sort()
            p50 = int(v[(50 * c + 99) // 100 - 1])
            p95 = int(v[(95 * c + 99) // 100 - 1])
            mx = int(v[-1])
            name = names[i].decode('ascii')
            out_lines.append(
                'path %s %d %d.%d %d.%d %d.%d'
                % (name, c, p50 // 10, p50 % 10, p95 // 10, p95 % 10,
                   mx // 10, mx % 10)
            )

    sys.stdout.write('\n'.join(out_lines) + '\n')
    sys.stdout.flush()


if __name__ == '__main__':
    main()
