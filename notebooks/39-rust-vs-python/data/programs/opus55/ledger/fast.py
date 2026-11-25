import json
import sys

import numpy as np

CHUNK = 1 << 24
PAD = b"\0" * 64

# Entry classes for the structural index.
QUOTE, BSLASH, OPEN, CLOSE, COLON = 1, 2, 3, 4, 5
CLS = np.zeros(256, np.uint8)
CLS[ord('"')] = QUOTE
CLS[ord("\\")] = BSLASH
CLS[ord("{")] = OPEN
CLS[ord("[")] = OPEN
CLS[ord("}")] = CLOSE
CLS[ord("]")] = CLOSE
CLS[ord(":")] = COLON

# code = class * 2 + (1 if inside a string); depth change of outside-string brackets.
DELTA = np.zeros(16, np.int8)
DELTA[OPEN * 2] = 1
DELTA[CLOSE * 2] = -1
# Query codes on X = depth * 16 + code ("depth" is the depth after the entry).
X_REC_START = 1 * 16 + OPEN * 2
X_REC_END = 0 * 16 + CLOSE * 2
X_COLON1 = 1 * 16 + COLON * 2
X_COLON2 = 2 * 16 + COLON * 2
X_OPENQ2 = 2 * 16 + QUOTE * 2  # opening quote: parity before it is even

POW10 = 10 ** np.arange(19, dtype=np.int64)
AR8 = np.arange(8)


def key_pattern(name):
    """(value, mask) to match 'name"' (or exactly 8 bytes of name) as a little-endian uint64."""
    raw = (name + '"').encode()[:8]
    raw8 = raw.ljust(8, b"\0")
    mask = (b"\xff" * len(raw)).ljust(8, b"\0")
    return (np.frombuffer(raw8, np.uint64)[0], np.frombuffer(mask, np.uint64)[0], len(name))


K_ACCOUNT, K_TYPE, K_AMOUNT, K_CURRENCY, K_TAGS, K_META = 1, 2, 3, 4, 5, 6
KEYS = [(K_ACCOUNT, key_pattern("account")), (K_TYPE, key_pattern("type")),
        (K_AMOUNT, key_pattern("amount")), (K_CURRENCY, key_pattern("currency")),
        (K_TAGS, key_pattern("tags")), (K_META, key_pattern("meta"))]
CHANNEL_PAT = key_pattern("channel")


def u64_view(a):
    """Unaligned view: element i is the little-endian uint64 of bytes a[i:i+8]."""
    return np.ndarray(shape=(a.size - 7,), dtype="<u8", buffer=a, strides=(1,))


MASK8 = np.array([(1 << (8 * n)) - 1 for n in range(8)] + [(1 << 64) - 1], np.uint64)


def match_key(k8, klen, pat):
    val, mask, n = pat
    return ((k8 & mask) == val) & (klen == n)


def pack_strings(a, s, e, width):
    """Zero-padded (n, width) byte matrix of a[s:e] spans (width a multiple of 8)."""
    if width == 8:
        w = u64_view(a)[s] & MASK8[e - s]
        return w.view(np.uint8).reshape(-1, 8)
    pos = s[:, None] + np.arange(width)
    m = a[np.minimum(pos, a.size - 1)]
    m[pos >= e[:, None]] = 0
    return m


def group_strings(a, s, e):
    """Group byte spans: returns (list of bytes keys, inverse index)."""
    width = int((e - s).max()) if s.size else 1
    width = max(8, (width + 7) // 8 * 8)
    m = pack_strings(a, s, e, width)
    words = m.view(np.uint64)
    if width == 8:
        uniq, first, inv = np.unique(words[:, 0], return_index=True, return_inverse=True)
    else:
        h = words[:, 0].copy()
        for j in range(1, words.shape[1]):
            h = (h * np.uint64(0x9E3779B97F4A7C15)) ^ words[:, j]
        uniq, first, inv = np.unique(h, return_index=True, return_inverse=True)
        if not np.array_equal(words[first[inv]], words):  # hash collision: exact grouping
            sv = m.view(f"S{width}").ravel()
            uniq, first, inv = np.unique(sv, return_index=True, return_inverse=True)
    keys = m[first].view(f"S{width}").ravel().tolist()
    return keys, inv.ravel()


class Ledger:
    def __init__(self, rates):
        self.rates = {k.encode(): v for k, v in rates.items()}
        self.accounts = {}
        self.channels = {}
        self.counted = 0
        self.net = 0
        names = sorted(self.rates)
        self.cur_width = max(8, (max(len(n) for n in names) + 7) // 8 * 8)
        mat = np.zeros((len(names), self.cur_width), np.uint8)
        for i, n in enumerate(names):
            mat[i, :len(n)] = np.frombuffer(n, np.uint8)
        self.cur_words = mat.view(np.uint64)
        self.cur_rates = np.array([self.rates[n] for n in names], np.int64)
        if self.cur_width == 8:
            order = np.argsort(self.cur_words[:, 0])
            self.cur_sorted = self.cur_words[order, 0]
            self.cur_rates_sorted = self.cur_rates[order]

    def add_slow(self, text):
        d = json.loads(text)
        t = d["type"]
        if t == "void" or "test" in d["tags"]:
            return
        amt = d["amount"]
        ip, _, fp = amt.partition(".")
        h = int(ip) * 100 + (int(fp) * (10 if len(fp) == 1 else 1) if fp else 0)
        v = h * self.rates[d["currency"].encode()] // 1000000
        if t == "debit":
            v = -v
        self.counted += 1
        self.net += v
        acct = d["account"].encode()
        self.accounts[acct] = self.accounts.get(acct, 0) + v
        ch = d["meta"]["channel"].encode()
        cv = self.channels.get(ch)
        if cv is None:
            self.channels[ch] = [1, v]
        else:
            cv[0] += 1
            cv[1] += v

    def lookup_rates(self, a, s, e):
        if self.cur_width == 8:
            w = pack_strings(a, s, e, 8).view(np.uint64).ravel()
            j = np.searchsorted(self.cur_sorted, w)
            j = np.minimum(j, self.cur_sorted.size - 1)
            ok = self.cur_sorted[j] == w
            return self.cur_rates_sorted[j], ok
        w = pack_strings(a, s, e, self.cur_width).view(np.uint64)
        rate = np.zeros(s.size, np.int64)
        ok = np.zeros(s.size, bool)
        for i in range(self.cur_words.shape[0]):
            hit = (w == self.cur_words[i]).all(axis=1)
            rate[hit] = self.cur_rates[i]
            ok |= hit
        return rate, ok

    def chunk(self, data):
        n_data = len(data)
        a = np.frombuffer(data + PAD, np.uint8)
        gather8_ = u64_view(a).__getitem__
        cls = CLS[a[:n_data]]
        idx = np.flatnonzero(cls)
        c = cls[idx]
        ne = idx.size

        # Escapes: a backslash at an even offset within its run escapes the next byte.
        bsk = np.flatnonzero(c == BSLASH)
        if bsk.size:
            pb = idx[bsk]
            cont = np.zeros(bsk.size, bool)
            cont[1:] = pb[1:] == pb[:-1] + 1
            ar = np.arange(bsk.size)
            run_start = np.maximum.accumulate(np.where(cont, 0, ar))
            esc = bsk[((ar - run_start) & 1) == 0]
            nxt = esc + 1
            nxt = nxt[nxt < ne]
            hit = nxt[idx[nxt] == idx[nxt - 1] + 1]
            c[hit] = 0  # escaped char is not structural (marks the string as "dirty")

        q = c == QUOTE
        # Parity of quotes before each entry (uint8 wraps but keeps parity).
        par = np.cumsum(q, dtype=np.uint8)
        par -= q
        par &= 1
        code = c << 1
        code |= par
        del par, q
        depth = np.cumsum(DELTA[code], dtype=np.int32)
        X = depth << 4
        X |= code
        del depth

        rec_start = np.flatnonzero(X == X_REC_START)
        rec_end = np.flatnonzero(X == X_REC_END)
        R = rec_start.size
        if R == 0:
            return
        bad = np.zeros(R, bool)
        rs_pos = idx[rec_start]
        re_pos = idx[rec_end]

        # Top-level keys.
        k1 = np.flatnonzero(X == X_COLON1)
        k1rec = np.repeat(np.arange(R), np.diff(np.searchsorted(k1, rec_start), append=k1.size))
        clean_key = (c[k1 - 1] == QUOTE) & (c[k1 - 2] == QUOTE)
        bad[k1rec[~clean_key]] = True
        kstart = idx[k1 - 2] + 1
        klen = idx[k1 - 1] - kstart
        k8 = gather8_(kstart)
        kid = np.zeros(k1.size, np.int8)
        for kv, pat in KEYS:
            kid[match_key(k8, klen, pat)] = kv
        kid[~clean_key] = 0

        # Each wanted key exactly once per record; string values must be escape-free.
        vk = np.minimum(k1 + 2, ne - 1)
        str_clean = (c[np.minimum(k1 + 1, ne - 1)] == QUOTE) & (c[vk] == QUOTE)
        vals = {}
        for kv in (K_ACCOUNT, K_TYPE, K_AMOUNT, K_CURRENCY, K_TAGS, K_META):
            sel = np.flatnonzero(kid == kv)
            cnt = np.bincount(k1rec[sel], minlength=R)
            bad |= cnt != 1
            if kv not in (K_TAGS, K_META):
                bad[k1rec[sel[~str_clean[sel]]]] = True
            vals[kv] = sel  # indices into k1; for good records one per record, in record order

        # Tag elements: opening quotes at depth 2 owned by a "tags" key.
        oq = np.flatnonzero(X == X_OPENQ2)
        owner = np.searchsorted(k1, oq) - 1
        oq = oq[kid[owner] == K_TAGS]
        orec = np.searchsorted(rec_start, oq) - 1
        tclean = c[np.minimum(oq + 1, ne - 1)] == QUOTE
        bad[orec[~tclean]] = True
        ts = idx[oq] + 1
        te = idx[np.minimum(oq + 1, ne - 1)]
        is_test = tclean & (te - ts == 4) & (gather8_(ts) & np.uint64(0xFFFFFFFF) == np.uint64(0x74736574))
        has_test = np.zeros(R, bool)
        has_test[orec[is_test]] = True

        # meta.channel: depth-2 colons owned by a "meta" key.
        k2 = np.flatnonzero(X == X_COLON2)
        owner = np.searchsorted(k1, k2) - 1
        k2 = k2[kid[owner] == K_META]
        k2rec = np.searchsorted(rec_start, k2) - 1
        clean2 = (c[k2 - 1] == QUOTE) & (c[k2 - 2] == QUOTE)
        bad[k2rec[~clean2]] = True
        k2s = idx[k2 - 2] + 1
        is_ch = clean2 & match_key(gather8_(k2s), idx[k2 - 1] - k2s, CHANNEL_PAT)
        ch_sel = k2[is_ch]
        ch_rec = k2rec[is_ch]
        bad |= np.bincount(ch_rec, minlength=R) != 1
        ch_clean = (c[np.minimum(ch_sel + 1, ne - 1)] == QUOTE) & (c[np.minimum(ch_sel + 2, ne - 1)] == QUOTE)
        bad[ch_rec[~ch_clean]] = True

        good = ~bad
        ng = int(good.sum())

        def str_spans(kv):
            sel = vals[kv]
            sel = sel[good[k1rec[sel]]]
            kk = k1[sel]
            return idx[kk + 1] + 1, idx[kk + 2]

        if ng:
            # type / tags filter
            ts_, _ = str_spans(K_TYPE)
            t0 = a[ts_]
            keep = (t0 != ord("v")) & ~has_test[good]
            sign = np.where(t0 == ord("d"), -1, 1).astype(np.int64)

            # amount -> hundredths
            s, e = str_spans(K_AMOUNT)
            ln = e - s
            too_long = ln > 18
            if too_long.any():
                gidx = np.flatnonzero(good)
                bad[gidx[too_long]] = True
                keep &= ~too_long
            W = 19
            pos = s[:, None] + np.arange(W)
            valid = pos < e[:, None]
            ch = a[np.minimum(pos, a.size - 1)]
            isdot = (ch == ord(".")) & valid
            hasdot = isdot.any(axis=1)
            dotpos = np.where(hasdot, s + isdot.argmax(axis=1), -1)
            fraclen = np.where(hasdot, e - dotpos - 1, 0)
            place = (e[:, None] - 1 - pos) - (pos < dotpos[:, None])
            dig = valid & ~isdot
            place = np.where(dig, place, 0)
            digits = np.where(dig, ch.astype(np.int64) - 48, 0)
            num = (digits * POW10[np.clip(place, 0, 18)]).sum(axis=1)
            hund = num * np.array([100, 10, 1], np.int64)[np.clip(fraclen, 0, 2)]

            s, e = str_spans(K_CURRENCY)
            rate, ok = self.lookup_rates(a, s, e)
            if not ok.all():
                raise KeyError("unknown currency")
            v = (hund * rate) // 1000000 * sign

            keep_idx = np.flatnonzero(keep)
            v = v[keep_idx]
            self.counted += int(keep_idx.size)
            self.net += int(v.sum())

            s, e = str_spans(K_ACCOUNT)
            keys, inv = group_strings(a, s[keep_idx], e[keep_idx])
            sums = np.zeros(len(keys), np.int64)
            np.add.at(sums, inv, v)
            acc = self.accounts
            for k, sv in zip(keys, sums.tolist()):
                acc[k] = acc.get(k, 0) + sv

            cg = good[ch_rec]
            cs = ch_sel[cg]
            s = idx[cs + 1] + 1
            e = idx[cs + 2]
            keys, inv = group_strings(a, s[keep_idx], e[keep_idx])
            cnts = np.bincount(inv, minlength=len(keys))
            sums = np.zeros(len(keys), np.int64)
            np.add.at(sums, inv, v)
            chans = self.channels
            for k, cn, sv in zip(keys, cnts.tolist(), sums.tolist()):
                cv = chans.get(k)
                if cv is None:
                    chans[k] = [cn, sv]
                else:
                    cv[0] += cn
                    cv[1] += sv

        for r in np.flatnonzero(bad).tolist():
            self.add_slow(data[rs_pos[r]:re_pos[r] + 1].decode("utf-8"))


def main():
    path = sys.argv[1]
    with open(path, "rb", buffering=0) as f:
        first = b""
        rest = b""
        while True:
            blk = f.read(1 << 16)
            if not blk:
                first = rest
                rest = b""
                break
            rest += blk
            nl = rest.find(b"\n")
            if nl >= 0:
                first, rest = rest[:nl], rest[nl + 1:]
                break
        led = Ledger(json.loads(first)["rates"])
        while True:
            blk = f.read(CHUNK)
            if not blk:
                if rest.strip():
                    led.chunk(rest)
                break
            data = rest + blk
            nl = data.rfind(b"\n")
            if nl < 0:
                rest = data
                continue
            rest = data[nl + 1:]
            led.chunk(data[:nl + 1])

    out = [f"counted {led.counted}", f"net {led.net}"]
    for ch in sorted(led.channels):
        cn, sv = led.channels[ch]
        out.append(f"channel {ch.decode()} {cn} {sv}")
    top = sorted(led.accounts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for acct, sv in top:
        out.append(f"account {acct.decode()} {sv}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


main()
