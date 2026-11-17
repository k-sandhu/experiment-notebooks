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
