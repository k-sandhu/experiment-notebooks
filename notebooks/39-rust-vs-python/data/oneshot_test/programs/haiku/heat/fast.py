import sys
import numpy as np


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read()

    parts = data.split()
    H = int(parts[0])
    W = int(parts[1])
    S = int(parts[2])

    # Grid rows contain no whitespace, so whitespace splitting is safe.
    arr = np.frombuffer(b''.join(parts[3:3 + H]), dtype=np.uint8).reshape(H, W)

    wall = arr == 35                      # '#'
    openm = ~wall                         # open cells or sources
    dig = (arr >= 48) & (arr <= 57)       # '1'..'9' (and '0', never present)
    free = (arr == 46).astype(np.int32)   # plain open cells
    fixed = np.where(dig, (arr.astype(np.int32) - 48) * 1000, 0).astype(np.int32)

    # Padded occupancy map (border is zero => outside the grid is not open).
    P = np.zeros((H + 2, W + 2), dtype=np.bool_)
    P[1:-1, 1:-1] = openm

    # valid = number of neighbours that are open or sources.
    # Numerator = 4*old + sum(neighbour or old) = (8 - valid)*old + sum(valid neighbour values).
    valid = np.zeros((H, W), dtype=np.int32)
    valid += P[:-2, 1:-1]
    valid += P[2:, 1:-1]
    valid += P[1:-1, :-2]
    valid += P[1:-1, 2:]
    k = (8 - valid).astype(np.int32)

    # Padded value buffers; walls and border stay 0 forever.
    A = np.zeros((H + 2, W + 2), dtype=np.int32)
    B = np.zeros((H + 2, W + 2), dtype=np.int32)
    A[1:-1, 1:-1] = fixed

    tmp = np.empty((H, W), dtype=np.int32)
    t2 = np.empty((H, W), dtype=np.int32)

    cur, nxt = A, B
    add = np.add
    mul = np.multiply
    for _ in range(S):
        # Sum of the four neighbour values (walls/border are 0).
        add(cur[:-2, 1:-1], cur[2:, 1:-1], out=tmp)
        tmp += cur[1:-1, :-2]
        tmp += cur[1:-1, 2:]
        # (8 - valid) * old + neighbour sum, then floor-divide by 8.
        mul(cur[1:-1, 1:-1], k, out=t2)
        t2 += tmp
        t2 >>= 3
        # Free cells keep the new value; sources get fixed value; walls get 0.
        t2 *= free
        add(t2, fixed, out=nxt[1:-1, 1:-1])
        cur, nxt = nxt, cur

    c = cur[1:-1, 1:-1]
    c64 = c.astype(np.int64)

    T = int(c64.sum())

    masked = np.where(openm, c64, -1).ravel()
    idx = int(np.argmax(masked))
    V = int(masked[idx])
    R = idx // W
    C = idx % W

    ids = np.arange(1, H * W + 1, dtype=np.int64)
    K = int((c64.ravel() * ids).sum())

    sys.stdout.write(f"sum {T}\n")
    sys.stdout.write(f"max {V} {R} {C}\n")
    sys.stdout.write(f"checksum {K}\n")


if __name__ == "__main__":
    main()
