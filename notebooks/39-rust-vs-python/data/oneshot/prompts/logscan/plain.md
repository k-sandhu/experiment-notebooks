Write one complete Python program for the task below. It will be compiled and run automatically with no
human in the loop, and judged first on whether its output is exactly right and then on how fast it runs.

## The program

- File: `plain.py`.
- Interpreter: CPython 3.13 on Windows.
- Libraries: the standard library only. No third-party packages (no NumPy).

## How it is run

- Command: `C:\Python313\python.exe plain.py INPUT_PATH`. `INPUT_PATH` is the path of the input file.
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
# Log scan

Summarise a web server's access log: count requests by status class, and find the busiest URL paths with
their latency percentiles.

## Input

A text file of ASCII lines. Every line, including the last, ends in `\n`; there are no `\r` characters. A
well-formed line matches this regular expression in full (Python `re.fullmatch` on the line without its
newline, or Rust `regex` as written):

```
^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z [a-z]+-\d+ (GET|POST|PUT|DELETE|PATCH) (/[A-Za-z0-9_/-]*)(\?[^ ]*)? (\d{3}) \d+B (\d+)\.(\d)ms "[^"]*"$
```

Here `\d` means an ASCII digit 0-9. An example of a well-formed line:

```
2026-10-03T14:22:05.123Z web-17 GET /api/v2/items/48213?ref=abc 200 1834B 45.2ms "Mozilla/5.0 (X11; Linux x86_64)"
```

Any line that does not match is malformed. Malformed lines include truncated lines, stack traces and near
misses such as a lower-case method or a latency without its decimal digit.

## Rules

- Status class: the first digit of the status followed by `xx` (200 is `2xx`).
- Path template: take the path (the second capture group, which excludes any `?` query string), split it on
  `/`, replace every segment that is non-empty and made only of digits with `{id}`, and join the segments
  again with `/`. `/api/v2/items/48213` becomes `/api/v2/items/{id}`, and `/users/7/orders/` becomes
  `/users/{id}/orders/`.
- Latency: read it as an integer number of tenths of a millisecond (`45.2ms` is 452).
- Percentile p of a list of n latencies: sort the list ascending and take the element at 1-based position
  `ceil(p * n / 100)` (the nearest-rank method). For [10, 20, 30, 40], p50 is 20 and p95 is 40.

## Output

```
lines L
malformed M
status CLASS COUNT
...
path TEMPLATE COUNT P50 P95 MAX
...
```

L counts all lines and M the malformed ones. Then one `status` line per status class that occurs, sorted by
class ascending. Then one `path` line for each of the 10 path templates with the most well-formed requests,
sorted by COUNT descending and then by TEMPLATE ascending (byte order); print all templates if there are
fewer than 10. Status and path lines count well-formed lines only. P50, P95 and MAX are latencies of that
template's requests in milliseconds with exactly one decimal (452 tenths prints as `45.2`, 7 tenths as `0.7`).

## Benchmark size

About 2,000,000 lines (about 230 MB), of which about 1% are malformed. The samples are smaller.
</task>

## Exact input and output for this task

- Input: ASCII lines; every line, including the last, ends in `\n`, and there are no `\r` bytes. A line can be
  empty, and tabs can occur.
- A line is well-formed only if the whole line, without its `\n`, matches the regular expression in the task.
  Every other line is malformed, including an empty line, a tab in place of a separating space, a lower-case
  method, a latency without exactly one decimal digit, a four-digit status, a missing closing quote or text
  after the closing quote.
- Output: `lines L` (L is the number of `\n` characters in the file, so every line counts, well-formed or
  not), `malformed M`, then one `status CLASS COUNT` line per status class seen in well-formed lines, sorted
  ascending, then up to 10 `path TEMPLATE COUNT P50 P95 MAX` lines.
- Template: drop the query string, split the path on `/`, replace each non-empty segment made only of the
  digits 0-9 with `{id}`, and keep every other segment unchanged, including empty segments: `/x//42/12a`
  becomes `/x//{id}/12a`.
- Latencies are whole numbers of tenths: `45.2ms` is 452 and `0.7ms` is 7. With a template's n latencies
  sorted ascending, P50 is the element at 1-based position ceil(50n/100), P95 the element at ceil(95n/100),
  and MAX the largest. Print each with exactly one decimal: 7 prints `0.7`, 452 prints `45.2` and 6020 prints
  `602.0`.
- Sort path lines by COUNT descending, then TEMPLATE ascending as plain byte strings (`/` sorts before digits,
  digits before letters, and `{` after letters).

## Examples

Each example is a complete input file and the exact output your program must print for it.

Example `e1` input:

<input>
2026-10-30T14:22:05.123Z web-17 GET /api/v2/items/48213 200 1834B 45.2ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET
2026-10-30T14:22:05.123Z web-17 GET /api/v2/items/7?ref=abc&item=12 200 1834B 0.7ms "Mozilla/5.0 (X11; Linux x86_64)"
    at handler (server.js:1)
Traceback:
2026-10-30T14:22:05.123Z web-17 GET /users/29058/orders/ 404 1834B 120.0ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 get /health 200 1834B 12.1ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /x//42733/12a?ref=abc&item=12 204 1834B 11.9ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /health 200 1834B 45ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /health 200 1834B 45.25ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /health 500 1834B 9.5ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /health 200 1834B 12.1ms "Mozilla/5.0 (X11; Linux x86_64)
2026-10-30T14:22:05.123Z web-17 POST /api/v2/items/99 301 1834B 3.1ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /health 200 1834B 12.1ms "Mozilla/5.0 (X11; Linux x86_64)" extra
2026-10-30T14:22:05.123Z	web-17 GET /health 200 1834B 12.1ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /45287/2866/48615 101 1834B 18.0ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /health 2000 1834B 12.1ms "Mozilla/5.0 (X11; Linux x86_64)"
2026/10/30T14:22:05.123Z web-17 GET /health 200 1834B 12.1ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web-17 GET /api/v2/items/5 200 1834B 602.0ms "Mozilla/5.0 (X11; Linux x86_64)"
2026-10-30T14:22:05.123Z web GET /health 200 1834B 12.1ms "Mozilla/5.0 (X11; Linux x86_64)"

</input>

Expected output:

<output>
lines 21
malformed 13
status 1xx 1
status 2xx 4
status 3xx 1
status 4xx 1
status 5xx 1
path /api/v2/items/{id} 4 3.1 602.0 602.0
path /health 1 9.5 9.5 9.5
path /users/{id}/orders/ 1 120.0 120.0 120.0
path /x//{id}/12a 1 11.9 11.9 11.9
path /{id}/{id}/{id} 1 18.0 18.0 18.0
</output>


## Goals, in order

1. Print the correct output for every valid input the task allows, not only for the examples.
2. Make the program as fast as you can, written the way a skilled Python developer writes fast code.

Use a single thread and a single process unless the task says otherwise. Do not precompute or embed answers,
and do not start other programs. The benchmark runs on Windows 11 on a 16-core laptop with the input size
the task gives.

## Your reply

Reply with the complete contents of `plain.py` in one fenced code block and nothing else. You cannot compile or
run the code, so before you reply, check that it compiles with exactly the toolchain above and that it follows
every rule under "Exact input and output for this task". The examples show the exact output format; you do not
need to trace them by hand.
