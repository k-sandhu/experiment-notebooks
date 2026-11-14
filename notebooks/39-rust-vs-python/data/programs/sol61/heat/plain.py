"""Integer heat diffusion, using only the Python standard library."""

import sys


def main():
    with open(sys.argv[1], "rb") as f:
        height, width, steps = map(int, f.readline().split())
        grid = b"".join(f.readline().strip() for _ in range(height))

    positions = [i for i, cell in enumerate(grid) if cell == 46]
    if steps == 0 or not any(49 <= cell <= 57 for cell in grid):
        row, col = divmod(positions[0], width)
        print(f"sum 0\nmax 0 {row} {col}\nchecksum 0")
        return

    # Remove wall and source lookups from the simulation by grouping cells
    # according to their number of open neighbours.
    groups = [[] for _ in range(9)]
    for pos in positions:
        row, col = divmod(pos, width)
        neighbours = []
        weight = 4
        constant = 0
        for other in (
            pos - width if row else -1,
            pos + width if row + 1 < height else -1,
            pos - 1 if col else -1,
            pos + 1 if col + 1 < width else -1,
        ):
            cell = grid[other] if other >= 0 else 35
            if cell == 46:
                neighbours.append(other)
            elif cell == 35:
                weight += 1
            else:
                constant += (cell - 48) * 1000
        degree = len(neighbours)
        if constant:
            groups[8 - degree].append((pos, weight, constant, *neighbours))
        else:
            groups[4 - degree].append((pos, *neighbours))

    # Each comprehension produces the next buffer in its final layout.
    order = [node[0] for group in groups for node in group]
    index = [-1] * len(grid)
    for i, pos in enumerate(order):
        index[pos] = i
    for g in range(5):
        groups[g] = [tuple(index[pos] for pos in node) for node in groups[g]]
    for g in range(5, 9):
        groups[g] = [(index[node[0]], node[1], node[2],
                      *(index[pos] for pos in node[3:])) for node in groups[g]]
    four, three, two, one, isolated, heat3, heat2, heat1, heat0 = groups
    zeroes = [0] * len(isolated)
    del groups, index, positions, grid

    old = [0] * len(order)
    for _ in range(steps):
        new = [(4 * old[p] + old[a] + old[b] + old[c] + old[d]) >> 3
               for p, a, b, c, d in four]
        new.extend([(5 * old[p] + old[a] + old[b] + old[c]) >> 3
                    for p, a, b, c in three])
        new.extend([(6 * old[p] + old[a] + old[b]) >> 3 for p, a, b in two])
        new.extend([(7 * old[p] + old[a]) >> 3 for p, a in one])
        new.extend(zeroes)
        new.extend([(k * old[p] + c + old[a] + old[b] + old[d]) >> 3
                    for p, k, c, a, b, d in heat3])
        new.extend([(k * old[p] + c + old[a] + old[b]) >> 3
                    for p, k, c, a, b in heat2])
        new.extend([(k * old[p] + c + old[a]) >> 3
                    for p, k, c, a in heat1])
        new.extend([(k * old[p] + c) >> 3 for p, k, c in heat0])
        if new == old:
            break
        old = new

    total = sum(old)
    largest = max(old)
    best = min(pos for pos, value in zip(order, old) if value == largest)
    checksum = sum(value * (pos + 1) for pos, value in zip(order, old))
    row, col = divmod(best, width)
    print(f"sum {total}\nmax {largest} {row} {col}\nchecksum {checksum}")


if __name__ == "__main__":
    main()
