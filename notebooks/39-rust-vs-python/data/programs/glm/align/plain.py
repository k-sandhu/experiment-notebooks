import sys
from itertools import accumulate, chain, islice, repeat
from operator import add, sub


def solve(s, t, idx, ins, dele, sub):
    """Weighted edit distance.

    The sequential dependency cur[j-1] -> cur[j] in the DP row is unrolled
    into a prefix-sum plus a running minimum:

        cur[j] = min_{k<=j} ( G[k] + ins[t_{k+1}] + ... + ins[t_j] )
               = pin[j] + min_{k<=j} ( G[k] - pin[k] )

    where G[k] = min(prev[k] + del, prev[k-1] + sub) (G[0] = prev[0] + del).
    Every per-cell step then runs inside C-level map()/accumulate() calls.
    """
    m = len(t)
    tidx = [idx[b] for b in t]
    insrow = [ins[k] for k in tidx]
    pin = list(accumulate(insrow, initial=0))
    pin1 = pin[1:]
    subrows = {}
    prev = pin[:]  # row 0
    for b in s:
        k = idx[b]
        d = dele[k]
        sr = subrows.get(k)
        if sr is None:
            row = sub[k]
            sr = [row[j] for j in tidx]
            subrows[k] = sr
        # G_j = min(prev[j] + d, prev[j-1] + sr[j-1]) for j = 1..m
        g = map(
            min,
            map(add, islice(prev, 1, None), repeat(d)),
            map(add, prev, sr),
        )
        # running minimum of (G - pin), seeded with G_0 = prev[0] + d
        rm = accumulate(chain((prev[0] + d,), map(sub, g, pin1)), min)
        prev = list(map(add, rm, pin))
    return prev[-1]


def main():
    data = open(sys.argv[1], "rb").read()
    toks = data.split()
    pos = 0
    # Alphabet: leading tokens made of uppercase ASCII letters; either one
    # concatenated token ("ABC") or A single-letter tokens ("A B C").
    letters = []
    while pos < len(toks) and toks[pos].isalpha():
        letters.append(toks[pos])
        pos += 1
    alpha = b"".join(letters)
    a = len(alpha)
    idx = {ch: i for i, ch in enumerate(alpha)}
    ins = [int(x) for x in toks[pos : pos + a]]
    pos += a
    dele = [int(x) for x in toks[pos : pos + a]]
    pos += a
    sub = [
        [int(x) for x in toks[pos + i * a : pos + (i + 1) * a]] for i in range(a)
    ]
    pos += a * a
    p = int(toks[pos])
    pos += 1

    out = []
    total = 0
    for _ in range(p):
        s = toks[pos]
        t = toks[pos + 1]
        pos += 2
        cost = solve(s, t, idx, ins, dele, sub)
        out.append(str(cost))
        total += cost
    out.append(f"total {total}")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
