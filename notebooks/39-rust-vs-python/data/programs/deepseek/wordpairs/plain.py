import re
import sys


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read()

    # Letters are lowercased; sentence punctuation is padded with spaces so it
    # becomes its own token; every other byte becomes a word separator (space).
    marked = re.sub(rb"([.!?])", rb" \1 ", data)
    del data

    tbl = bytearray(256)
    for c in range(256):
        if 65 <= c <= 90:
            tbl[c] = c + 32
        elif 97 <= c <= 122:
            tbl[c] = c
        else:
            tbl[c] = 32
    tbl[0x2E] = 0x2E  # .
    tbl[0x21] = 0x21  # !
    tbl[0x3F] = 0x3F  # ?

    tokens = marked.translate(bytes(tbl)).split()
    del marked

    ids = {}
    counts = {}
    get_count = counts.get

    words = 0
    total_pairs = 0
    prev = -1

    ids_get = ids.get
    for t in tokens:
        if t[0] < 65:  # punctuation token, a sentence ends here
            prev = -1
            continue
        words += 1
        wid = ids_get(t)
        if wid is None:
            wid = len(ids)
            ids[t] = wid
        if prev >= 0:
            key = (prev << 32) | wid
            counts[key] = get_count(key, 0) + 1
            total_pairs += 1
        prev = wid
    del tokens

    id_word = [b""] * len(ids)
    for w, i in ids.items():
        id_word[i] = w

    best = []
    worst_count = 0
    worst_a = b""
    worst_b = b""
    for key, c in counts.items():
        a = id_word[key >> 32]
        b = id_word[key & 0xFFFFFFFF]
        if len(best) < 20:
            best.append((c, a, b))
            if len(best) == 20:
                best.sort(key=lambda x: (-x[0], x[1], x[2]))
                worst_count, worst_a, worst_b = best[19]
        else:
            if c < worst_count:
                continue
            if c == worst_count:
                if a > worst_a or (a == worst_a and b >= worst_b):
                    continue
            best.append((c, a, b))
            best.sort(key=lambda x: (-x[0], x[1], x[2]))
            best.pop()
            worst_count, worst_a, worst_b = best[19]

    if len(best) < 20:
        best.sort(key=lambda x: (-x[0], x[1], x[2]))

    out = [
        b"words %d\n" % words,
        b"pairs %d\n" % total_pairs,
        b"distinct %d\n" % len(counts),
    ]
    for c, a, b in best:
        out.append(b"%d %s %s\n" % (c, a, b))
    sys.stdout.buffer.write(b"".join(out))


if __name__ == "__main__":
    main()
