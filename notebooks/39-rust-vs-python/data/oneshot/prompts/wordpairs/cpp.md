Write one complete C++ program for the task below. It will be compiled and run automatically with no
human in the loop, and judged first on whether its output is exactly right and then on how fast it runs.

## The program

- File: `main.cpp`, the only source file.
- Toolchain: Microsoft Visual C++ 19.40 (Visual Studio 2022) on Windows, built with `cl /O2 /GL /DNDEBUG /EHsc /std:c++20 /utf-8 /I include main.cpp /link /LTCG`.
- Libraries: the C++20 standard library, plus nlohmann/json 3.12 as `#include <nlohmann/json.hpp>`. No other libraries.
- MSVC is not GCC or Clang: `<bits/stdc++.h>`, `__int128`, `__builtin_*` functions, variable-length arrays and `#pragma GCC` are not available.

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
</task>

## Exact input and output for this task

- Input: bytes that are newlines (0x0A) or printable ASCII (0x20 to 0x7E), with no `\r`. The file may or may
  not end with a newline.
- Words are runs of the letters `A`-`Z` and `a`-`z` only. Any other byte, including a digit, apostrophe,
  hyphen, space or newline, ends a word: `don't` is the two words `don` and `t`, and `abc123def` is `abc` and
  `def`. Words are lower-cased before counting.
- Only `.`, `!` and `?` end a sentence. A newline does not, so the words on either side of a line break form a
  pair when no `.`, `!` or `?` lies between them.
- Output: `words W`, `pairs T`, `distinct D`, then min(20, D) lines `C first second`, and nothing else. If D
  is 0, print only the first three lines.
- Sort the pair lines by C descending, then by the first word, then by the second word, both ascending as
  plain byte strings.

## Examples

Each example is a complete input file and the exact output your program must print for it.

Example `s1` input:

<input>
zzaa zzab. zzaa zzab. zzba zzbb. zzba zzbb. zzca zzcb. zzca zzcb. zzda zzdb
. zzda zzdb. zzea zzeb. zzea zzeb. zzfa zzfb. zzfa zzfb. zzga zzgb. zzga zzgb. 
zzha zzhb. zzha zzhb. zzia zzib. zzia zzib. zzja zzjb. zzja zzjb. 
zzka zzkb. zzka zzkb. zzla zzlb. zzla zzlb. zzma zzmb. zzma 
zzmb. zzna zznb. zzna zznb. zzoa zzob. zzoa zzob. zzpa zzpb. zzpa zzpb. 
zzqa zzqb. zzqa zzqb. zzra zzrb. zzra zzrb. zzsa zzsb. zzta zztb. zzua
zzub. don't. ?! ... !! abc123def. ?! ... !! red,fox. ?! ... !!
RED;FOX. ?! ... !! "red" (fox). ?! ... !! red-fox. ?! ... !! MiXeD
UPPER. ?! ... !! Title lower. ?! ... !! AQWLOUG brgqrz. wiborjbhvc
. laensxn") mzxbk; gfu123ffhsf'aqwloug; bfbd-aqwloug BRGQRZ, BFCUJMIQKFLH
") bfbd123iasa123rsj; aqwloug, gfu") Bfcujmiqkflh brgqrz123xomdcbps, aqwloug (
brgqrz Pzkdbhnzhgskod. rAcAi; gFcZxIcQ'bfbd, spr bfcujmiqkflh, aQwLoUg"
) aqwloug; aQwLoUg (ge. bFbD, daeb AQWLOUG aQwLoUg-xOmDcBpS (oir-
txlxd123rrjro (aqwloug'aqwloug (aQwLoUg; IJL, rsj'bfbd") wvdsuvude, 
Pyi (PZKDBHNZHGSKOD; aQwLoUg (AQWLOUG123Wiborjbhvc; bfcujmiqkflh'BFBD aqwloug-
aqwloug; kjkkram brgqrz-bfbd123Spr") rqrj bfcujmiqkflh Aqwloug123
laensxn Kjkkram (gllhb'
</input>

Expected output:

<output>
words 160
pairs 108
distinct 75
7 aqwloug aqwloug
4 red fox
3 aqwloug brgqrz
2 bfbd aqwloug
2 bfbd spr
2 bfcujmiqkflh aqwloug
2 bfcujmiqkflh bfbd
2 zzaa zzab
2 zzba zzbb
2 zzca zzcb
2 zzda zzdb
2 zzea zzeb
2 zzfa zzfb
2 zzga zzgb
2 zzha zzhb
2 zzia zzib
2 zzja zzjb
2 zzka zzkb
2 zzla zzlb
2 zzma zzmb
</output>


## Goals, in order

1. Print the correct output for every valid input the task allows, not only for the examples.
2. Make the program as fast as you can, written the way a skilled C++ developer writes fast code.

Use a single thread and a single process unless the task says otherwise. Do not precompute or embed answers,
and do not start other programs. The benchmark runs on Windows 11 on a 16-core laptop with the input size
the task gives.

## Your reply

Reply with the complete contents of `main.cpp` in one fenced code block and nothing else. You cannot compile or
run the code, so before you reply, check that it compiles with exactly the toolchain above and that it follows
every rule under "Exact input and output for this task". The examples show the exact output format; you do not
need to trace them by hand.
