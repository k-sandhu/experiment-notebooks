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
