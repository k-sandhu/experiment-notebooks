Write one complete Python program for the task below. It will be compiled and run automatically with no
human in the loop, and judged first on whether its output is exactly right and then on how fast it runs.

## The program

- File: `fast.py`.
- Interpreter: CPython 3.13 on Windows.
- Libraries: the standard library plus NumPy 2.2 (`import numpy as np`). No other packages. Names removed in NumPy 2.0, such as `np.float_`, `np.int0` and `np.in1d`, do not exist.

## How it is run

- Command: `C:\Python313\python.exe fast.py INPUT_PATH`. `INPUT_PATH` is the path of the input file.
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
# Alignment cost

Find the cheapest way to turn one string into another using weighted insertions, deletions and
substitutions, for many pairs of strings.

## Input

```
ALPHABET
ins_1 ins_2 ... ins_A
del_1 del_2 ... del_A
sub_1_1 sub_1_2 ... sub_1_A
...
sub_A_1 sub_A_2 ... sub_A_A
P
s t
...
```

The first line is the alphabet: A distinct upper-case letters (A is at most 26). The next line gives the cost
of inserting each letter, in alphabet order, and the line after it the cost of deleting each letter. Then A
rows give the substitution costs: the j-th number in row i is the cost of replacing the i-th letter with the
j-th letter. All costs are integers from 0 to 1000, and the diagonal of the substitution table is 0. The
costs need not obey the triangle inequality. Then comes a line with the number of pairs P, and P lines that
each hold two non-empty strings over the alphabet separated by one space. Numbers on a line are separated by
single spaces.

## Cost of a pair

For strings s (length n) and t (length m), with letters numbered from 1, define the table D by

```
D[0][0] = 0
D[i][0] = D[i-1][0] + del[s_i]                          for i = 1..n
D[0][j] = D[0][j-1] + ins[t_j]                          for j = 1..m
D[i][j] = min( D[i-1][j]   + del[s_i],
               D[i][j-1]   + ins[t_j],
               D[i-1][j-1] + sub[s_i][t_j] )            for i = 1..n, j = 1..m
```

The cost of the pair is D[n][m], exactly as this recurrence defines it. Use the substitution costs as given;
do not first replace them with cheaper chains of substitutions, deletions and insertions.

## Output

One line per pair with its cost, in input order, then a final line:

```
total X
```

where X is the sum of all the costs. All values fit in a signed 64-bit integer.

## Benchmark size

P = 300 pairs with string lengths from 100 to 1,000 letters, about 60 million table cells in all. The
samples are smaller.
</task>

## Exact input and output for this task

- Input: line 1 is the alphabet, A distinct upper-case letters with no spaces (A <= 26). Line 2 holds the A
  insertion costs and line 3 the A deletion costs, in alphabet order. Then A lines of A substitution costs:
  row i is the letter being replaced (from s) and column j the letter replacing it (from t). Then a line with
  P, then P lines `s t`. All costs are integers from 0 to 1000; an insertion or deletion cost can be 0.
- Letters are numbered by their position in the alphabet line, not by their place in `A`-`Z`: with the
  alphabet `DCAB`, `D` is letter 0 and `B` is letter 3.
- Output: P lines, each holding one pair's cost D[n][m] as a plain integer, in input order, then `total X`.
- Use the recurrence exactly as given, with the substitution table as given; do not simplify it with the
  triangle inequality. Add up the total in 64 bits.

## Examples

Each example is a complete input file and the exact output your program must print for it.

Example `s1` input:

<input>
ABCDEFGHIJ
0 434 100 466 495 277 474 184 240 25
340 0 110 309 114 470 148 249 355 401
0 1000 336 994 448 72 261 197 164 90
455 0 788 550 375 196 483 805 333 244
652 810 0 0 432 213 64 440 478 311
216 113 667 0 843 639 696 336 680 879
903 273 404 801 0 388 234 433 78 414
762 684 428 6 892 0 475 221 547 96
353 814 22 379 721 368 0 9 268 577
839 157 35 442 185 284 67 0 781 154
414 701 745 847 371 917 668 582 0 486
170 510 864 896 522 318 889 890 185 0
6
A A
J IIBHHIHBBHHI
BJIDAFGDACIA J
BJJDA BJJDA
ICCGFFDJ CGIEACABB
EGG GDGFBFDGHC
</input>

Expected output:

<output>
0
3127
3076
0
2558
2438
total 11199
</output>

Example `s2` input:

<input>
ABCDEFGHIJ
0 347 316 184 87 284 365 339 312 94
197 0 317 220 290 298 23 371 272 279
0 1000 764 532 906 900 189 752 809 386
452 0 232 522 131 86 829 54 706 188
623 589 0 0 919 513 857 227 731 543
538 148 502 0 636 421 645 490 686 70
252 625 94 848 0 340 386 704 199 522
437 765 617 441 860 0 407 136 929 824
171 372 212 73 602 242 0 646 301 443
130 571 629 451 987 684 785 0 910 273
844 323 654 760 481 654 970 549 0 457
893 640 889 523 699 212 400 250 760 0
6
FBIDABEI DHFJHEIBDBBFBGFACCBHACCEHEGIGABHHFCHCJIH
JGBCEBEJCBABBBGBBHGGJBHEHAHFEHGHHC JJBJJBAFCECEFBCAGHBCJHGBIGJHHIDGEHH
ECGDAGDFHFHECJABJDHAJJHA BHJJGCBCJGJBBCGBFIICFBAH
FCJACIFEGGGHEFIAIFJCEHJJEHECJAG FCJACIFEGGGHEFIAIFJCEHJJEHECJAG
HJJCGAJCBHBJD GBIEDJCFIEIFAHJDABJJIHJIJAHEBI
BEDAIHCGIEGHGBDAFE BAHGAJGFDGIGCGGCEDBGGAEDGCICHEC
</input>

Expected output:

<output>
8537
4856
6478
0
5069
5502
total 30442
</output>


## Goals, in order

1. Print the correct output for every valid input the task allows, not only for the examples.
2. Make the program as fast as you can, written the way a skilled Python developer writes fast code.

Use a single thread and a single process unless the task says otherwise. Do not precompute or embed answers,
and do not start other programs. The benchmark runs on Windows 11 on a 16-core laptop with the input size
the task gives.

## Your reply

Reply with the complete contents of `fast.py` in one fenced code block and nothing else. You cannot compile or
run the code, so before you reply, check that it compiles with exactly the toolchain above and that it follows
every rule under "Exact input and output for this task". The examples show the exact output format; you do not
need to trace them by hand.
