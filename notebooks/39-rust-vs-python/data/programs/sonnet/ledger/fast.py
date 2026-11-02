import sys
import gc
import json
from itertools import compress, repeat
from operator import contains, itemgetter

import numpy as np

CHUNK = 4 << 20


class Grouper:
    """Maps keys to dense ids and accumulates exact int64 sums per id."""

    def __init__(self):
        self.ids = {}
        self.sums = np.zeros(1024, dtype=np.int64)
        self.counts = np.zeros(1024, dtype=np.int64)

    def add(self, keys, vals):
        ids = self.ids
        new = set(keys).difference(ids)
        if new:
            for k in new:
                ids[k] = len(ids)
            if len(ids) > len(self.sums):
                size = max(len(ids), 2 * len(self.sums))
                s = np.zeros(size, dtype=np.int64)
                c = np.zeros(size, dtype=np.int64)
                s[:len(self.sums)] = self.sums
                c[:len(self.counts)] = self.counts
                self.sums = s
                self.counts = c
        idx = np.fromiter(map(ids.__getitem__, keys), dtype=np.int64, count=len(keys))
        np.add.at(self.sums, idx, vals)
        bc = np.bincount(idx)
        self.counts[:len(bc)] += bc


def hundredths(amounts):
    n = len(amounts)
    arr = np.array(amounts)  # fixed-width unicode, zero padded
    w = arr.dtype.itemsize // 4
    c = arr.view(np.uint32).reshape(n, w)
    isdig = (c >= 48) & (c <= 57)
    digits = (c - 48).astype(np.int64)
    v = np.zeros(n, dtype=np.int64)
    for j in range(w):
        v = np.where(isdig[:, j], v * 10 + digits[:, j], v)
    after = np.cumsum(c == 46, axis=1) > 0
    fd = (isdig & after).sum(axis=1)
    scale = np.array([100, 10, 1], dtype=np.int64)[fd]
    return v * scale


def main():
    gc.disable()
    path = sys.argv[1]
    loads = json.loads
    g_type = itemgetter("type")
    g_tags = itemgetter("tags")
    g_amount = itemgetter("amount")
    g_curr = itemgetter("currency")
    g_acc = itemgetter("account")
    g_meta = itemgetter("meta")
    g_chan = itemgetter("channel")
    sign_of = {"credit": 1, "refund": 1, "debit": -1, "void": 0}.__getitem__
    rates = None
    count = 0
    net = 0
    chans = Grouper()
    accts = Grouper()

    with open(path, "rb") as f:
        tail = b""
        eof = False
        while not eof:
            data = f.read(CHUNK)
            if not data:
                eof = True
                block = tail
                tail = b""
            else:
                data = tail + data
                cut = data.rfind(b"\n")
                if cut < 0:
                    tail = data
                    continue
                block = data[:cut]
                tail = data[cut + 1:]
            block = block.strip()
            if not block:
                continue
            if rates is None:
                nl = block.find(b"\n")
                if nl < 0:
                    first, block = block, b""
                else:
                    first, block = block[:nl], block[nl + 1:]
                rates = loads(first)["rates"]
                if not block:
                    continue
            objs = loads(b"[" + block.replace(b"\n", b",") + b"]")
            sgn = np.fromiter(map(sign_of, map(g_type, objs)), dtype=np.int64, count=len(objs))
            test = np.fromiter(map(contains, map(g_tags, objs), repeat("test")), dtype=np.bool_, count=len(objs))
            keep = ((sgn != 0) & ~test)
            n = int(keep.sum())
            if n == 0:
                continue
            klist = keep.tolist()
            if n != len(objs):
                objs = list(compress(objs, klist))
                sgn = sgn[keep]
            amounts = list(map(g_amount, objs))
            currs = map(g_curr, objs)
            accs = list(map(g_acc, objs))
            chs = list(map(g_chan, map(g_meta, objs)))
            rate = np.fromiter(map(rates.__getitem__, currs), dtype=np.int64, count=n)
            vals = (hundredths(amounts) * rate // 1000000) * sgn
            count += n
            net += int(vals.sum())
            chans.add(chs, vals)
            accts.add(accs, vals)

    out = ["counted %d" % count, "net %d" % net]
    cnames = list(chans.ids)
    for name in sorted(cnames, key=lambda s: s.encode("utf-8")):
        i = chans.ids[name]
        out.append("channel %s %d %d" % (name, chans.counts[i], chans.sums[i]))
    anames = list(accts.ids)
    sums = accts.sums[:len(anames)].tolist()
    if len(anames) > 10:
        # Only the best few by sum can reach the top 10; include all ties at the cutoff.
        arr = accts.sums[:len(anames)]
        cutoff = np.sort(arr)[len(arr) - 10]
        cand = np.nonzero(arr >= cutoff)[0].tolist()
    else:
        cand = range(len(anames))
    top = sorted(((-sums[i], anames[i].encode("utf-8"), anames[i]) for i in cand))[:10]
    for negv, _, name in top:
        out.append("account %s %d" % (name, -negv))
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))


main()
