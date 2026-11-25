Write one complete Go program for the task below. It will be compiled and run automatically with no
human in the loop, and judged first on whether its output is exactly right and then on how fast it runs.

## The program

- File: `main.go`, the only source file, in `package main` of the module `solution` (`go.mod` says `go 1.27`).
- Toolchain: Go 1.27, built with `go build -o solution.exe .` and `CGO_ENABLED=0`.
- Libraries: the standard library only. No third-party modules.

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
# Routes

Find the shortest road distances from a few starting points in a large road network.

## Input

```
N M Q
u v w
...
s1 s2 ... sQ
```

The first line gives the number of nodes N, the number of roads M and the number of sources Q. Nodes are
numbered 0 to N-1. Each of the next M lines is an undirected road between nodes u and v with length w, an
integer from 1 to 1000. There can be several roads between the same two nodes, and roads from a node to
itself. The last line lists the Q source nodes, separated by single spaces. Some nodes cannot be reached from
some sources.

## Output

One line per source, in input order:

```
s R TOTAL FAR NODE
```

s is the source. R is the number of nodes reachable from s, counting s itself. TOTAL is the sum of the
shortest distances from s to all reachable nodes, and FAR is the largest of those distances. NODE is the
smallest node number whose shortest distance from s equals FAR. All values fit in a signed 64-bit integer.

## Benchmark size

N = 300,000 nodes, M = 900,000 roads and Q = 6 sources. The samples are smaller.
</task>

## Exact input and output for this task

- Input: line 1 is `N M Q`. Then exactly M lines `u v w` with 0 <= u, v < N and 1 <= w <= 1000, then one line
  with Q source node numbers separated by single spaces. Roads are undirected. A road can join a node to
  itself, and several roads with different lengths can join the same two nodes.
- Output: exactly Q lines, one per source in input order, `s R TOTAL FAR NODE`, and nothing else.
- R counts the reachable nodes, including s itself at distance 0. A source with no roads prints `s 1 0 0 s`.
  Unreachable nodes are left out of R, TOTAL, FAR and NODE.
- TOTAL can exceed 2^31, so add it up in 64 bits. NODE is the smallest node number whose shortest distance
  equals FAR.

## Examples

Each example is a complete input file and the exact output your program must print for it.

Example `s1` input:

<input>
12 36 6
0 1 5
0 2 5
3 4 2
4 5 2
6 7 1
8 9 3
0 0 1
6 7 4
6 7 6
4 5 2
8 9 11
0 2 8
3 4 9
8 9 6
3 4 9
0 1 9
0 2 7
0 1 12
6 7 6
0 2 12
3 4 5
8 9 9
4 5 5
0 1 11
4 5 6
0 2 6
8 9 8
8 9 7
4 5 8
0 2 11
0 1 11
8 9 9
0 1 12
0 2 13
0 1 10
0 1 10
0 3 6 8 10 11
</input>

Expected output:

<output>
0 3 10 5 1
3 3 6 4 5
6 2 1 1 7
8 2 3 3 9
10 1 0 0 10
11 1 0 0 11
</output>


## Goals, in order

1. Print the correct output for every valid input the task allows, not only for the examples.
2. Make the program as fast as you can, written the way a skilled Go developer writes fast code.

Use a single thread and a single process unless the task says otherwise. Do not precompute or embed answers,
and do not start other programs. The benchmark runs on Windows 11 on a 16-core laptop with the input size
the task gives.

## Your reply

Reply with the complete contents of `main.go` in one fenced code block and nothing else. You cannot compile or
run the code, so before you reply, check that it compiles with exactly the toolchain above and that it follows
every rule under "Exact input and output for this task". The examples show the exact output format; you do not
need to trace them by hand.
