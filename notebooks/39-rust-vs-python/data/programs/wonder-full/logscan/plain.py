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


def main():
    lines = 0
    malformed = 0
    status = [0] * 10
    templates = {}          # template -> list of latencies (tenths of ms)
    templates_get = templates.get
    path_cache = {}         # raw path -> template, only for digit-free paths
    path_cache_get = path_cache.get
    lat_cache = {}          # latency token -> tenths
    lat_cache_get = lat_cache.get
    good_ts = b""
    good_host = b""
    good_size = b""
    good_ua = b""
    methods = METHODS
    status_get = STATUS.get
    digit_table = DIGIT_TABLE
    ts_canon = TS_CANON
    path_chars = PATH_CHARS
    id_seg = ID

    with open(sys.argv[1], "rb", buffering=1024 * 1024) as f:
        for raw in f:
            lines += 1
            try:
                ts, host, method, url, st, size, lat_tok, ua = \
                    raw.split(b" ", 7)
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
            sclass = status_get(st)
            if sclass is None:
                malformed += 1
                continue
            if size != good_size:
                if len(size) < 2 or size[-1] != 66 or not size[:-1].isdigit():
                    malformed += 1
                    continue
                good_size = size

            lat = lat_cache_get(lat_tok)
            if lat is None:
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

            # ua still carries the trailing newline (except possibly at EOF).
            if ua != good_ua:
                if len(ua) < 2 or ua[0] != 34:
                    malformed += 1
                    continue
                q = ua.find(b'"', 1)
                if q != len(ua) - 1 and not (q == len(ua) - 2
                                             and ua[-1] == 10):
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
            lst = templates_get(template)
            if lst is None:
                templates[template] = [lat]
            else:
                lst.append(lat)

    out = [f"lines {lines}", f"malformed {malformed}"]
    ap = out.append
    for d in range(10):
        c = status[d]
        if c:
            ap(f"status {d}xx {c}")
    top = sorted(templates.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:10]
    for template, lats in top:
        lats.sort()
        n = len(lats)
        p50 = lats[(50 * n + 99) // 100 - 1]
        p95 = lats[(95 * n + 99) // 100 - 1]
        mx = lats[-1]
        ap(f"path {template.decode()} {n} "
           f"{p50 // 10}.{p50 % 10} {p95 // 10}.{p95 % 10} {mx // 10}.{mx % 10}")
    sys.stdout.buffer.write(("\n".join(out) + "\n").encode())


if __name__ == "__main__":
    main()
