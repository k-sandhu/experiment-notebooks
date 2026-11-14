import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        tokens = iter(f.read().split())

    alphabet = next(tokens)
    size = len(alphabet)

    insertion = [int(next(tokens)) for _ in range(size)]
    deletion = [int(next(tokens)) for _ in range(size)]
    substitution = np.fromiter(
        (int(next(tokens)) for _ in range(size * size)),
        dtype=np.int32,
        count=size * size,
    ).reshape(size, size)

    ins = np.array(insertion, dtype=np.int32)
    dele = np.array(deletion, dtype=np.int32)
    gains = dele[:, None] + ins[None, :] - substitution
    transposed_gains = gains.T

    translation = bytes.maketrans(alphabet, bytes(range(size)))
    pair_count = int(next(tokens))

    add = np.add
    maximum = np.maximum
    accumulate = maximum.accumulate

    output = []
    total = 0

    for _ in range(pair_count):
        s = next(tokens)
        t = next(tokens)

        if s == t:
            output.append("0")
            continue

        s = s.translate(translation)
        t = t.translate(translation)

        if len(s) <= len(t):
            matrix = gains
            source_costs = deletion
            target_costs = insertion
        else:
            s, t = t, s
            matrix = transposed_gains
            source_costs = insertion
            target_costs = deletion

        base = (
            sum(map(source_costs.__getitem__, s))
            + sum(map(target_costs.__getitem__, t))
        )

        if base == 0:
            output.append("0")
            continue

        dtype = np.int32 if len(s) <= 1_000_000 else np.int64
        if dtype is np.int64:
            matrix = matrix.astype(np.int64)

        target = np.frombuffer(t, dtype=np.uint8)
        weight_rows = list(matrix.take(target, axis=1))

        previous = np.zeros(len(t) + 1, dtype=dtype)
        diagonal = previous[:-1]
        current = previous[1:]
        work = np.empty(len(t), dtype=dtype)

        # Store the maximum savings relative to deleting and inserting
        # everything. Prefix maxima account for horizontal transitions.
        for letter in s:
            add(diagonal, weight_rows[letter], out=work)
            maximum(current, work, out=current)
            accumulate(current, out=current)

        cost = base - int(previous[-1])
        output.append(str(cost))
        total += cost

    output.append("total " + str(total))
    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
