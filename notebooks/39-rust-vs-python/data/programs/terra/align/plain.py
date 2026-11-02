import sys


def main():
    data = open(sys.argv[1], 'rb').read().split()
    alphabet = data[0]
    a = len(alphabet)
    pos = 1
    ins = list(map(int, data[pos:pos+a])); pos += a
    delete = list(map(int, data[pos:pos+a])); pos += a
    sub = []
    for _ in range(a):
        sub.append(list(map(int, data[pos:pos+a])))
        pos += a
    p = int(data[pos]); pos += 1
    lookup = [0] * 256
    for i, c in enumerate(alphabet):
        lookup[c] = i
    results = []
    total = 0
    for _ in range(p):
        s, t = data[pos], data[pos+1]; pos += 2
        # Transposition exchanges insertions and deletions and reverses substitutions.
        if len(t) > len(s):
            s, t = t, s
            row_cost, col_cost = ins, delete
            matrix = [list(x) for x in zip(*sub)]
        else:
            row_cost, col_cost, matrix = delete, ins, sub
        si = [lookup[c] for c in s]
        ti = [lookup[c] for c in t]
        costs = [col_cost[c] for c in ti]
        prev = [0]
        v = 0
        for c in costs:
            v += c
            prev.append(v)
        # Precompute substitution costs for all possible row characters.
        subs = [[row[c] for c in ti] for row in matrix]
        for c in si:
            d = row_cost[c]
            diagonal = prev[0]
            left = diagonal + d
            prev[0] = left
            sr = subs[c]
            for j in range(len(ti)):
                above = prev[j+1]
                x = above + d
                y = diagonal + sr[j]
                if y < x: x = y
                y = left + costs[j]
                if y < x: x = y
                prev[j+1] = left = x
                diagonal = above
        result = prev[-1]
        results.append(str(result))
        total += result
    sys.stdout.write('\n'.join(results + ['total ' + str(total)]) + '\n')


if __name__ == '__main__':
    main()
