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
# Springs on a ring

A ring of N masses is joined by N springs. Spring i joins mass i to mass i+1, and spring N-1 joins mass N-1
back to mass 0. The masses move along a line. The ring has circumference P, so seen from mass N-1, mass 0 sits
at x[0] + P. Simulate the ring for S time steps and report its energy.

## Input

Plain text. The first line holds `N S dt P`: two integers, then two decimal numbers. N lines follow, one per
mass i = 0..N-1, each holding six decimal numbers separated by single spaces:

```
x v m k r c
```

x is the position, v the velocity, m the mass (always > 0), k the stiffness of spring i, r the rest length of
spring i and c the damping of mass i. Parse every decimal as an IEEE 754 double, correctly rounded (Python's
`float()` and Rust's `str::parse::<f64>()` both do this).

## One time step

All arithmetic is in double precision. Using the positions and velocities at the start of the step:

1. Stretch of each spring: for i < N-1, `s[i] = (x[i+1] - x[i]) - r[i]`; for the last spring,
   `s[N-1] = ((x[0] + P) - x[N-1]) - r[N-1]`.
2. Spring force: `f[i] = k[i] * s[i]`.
3. Force on each mass: `F[i] = (f[i] - f[i-1]) - (c[i] * v[i])`, where `f[-1]` means `f[N-1]`.
4. New velocity: `v[i] = v[i] + dt * (F[i] / m[i])`.
5. New position, using the new velocity: `x[i] = x[i] + dt * v[i]`.

Steps 1 to 3 use the old values for every i. Steps 4 and 5 then update every mass.

## Output

After S steps, print four lines:

```
kinetic K
potential U
position X
fastest J
```

- K is the sum over all masses of `((0.5 * m[i]) * v[i]) * v[i]`.
- U is the sum over all springs of `((0.5 * k[i]) * s[i]) * s[i]`, with s computed from the final positions as
  in step 1.
- X is the sum of all `x[i]`.
- J is the index of the mass with the largest `|v[i]|`; on a tie, the smallest such index.

Print K, U and X in any format that parses as a decimal floating-point number and keeps at least 12
significant digits, for example Python `f"{K:.12e}"` or Rust `format!("{:.12e}", K)`. They are checked with a
relative tolerance of 1e-9, so the order in which you add up a sum does not matter. J must match exactly.

## Benchmark size

N = 4,000 masses and S = 15,000 steps (60 million mass updates). The samples are smaller.
</task>

## Exact input and output for this task

- Input: line 1 is `N S dt P` (N >= 1 and S >= 0 are integers; dt and P are decimals). Then exactly N lines,
  each with six decimals `x v m k r c` separated by single spaces. A decimal may have a leading `-` and an
  exponent (`1e-3`); parse each one as an IEEE 754 double.
- Output: exactly four lines, `kinetic K`, `potential U`, `position X` and `fastest J`. Print K, U and X with
  at least 12 significant digits, for example in exponent form with 15 digits after the point
  (`9.999644492797053e+01`); they are compared with a relative tolerance of 1e-9. J is an integer index from
  0 to N-1 and must match exactly.
- Within one step, compute every spring force from the positions at the start of the step before you update
  any mass. Then update each velocity, and then that mass's position using its new velocity.
- With N = 1 the single spring joins mass 0 to itself around the ring: its stretch is
  `((x[0] + P) - x[0]) - r[0]`, the two spring forces on mass 0 cancel, and only damping acts.
- U uses stretches computed from the final positions, exactly as in step 1.

## Examples

Each example is a complete input file and the exact output your program must print for it.

Example `s1a` input:

<input>
1 3 0.0005 1
0.00162304265009129 2 50 0.02 0 0.0001
</input>

Expected output:

<output>
kinetic 9.9999999400000007e+01
potential 9.9999999999999967e-03
position 4.6230426440912898e-03
fastest 0
</output>

Example `s1b` input:

<input>
2 4 0.0005 2
0.00162304265009129 -0.0183147302679518 2.93050221412222 1.87075988285055 0 0.0001
1.0032694128906 2 50 0.02 0 0.0001
</input>

Expected output:

<output>
kinetic 9.9992998231368844e+01
potential 9.5592522193134821e-01
position 1.0088573164416643e+00
fastest 1
</output>

Example `s1c` input:

<input>
5 6 0.0005 5
0.00162304265009129 -0.0183147302679518 2.93050221412222 1.87075988285055 0 0.0001
1.0032694128906 -0.0171286218157219 1.44339249905248 0.790488136748135 0 0.0001
1.99424753536717 2 50 0.02 0 0.0001
3.0053978387322 -0.00800910151379794 1.94336452761707 0.854248053625185 0 0.0001
3.99807788661455 -0.0175039377527391 1.86030807297998 0.817292680293107 0 0.0001
</input>

Expected output:

<output>
kinetic 9.9996444927970529e+01
potential 2.1738797233951037e+00
position 1.0008432850726615e+01
fastest 2
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
