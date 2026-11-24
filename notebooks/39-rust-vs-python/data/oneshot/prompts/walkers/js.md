Write one complete JavaScript program for the task below. It will be compiled and run automatically with no
human in the loop, and judged first on whether its output is exactly right and then on how fast it runs.

## The program

- File: `main.js`, a CommonJS script: load modules with `require`, not `import`.
- Runtime: Node.js 22, with no build step and default flags.
- Libraries: built-in Node modules only. No npm packages.

## How it is run

- Command: `node main.js INPUT_PATH WORKERS`. `INPUT_PATH` is the path of the input file and `WORKERS` is an integer from 1 to 32 (see the task).
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
# Random walkers

Simulate many independent random walks inside a box, using a fixed random number generator, and spread the
work over several workers running in parallel.

## How the program is run

Unlike a single-threaded task, this program takes a second argument:

```
<program> INPUT_PATH WORKERS
```

WORKERS is an integer from 1 to 32. Split the walkers over WORKERS threads or processes that run in parallel.
The output must not depend on WORKERS.

## Input

One line:

```
J L B SEED
```

J walkers each take L steps on a square grid, inside the box |x| <= B, |y| <= B, with B >= 1. SEED is an
unsigned 64-bit integer.

## Random numbers

Walker j (numbered from 0) has its own SplitMix64 generator, whose 64-bit state starts at
(SEED + j) mod 2^64. All arithmetic is unsigned 64-bit and wraps on overflow:

```
next():
    state = state + 0x9E3779B97F4A7C15
    z = state
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
    z = (z ^ (z >> 27)) * 0x94D049BB133111EB
    return z ^ (z >> 31)
```

## One walk

Each walker starts at (0, 0). In each of its L steps it draws r = next() and takes d = r >> 62, the top two
bits. d = 0 moves the walker to x + 1, d = 1 to x - 1, d = 2 to y + 1 and d = 3 to y - 1. If the move would
take the walker outside the box, it stays where it is, and the step counts as a bump. A step in which the
walker moves and lands on (0, 0) counts as a return.

## Output

```
spread X
bumps Y
returns Z
farthest J D
```

X is the sum over all walkers of x * x + y * y at their final positions. Y is the total number of bumps and
Z the total number of returns, over all walkers. D is the largest final distance |x| + |y| of any walker, and
J is the number of the walker that has it; on a tie, the smallest such number. All values fit in a signed
64-bit integer.

## Benchmark size

J = 64 walkers, L = 500,000 steps each and B = 300 (32 million steps). The samples are smaller.
</task>

## Exact input and output for this task

- The program gets two arguments, `INPUT_PATH WORKERS`. WORKERS is an integer from 1 to 32. Split the walkers
  over that many threads or processes; the output must be identical for every WORKERS value.
- Input: one line `J L B SEED` followed by `\n`. J, L and B are positive integers. SEED can be as large as
  18446744073709551615 (2^64 - 1), which does not fit in a signed 64-bit integer.
- The generator for walker j starts with state `(SEED + j) mod 2^64`. All generator arithmetic is unsigned
  64-bit and wraps on overflow, and `>>` is a logical (unsigned) shift.
- A step that would leave the box is a bump, and the walker stays where it is. A return is a step in which the
  walker moves and ends on (0, 0); a bump while standing on (0, 0) is not a return.
- Output: exactly four lines, `spread X`, `bumps Y`, `returns Z` and `farthest J D`. On a tie for D, J is the
  smallest walker number.

## Examples

Each example is a complete input file and the exact output your program must print for it.

Example `s1a` input:

<input>
4 12 1 18446744073709551615
</input>
Run with `WORKERS` = 4.

Expected output:

<output>
spread 6
bumps 22
returns 3
farthest 0 2
</output>

Example `s1b` input:

<input>
4 15 2 18446744073709551615
</input>
Run with `WORKERS` = 4.

Expected output:

<output>
spread 20
bumps 20
returns 0
farthest 0 4
</output>

Example `s2` input:

<input>
64 500 300 18446744073709551606
</input>
Run with `WORKERS` = 4.

Expected output:

<output>
spread 33538
bumps 0
returns 103
farthest 57 76
</output>

Example `s3` input:

<input>
64 25000 300 18446744073709551586
</input>
Run with `WORKERS` = 4.

Expected output:

<output>
spread 1521353
bumps 75
returns 215
farthest 2 408
</output>


## Goals, in order

1. Print the correct output for every valid input the task allows, not only for the examples.
2. Make the program as fast as you can, written the way a skilled JavaScript developer writes fast code.

Use a single thread and a single process unless the task says otherwise. Do not precompute or embed answers,
and do not start other programs. The benchmark runs on Windows 11 on a 16-core laptop with the input size
the task gives.

## Your reply

Reply with the complete contents of `main.js` in one fenced code block and nothing else. You cannot compile or
run the code, so before you reply, check that it compiles with exactly the toolchain above and that it follows
every rule under "Exact input and output for this task". The examples show the exact output format; you do not
need to trace them by hand.
