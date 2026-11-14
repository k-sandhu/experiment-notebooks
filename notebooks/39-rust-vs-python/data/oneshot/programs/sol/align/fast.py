import sys
import numpy as np


def main():
    with open(sys.argv[1], "rb") as f:
        tokens = f.read().split()

    alphabet = tokens[0]
    size = len(alphabet)
    translation = bytes.maketrans(alphabet, bytes(range(size)))

    pos = 1
    insertion = np.array(tokens[pos:pos + size], dtype=np.int32)
    pos += size
    deletion = np.array(tokens[pos:pos + size], dtype=np.int32)
    pos += size
    substitution = np.array(
        tokens[pos:pos + size * size], dtype=np.int32
    ).reshape(size, size)
    pos += size * size

    rewards = deletion[:, None] + insertion[None, :] - substitution
    reversed_rewards = rewards.T

    pairs = int(tokens[pos])
    pos += 1

    add = np.add
    maximum = np.maximum
    accumulate = maximum.accumulate
    frombuffer = np.frombuffer

    output = []
    total = 0

    for _ in range(pairs):
        s = tokens[pos]
        t = tokens[pos + 1]
        pos += 2

        if s == t:
            answer = 0
        elif size == 1:
            difference = len(t) - len(s)
            if difference >= 0:
                answer = difference * int(insertion[0])
            else:
                answer = -difference * int(deletion[0])
        else:
            if len(s) > len(t):
                s, t = t, s
                dc, ic = insertion, deletion
                matrix = reversed_rewards
            else:
                dc, ic = deletion, insertion
                matrix = rewards

            source = s.translate(translation)
            target = t.translate(translation)
            source_indices = frombuffer(source, dtype=np.uint8)
            target_indices = frombuffer(target, dtype=np.uint8)

            baseline = (
                int(dc[source_indices].sum(dtype=np.int64))
                + int(ic[target_indices].sum(dtype=np.int64))
            )

            if baseline == 0:
                answer = 0
            else:
                weights = list(np.take(matrix, target_indices, axis=1))
                dtype = np.int32 if len(source) <= 1_073_741 else np.int64

                row = np.zeros(len(target) + 1, dtype=dtype)
                previous_diagonal = row[:-1]
                values = row[1:]
                temporary = np.empty(len(target), dtype=dtype)

                # Store cumulative deletion/insertion cost minus D.
                for letter in source:
                    add(previous_diagonal, weights[letter], out=temporary)
                    maximum(values, temporary, out=values)
                    accumulate(values, out=values)

                answer = baseline - int(row[-1])

        output.append(str(answer))
        total += answer

    output.append("total " + str(total))
    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
