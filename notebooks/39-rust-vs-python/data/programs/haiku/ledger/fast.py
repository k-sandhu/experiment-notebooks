import heapq
import json
import sys

import numpy as np

BLOCK = 1 << 23  # bytes of whole lines per vectorised pass
WIN = 20  # longest amount string handled by the vector path
COLS8 = np.arange(8)
SHIFTS = np.arange(8, dtype=np.uint64) * np.uint64(8)
WS = np.zeros(256, bool)
WS[[32, 9, 10, 13]] = True
STRUCT = np.zeros(256, bool)
STRUCT[list(b"{}[]:,")] = True


def word(name):
    return np.uint64(int.from_bytes(name, "little"))


def count_in(prefix, a, b):
    """Entries in [a, b), given prefix[p] = entries before p."""
    return prefix[b] - prefix[a]


def skip_ws(arr, pos):
    while True:
        w = WS[arr[pos]]
        if not w.any():
            return pos
        pos = pos + w


def key_words(arr, starts, lens):
    """First 8 bytes of each string packed little-endian, zero past its length."""
    idx = starts[:, None] + COLS8
    np.minimum(idx, arr.size - 1, out=idx)
    b = arr[idx].astype(np.uint64)
    b[COLS8 >= lens[:, None]] = 0
    return (b << SHIFTS).sum(axis=1, dtype=np.uint64)


def unique_strings(arr, starts, lens):
    """Maps strings to dense ids. Returns (ids, list of distinct byte strings)."""
    width = int(lens.max())
    cols = np.arange(width)
    idx = starts[:, None] + cols
    np.minimum(idx, arr.size - 1, out=idx)
    raw = arr[idx]
    raw[cols >= lens[:, None]] = 0
    keys = np.zeros((starts.size, width + 4), np.uint8)
    keys[:, :width] = raw
    keys[:, width:] = lens.astype("<u4").view(np.uint8).reshape(-1, 4)
    rows = keys.view(np.dtype((np.void, width + 4))).ravel()
    uniq, inv = np.unique(rows, return_inverse=True)
    names = []
    for row in uniq:
        b = row.tobytes()
        names.append(b[: int.from_bytes(b[width:], "little")])
    return inv.ravel(), names


def hundredths_of(arr, starts, lens):
    """Parses amounts like 12, 12.5, 12.05 into hundredths. Returns (values, bad mask)."""
    cols = np.arange(WIN)
    idx = starts[:, None] + cols
    np.minimum(idx, arr.size - 1, out=idx)
    b = arr[idx].astype(np.int64)
    inside = cols < lens[:, None]
    digit = inside & (b >= 48) & (b <= 57)
    dot = inside & (b == 46)
    has_dot = dot.any(axis=1)
    dot_at = np.where(has_dot, dot.argmax(axis=1), lens)
    value = np.zeros(starts.size, np.int64)
    for j in range(WIN):
        value = np.where(digit[:, j], value * 10 + (b[:, j] - 48), value)
    frac = np.where(has_dot, lens - dot_at - 1, 0)
    scale = np.array([100, 10, 1, 0], np.int64)[np.clip(frac, 0, 3)]
    return value * scale, (frac > 2) | (lens > WIN)


def add_txn(accounts, channels, totals, account, channel, value):
    totals[0] += 1
    totals[1] += value
    entry = channels.get(channel)
    if entry is None:
        channels[channel] = [1, value]
    else:
        entry[0] += 1
        entry[1] += value
    accounts[account] = accounts.get(account, 0) + value


def span_mask(n, starts, ends):
    """Boolean mask of positions inside any of the disjoint spans [start, end)."""
    mark = np.zeros(n + 1, np.int32)
    mark[starts] += 1
    mark[ends] -= 1
    return np.cumsum(mark[:n]) > 0


def process_block(data, n, rates, accounts, channels, totals):
    arr = np.frombuffer(data, dtype=np.uint8, count=n)
    nl = np.flatnonzero(arr == 10)  # every line ends with a newline
    lines = nl.size
    starts = np.zeros(lines, np.int64)
    starts[1:] = nl[:-1] + 1
    bad = np.zeros(lines, bool)  # lines that need the json fallback

    # Dense prefix counts: every lookup below is a gather instead of a binary search.
    line_before = np.cumsum(arr == 10, dtype=np.int32)  # line index of a position
    bs_before = np.zeros(n + 1, np.int32)  # bs_before[b] - bs_before[a] = backslashes in [a, b)
    np.cumsum(arr == 92, dtype=np.int32, out=bs_before[1:])

    # A quote is escaped when an odd number of backslashes come right before it.
    qpos = np.flatnonzero(arr == 34)
    bpos = np.flatnonzero(arr == 92)
    esc = np.zeros(qpos.size, bool)
    qi = np.flatnonzero((qpos > 0) & (arr[np.maximum(qpos - 1, 0)] == 92))
    if qi.size:
        qq = qpos[qi]
        run_start = np.ones(bpos.size, bool)
        run_start[1:] = np.diff(bpos) != 1
        first_of_run = np.maximum.accumulate(np.where(run_start, np.arange(bpos.size), 0))
        run = qq - bpos[first_of_run[np.searchsorted(bpos, qq - 1)]]
        esc[qi] = (run & 1) == 1
    rq = qpos[~esc]
    op = rq[0::2]  # string openers and closers alternate
    cl = rq[1::2]
    closer_of = np.zeros(n, np.int32)
    closer_of[op] = cl
    quotes_upto = np.zeros(n, np.int32)
    quotes_upto[rq] = 1
    np.cumsum(quotes_upto, out=quotes_upto)
    openers_upto = (quotes_upto + 1) >> 1  # number of openers at or before a position

    # Structural characters outside strings, and the nesting depth before each one.
    st_cand = np.flatnonzero(STRUCT[arr])
    spos = st_cand[(quotes_upto[st_cand] & 1) == 0]
    sch = arr[spos]
    delta = np.where((sch == 123) | (sch == 91), 1, np.where((sch == 125) | (sch == 93), -1, 0))
    dcum = np.zeros(spos.size + 1, np.int64)
    np.cumsum(delta, out=dcum[1:])
    dep = dcum[:-1]
    struct_upto = np.zeros(n, np.int32)
    struct_upto[spos] = 1
    np.cumsum(struct_upto, out=struct_upto)
    sdep_o = dcum[struct_upto[op]]  # depth of each string opener

    # Members of the transaction object (depth 1): key, then value after the colon.
    colon = spos[(sch == 58) & (dep == 1)]
    ln = line_before[colon]
    kopen = op[openers_upto[colon] - 1]  # the key is the last string opened before its colon
    kclose = closer_of[kopen]
    klen = kclose - kopen - 1
    kw = key_words(arr, kopen + 1, klen)
    bad[ln[count_in(bs_before, kopen, kclose) > 0]] = True
    term = spos[(dep == 1) & ((sch == 44) | (sch == 125))]
    term_upto = np.zeros(n, np.int32)
    term_upto[term] = 1
    np.cumsum(term_upto, out=term_upto)
    ve = term[term_upto[colon]]  # first terminator after the colon
    vs = skip_ws(arr, colon + 1)

    def is_key(name):
        return (klen == len(name)) & (kw == word(name))

    def string_field(mask):
        line_ids = ln[mask]
        v = vs[mask]
        s = v + 1
        e = closer_of[v]
        bad[line_ids[count_in(bs_before, s, e) > 0]] = True
        return line_ids, s, e - s

    def assign(line_ids, s, n_):
        start = np.zeros(lines, np.int64)
        length = np.zeros(lines, np.int64)
        start[line_ids] = s
        length[line_ids] = n_
        return start, length

    acc_s, acc_n = assign(*string_field(is_key(b"account")))
    typ_s, typ_n = assign(*string_field(is_key(b"type")))
    amt_s, amt_n = assign(*string_field(is_key(b"amount")))
    cur_s, cur_n = assign(*string_field(is_key(b"currency")))

    # Tags: any depth-2 string inside a tags array equal to "test" excludes the line.
    test = np.zeros(lines, bool)
    m_tag = is_key(b"tags")
    ts = vs[m_tag]
    te = ve[m_tag]
    bad[ln[m_tag][count_in(bs_before, ts, te) > 0]] = True
    if ts.size:
        in_tags = span_mask(n, ts, te)
        o2 = op[(sdep_o == 2) & in_tags[op]]
        len2 = closer_of[o2] - o2 - 1
        is_test = (len2 == 4) & (key_words(arr, o2 + 1, len2) == word(b"test"))
        test[line_before[o2[is_test]]] = True

    # meta.channel: a depth-2 key inside a meta object.
    ch_s = np.zeros(lines, np.int64)
    ch_n = np.zeros(lines, np.int64)
    m_meta = is_key(b"meta")
    ms = vs[m_meta]
    me = ve[m_meta]
    if ms.size:
        in_meta = span_mask(n, ms, me)
        ccol = spos[(sch == 58) & (dep == 2) & in_meta[spos]]
        ko2 = op[openers_upto[ccol] - 1]
        kc2 = closer_of[ko2]
        klen2 = kc2 - ko2 - 1
        cl_line = line_before[ccol]
        bad[cl_line[count_in(bs_before, ko2, kc2) > 0]] = True
        is_ch = (klen2 == 7) & (key_words(arr, ko2 + 1, klen2) == word(b"channel"))
        ch_line = cl_line[is_ch]
        v2 = skip_ws(arr, ccol[is_ch] + 1)
        s2 = v2 + 1
        e2 = closer_of[v2]
        bad[ch_line[count_in(bs_before, s2, e2) > 0]] = True
        ch_s[ch_line] = s2
        ch_n[ch_line] = e2 - s2

    typ_w = key_words(arr, typ_s, typ_n)
    is_void = (typ_n == 4) & (typ_w == word(b"void"))
    is_debit = (typ_n == 5) & (typ_w == word(b"debit"))

    hund, amt_bad = hundredths_of(arr, amt_s, amt_n)
    bad |= amt_bad

    ok_idx = np.flatnonzero(~(bad | is_void | test))
    if ok_idx.size:
        cur_inv, cur_names = unique_strings(arr, cur_s[ok_idx], cur_n[ok_idx])
        rate_tab = np.array([rates[name] for name in cur_names], np.int64)
        usd = hund[ok_idx] * rate_tab[cur_inv] // 1000000
        sv = np.where(is_debit[ok_idx], -usd, usd)

        acc_inv, acc_names = unique_strings(arr, acc_s[ok_idx], acc_n[ok_idx])
        acc_sum = np.zeros(len(acc_names), np.int64)
        np.add.at(acc_sum, acc_inv, sv)
        for name, s in zip(acc_names, acc_sum.tolist()):
            accounts[name] = accounts.get(name, 0) + s

        ch_inv, ch_names = unique_strings(arr, ch_s[ok_idx], ch_n[ok_idx])
        ch_count = np.bincount(ch_inv, minlength=len(ch_names))
        ch_sum = np.zeros(len(ch_names), np.int64)
        np.add.at(ch_sum, ch_inv, sv)
        for name, c, s in zip(ch_names, ch_count.tolist(), ch_sum.tolist()):
            entry = channels.get(name)
            if entry is None:
                channels[name] = [c, s]
            else:
                entry[0] += c
                entry[1] += s

        totals[0] += ok_idx.size
        totals[1] += int(sv.sum())

    # Lines the vector path cannot read exactly (escapes in relevant fields, long amounts).
    for li in np.flatnonzero(bad).tolist():
        t = json.loads(data[int(starts[li]) : int(nl[li])])
        kind = t["type"]
        if kind == "void" or "test" in t["tags"]:
            continue
        whole, _, frac = t["amount"].partition(".")
        hundredth = int(whole) * 100 + (int(frac.ljust(2, "0")) if frac else 0)
        usd = hundredth * rates[t["currency"].encode()] // 1000000
        value = -usd if kind == "debit" else usd
        add_txn(
            accounts,
            channels,
            totals,
            t["account"].encode(),
            t["meta"]["channel"].encode(),
            value,
        )


def main():
    accounts = {}  # id bytes -> sum
    channels = {}  # name bytes -> [count, sum]
    totals = [0, 0]  # counted, net
    with open(sys.argv[1], "rb") as f:
        rates = {k.encode(): v for k, v in json.loads(f.readline())["rates"].items()}
        tail = b""
        while True:
            chunk = f.read(BLOCK)
            if not chunk:
                if tail:
                    if not tail.endswith(b"\n"):
                        tail += b"\n"
                    process_block(tail, len(tail), rates, accounts, channels, totals)
                break
            data = tail + chunk
            cut = data.rfind(b"\n") + 1
            tail = data[cut:]
            if cut:
                process_block(data, cut, rates, accounts, channels, totals)

    out = [b"counted %d" % totals[0], b"net %d" % totals[1]]
    for name in sorted(channels):
        c, s = channels[name]
        out.append(b"channel %s %d %d" % (name, c, s))
    for name, s in heapq.nsmallest(10, accounts.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(b"account %s %d" % (name, s))
    sys.stdout.buffer.write(b"\n".join(out) + b"\n")


if __name__ == "__main__":
    main()
