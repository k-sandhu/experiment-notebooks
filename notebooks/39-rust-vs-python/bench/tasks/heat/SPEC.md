# Heat on a grid

Spread heat across a floor plan with walls and fixed heat sources, in exact integer steps.

## Input

```
H W S
row_0
...
row_(H-1)
```

The first line gives the number of rows H, the number of columns W and the number of steps S. Then H lines
of exactly W characters each: `.` is an open cell, `#` is a wall, and a digit `1`-`9` is a heat source. The
grid contains at least one open cell.

## Simulation

Open cells start at value 0. A source with digit d has the fixed value 1000 * d at all times. Walls have no
value.

In each of the S steps, every open cell gets a new value computed from the values at the start of the step:

```
new = (4 * old + n_up + n_down + n_left + n_right) // 8
```

n_up is the value of the cell above if that cell is open or a source, and the cell's own old value if the
cell above is a wall or lies outside the grid. n_down, n_left and n_right are defined the same way for the
other three neighbours. `//` is integer division rounding down. All open cells update at the same time.
Sources and walls never change.

## Output

```
sum T
max V R C
checksum K
```

After S steps, T is the sum of the values of all open cells. V is the largest open-cell value, found at row
R and column C (both 0-based, row 0 at the top); on a tie, report the first such cell in row-major order
(smallest R, then smallest C). K is the sum over all open cells of `value * (R * W + C + 1)`. All values fit
in a signed 64-bit integer.

## Benchmark size

H = 400 rows, W = 400 columns and S = 250 steps (about 40 million cell updates). The samples are smaller.
