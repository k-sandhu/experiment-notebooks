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
