- Input: line 1 is the alphabet, A distinct upper-case letters with no spaces (A <= 26). Line 2 holds the A
  insertion costs and line 3 the A deletion costs, in alphabet order. Then A lines of A substitution costs:
  row i is the letter being replaced (from s) and column j the letter replacing it (from t). Then a line with
  P, then P lines `s t`. All costs are integers from 0 to 1000; an insertion or deletion cost can be 0.
- Letters are numbered by their position in the alphabet line, not by their place in `A`-`Z`: with the
  alphabet `DCAB`, `D` is letter 0 and `B` is letter 3.
- Output: P lines, each holding one pair's cost D[n][m] as a plain integer, in input order, then `total X`.
- Use the recurrence exactly as given, with the substitution table as given; do not simplify it with the
  triangle inequality. Add up the total in 64 bits.
