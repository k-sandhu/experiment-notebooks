import sys


def main():
    with open(sys.argv[1], "rb") as f:
        tokens = iter(f.read().split())

    alphabet = next(tokens)
    size = len(alphabet)

    insertion = [int(next(tokens)) for _ in range(size)]
    deletion = [int(next(tokens)) for _ in range(size)]
    substitution = [
        [int(next(tokens)) for _ in range(size)]
        for _ in range(size)
    ]

    # Removing all letters and inserting the target gives a baseline.
    # An aligned pair saves deletion + insertion - substitution.
    gains = [
        [
            max(0, deletion[i] + insertion[j] - substitution[i][j])
            for j in range(size)
        ]
        for i in range(size)
    ]
    transposed_gains = list(zip(*gains))
    largest_gain = max(map(max, gains))

    translation = bytearray(256)
    for i, letter in enumerate(alphabet):
        translation[letter] = i
    translation = bytes(translation)

    encoded_cache = {}
    output = []
    total = 0
    pair_count = int(next(tokens))

    for _ in range(pair_count):
        raw_s = next(tokens)
        raw_t = next(tokens)

        if raw_s == raw_t:
            output.append("0")
            continue

        s = raw_s.translate(translation)
        t = raw_t.translate(translation)

        baseline = (
            sum(map(deletion.__getitem__, s))
            + sum(map(insertion.__getitem__, t))
        )

        if baseline == 0:
            output.append("0")
            continue

        swapped = len(s) < len(t)
        if swapped:
            s, t = t, s
            weights = transposed_gains
        else:
            weights = gains

        m = len(t)

        if m == 1:
            letter = t[0]
            saving = max(weights[c][letter] for c in s)
        else:
            # Pack independent unsigned lanes into a Python integer.
            # Each lane has a guard bit above every possible DP value.
            upper_bound = min(baseline, m * largest_gain)
            lane_bytes = max(2, (upper_bound.bit_length() + 8) // 8)
            bits = lane_bytes * 8
            guard_shift = bits - 1
            total_bits = bits * m

            cache_key = (lane_bytes, swapped)
            encoded = encoded_cache.get(cache_key)
            if encoded is None:
                encoded = [
                    tuple(value.to_bytes(lane_bytes, "little") for value in row)
                    for row in weights
                ]
                encoded_cache[cache_key] = encoded

            packed_weights = [0] * size
            for c in set(s):
                packed_weights[c] = int.from_bytes(
                    b"".join(map(encoded[c].__getitem__, t)), "little"
                )

            lane_ones = ((1 << total_bits) - 1) // ((1 << bits) - 1)
            guards = lane_ones << guard_shift
            value_mask = guards - lane_ones

            dp = 0
            for c in s:
                scores = packed_weights[c]
                if scores == 0:
                    continue

                diagonal = ((dp << bits) + scores) & value_mask

                # Lane-wise maximum of the previous row and diagonal.
                flags = ((diagonal | guards) - dp) & guards
                selection = flags - (flags >> guard_shift)
                row = dp ^ ((dp ^ diagonal) & selection)

                # Parallel prefix maximum supplies the left transition.
                shift = bits
                while shift < total_bits:
                    shifted = (row << shift) & value_mask
                    flags = ((row | guards) - shifted) & guards
                    selection = flags - (flags >> guard_shift)
                    updated = shifted ^ ((shifted ^ row) & selection)

                    if updated == row:
                        break
                    row = updated
                    shift <<= 1

                dp = row

            saving = dp >> (total_bits - bits)

        cost = baseline - saving
        output.append(str(cost))
        total += cost

    output.append(f"total {total}")
    sys.stdout.write("\n".join(output) + "\n")


if __name__ == "__main__":
    main()
