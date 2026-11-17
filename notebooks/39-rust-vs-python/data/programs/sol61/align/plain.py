"""Weighted alignment with parallel integer fields for large rolling rows.

Subtract maximum order-preserving substitution savings from the cost of
deleting the entire source and inserting the entire target.
"""

import sys


def scalar_savings(source, target, gain):
    # Keep the rolling row on the shorter dimension.
    if len(source) < len(target):
        source, target = target, source
        gain = tuple(zip(*gain))

    width = len(target)
    profiles = [[weights[c] for c in target] for weights in gain]
    row = [0] * (width + 1)
    for c in source:
        diagonal = 0
        left = 0
        for j, weight in enumerate(profiles[c], 1):
            above = row[j]
            candidate = diagonal + weight
            if above > left:
                left = above
            if candidate > left:
                left = candidate
            row[j] = left
            diagonal = above
    return row[width]


def alignment(source, target, gain, baseline):
    if len(source) * len(target) < 4096 or min(len(source), len(target)) < 8:
        return scalar_savings(source, target, gain)
    # Big integers process an entire row in native code. Minimize row count.
    if len(source) > len(target):
        source, target = target, source
        gain = tuple(zip(*gain))
    width = len(target)
    # Each unsigned field has a guard bit above every possible DP score.
    field_bytes = max(2, (baseline.bit_length() + 8) // 8)
    bits = field_bytes * 8
    guard_shift = bits - 1
    mask = (1 << (width * bits)) - 1
    guards = (mask // ((1 << bits) - 1)) << guard_shift

    # Gains are at most 2000, so two byte planes suffice. Translation and
    # strided bytearray assignment build profiles without per-column loops.
    profiles = []
    encoded = bytearray(width * field_bytes)
    for weights in gain:
        # A nonpositive gain cannot improve on leaving both letters unmatched.
        positive = [max(0, w) for w in weights]
        low = bytes([w & 255 for w in positive] + [0] * (256 - len(weights)))
        high = bytes([w >> 8 for w in positive] + [0] * (256 - len(weights)))
        encoded[0::field_bytes] = target.translate(low)
        encoded[1::field_bytes] = target.translate(high)
        profiles.append(int.from_bytes(encoded, "little"))

    shifts = [bits * (1 << k) for k in range((width - 1).bit_length())]
    previous = 0
    for c in source:
        candidate = ((previous << bits) & mask) + profiles[c]
        # Guarded subtraction compares all fields independently, without
        # borrows crossing field boundaries. Expand comparison bits to masks.
        comparison = ((candidate | guards) - previous) & guards
        selection = comparison - (comparison >> guard_shift)
        row = previous ^ ((candidate ^ previous) & selection)
        # Inclusive prefix maximum, doubling the covered interval each step.
        for shift in shifts:
            other = (row << shift) & mask
            comparison = ((row | guards) - other) & guards
            if comparison == guards:
                break
            selection = comparison - (comparison >> guard_shift)
            row = other ^ ((row ^ other) & selection)
        previous = row
    return previous >> (bits * (width - 1))


def main():
    output = []
    total = 0
    with open(sys.argv[1], "rb") as stream:
        alphabet = stream.readline().strip()
        size = len(alphabet)
        translation = bytearray(256)
        for i, c in enumerate(alphabet):
            translation[c] = i
        translation = bytes(translation)
        insert = list(map(int, stream.readline().split()))
        delete = list(map(int, stream.readline().split()))
        gain = [
            [delete[i] + insert[j] - cost for j, cost in enumerate(
                map(int, stream.readline().split())
            )]
            for i in range(size)
        ]
        for _ in range(int(stream.readline())):
            source, target = stream.readline().split()
            if source == target:
                cost = 0
            else:
                source = source.translate(translation)
                target = target.translate(translation)
                baseline = sum(map(delete.__getitem__, source)) + sum(
                    map(insert.__getitem__, target)
                )
                cost = baseline - alignment(source, target, gain, baseline) if baseline else 0
            total += cost
            output.append(str(cost))
    output.append(f"total {total}")
    sys.stdout.buffer.write(("\n".join(output) + "\n").encode("ascii"))


if __name__ == "__main__":
    main()
