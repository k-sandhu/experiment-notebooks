- Input: line 1 is `H W S`. Then exactly H lines of exactly W characters, each `.` (open cell), `#` (wall) or a
  digit `1`-`9` (heat source), each line ending in `\n`.
- Only open cells (`.`) change, and only open cells count in the output. Heat sources and walls are not open
  cells: leave them out of the sum T, the maximum V and its position R C, and the checksum K, even though a
  source has a value.
- In the update, a neighbour that is an open cell or a source contributes its value at the start of the step
  (a source always contributes `1000 * d`). A neighbour that is a wall, or that lies outside the grid,
  contributes the updating cell's own old value. Values are never negative, so `//` is ordinary integer
  division.
- Output: exactly three lines, `sum T`, `max V R C` and `checksum K`. R and C are 0-based; on a tie for the
  maximum, take the first open cell in row-major order. Compute T and K in 64 bits.
