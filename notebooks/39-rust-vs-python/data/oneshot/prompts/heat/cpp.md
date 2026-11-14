Write one complete C++ program for the task below. It will be compiled and run automatically with no
human in the loop, and judged first on whether its output is exactly right and then on how fast it runs.

## The program

- File: `main.cpp`, the only source file.
- Toolchain: Microsoft Visual C++ 19.40 (Visual Studio 2022) on Windows, built with `cl /O2 /GL /DNDEBUG /EHsc /std:c++20 /utf-8 /I include main.cpp /link /LTCG`.
- Libraries: the C++20 standard library, plus nlohmann/json 3.12 as `#include <nlohmann/json.hpp>`. No other libraries.
- MSVC is not GCC or Clang: `<bits/stdc++.h>`, `__int128`, `__builtin_*` functions, variable-length arrays and `#pragma GCC` are not available.

## How it is run

- Command: `solution.exe INPUT_PATH`. `INPUT_PATH` is the path of the input file.
- Read the input only from that file. Do not read standard input or any other file, and do not wait for
  anything.
- Write the answer to standard output and nothing else: no prompts, labels, debug lines or blank lines.
  Standard error is ignored. Exit with status 0.

## Output rules that apply to every task

- Print the lines in exactly the order and form the task gives. Each line starts with its keyword (where the
  task shows one) and its fields are separated by exactly one space, with no spaces at the start or end.
- End every line with a newline, including the last one. `\r\n` line endings are also accepted.
- Print integers in plain decimal: an optional leading `-` and digits only, with no `+`, no thousands
  separators, no decimal point and no exponent.

## The task

<task>
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
</task>

## Exact input and output for this task

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

## Examples

Each example is a complete input file and the exact output your program must print for it.

Example `s1` input:

<input>
7 9 4
#9.9.9#.#
#####.#..
..1..#...
.....#...
##.###...
.....#...
.#2..#..3
</input>

Expected output:

<output>
sum 21557
max 6151 0 2
checksum 369130
</output>

Example `s2` input:

<input>
13 13 250
#9....#......
.............
........6....
......#......
......#......
##..#########
....3.#......
......#......
......#......
......#......
.........3...
.............
......#....1#
</input>

Expected output:

<output>
sum 519540
max 7440 0 2
checksum 33357316
</output>


## Goals, in order

1. Print the correct output for every valid input the task allows, not only for the examples.
2. Make the program as fast as you can, written the way a skilled C++ developer writes fast code.

Use a single thread and a single process unless the task says otherwise. Do not precompute or embed answers,
and do not start other programs. The benchmark runs on Windows 11 on a 16-core laptop with the input size
the task gives.

## Your reply

Reply with the complete contents of `main.cpp` in one fenced code block and nothing else. You cannot compile or
run the code, so before you reply, check that it compiles with exactly the toolchain above and that it follows
every rule under "Exact input and output for this task". The examples show the exact output format; you do not
need to trace them by hand.
