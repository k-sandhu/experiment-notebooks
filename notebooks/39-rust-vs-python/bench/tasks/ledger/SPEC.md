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
