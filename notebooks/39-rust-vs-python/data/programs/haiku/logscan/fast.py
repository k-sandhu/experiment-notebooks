"""Web access log summary (standard library + NumPy).

The file is read in blocks of whole lines. Each block is validated with
vectorised NumPy operations: the seven field separators are located first, then
each field is checked on concatenated byte arrays. Path templates are keyed by
polynomial hashes modulo two primes. If a latency is too large for 64-bit
arithmetic, the file is re-read by the exact per-line scanner.
Usage: python fast.py INPUT_PATH
"""

import re
import sys

import numpy as np

BLOCK = 4 << 20
PAD = 64
MOD1, MOD2 = 2147483647, 1000000007
BASE1, BASE2 = 131071, 300007
METHODS = (b"GET", b"POST", b"PUT", b"DELETE", b"PATCH")
TS_DIGIT_COLS = np.array([0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22])
TS_LITERAL_COLS = np.array([4, 7, 10, 13, 16, 19, 23])
TS_LITERALS = np.frombuffer(b"--T::.Z", np.uint8)
PATH_CHAR = np.zeros(256, bool)
PATH_CHAR[np.frombuffer(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_/-", np.uint8)] = True
POW10 = np.array([10**k for k in range(18)], np.uint64)
ZERO = np.uint64(0)
BIG = np.int64(1 << 40)

LINE = re.compile(
    rb'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z'
    rb' [a-z]+-[0-9]+ (?:GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(?:\?[^ ]*)?'
    rb' ([0-9])[0-9]{2} [0-9]+B ([0-9]+)\.([0-9])ms "[^"]*"'
)


class Fallback(Exception):
    """Raised when a latency needs more than 64-bit arithmetic."""


class Powers:
    """Table of base**i mod m, stored as uint64 and grown on demand."""

    def __init__(self, base, mod):
        self.base, self.mod = base, mod
        self.table = np.ones(1, np.uint64)

    def upto(self, n):
        while len(self.table) < n:
            k = len(self.table)
            mult = np.uint64(pow(self.base, k, self.mod))
            self.table = np.concatenate([self.table, self.table * mult % np.uint64(self.mod)])
        return self.table


POWERS1 = Powers(BASE1, MOD1)
POWERS2 = Powers(BASE2, MOD2)


def gather(buf, a, b):
    """Concatenates buf[a[i]:b[i]] over all lines.

    Returns the bytes, each byte's index within its line, the line offsets
    (length n+1) and the line lengths.
    """
    lens = np.maximum(b - a, 0)
    offs = np.zeros(len(a) + 1, np.int64)
    np.cumsum(lens, out=offs[1:])
    total = int(offs[-1])
    local = np.arange(total, dtype=np.int64) - np.repeat(offs[:-1], lens)
    return buf[np.repeat(a, lens) + local], local, offs, lens


def seg_all(good, offs):
    if len(good) == 0:
        return np.ones(len(offs) - 1, bool)
    return np.logical_and.reduceat(good, np.minimum(offs[:-1], len(good) - 1))


def seg_sum(vals, offs):
    if len(vals) == 0:
        return np.zeros(len(offs) - 1, vals.dtype)
    return np.add.reduceat(vals, np.minimum(offs[:-1], len(vals) - 1))


def seg_min(vals, offs):
    if len(vals) == 0:
        return np.full(len(offs) - 1, BIG)
    return np.minimum.reduceat(vals, np.minimum(offs[:-1], len(vals) - 1))


def template_keys(praw, local, offs, lens):
    """One uint64 hash per path; equal templates give equal hashes.

    Each digit-only segment is treated as the text "{id}", and the hash is
    the sum of code * base**position over the emitted template bytes.
    """
    total = len(praw)
    starts = offs[:-1]
    is_slash = praw == 47
    nonslash = ~is_slash
    prev_slash = np.zeros(total, bool)
    prev_slash[1:] = is_slash[:-1]
    run_start = nonslash & ((local == 0) | prev_slash)
    run_id = np.cumsum(run_start) - 1
    is_digit = (praw >= 48) & (praw <= 57)
    runs = int(np.count_nonzero(run_start))
    non_digits = np.bincount(run_id[nonslash & ~is_digit], minlength=runs)
    numeric = np.append(non_digits == 0, False)  # run_id -1 (slashes) maps to False
    in_numeric = numeric[run_id]
    num_start = run_start & in_numeric
    literal = is_slash | (nonslash & ~in_numeric)
    emitted = literal.astype(np.int64) + num_start.astype(np.int64) * 4
    before = np.cumsum(emitted) - emitted
    pos = before - np.repeat(before[starts], lens)
    max_pos = int(pos.max()) + 4
    code = praw.astype(np.uint64)
    parts = []
    for powers, mod in ((POWERS1, MOD1), (POWERS2, MOD2)):
        table = powers.upto(max_pos)
        term = np.where(literal, code * table[pos], ZERO)
        for k, c in enumerate(b"{id}"):
            term += np.where(num_start, np.uint64(c) * table[pos + k], ZERO)
        parts.append(np.add.reduceat(term, starts) % np.uint64(mod))
    return parts[0] * np.uint64(MOD2) + parts[1]


class Acc:
    def __init__(self):
        self.lines = 0
        self.status = []
        self.keys = []
        self.lat = []
        self.raws = {}  # template key -> one raw path with that template


def process(body, acc):
    """Validates the whole lines in body (ending in b"\\n") and records the matches."""
    n = len(body)
    buf = np.zeros(n + PAD, np.uint8)
    buf[:n] = np.frombuffer(body, np.uint8)
    ends = np.flatnonzero(buf[:n] == 10).astype(np.int64)
    count = len(ends)
    acc.lines += count
    starts = np.zeros(count, np.int64)
    starts[1:] = ends[:-1] + 1

    # The first seven spaces of a matching line are its field separators.
    spaces = np.flatnonzero(buf[:n] == 32).astype(np.int64)
    if len(spaces) < 7:
        return
    first = np.searchsorted(spaces, starts)
    sep = first[:, None] + np.arange(7)
    keep = sep[:, 6] < len(spaces)
    S = spaces[np.minimum(sep, len(spaces) - 1)]
    keep &= S[:, 6] < ends
    rows = np.flatnonzero(keep)
    if len(rows) == 0:
        return
    starts, ends, S = starts[rows], ends[rows], S[rows]

    # Timestamp: fixed shape, then a space.
    cols = buf[starts[:, None] + np.arange(24)]
    ok = ((cols[:, TS_DIGIT_COLS] - 48) <= 9).all(1)
    ok &= (cols[:, TS_LITERAL_COLS] == TS_LITERALS).all(1)
    ok &= S[:, 0] == starts + 24

    # Host: [a-z]+-[0-9]+
    hv, hj, hoff, hl = gather(buf, S[:, 0] + 1, S[:, 1])
    low = (hv >= 97) & (hv <= 122)
    digit = (hv >= 48) & (hv <= 57)
    dash = hv == 45
    dash_pos = seg_sum(np.where(dash, hj, 0), hoff)
    ok &= seg_all(low | digit | dash, hoff)
    ok &= seg_sum(dash.astype(np.int64), hoff) == 1
    ok &= (dash_pos >= 1) & (dash_pos <= hl - 2)
    at_dash = np.repeat(dash_pos, hl)
    ok &= seg_all(~((hj < at_dash) & digit), hoff)
    ok &= seg_all(~((hj > at_dash) & low), hoff)

    # Method: one of the five words, exact length.
    win = buf[S[:, 1][:, None] + 1 + np.arange(6)]
    mlen = S[:, 2] - S[:, 1] - 1
    method_ok = np.zeros(len(rows), bool)
    for word in METHODS:
        method_ok |= (mlen == len(word)) & (win[:, :len(word)] == np.frombuffer(word, np.uint8)).all(1)
    ok &= method_ok

    # Path: starts with '/', path characters up to '?' or the end of the field.
    pstart = S[:, 2] + 1
    pv, pj, poff, plen = gather(buf, pstart, S[:, 3])
    q = np.minimum(seg_min(np.where(PATH_CHAR[pv], BIG, pj), poff), plen)
    ok &= (plen >= 1) & (buf[pstart] == 47) & ((q == plen) | (buf[pstart + q] == 63))

    # Status: exactly three digits.
    s0 = S[:, 3] + 1
    sc = buf[s0[:, None] + np.arange(3)]
    ok &= (S[:, 4] == s0 + 3) & ((sc - 48) <= 9).all(1)
    status_digit = sc[:, 0] - 48

    # Size: digits, then 'B'.
    zv, zj, zoff, zl = gather(buf, S[:, 4] + 1, S[:, 5])
    is_last = zj == np.repeat(zl - 1, zl)
    ok &= seg_all(np.where(is_last, zv == 66, (zv >= 48) & (zv <= 57)), zoff) & (zl >= 2)

    # Latency: digits '.' digit "ms", read from the end of the field.
    lv, lj, loff, ll = gather(buf, S[:, 5] + 1, S[:, 6])
    rel = np.repeat(ll, ll) - lj  # 1 for the last byte
    ldigit = (lv >= 48) & (lv <= 57)
    shape = np.where(
        rel >= 5,
        ldigit,
        np.where(rel == 4, lv == 46, np.where(rel == 3, ldigit, np.where(rel == 2, lv == 109, lv == 115))),
    )
    ok &= seg_all(shape, loff) & (ll >= 5)
    big = ll > 22  # more than 18 integer digits
    dv = lv.astype(np.uint64) - np.uint64(48)
    weight = POW10[np.clip(rel - 5, 0, 17)]
    whole = seg_sum(np.where(rel >= 5, dv * weight, ZERO), loff)
    frac = seg_sum(np.where(rel == 3, dv, ZERO), loff)
    tenths = whole * np.uint64(10) + frac

    # User agent: "[^"]*" running to the end of the line.
    quotes = np.flatnonzero(buf[:n] == 34)
    quote_count = np.searchsorted(quotes, ends) - np.searchsorted(quotes, S[:, 6] + 1)
    ok &= (
        (quote_count == 2)
        & (buf[S[:, 6] + 1] == 34)
        & (buf[ends - 1] == 34)
        & (ends - 1 >= S[:, 6] + 2)
    )

    if np.any(ok & big):
        raise Fallback
    good = np.flatnonzero(ok)
    if len(good) == 0:
        return
    acc.status.append(status_digit[good])
    acc.lat.append(tenths[good])

    gs = pstart[good]
    gl = q[good]
    praw, local, goff, glens = gather(buf, gs, gs + gl)
    keys = template_keys(praw, local, goff, glens)
    acc.keys.append(keys)
    uniq, first_idx = np.unique(keys, return_index=True)
    for key, idx in zip(uniq.tolist(), first_idx.tolist()):
        if key not in acc.raws:
            acc.raws[key] = praw[goff[idx]:goff[idx + 1]].tobytes()


def template_name(raw):
    return b"/".join([b"{id}" if seg.isdigit() else seg for seg in raw.split(b"/")])


def tenths_text(value):
    return f"{value // 10}.{value % 10}"


def summarize(lines, malformed, status, names, counts, values_of):
    out = [f"lines {lines}", f"malformed {malformed}"]
    for cls, count in enumerate(status):
        if count:
            out.append(f"status {cls}xx {count}")
    order = sorted(range(len(names)), key=lambda g: (-counts[g], names[g]))[:10]
    for g in order:
        values = values_of(g)
        n = len(values)
        p50 = int(values[(50 * n + 99) // 100 - 1])
        p95 = int(values[(95 * n + 99) // 100 - 1])
        top = int(values[n - 1])
        out.append(
            f"path {names[g].decode('ascii')} {counts[g]} {tenths_text(p50)} "
            f"{tenths_text(p95)} {tenths_text(top)}"
        )
    return "\n".join(out) + "\n"


def fast(path):
    acc = Acc()
    carry = b""
    with open(path, "rb") as f:
        while True:
            block = f.read(BLOCK)
            if not block:
                break
            data = carry + block
            cut = data.rfind(b"\n")
            if cut < 0:
                carry = data
                continue
            carry = data[cut + 1:]
            process(data[:cut + 1], acc)
    if carry:
        process(carry + b"\n", acc)

    if acc.keys:
        keys = np.concatenate(acc.keys)
        lat = np.concatenate(acc.lat)
        status = np.concatenate(acc.status)
    else:
        keys = np.zeros(0, np.uint64)
        lat = np.zeros(0, np.uint64)
        status = np.zeros(0, np.uint8)
    uniq, inv, counts = np.unique(keys, return_inverse=True, return_counts=True)
    names = [template_name(acc.raws[k]) for k in uniq.tolist()]
    status_counts = np.bincount(status, minlength=10).tolist()
    return summarize(
        acc.lines,
        acc.lines - len(keys),
        status_counts,
        names,
        counts.tolist(),
        lambda g: np.sort(lat[inv == g]),
    )


def slow(path):
    """Exact per-line scan, used only when the fast path cannot represent a value."""
    lines = 0
    malformed = 0
    status = [0] * 10
    groups = {}
    with open(path, "rb") as f:
        for raw in f:
            lines += 1
            m = LINE.fullmatch(raw.rstrip(b"\n"))
            if m is None:
                malformed += 1
                continue
            path_, code, whole, frac = m.group(1, 2, 3, 4)
            status[int(code)] += 1
            key = template_name(path_)
            groups.setdefault(key, []).append(int(whole) * 10 + int(frac))
    names = list(groups)
    counts = [len(groups[k]) for k in names]
    return summarize(
        lines,
        malformed,
        status,
        names,
        counts,
        lambda g: sorted(groups[names[g]]),
    )


def main():
    path = sys.argv[1]
    try:
        text = fast(path)
    except Fallback:
        text = slow(path)
    sys.stdout.buffer.write(text.encode("ascii"))


if __name__ == "__main__":
    main()
