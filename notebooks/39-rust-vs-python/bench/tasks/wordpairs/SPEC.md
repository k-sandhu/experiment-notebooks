# Word pairs

Count how often each pair of adjacent words occurs in a large text, and report the most common pairs.

## Input

An ASCII text file. Every byte is a newline (0x0A) or a printable character from 0x20 to 0x7E.

## Definitions

- A word is a maximal run of ASCII letters (`A`-`Z`, `a`-`z`). Every other character separates words. Words
  are compared in lower case, so "The" and "the" are the same word.
- A sentence ends at each `.`, `!` or `?`. Text after the last such character forms a final sentence.
  Newlines do not end sentences.
- A pair is two words that are next to each other within one sentence: the first and second word of a
  sentence, the second and third, and so on. Words separated by other characters (digits, commas, quotes,
  newlines) still form a pair when no sentence end lies between them. A sentence with w words has w-1 pairs,
  and none when w is 0 or 1.
- A pair is ordered: "red fox" and "fox red" are different pairs.

## Output

```
words W
pairs T
distinct D
C first second
...
```

W is the total number of words, T the total number of pairs and D the number of different pairs. Then one
line per pair for the 20 most frequent pairs: its count C, its first word and its second word. Pair lines are
sorted by count descending; pairs with equal counts are sorted by the first word, then by the second word, in
ascending byte order. If there are fewer than 20 different pairs, print all of them. Words are printed in
lower case. Fields are separated by single spaces.

## Benchmark size

About 60 MB of text: about 10 million words drawn from a vocabulary of about 40,000 words. The samples are
smaller.
