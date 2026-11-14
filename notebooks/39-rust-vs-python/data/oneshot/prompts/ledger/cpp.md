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
# Ledger

Total a large file of bank transactions written as JSON, converting currencies with exact integer arithmetic.

## Input

JSON Lines: one JSON object per line, UTF-8, each line ending in a newline, no blank lines.

The first line holds the exchange rates:

```
{"rates": {"USD": 1000000, "EUR": 1083250, "JPY": 6612}}
```

A rate is an integer number of millionths of a US dollar per unit of that currency: 1 EUR is
1083250 / 1000000 USD.

Every later line is one transaction, for example:

```
{"id": 18342, "account": "AC-04821", "type": "credit", "amount": "1523.07", "currency": "EUR", "tags": ["payroll", "q4"], "meta": {"channel": "mobile", "ts": "2026-10-03T14:22:05Z", "note": "rent \"October\""}}
```

Keys can appear in any order, the whitespace between tokens varies, and strings can contain JSON escapes
(`\"`, `\\`, `\/`, `\n`, `\uXXXX`, including surrogate pairs). Objects can hold extra keys, with nested
objects and arrays as values, which you should ignore. Every transaction has these fields:

- `account`: a string.
- `type`: `"credit"`, `"debit"`, `"refund"` or `"void"`.
- `amount`: a string of decimal digits, optionally followed by `.` and one or two digits (`"12"`, `"12.5"`,
  `"12.05"`). It is never negative.
- `currency`: a string that is a key of the rates object.
- `tags`: an array of strings, possibly empty.
- `meta`: an object with a string field `channel`, among other fields.

## Rules

1. Skip a transaction whose type is `"void"` or whose tags contain the string `"test"`. Skipped transactions
   are not counted anywhere.
2. Convert the amount to integer hundredths: `"12"` is 1200, `"12.5"` is 1250 and `"12.05"` is 1205.
3. Convert to US cents with exact integer arithmetic, rounding down: `usd = (hundredths * rate) // 1000000`.
   The product fits in a signed 64-bit integer.
4. The signed value is `+usd` for `"credit"` and `"refund"`, and `-usd` for `"debit"`.

## Output

```
counted N
net T
channel NAME COUNT NET
...
account ID NET
...
```

N is the number of counted transactions and T the sum of their signed values. Then one `channel` line per
channel, sorted by name ascending (byte order), giving the number of counted transactions in that channel and
the sum of their signed values. Then one `account` line for each of the 10 accounts with the largest sum of
signed values, sorted by that sum descending and then by account ID ascending (byte order); print all
accounts if there are fewer than 10. All sums fit in a signed 64-bit integer. Channel names and account IDs
are ASCII and contain no spaces.

## Benchmark size

About 1,000,000 transactions (about 380 MB). The samples are smaller.
</task>

## Exact input and output for this task

- Input: UTF-8 JSON Lines; every line, including the last, ends in `\n`. The first line is the rates object
  and every later line is one transaction object. Strings can hold raw non-ASCII characters (`café`) and
  escapes (`\"`, `\\`, `\/`, `\n`, `\uXXXX`, surrogate pairs). Spacing varies: `"a":1`, `"a": 1` and
  `"a" :  1` all occur. Use a JSON parser or a correct tokenizer, not substring searches.
- Only the top-level fields `type`, `amount`, `currency`, `account` and `tags`, and `channel` inside the
  top-level `meta` object, matter. Transactions carry extra keys whose values are nested objects that can
  themselves contain keys named `account`, `type`, `tags` or `channel`; ignore all of those.
- Skip a transaction only if `type` is exactly `"void"` or `tags` contains exactly the string `"test"`. Tags
  such as `"testing"` or `"Test"` do not cause a skip.
- Amounts `"0"`, `"12"`, `"12.5"` and `"12.05"` are 0, 1200, 1250 and 1205 hundredths. Compute
  `usd = (hundredths * rate) // 1000000` on the non-negative amount first, then negate it for a debit: a debit
  of 0.5 JPY is 0, not -1. The product fits in a signed 64-bit integer.
- Output: `counted N`, `net T`, then one `channel NAME COUNT NET` line for each channel that has at least one
  counted transaction (sorted by name), then up to 10 `account ID NET` lines (sorted by NET descending, then
  by ID ascending). NET can be negative or zero. Only accounts with a counted transaction appear.
- Every channel name and account ID is ASCII without spaces.

## Examples

Each example is a complete input file and the exact output your program must print for it.

Example `e1` input:

<input>
{"rates": {"USD": 1000000, "EUR": 1083250, "JPY": 6612}}
{"type":"credit","id":1,"account":"AC-00001","amount":"12","currency":"USD","tags":[],"meta":{"channel":"web","ts":"2026-10-30T14:22:05Z","note":"rent \"October\""},"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}}
{"meta": {"note": "café", "channel": "mobile", "ts": "2026-10-30T14:22:05Z"}, "account": "AC-00002", "currency": "EUR", "amount": "1523.07", "tags": ["payroll"], "type": "debit", "id": 2}
{"id" :  3,  "tags" :  ["testing"],  "amount" :  "12.5",  "account" :  "AC-00001",  "meta" :  {"channel" :  "web",  "note" :  "folder \\ archive \/receipt"},  "currency" :  "JPY",  "type" :  "refund"}
{"id":4,"account":"AC-00003","type":"void","amount":"99.99","currency":"USD","tags":[],"meta":{"channel":"atm"}}
{"id": 5, "account": "AC-00003", "type": "credit", "amount": "5.05", "currency": "USD", "tags": ["rent", "test"], "meta": {"channel": "atm"}}
{"currency": "EUR", "meta": {"extra": {"account": "ignored", "tags": ["test", {"type": "void"}]}, "channel": "branch", "note": "emoji \ud83d\ude00 and line\nnext"}, "tags": ["Test"], "type": "credit", "amount": "0.05", "account": "AC-00004", "id": 6}
{"id":7,"account":"AC-00002","type":"debit","amount":"0.5","currency":"JPY","tags":[],"meta":{"channel":"web"}}
{"id": 8, "account": "AC-00005", "type": "credit", "amount": "0", "currency": "USD", "tags": [], "meta": {"channel": "mobile"}}
{"id":9,"account":"AC-00004","type":"debit","amount":"250.75","currency":"USD","tags":[],"meta":{"channel":"branch"}}
</input>

Expected output:

<output>
counted 7
net -188848
channel branch 2 -25070
channel mobile 2 -164986
channel web 3 1208
account AC-00001 1208
account AC-00005 0
account AC-00004 -25070
account AC-00002 -164986
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
