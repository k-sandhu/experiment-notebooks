import sys


def alignment_cost(s, t, insertion, deletion, weights, transposed):
    if s == t:
        return 0

    baseline = sum(deletion[c] for c in s) + sum(insertion[c] for c in t)
    if baseline == 0:
        return 0

    if len(t) > len(s):
        s, t = t, s
        weights = transposed

    target_letters = set(t)
    patterns = [()] * len(weights)

    for c in set(s):
        row = weights[c]
        if any(row[k] for k in target_letters):
            patterns[c] = [(j, row[k]) for j, k in enumerate(t)]

    dp = [0] * len(t)

    for c in s:
        diagonal = 0
        left = 0

        for j, weight in patterns[c]:
            above = dp[j]
            candidate = diagonal + weight

            if above > left:
                left = above
            if candidate > left:
                left = candidate

            dp[j] = left
            diagonal = above

    return baseline - dp[-1]


def main():
    with open(sys.argv[1], "rb") as file:
        tokens = iter(file.read().split())

    alphabet = next(tokens)
    size = len(alphabet)

    insertion = [int(next(tokens)) for _ in range(size)]
    deletion = [int(next(tokens)) for _ in range(size)]

    # Savings relative to deleting the source and inserting the target.
    weights = []
    for i in range(size):
        delete_cost = deletion[i]
        row = []
        for j in range(size):
            substitution = int(next(tokens))
            saving = delete_cost + insertion[j] - substitution
            row.append(saving if saving > 0 else 0)
        weights.append(row)

    transposed = list(zip(*weights))

    translation = bytearray(range(256))
    for i, letter in enumerate(alphabet):
        translation[letter] = i
    translation = bytes(translation)

    pair_count = int(next(tokens))
    output = []
    total = 0

    for _ in range(pair_count):
        s = next(tokens).translate(translation)
        t = next(tokens).translate(translation)

        cost = alignment_cost(
            s, t, insertion, deletion, weights, transposed
        )
        output.append(str(cost))
        total += cost

    output.append("total " + str(total))
    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
