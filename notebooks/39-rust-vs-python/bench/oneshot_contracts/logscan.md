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
