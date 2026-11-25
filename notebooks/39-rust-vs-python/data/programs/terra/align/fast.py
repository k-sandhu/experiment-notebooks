import sys
import numpy as np


def main():
    data = open(sys.argv[1], 'rb').read().split()
    alphabet = data[0]
    a = len(alphabet)
    pos = 1
    ins = np.array(data[pos:pos+a], dtype=np.int64); pos += a
    delete = np.array(data[pos:pos+a], dtype=np.int64); pos += a
    sub = np.array(data[pos:pos+a*a], dtype=np.int64).reshape(a, a); pos += a*a
    p = int(data[pos]); pos += 1
    lookup = np.zeros(256, dtype=np.uint8)
    lookup[np.frombuffer(alphabet, dtype=np.uint8)] = np.arange(a, dtype=np.uint8)
    results = []
    total = 0
    for _ in range(p):
        s, t = data[pos], data[pos+1]; pos += 2
        if len(t) > len(s):
            s, t = t, s
            row_cost, col_cost, matrix = ins, delete, sub.T
        else:
            row_cost, col_cost, matrix = delete, ins, sub
        si = lookup[np.frombuffer(s, dtype=np.uint8)]
        ti = lookup[np.frombuffer(t, dtype=np.uint8)]
        prefix = np.empty(len(ti) + 1, dtype=np.int64)
        prefix[0] = 0
        np.cumsum(col_cost[ti], out=prefix[1:])
        prev = prefix.copy()
        subs = matrix[:, ti]
        candidate = np.empty(len(ti) + 1, dtype=np.int64)
        for c in si:
            d = row_cost[c]
            candidate[0] = prev[0] + d
            np.add(prev[1:], d, out=candidate[1:])
            np.minimum(candidate[1:], prev[:-1] + subs[c], out=candidate[1:])
            np.subtract(candidate, prefix, out=candidate)
            np.minimum.accumulate(candidate, out=candidate)
            np.add(candidate, prefix, out=prev)
        result = int(prev[-1])
        results.append(str(result))
        total += result
    sys.stdout.write('\n'.join(results + ['total ' + str(total)]) + '\n')


if __name__ == '__main__':
    main()
