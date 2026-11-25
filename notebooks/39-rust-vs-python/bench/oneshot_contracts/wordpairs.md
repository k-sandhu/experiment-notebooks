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
