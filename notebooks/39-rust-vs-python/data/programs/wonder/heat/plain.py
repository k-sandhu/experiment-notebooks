import sys
from array import array


def main() -> None:
    path = sys.argv[1]
    with open(path, "rb") as f:
        data = f.read()

    parts = data.split()
    if len(parts) < 3:
        return
    h = int(parts[0])
    w = int(parts[1])
    s = int(parts[2])
    n = h * w

    # Join grid rows into one bytes object of length n.
    rows = parts[3:3 + h]
    grid = b"".join(rows)
    # Defensive: if rows contained whitespace splitting surprises, grid may be
    # shorter; samples/spec guarantee exactly W chars per row.
    if len(grid) != n:
        # Fallback: strip all whitespace from the tail and take n chars.
        tail = b"".join(parts[3:])
        grid = tail[:n]

    lane = 32  # bits per cell
    nbytes = 4 * n

    init = array("i", bytes(nbytes))  # all zero
    valid_b = bytearray(b"\xff" * nbytes)   # lane all-ones iff non-wall
    open_b = bytearray(b"\xff" * nbytes)    # lane all-ones iff open
    left_ok_b = bytearray(b"\xff" * nbytes)  # lane all-ones iff c != 0
    right_ok_b = bytearray(b"\xff" * nbytes)  # lane all-ones iff c != w-1

    open_indices = []

    # Parse cells. Iterating bytes yields ints.
    idx = 0
    for ch in grid:
        if ch == 35:  # '#'
            o = idx * 4
            valid_b[o:o + 4] = b"\x00\x00\x00\x00"
            open_b[o:o + 4] = b"\x00\x00\x00\x00"
        elif ch == 46:  # '.'
            open_indices.append(idx)
        else:  # digit '1'..'9'
            init[idx] = 1000 * (ch - 48)
            o = idx * 4
            open_b[o:o + 4] = b"\x00\x00\x00\x00"
        idx += 1

    # Edge-clear masks for left/right neighbour shifts.
    if w > 1:
        for r in range(h):
            o = (r * w) * 4
            left_ok_b[o:o + 4] = b"\x00\x00\x00\x00"
            o2 = (r * w + (w - 1)) * 4
            right_ok_b[o2:o2 + 4] = b"\x00\x00\x00\x00"
    else:
        # W == 1: both left and right are always outside.
        left_ok_b = bytearray(nbytes)
        right_ok_b = bytearray(nbytes)

    all_mask = int.from_bytes(b"\xff" * nbytes, "little")
    valid_mask = int.from_bytes(valid_b, "little")
    open_mask = int.from_bytes(open_b, "little")
    left_ok = int.from_bytes(left_ok_b, "little")
    right_ok = int.from_bytes(right_ok_b, "little")

    shift_w = w * lane
    if h > 1:
        up_mask = (valid_mask << shift_w) & all_mask
        down_mask = valid_mask >> shift_w
    else:
        up_mask = 0
        down_mask = 0
    left_mask = (valid_mask << lane) & left_ok
    right_mask = (valid_mask >> lane) & right_ok

    inv_up = all_mask ^ up_mask
    inv_down = all_mask ^ down_mask
    inv_left = all_mask ^ left_mask
    inv_right = all_mask ^ right_mask

    # After >>3, top 3 bits of each lane may hold bits from the next lane;
    # mask them off. Values are <= 9000, well within 29 bits.
    clean_pattern = int.from_bytes(b"\xff\xff\xff\x1f" * n, "little")
    open_clean = clean_pattern & open_mask

    source_packed = int.from_bytes(init.tobytes(), "little")
    g = source_packed

    for _ in range(s):
        eff_up = ((g << shift_w) & up_mask) | (g & inv_up)
        eff_down = ((g >> shift_w) & down_mask) | (g & inv_down)
        eff_left = ((g << lane) & left_mask) | (g & inv_left)
        eff_right = ((g >> lane) & right_mask) | (g & inv_right)
        total = (g << 2) + eff_up + eff_down + eff_left + eff_right
        g = ((total >> 3) & open_clean) | source_packed

    # Decode final values.
    vals = array("i")
    vals.frombytes(g.to_bytes(nbytes, "little"))

    total_sum = 0
    checksum = 0
    best = -1
    best_idx = 0
    for i in open_indices:
        v = vals[i]
        total_sum += v
        checksum += v * (i + 1)
        if v > best:
            best = v
            best_idx = i

    if open_indices:
        br = best_idx // w
        bc = best_idx % w
    else:
        best = 0
        br = 0
        bc = 0

    sys.stdout.buffer.write(f"sum {total_sum}\nmax {best} {br} {bc}\nchecksum {checksum}\n".encode())


if __name__ == "__main__":
    main()
