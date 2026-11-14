Write one program in Java for the task described below. Its run time and memory use will be measured.

The program is `Main.java` (class `Main`, no package): Java 23, compiled with `javac`. Java SE only, plus Jackson 2.22 (core, databind and annotations) on the class path. It is run as `java -cp "out;lib\*" Main INPUT_PATH` with the default JVM settings (the task says if it takes more arguments).

Your goals, in order:

1. The program must print the correct output for any valid input as the task defines it, not only for the
   examples.
2. Make it as fast as you can. Write it the way a skilled Java developer would write fast code, using the
   language's own strengths.

Use a single thread and a single process unless the task says otherwise. Do not precompute or embed answers,
start other programs, or read any file other than the input. The program will be run on Windows 11 on a 16-core
laptop, on larger inputs of the same kind; the task gives the benchmark size.

Reply with the complete contents of `Main.java` in one fenced code block and nothing else. You cannot run or test
the code, so check it carefully before you reply.

The task:

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

Example `s1` input:

<input>
{"rates": {"USD": 1000000, "EUR": 1083250, "JPY": 6612, "GBP": 1295000, "CAD": 724500, "AUD": 658000, "CHF": 1144000, "INR": 11910}}
{"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"type":"credit","amount":"1","meta":{"channel":"branch","ts":"2026-10-30T14:22:05Z","note":"rent \"October\"","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"account":"AC-00000","currency":"USD","tags":[],"id":0}
{"currency": "USD", "meta": {"channel": "mobile", "ts": "2026-10-30T14:22:05Z", "note": "folder \\ archive", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "tags": [], "type": "credit", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "id": 1, "account": "AC-00001", "amount": "1"}
{"currency" :  "USD",  "tags" :  [],  "id" :  2,  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "type" :  "credit",  "meta" :  {"channel" :  "web",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "path \/receipt",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "amount" :  "1",  "account" :  "AC-00002"}
{"type":"credit","currency":"USD","account":"AC-00003","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"tags":[],"amount":"1","id":3,"meta":{"channel":"atm","ts":"2026-10-30T14:22:05Z","note":"line\nnext","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}}}
{"currency": "USD", "tags": [], "meta": {"channel": "api", "ts": "2026-10-30T14:22:05Z", "note": "caf\u00e9", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "account": "AC-00004", "amount": "1", "id": 4, "type": "credit"}
{"meta" :  {"channel" :  "phone",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "naïve raw UTF-8",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "id" :  5,  "tags" :  [],  "account" :  "AC-00005",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "currency" :  "USD",  "amount" :  "1",  "type" :  "credit"}
{"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"id":6,"type":"credit","amount":"1","currency":"USD","meta":{"channel":"branch","ts":"2026-10-30T14:22:05Z","note":"emoji \ud83d\ude00","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"tags":[],"account":"AC-00006"}
{"amount": "1", "meta": {"channel": "mobile", "ts": "2026-10-30T14:22:05Z", "note": "rent \"October\"", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "tags": [], "currency": "USD", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "account": "AC-00007", "id": 7, "type": "credit"}
{"currency" :  "USD",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "account" :  "AC-00008",  "id" :  8,  "meta" :  {"channel" :  "web",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "folder \\ archive",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "tags" :  [],  "type" :  "credit",  "amount" :  "1"}
{"meta":{"channel":"atm","ts":"2026-10-30T14:22:05Z","note":"path \/receipt","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"currency":"USD","amount":"1","id":9,"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"tags":[],"type":"credit","account":"AC-00009"}
{"meta": {"channel": "api", "ts": "2026-10-30T14:22:05Z", "note": "line\nnext", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "id": 10, "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "type": "credit", "account": "AC-00010", "tags": [], "amount": "1", "currency": "USD"}
{"meta" :  {"channel" :  "phone",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "caf\u00e9",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "type" :  "credit",  "amount" :  "1",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "currency" :  "USD",  "account" :  "AC-00011",  "tags" :  [],  "id" :  11}
{"currency":"INR","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"id":12,"account":"AC-00003","type":"credit","meta":{"channel":"branch","ts":"2026-10-30T14:22:05Z","note":"naïve raw UTF-8","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"tags":[],"amount":"0"}
{"tags": [], "currency": "CAD", "id": 13, "type": "credit", "meta": {"channel": "mobile", "ts": "2026-10-30T14:22:05Z", "note": "emoji \ud83d\ude00", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "account": "AC-00001", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "amount": "0"}
{"meta" :  {"channel" :  "web",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "rent \"October\"",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "amount" :  "0",  "tags" :  [],  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "account" :  "AC-00000",  "currency" :  "INR",  "type" :  "refund",  "id" :  14}
{"amount":"0","account":"AC-00000","type":"debit","currency":"JPY","id":15,"meta":{"channel":"atm","ts":"2026-10-30T14:22:05Z","note":"folder \\ archive","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"tags":[],"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}}
{"extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "currency": "EUR", "account": "AC-00002", "id": 16, "meta": {"channel": "api", "ts": "2026-10-30T14:22:05Z", "note": "path \/receipt", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "tags": ["Test"], "amount": "0", "type": "credit"}
{"type" :  "credit",  "id" :  17,  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "currency" :  "GBP",  "meta" :  {"channel" :  "phone",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "line\nnext",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "account" :  "AC-00000",  "tags" :  [],  "amount" :  "0"}
{"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"tags":[],"amount":"0","type":"credit","id":18,"meta":{"channel":"branch","ts":"2026-10-30T14:22:05Z","note":"caf\u00e9","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"currency":"GBP","account":"AC-00000"}
{"amount": "0", "type": "credit", "account": "AC-00002", "id": 19, "tags": [], "meta": {"channel": "mobile", "ts": "2026-10-30T14:22:05Z", "note": "naïve raw UTF-8", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "currency": "USD", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}
{"id" :  20,  "amount" :  "0",  "tags" :  [],  "currency" :  "USD",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "meta" :  {"channel" :  "web",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "emoji \ud83d\ude00",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "type" :  "void",  "account" :  "AC-00005"}
{"tags":["test"],"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"currency":"AUD","meta":{"channel":"atm","ts":"2026-10-30T14:22:05Z","note":"rent \"October\"","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"amount":"0","type":"credit","account":"AC-00003","id":21}
{"currency": "INR", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "tags": ["testing"], "meta": {"channel": "api", "ts": "2026-10-30T14:22:05Z", "note": "folder \\ archive", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "account": "AC-00000", "id": 22, "type": "credit", "amount": "0"}
{"id" :  23,  "amount" :  "0",  "account" :  "AC-00000",  "type" :  "credit",  "meta" :  {"channel" :  "phone",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "path \/receipt",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "tags" :  ["Test"],  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "currency" :  "JPY"}
{"meta":{"channel":"branch","ts":"2026-10-30T14:22:05Z","note":"line\nnext","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"account":"AC-00007","currency":"JPY","tags":[],"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"amount":"0","type":"void","id":24}
{"currency": "EUR", "id": 25, "account": "AC-00000", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "meta": {"channel": "mobile", "ts": "2026-10-30T14:22:05Z", "note": "caf\u00e9", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "tags": [], "amount": "0", "type": "void"}
{"tags" :  ["test"],  "meta" :  {"channel" :  "web",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "naïve raw UTF-8",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "currency" :  "JPY",  "id" :  26,  "amount" :  "0",  "account" :  "AC-00003",  "type" :  "credit",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}}
{"amount":"0","id":27,"meta":{"channel":"atm","ts":"2026-10-30T14:22:05Z","note":"emoji \ud83d\ude00","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"account":"AC-00004","type":"credit","currency":"INR","tags":[]}
{"tags": [], "type": "debit", "account": "AC-00005", "amount": "0", "meta": {"channel": "api", "ts": "2026-10-30T14:22:05Z", "note": "rent \"October\"", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "currency": "EUR", "id": 28, "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}
{"tags" :  ["rent"],  "currency" :  "CHF",  "amount" :  "0",  "type" :  "credit",  "id" :  29,  "account" :  "AC-00006",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "meta" :  {"channel" :  "phone",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "folder \\ archive",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}}}
{"amount":"0","id":30,"type":"credit","account":"AC-00000","tags":[],"meta":{"channel":"branch","ts":"2026-10-30T14:22:05Z","note":"path \/receipt","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"currency":"JPY"}
{"tags": [], "currency": "EUR", "id": 31, "account": "AC-00000", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "meta": {"channel": "mobile", "ts": "2026-10-30T14:22:05Z", "note": "line\nnext", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "amount": "0", "type": "credit"}
{"tags" :  [],  "meta" :  {"channel" :  "web",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "caf\u00e9",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "amount" :  "0",  "id" :  32,  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "type" :  "credit",  "currency" :  "AUD",  "account" :  "AC-00000"}
{"amount":"0","currency":"JPY","id":33,"type":"credit","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"tags":[],"account":"AC-00000","meta":{"channel":"atm","ts":"2026-10-30T14:22:05Z","note":"naïve raw UTF-8","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}}}
{"account": "AC-00000", "tags": [], "id": 34, "amount": "0", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "meta": {"channel": "api", "ts": "2026-10-30T14:22:05Z", "note": "emoji \ud83d\ude00", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "type": "debit", "currency": "GBP"}
{"extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "type" :  "credit",  "id" :  35,  "meta" :  {"channel" :  "phone",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "rent \"October\"",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "tags" :  [],  "amount" :  "0",  "account" :  "AC-00004",  "currency" :  "JPY"}
{"type":"debit","tags":[],"id":36,"amount":"0","meta":{"channel":"branch","ts":"2026-10-30T14:22:05Z","note":"folder \\ archive","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"account":"AC-00000","currency":"USD"}
{"meta": {"channel": "mobile", "ts": "2026-10-30T14:22:05Z", "note": "path \/receipt", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "tags": [], "currency": "CAD", "type": "debit", "amount": "0", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "account": "AC-00002", "id": 37}
{"amount" :  "0",  "tags" :  [],  "currency" :  "INR",  "id" :  38,  "meta" :  {"channel" :  "web",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "line\nnext",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "account" :  "AC-00006",  "type" :  "debit"}
{"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"id":39,"currency":"AUD","type":"debit","meta":{"channel":"atm","ts":"2026-10-30T14:22:05Z","note":"caf\u00e9","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"tags":[],"amount":"0","account":"AC-00005"}
{"currency": "AUD", "type": "credit", "account": "AC-00004", "amount": "0", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "meta": {"channel": "api", "ts": "2026-10-30T14:22:05Z", "note": "naïve raw UTF-8", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "id": 40, "tags": ["payroll"]}
{"account" :  "AC-00000",  "id" :  41,  "amount" :  "0",  "tags" :  [],  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "meta" :  {"channel" :  "phone",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "emoji \ud83d\ude00",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "currency" :  "GBP",  "type" :  "debit"}
{"id":42,"amount":"0","account":"AC-00008","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"currency":"JPY","type":"credit","tags":[],"meta":{"channel":"branch","ts":"2026-10-30T14:22:05Z","note":"rent \"October\"","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}}}
{"currency": "CHF", "amount": "0", "meta": {"channel": "mobile", "ts": "2026-10-30T14:22:05Z", "note": "folder \\ archive", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "account": "AC-00004", "tags": [], "type": "credit", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "id": 43}
{"meta" :  {"channel" :  "web",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "path \/receipt",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "amount" :  "0",  "id" :  44,  "tags" :  [],  "account" :  "AC-00005",  "type" :  "credit",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "currency" :  "EUR"}
{"extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]},"type":"credit","account":"AC-00000","currency":"INR","amount":"0","id":45,"meta":{"channel":"atm","ts":"2026-10-30T14:22:05Z","note":"line\nnext","extra":{"account":"ignored","tags":["test",{"type":"void"}],"x":[1,null,true]}},"tags":["Test"]}
{"type": "credit", "currency": "INR", "meta": {"channel": "api", "ts": "2026-10-30T14:22:05Z", "note": "caf\u00e9", "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}}, "id": 46, "tags": [], "extra": {"account": "ignored", "tags": ["test", {"type": "void"}], "x": [1, null, true]}, "amount": "0", "account": "AC-00004"}
{"type" :  "credit",  "account" :  "AC-00000",  "currency" :  "CAD",  "id" :  47,  "meta" :  {"channel" :  "phone",  "ts" :  "2026-10-30T14:22:05Z",  "note" :  "naïve raw UTF-8",  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]}},  "extra" :  {"account" :  "ignored",  "tags" :  ["test",  {"type" :  "void"}],  "x" :  [1,  null,  true]},  "tags" :  [],  "amount" :  "0"}
</input>

Expected output:

<output>
counted 43
net 1200
channel api 8 200
channel atm 7 200
channel branch 7 200
channel mobile 7 200
channel phone 8 200
channel web 6 200
account AC-00000 100
account AC-00001 100
account AC-00002 100
account AC-00003 100
account AC-00004 100
account AC-00005 100
account AC-00006 100
account AC-00007 100
account AC-00008 100
account AC-00009 100
</output>
