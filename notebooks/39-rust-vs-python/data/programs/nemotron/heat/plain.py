import sys


def main() -> None:
    path = sys.argv[1]
    with open(path, "r") as f:
        text = f.read()
    lines = text.split("\n")
    header = lines[0].rstrip("\r")
    H, W, S = (int(x) for x in header.split())

    walkable = [False] * (H * W)  # not a wall: open cell or source (a valid neighbour)
    open_mask = [False] * (H * W)
    cur = [0] * (H * W)
    for r in range(H):
        line = lines[1 + r].rstrip("\r")
        base = r * W
        for c, ch in enumerate(line):
            if ch == "#":
                continue
            walkable[base + c] = True
            if ch == ".":
                open_mask[base + c] = True
            else:
                cur[base + c] = 1000 * (ord(ch) - 48)

    # Precompute, for every open cell, the flat index of each of its four
    # neighbours. A neighbour that is a wall or outside the grid is replaced
    # by the cell itself, which implements "use the cell's own old value".
    cells = []
    append = cells.append
    for r in range(H):
        base = r * W
        for c in range(W):
            i = base + c
            if not open_mask[i]:
                continue
            o_up = i - W if (r > 0 and walkable[i - W]) else i
            o_down = i + W if (r + 1 < H and walkable[i + W]) else i
            o_left = i - 1 if (c > 0 and walkable[i - 1]) else i
            o_right = i + 1 if (c + 1 < W and walkable[i + 1]) else i
            append((i, o_up, o_down, o_left, o_right))

    nxt = list(cur)
    for _ in range(S):
        for i, o_up, o_down, o_left, o_right in cells:
            v = cur[i]
            nxt[i] = (4 * v + cur[o_up] + cur[o_down] + cur[o_left] + cur[o_right]) >> 3
        cur, nxt = nxt, cur

    total = 0
    maxv = -1
    maxr = 0
    maxc = 0
    chk = 0
    for r in range(H):
        base = r * W
        for c in range(W):
            i = base + c
            if not open_mask[i]:
                continue
            v = cur[i]
            total += v
            chk += v * (i + 1)
            if v > maxv:
                maxv = v
                maxr = r
                maxc = c

    out = f"sum {total}\nmax {maxv} {maxr} {maxc}\nchecksum {chk}\n"
    sys.stdout.buffer.write(out.encode("ascii"))


if __name__ == "__main__":
    main()
