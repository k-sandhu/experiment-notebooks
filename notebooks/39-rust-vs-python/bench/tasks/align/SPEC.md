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

The cost of the pair is D[n][m].

## Output

One line per pair with its cost, in input order, then a final line:

```
total X
```

where X is the sum of all the costs. All values fit in a signed 64-bit integer.

## Benchmark size

P = 300 pairs with string lengths from 100 to 1,000 letters, about 60 million table cells in all. The
samples are smaller.
