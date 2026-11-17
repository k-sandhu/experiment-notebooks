import sys
import os
import gc
from collections import Counter
from itertools import pairwise, compress
from operator import itemgetter
from heapq import nlargest, nsmallest


def main():
    gc.disable()

    with open(sys.argv[1], 'rb') as f:
        raw = f.read()

    # Translation table: letters -> lower case, sentence enders -> '.',
    # everything else -> space.
    tbl = bytearray(b' ' * 256)
    for i in range(26):
        tbl[65 + i] = 97 + i
        tbl[97 + i] = 97 + i
    for ch in b'.!?':
        tbl[ch] = 46
    data = raw.translate(bytes(tbl)).decode('ascii')
    del raw

    n = len(data)
    ndots = data.count('.')

    DOT = '.'
    vocab = {DOT: DOT}
    intern = vocab.setdefault
    counts = Counter()
    update = counts.update
    find = data.find
    rfind = data.rfind

    ntok = 0
    start = 0
    CH = 1 << 19
    while start < n:
        end = start + CH
        if end >= n:
            end = n
        else:
            p = rfind('.', start, end)
            if p < 0:
                p = find('.', end)
                end = n if p < 0 else p + 1
            else:
                end = p + 1
        toks = data[start:end].replace('.', ' . ').split()
        start = end
        ntok += len(toks)
        update(pairwise(map(intern, toks, toks)))

    # Remove pseudo-pairs that involve the sentence marker.
    pop = counts.pop
    for w in vocab:
        pop((w, DOT), None)
        pop((DOT, w), None)

    total_pairs = sum(counts.values())
    distinct = len(counts)

    out = [
        'words %d' % (ntok - ndots),
        'pairs %d' % total_pairs,
        'distinct %d' % distinct,
    ]

    if distinct:
        vals = counts.values()
        dv = sorted(set(vals), reverse=True)
        t0 = dv[19] if len(dv) >= 20 else dv[-1]
        cand = list(compress(counts.items(), map(t0.__le__, vals)))
        if len(cand) > 20:
            top = nlargest(20, map(itemgetter(1), cand))
            t = top[-1]
            gt = [kv for kv in cand if kv[1] > t]
            eq = nsmallest(20 - len(gt), [kv[0] for kv in cand if kv[1] == t])
            cand = gt + [(k, t) for k in eq]
        cand.sort(key=lambda kv: (-kv[1], kv[0]))
        for (a, b), c in cand[:20]:
            out.append('%d %s %s' % (c, a, b))

    sys.stdout.write('\n'.join(out) + '\n')
    sys.stdout.flush()
    os._exit(0)


main()
