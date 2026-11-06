import sys

METHODS = {b"GET", b"POST", b"PUT", b"DELETE", b"PATCH"}
# Maps every ASCII digit to '0', every other byte to itself.  A timestamp
# translates to TS_CANON iff it has digits and separators in the right places.
DIGIT_TABLE = bytes(48 if 48 <= i <= 57 else i for i in range(256))
TS_CANON = b"0000-00-00T00:00:00.000Z"
PATH_CHARS = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_/-"
ID = b"{id}"
# Every valid 3-digit status token -> its class digit; anything else misses.
STATUS = {f"{i:03d}".encode(): i // 100 for i in range(1000)}


def order_stats(lats_list, np_mod):
    """(p50, p95, max) by the nearest-rank method, via NumPy when given."""
    n = len(lats_list)
    i50 = (50 * n + 99) // 100 - 1
    i95 = (95 * n + 99) // 100 - 1
    if np_mod is not None:
        try:
            arr = np_mod.asarray(lats_list, dtype=np_mod.int64)
        except OverflowError:
            pass
        else:
            arr.sort()
            return int(arr[i50]), int(arr[i95]), int(arr[-1])
    lats_list.sort()
    return lats_list[i50], lats_list[i95], lats_list[-1]


def main():
    malformed = 0
    status = [0] * 10
    templates = {}          # template -> list of latencies (tenths of ms)
    path_cache = {}         # raw path -> template, only for digit-free paths
    path_cache_get = path_cache.get
    lat_cache = {}          # latency token -> tenths
    good_ts = b""
    good_host = b""
    good_size = b""
    good_ua = b""
    methods = METHODS
    status_tbl = STATUS
    digit_table = DIGIT_TABLE
    ts_canon = TS_CANON
    path_chars = PATH_CHARS
    id_seg = ID

    # Read and split the whole file in C instead of iterating the file.
    with open(sys.argv[1], "rb") as f:
        data = f.read()
    raw_lines = data.split(b"\n")
    del data
    if raw_lines and raw_lines[-1] == b"":
        # Artifact of the final newline (or an empty file), not a line.
        del raw_lines[-1]
    lines = len(raw_lines)

    for raw in raw_lines:
        try:
            ts, host, method, url, st, size, lat_tok, ua = raw.split(b" ", 7)
        except ValueError:
            malformed += 1
            continue

        if method != b"GET" and method not in methods:
            malformed += 1
            continue
        if ts != good_ts:
            if ts.translate(digit_table) != ts_canon:
                malformed += 1
                continue
            good_ts = ts
        if host != good_host:
            name, sep, num = host.partition(b"-")
            if not sep or not name.isalpha() or not name.islower() \
                    or not num.isdigit():
                malformed += 1
                continue
            good_host = host
        try:
            sclass = status_tbl[st]
        except KeyError:
            malformed += 1
            continue
        if size != good_size:
            if len(size) < 2 or size[-1] != 66 or not size[:-1].isdigit():
                malformed += 1
                continue
            good_size = size

        try:
            lat = lat_cache[lat_tok]
        except KeyError:
            if not lat_tok.endswith(b"ms"):
                malformed += 1
                continue
            whole, dot, frac = lat_tok[:-2].partition(b".")
            if not dot or len(frac) != 1 or not whole.isdigit() \
                    or not frac.isdigit():
                malformed += 1
                continue
            lat = int(whole) * 10 + frac[0] - 48
            lat_cache[lat_tok] = lat

        if ua != good_ua:
            if len(ua) < 2 or ua[0] != 34 \
                    or ua.find(b'"', 1) != len(ua) - 1:
                malformed += 1
                continue
            good_ua = ua

        path = url.partition(b"?")[0]
        if not path.startswith(b"/"):
            malformed += 1
            continue
        template = path_cache_get(path)
        if template is None:
            if path.translate(None, path_chars):
                malformed += 1
                continue
            segs = [id_seg if seg.isdigit() else seg
                    for seg in path.split(b"/")]
            if id_seg in segs:
                template = b"/".join(segs)
            else:
                template = path
                path_cache[path] = path

        status[sclass] += 1
        try:
            templates[template].append(lat)
        except KeyError:
            templates[template] = [lat]

    out = [f"lines {lines}", f"malformed {malformed}"]
    ap = out.append
    for d in range(10):
        c = status[d]
        if c:
            ap(f"status {d}xx {c}")
    top = sorted(templates.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:10]
    # Importing NumPy takes ~0.3 s; its faster int64 sort only repays that
    # when the top-10 lists hold well over a million latencies in total.
    np_mod = None
    if sum(len(v) for _, v in top) >= 1_500_000:
        import numpy as np_mod
    for template, lats_list in top:
        n = len(lats_list)
        p50, p95, mx = order_stats(lats_list, np_mod)
        ap(f"path {template.decode()} {n} "
           f"{p50 // 10}.{p50 % 10} {p95 // 10}.{p95 % 10} {mx // 10}.{mx % 10}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


if __name__ == "__main__":
    main()
