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
