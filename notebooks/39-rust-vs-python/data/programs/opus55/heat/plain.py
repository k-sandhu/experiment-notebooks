import sys
from operator import mul

# The whole grid is packed into one big integer with one 17-bit lane per cell
# (SIMD within a register), so each step is a few big-int shifts, adds and
# masks over the whole grid at once.  Values never exceed 9000 < 2**14 and the
# per-cell sum before the division is at most 8 * 9000 = 72000 < 2**17, so
# lanes never carry into each other.
B = 17
PAD = "0" * (B - 1)
VMASK = (1 << 14) - 1


def main():
    with open(sys.argv[1], "rb") as f:
        data = f.read().split()
    H, W, S = int(data[0]), int(data[1]), int(data[2])
    rows = data[3:3 + H]

    # Padded layout: row stride LR = W + 1 (one wall column shared between
    # neighbouring rows), plus a wall row above and below.  Cell (r, c) lives
    # in lane p = (r+1)*LR + c + 1.
    LR = W + 1
    N = (H + 2) * LR
    grid = b"#" * LR + b"".join([b"#" + row for row in rows]) + b"#" * LR
    # Big-endian binary text has lane 0 at the end, so reverse the grid.
    rgrid = grid[::-1]

    def ones(src, dst):
        # Lane value 1 for every cell whose character maps to "1".
        s = rgrid.translate(bytes.maketrans(src, dst)).decode()
        return int(PAD + PAD.join(s), 2)

    chars = b".#123456789"
    ONE_OPEN = ones(chars, b"10000000000")
    ONE_WALL = ones(chars, b"01000000000")
    SRC = 0
    for bit in range(4):
        dst = bytes([48 + ((d >> bit) & 1) for d in range(10)])
        SRC += ones(b"0123456789.#", dst + b"00") << bit
    SRC *= 1000

    row = B * LR
    # Number of wall/outside neighbours per lane (0..4).
    K = (ONE_WALL << B) + (ONE_WALL >> B) + (ONE_WALL << row) + (ONE_WALL >> row)
    # An open cell walled in on all four sides keeps its value 0 forever, so it
    # is simply left out; the others need (4 + k) * old with k in 0..3.
    ONE_ACTIVE = ONE_OPEN & ~((K >> 2) & ONE_OPEN)
    OPEN = ONE_ACTIVE * VMASK
    # All step terms are computed scaled by 2**B so that the horizontal and
    # centre terms come from one small multiplication; the final shift undoes it.
    K1 = ((K & ONE_ACTIVE) * VMASK) << B
    K2 = (((K >> 1) & ONE_ACTIVE) * VMASK) << B
    MH = (1 << 2 * B) | (1 << (B + 2)) | 1  # right, 4 * centre, left
    up = row + B
    down = row - B
    fin = B + 3

    X = SRC
    if K1 and K2:
        for _ in range(S):
            t = X * MH
            t += X << up
            t += X >> down
            XB = X << B
            t += XB & K1
            t += (XB & K2) << 1
            X = ((t >> fin) & OPEN) | SRC
    else:
        for _ in range(S):
            t = X * MH
            t += X << up
            t += X >> down
            if K1:
                t += (X << B) & K1
            if K2:
                t += ((X << B) & K2) << 1
            X = ((t >> fin) & OPEN) | SRC

    # Extract the lane values from the binary text (lane 0 is at the end).
    total = N * B
    bits = format(X & OPEN, "b").zfill(total)
    vals = [int(bits[i - B:i], 2) for i in range(total, 0, -B)]

    # Only active open cells are non-zero, and lane order is row-major order.
    total_sum = sum(vals)
    best = max(vals)
    best_p = vals.index(best) if best else grid.index(b".")
    # Cell number R*W + C + 1 of lane p is p - p // LR - W.
    chk = sum(map(mul, vals, range(N))) - W * total_sum
    for r in range(1, H + 1):
        chk -= r * sum(vals[r * LR:(r + 1) * LR])
    r, c = divmod(best_p, LR)
    sys.stdout.buffer.write(
        f"sum {total_sum}\nmax {best} {r - 1} {c - 1}\nchecksum {chk}\n".encode())


main()
