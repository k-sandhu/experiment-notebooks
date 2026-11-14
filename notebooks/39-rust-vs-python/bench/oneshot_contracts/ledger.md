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
