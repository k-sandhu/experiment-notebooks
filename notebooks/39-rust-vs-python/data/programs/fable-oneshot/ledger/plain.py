import sys
import gc
import re
import json
from collections import defaultdict
from heapq import nsmallest


def main():
    gc.disable()
    try:
        sys.set_int_max_str_digits(0)
    except Exception:
        pass

    path = sys.argv[1]
    scan = json.JSONDecoder().scan_once
    skip_ws = re.compile(r'[ \t\r\n]+').match

    chan = defaultdict(lambda: [0, 0])
    acc = defaultdict(int)

    CHUNK = 1 << 20

    with open(path, 'rb', buffering=1 << 16) as f:
        first = f.readline()
        rates_raw = json.loads(first.decode('utf-8-sig'))['rates']
        rates = {k: int(v) for k, v in rates_raw.items()}

        read = f.read
        readline = f.readline
        while True:
            chunk = read(CHUNK)
            if not chunk:
                break
            if chunk[-1] != 10:
                chunk += readline()
            text = chunk.decode('utf-8')
            n = len(text)
            pos = 0
            while pos < n:
                try:
                    d, pos = scan(text, pos)
                except StopIteration:
                    m = skip_ws(text, pos)
                    if m is None:
                        raise
                    pos = m.end()
                    continue
                pos += 1
                t = d['type']
                if t == 'void' or 'test' in d['tags']:
                    continue
                a = d['amount']
                h = int(a.replace('.', ''))
                if a[-3:-2] != '.':
                    if a[-2:-1] == '.':
                        h *= 10
                    else:
                        h *= 100
                usd = h * rates[d['currency']] // 1000000
                if t == 'debit':
                    usd = -usd
                c = chan[d['meta']['channel']]
                c[0] += 1
                c[1] += usd
                acc[d['account']] += usd

    counted = 0
    net = 0
    for c in chan.values():
        counted += c[0]
        net += c[1]

    out = ['counted %d' % counted, 'net %d' % net]
    for name in sorted(chan):
        c = chan[name]
        out.append('channel %s %d %d' % (name, c[0], c[1]))
    top = nsmallest(10, acc.items(), key=lambda kv: (-kv[1], kv[0]))
    for name, v in top:
        out.append('account %s %d' % (name, v))
    out.append('')
    sys.stdout.write('\n'.join(out))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
