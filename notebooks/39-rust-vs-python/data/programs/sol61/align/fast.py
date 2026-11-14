"""Weighted alignment using NumPy row operations and prefix maxima.

Subtract maximum order-preserving substitution savings from the cost of
deleting the entire source and inserting the entire target.
"""

import os
import sys

# All array operations below are single-threaded; also constrain BLAS backends.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np


def alignment(source, target, gain, baseline):
    # Fewer rows mean fewer Python-to-NumPy calls. Columns run in native code.
    if len(source) > len(target):
        source, target = target, source
        gain = gain.T
    dtype = np.int32 if baseline <= 2147483647 else np.int64
    columns = np.frombuffer(target, dtype=np.uint8)
    profiles = np.ascontiguousarray(gain[:, columns], dtype=dtype)
    previous = np.zeros(len(target) + 1, dtype=dtype)
    current = np.empty_like(previous)
    diagonal = previous[:-1]
    above = previous[1:]
    result = current[1:]
    add = np.add
    maximum = np.maximum
    accumulate = maximum.accumulate
    # Swapping views along with buffers avoids creating slices per row.
    other_diagonal = current[:-1]
    for c in source:
        add(diagonal, profiles[c], out=result)
        maximum(result, above, out=result)
        current[0] = 0
        accumulate(current, out=current)
        previous, current = current, previous
        diagonal, other_diagonal = other_diagonal, diagonal
        above, result = result, above
    return int(previous[-1])


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
        gain = np.array([
            [delete[i] + insert[j] - cost for j, cost in enumerate(
                map(int, stream.readline().split())
            )]
            for i in range(size)
        ], dtype=np.int64)
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
