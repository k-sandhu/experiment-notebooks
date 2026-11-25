import sys
from itertools import islice


def main() -> None:
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()
    toks = data.split()
    if not toks:
        return
    alphabet = toks[0]
    A = len(alphabet)
    pos = 1
    n_ints = 2 * A + A * A + 1
    nums = list(map(int, islice(toks, pos, pos + n_ints)))
    pos += n_ints
    ins0 = nums[0:A]
    del0 = nums[A:2 * A]
    flat = nums[2 * A:2 * A + A * A]
    sub0 = [flat[i * A:(i + 1) * A] for i in range(A)]
    P = nums[-1]

    # byte -> alphabet index translation table
    trans = bytearray(range(256))
    for i, ch in enumerate(alphabet):
        trans[ch] = i
    table = bytes(trans)

    out_lines = []
    total = 0

    for _ in range(P):
        s_tok = toks[pos]
        t_tok = toks[pos + 1]
        pos += 2
        if s_tok == t_tok:
            out_lines.append("0")
            continue
        s = s_tok.translate(table)
        t = t_tok.translate(table)
        # Choose orientation with the shorter string as columns (t),
        # so the DP rows are as short as possible. Transposing swaps
        # ins<->del and transposes the substitution table; the cost
        # of the pair is unchanged.
        if len(t) > len(s):
            ins_c = del0
            del_c = ins0
            # sub transposed
            sub = [[sub0[j][i] for j in range(A)] for i in range(A)]
            s, t = t, s
        else:
            ins_c = ins0
            del_c = del0
            sub = sub0

        m = len(t)
        n = len(s)
        # Column helpers for t.
        ins_t = [ins_c[c] for c in t]
        # Pc[j] = cost of inserting t[:j]
        Pc = [0] * (m + 1)
        acc = 0
        for j in range(m):
            acc += ins_t[j]
            Pc[j + 1] = acc
        # sub-vector per source letter, built lazily for letters in s.
        subv_cache: dict[int, list[int]] = {}

        prev = Pc  # row 0; Pc itself is never mutated afterwards
        prev = prev[:]
        for i in range(n):
            si = s[i]
            d = del_c[si]
            sv = subv_cache.get(si)
            if sv is None:
                row = sub[si]
                sv = [row[c] for c in t]
                subv_cache[si] = sv
            cur = [0] * (m + 1)
            left = prev[0] + d
            cur[0] = left
            # Inner loop: zip iterates in C; locals are bound tightly.
            for j, (up, dg, ic, sc) in enumerate(
                zip(prev[1:], prev, ins_t, sv), 1
            ):
                v = up + d
                w = dg + sc
                if w < v:
                    v = w
                w = left + ic
                if w < v:
                    v = w
                cur[j] = v
                left = v
            prev = cur
        cost = prev[m]
        total += cost
        out_lines.append(str(cost))

    out_lines.append(f"total {total}")
    sys.stdout.write("\n".join(out_lines) + "\n")


if __name__ == "__main__":
    main()
