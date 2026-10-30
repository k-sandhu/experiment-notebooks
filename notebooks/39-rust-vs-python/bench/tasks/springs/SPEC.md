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
