import sys
import re
import gc
from collections import defaultdict, Counter
from heapq import nsmallest
from itertools import chain

CHUNK = 1 << 22


def fmt(v):
    return f"{v // 10}.{v % 10}"


def main():
    gc.disable()
    try:
        sys.set_int_max_str_digits(0)
    except Exception:
        pass

    D = '[0-9]'
    pat = (
        '^' + D * 4 + '-' + D * 2 + '-' + D * 2 + 'T' + D * 2 + ':' + D * 2 + ':' + D * 2
        + r'\.' + D * 3 + 'Z '
        + '[a-z]++-[0-9]++ '
        + '(?:GET|P(?:OST|UT|ATCH)|DELETE) '
        + '(/[A-Za-z0-9_/-]*+)'
        + r'(?: |\?[^ \n]*+ )'
        + '([0-9])[0-9][0-9] '
        + '[0-9]++B '
        + r'([0-9]++\.[0-9])ms '
        + r'"[^"\n]*+"\n'
    )
    findall = re.compile(pat.encode('ascii'), re.M).findall
    # digit-only path segments -> {id}; applied to newline-joined paths
    sub = re.compile(rb'/[0-9]++(?![^/\n])').sub

    lines = 0
    good = 0
    st_parts = []
    groups = defaultdict(list)
    from_iter = chain.from_iterable

    with open(sys.argv[1], 'rb') as f:
        read = f.read
        readline = f.readline
        while True:
            chunk = read(CHUNK)
            if not chunk:
                break
            if chunk[-1] != 10:
                chunk += readline()
            lines += chunk.count(b'\n')
            res = findall(chunk)
            if not res:
                continue
            good += len(res)
            flat = list(from_iter(res))
            del res
            st_parts.append(b''.join(flat[1::3]))
            tpls = sub(b'/{id}', b'\n'.join(flat[0::3])).split(b'\n')
            for t, lat in zip(tpls, flat[2::3]):
                groups[t].append(lat)

    out = [f"lines {lines}", f"malformed {lines - good}"]

    sb = b''.join(st_parts)
    for i in range(10):
        c = sb.count(48 + i)
        if c:
            out.append(f"status {i}xx {c}")

    top = nsmallest(10, groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for tpl, lst in top:
        n = len(lst)
        cnt = Counter(lst)
        pairs = sorted((int(k.replace(b'.', b'')), c) for k, c in cnt.items())
        r50 = (n + 1) // 2
        r95 = (95 * n + 99) // 100
        cum = 0
        p50 = None
        p95 = None
        for v, c in pairs:
            cum += c
            if p50 is None and cum >= r50:
                p50 = v
            if cum >= r95:
                p95 = v
                break
        mx = pairs[-1][0]
        out.append(
            f"path {tpl.decode('ascii')} {n} {fmt(p50)} {fmt(p95)} {fmt(mx)}"
        )

    sys.stdout.write('\n'.join(out) + '\n')
    sys.stdout.flush()


if __name__ == '__main__':
    main()
