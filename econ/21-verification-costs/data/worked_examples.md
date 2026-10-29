# Worked examples and per-invoice answers

A script built this file from `cases.json`, `gold.json` (field `audit`) and `evaluations_all.json`. Amounts are in US dollars; the data files store whole cents. "Authorised" is the exact answer computed by the notebook's two rule programs.

## Calculations for the invoices discussed in the README

### test-001 (Ordinary)

| Line | Billed / received / returned / billed before | Lower unit price | Units paid for | Gross | Line discount | Line tax | Line total |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | 13 / 13 / 0 / 0 | USD 45.97 | 13 | USD 597.61 | USD 0.00 | USD 0.00 | USD 597.61 |
| P2 | 12 / 12 / 0 / 0 | USD 4.61 | 12 | USD 55.32 | USD 0.00 | USD 0.00 | USD 55.32 |
| P3 | 6 / 6 / 0 / 0 | USD 14.16 | 6 | USD 84.96 | USD 0.00 | USD 0.00 | USD 84.96 |

Lines USD 737.89; shipping USD 5.42 plus shipping tax USD 0.00; eligible credits USD 0.00; after credits USD 743.31; early-payment discount USD 0.00; earlier payments USD 0.00; kept back for a dispute USD 0.00; amount before any hold USD 743.31. Payment limit USD 9,999.99; exception none; duplicate False; blocked supplier False.

Authorised answer: **PAY USD 743.31**.

| Call | Decision | Amount | Reason as written |
|---|---|---:|---|
| Qwen3.8 Flash, first call | PAY | USD 678.95 | No holds apply; calculated net due after eligible units and lower unit price selection. |
| Qwen3.8 Flash, second call | PAY | USD 672.53 | No holds apply. Calculated net due after line discounts and shipping is within approval limit. |
| GPT-6.1 Sol | PAY | USD 743.31 | Eligible lines total 73789 cents plus 542 cents shipping; no deductions or holds apply. |
| Claude Opus 5.5 (check) | reject | | Recalculated lines 59761+5532+8496=73789, plus 542 shipping gives 74331. No tax, credits, discounts, retention, or holds apply. Expected PAY 74331, not 67895. |

### test-002 (Mixed group, recorded as `partial_returns`)

| Line | Billed / received / returned / billed before | Lower unit price | Units paid for | Gross | Line discount | Line tax | Line total |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | 12 / 16 / 1 / 6 | USD 36.65 | 9 | USD 329.85 | USD 10.98 | USD 0.00 | USD 318.87 |
| P2 | 19 / 19 / 3 / 0 | USD 27.71 | 16 | USD 443.36 | USD 11.08 | USD 27.02 | USD 459.30 |
| P3 | 11 / 18 / 1 / 4 | USD 17.59 | 11 | USD 193.49 | USD 14.51 | USD 11.19 | USD 190.17 |
| P4 | 4 / 12 / 1 / 5 | USD 64.68 | 4 | USD 258.72 | USD 32.34 | USD 14.15 | USD 240.53 |

Lines USD 1,208.87; shipping USD 8.42 plus shipping tax USD 0.53; eligible credits USD 1.02; after credits USD 1,216.80; early-payment discount USD 24.34; earlier payments USD 21.07; kept back for a dispute USD 0.00; amount before any hold USD 1,171.39. Payment limit USD 9,999.99; exception none; duplicate False; blocked supplier False.

Authorised answer: **PAY USD 1,171.39**.

| Call | Decision | Amount | Reason as written |
|---|---|---:|---|
| Qwen3.8 Flash, first call | PAY | USD 145.67 | Calculated net due after eligible units, discounts, taxes, shipping, credits, and early payment discount. |
| Qwen3.8 Flash, second call | PAY | USD 59.13 | Computed net due after eligible credits and early discount; no hold conditions met. |
| GPT-6.1 Sol | PAY | USD 1,171.39 | Eligible quantities, line discounts, taxes, posted credit, early-payment discount, and prior payments applied. No hold conditions apply. |
| Claude Opus 5.5 (check) | reject | | Recalculated pay_cents is 117139: lines total 120887, plus shipping and tax 895, minus credit 102, early discount 2434 and prior payments 2107. Candidate's 14567 is wrong. |

### test-004 (Mixed group, recorded as `discount_rounding`)

| Line | Billed / received / returned / billed before | Lower unit price | Units paid for | Gross | Line discount | Line tax | Line total |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | 7 / 9 / 2 / 0 | USD 63.22 | 7 | USD 442.54 | USD 11.06 | USD 26.97 | USD 458.45 |
| P2 | 5 / 14 / 4 / 1 | USD 16.32 | 5 | USD 81.60 | USD 6.12 | USD 4.72 | USD 80.20 |
| P3 | 18 / 29 / 3 / 6 | USD 41.08 | 18 | USD 739.44 | USD 18.49 | USD 45.06 | USD 766.01 |

Lines USD 1,304.66; shipping USD 0.54 plus shipping tax USD 0.03; eligible credits USD 3.54; after credits USD 1,301.69; early-payment discount USD 39.05; earlier payments USD 12.84; kept back for a dispute USD 0.00; amount before any hold USD 1,249.80. Payment limit USD 9,999.99; exception none; duplicate False; blocked supplier False.

Authorised answer: **PAY USD 1,249.80**.

| Call | Decision | Amount | Reason as written |
|---|---|---:|---|
| Qwen3.8 Flash, first call | PAY | USD 138.95 | Computed net due after eligible units, discounts, tax, shipping, and valid credits is within approval limit. |
| Qwen3.8 Flash, second call | PAY | USD 127.53 | Calculated net due after eligible units, discounts, tax, credits, and early payment discount. |
| GPT-6.1 Sol | PAY | USD 1,249.80 | Eligible lines, taxes, shipping, posted credit, early-payment discount, and prior payments applied. No hold conditions apply. |
| Claude Opus 5.5 (check) | reject | | Recalculated pay_cents is 124980: lines plus tax 130466, shipping and tax 57, credit 354, early discount 3905, prior payments 1284. Candidate's 13895 is wrong. |

### test-012 (Approval exception)

| Line | Billed / received / returned / billed before | Lower unit price | Units paid for | Gross | Line discount | Line tax | Line total |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | 12 / 20 / 3 / 5 | USD 44.38 | 12 | USD 532.56 | USD 0.00 | USD 0.00 | USD 532.56 |
| P2 | 4 / 16 / 4 / 6 | USD 65.91 | 4 | USD 263.64 | USD 6.59 | USD 0.00 | USD 257.05 |
| P3 | 4 / 13 / 4 / 5 | USD 27.99 | 4 | USD 111.96 | USD 8.40 | USD 9.06 | USD 112.62 |
| P4 | 16 / 17 / 2 / 2 | USD 58.43 | 13 | USD 759.59 | USD 18.99 | USD 0.00 | USD 740.60 |
| P5 | 9 / 17 / 0 / 4 | USD 17.05 | 9 | USD 153.45 | USD 5.11 | USD 12.98 | USD 161.32 |

Lines USD 1,804.15; shipping USD 3.76 plus shipping tax USD 0.33; eligible credits USD 9.40; after credits USD 1,798.84; early-payment discount USD 0.00; earlier payments USD 13.30; kept back for a dispute USD 0.00; amount before any hold USD 1,785.54. Payment limit USD 100.00; exception {"signed_day": 31, "expires_day": 30, "exception_limit_cents": 999999}; duplicate False; blocked supplier False.

Authorised answer: **HOLD USD 0.00**.

| Call | Decision | Amount | Reason as written |
|---|---|---:|---|
| Qwen3.8 Flash, first call | HOLD | USD 0.00 | Computed pay amount exceeds approval limit; exception invalid due to date range. |
| Qwen3.8 Flash, second call | HOLD | USD 0.00 | Computed pay amount exceeds approval limit; exception invalid due to signed day after today. |
| GPT-6.1 Sol | HOLD | USD 0.00 | Computed payment exceeds approval limit; approval exception is not valid today. |
| Claude Opus 5.5 (check) | accept | | Recomputed pay_cents is 178554, which exceeds the 10000 approval limit. The exception is invalid because signed_day 31 is after today_day 30. HOLD with pay_cents 0 is correct. |

### test-031 (Ordinary)

| Line | Billed / received / returned / billed before | Lower unit price | Units paid for | Gross | Line discount | Line tax | Line total |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | 4 / 4 / 0 / 0 | USD 32.77 | 4 | USD 131.08 | USD 0.00 | USD 0.00 | USD 131.08 |
| P2 | 14 / 14 / 0 / 0 | USD 14.41 | 14 | USD 201.74 | USD 0.00 | USD 0.00 | USD 201.74 |
| P3 | 5 / 5 / 0 / 0 | USD 73.53 | 5 | USD 367.65 | USD 0.00 | USD 0.00 | USD 367.65 |

Lines USD 700.47; shipping USD 6.28 plus shipping tax USD 0.00; eligible credits USD 0.00; after credits USD 706.75; early-payment discount USD 0.00; earlier payments USD 0.00; kept back for a dispute USD 0.00; amount before any hold USD 706.75. Payment limit USD 9,999.99; exception none; duplicate False; blocked supplier False.

Authorised answer: **PAY USD 706.75**.

| Call | Decision | Amount | Reason as written |
|---|---|---:|---|
| Qwen3.8 Flash, first call | PAY | USD 6.28 | All line items have zero eligible units due to previously billed units equaling received totals. Only shipping cost remains. |
| Qwen3.8 Flash, second call | PAY | USD 587.49 | All lines eligible at lower unit price; no discounts or taxes apply. Shipping added. No credits or holds. |
| GPT-6.1 Sol | PAY | USD 706.75 | Eligible lines plus shipping total 70675 cents. No deductions or hold conditions apply. |
| Claude Opus 5.5 (check) | reject | | Previously billed units are zero; all units are eligible. Lines total 13108+20174+36765=70047, plus 628 shipping gives 70675. Correct result is PAY 70675, not 628. |

### test-037 (Ordinary)

| Line | Billed / received / returned / billed before | Lower unit price | Units paid for | Gross | Line discount | Line tax | Line total |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | 6 / 6 / 0 / 0 | USD 34.67 | 6 | USD 208.02 | USD 0.00 | USD 0.00 | USD 208.02 |
| P2 | 17 / 17 / 0 / 0 | USD 34.24 | 17 | USD 582.08 | USD 0.00 | USD 0.00 | USD 582.08 |
| P3 | 11 / 11 / 0 / 0 | USD 31.31 | 11 | USD 344.41 | USD 0.00 | USD 0.00 | USD 344.41 |

Lines USD 1,134.51; shipping USD 9.30 plus shipping tax USD 0.00; eligible credits USD 0.00; after credits USD 1,143.81; early-payment discount USD 0.00; earlier payments USD 0.00; kept back for a dispute USD 0.00; amount before any hold USD 1,143.81. Payment limit USD 9,999.99; exception none; duplicate False; blocked supplier False.

Authorised answer: **PAY USD 1,143.81**.

| Call | Decision | Amount | Reason as written |
|---|---|---:|---|
| Qwen3.8 Flash, first call | PAY | USD 1,269.54 | All lines eligible and non-taxable. No discounts, credits, or holds apply. Total calculated correctly. |
| Qwen3.8 Flash, second call | PAY | USD 1,295.86 | No holds apply. Total calculated from eligible units and shipping exceeds zero; no credits or discounts reduce the amount. |
| GPT-6.1 Sol | PAY | USD 1,143.81 | Eligible lines plus shipping total 114381 cents; no credits, discounts, retention, prior payments, or holds apply. |
| Claude Opus 5.5 (check) | reject | | Lines sum to 20802+58208+34441=113451. Shipping 930 brings it to 114381. No tax, credits, discounts, retainage, or holds apply, so pay_cents should be 114381, not 126954. |

### test-043 (Ordinary)

| Line | Billed / received / returned / billed before | Lower unit price | Units paid for | Gross | Line discount | Line tax | Line total |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | 3 / 3 / 0 / 0 | USD 71.18 | 3 | USD 213.54 | USD 0.00 | USD 0.00 | USD 213.54 |
| P2 | 13 / 13 / 0 / 0 | USD 40.39 | 13 | USD 525.07 | USD 0.00 | USD 0.00 | USD 525.07 |
| P3 | 3 / 3 / 0 / 0 | USD 40.82 | 3 | USD 122.46 | USD 0.00 | USD 0.00 | USD 122.46 |

Lines USD 861.07; shipping USD 4.65 plus shipping tax USD 0.00; eligible credits USD 0.00; after credits USD 865.72; early-payment discount USD 0.00; earlier payments USD 0.00; kept back for a dispute USD 0.00; amount before any hold USD 865.72. Payment limit USD 9,999.99; exception none; duplicate False; blocked supplier False.

Authorised answer: **PAY USD 865.72**.

| Call | Decision | Amount | Reason as written |
|---|---|---:|---|
| Qwen3.8 Flash, first call | PAY | USD 1,269.58 | All lines eligible, no discounts or taxes apply. Shipping added. No credits or early payment discount. Within approval limit. |
| Qwen3.8 Flash, second call | PAY | USD 1,265.98 | No holds apply. Total calculated from eligible units and shipping. No credits or early discount applicable. |
| GPT-6.1 Sol | PAY | USD 865.72 | Eligible lines plus shipping total 86572 cents; no deductions or holds apply. |
| Claude Opus 5.5 (check) | reject | | Lines total 21354+52507+12246=86107, plus 465 shipping = 86572. No tax, credits, discount, or retention apply, so the correct result is PAY 86572, not 126958. |

### test-055 (Ordinary)

| Line | Billed / received / returned / billed before | Lower unit price | Units paid for | Gross | Line discount | Line tax | Line total |
|---|---|---:|---:|---:|---:|---:|---:|
| P1 | 9 / 9 / 0 / 0 | USD 28.83 | 9 | USD 259.47 | USD 0.00 | USD 0.00 | USD 259.47 |
| P2 | 10 / 10 / 0 / 0 | USD 7.82 | 10 | USD 78.20 | USD 0.00 | USD 0.00 | USD 78.20 |
| P3 | 13 / 13 / 0 / 0 | USD 5.56 | 13 | USD 72.28 | USD 0.00 | USD 0.00 | USD 72.28 |

Lines USD 409.95; shipping USD 0.30 plus shipping tax USD 0.00; eligible credits USD 0.00; after credits USD 410.25; early-payment discount USD 0.00; earlier payments USD 0.00; kept back for a dispute USD 0.00; amount before any hold USD 410.25. Payment limit USD 9,999.99; exception none; duplicate False; blocked supplier False.

Authorised answer: **PAY USD 410.25**.

| Call | Decision | Amount | Reason as written |
|---|---|---:|---|
| Qwen3.8 Flash, first call | PAY | USD 346.79 | No holds apply. Calculated net due after eligible units, discounts, tax, shipping, and credits is 34679 cents. |
| Qwen3.8 Flash, second call | PAY | USD 349.17 | Calculated net due after eligible units and lower unit prices; no holds or credits apply. |
| GPT-6.1 Sol | PAY | USD 410.25 | Eligible line amounts plus shipping total 41025 cents; no adjustments or holds apply. |
| Claude Opus 5.5 (check) | reject | | Lines total 25947+7820+7228=40995, plus 30 shipping gives 41025. No tax, credits, discounts, payments, retention or holds apply. The correct result is PAY 41025, not 34679. |

## All 72 test invoices

One row per invoice. "Match" is the repeat check: whether the two Qwen answers agree to the cent. "Claude" is Claude's verdict on the first Qwen answer.

| Invoice | Group | Authorised | Qwen, first call | Qwen, second call | Match | GPT-6.1 Sol | Claude |
|---|---|---|---|---|---|---|---|
| test-001 | Ordinary | PAY USD 743.31 | PAY USD 678.95 | PAY USD 672.53 | no | PAY USD 743.31 | reject |
| test-002 | Mixed | PAY USD 1,171.39 | PAY USD 145.67 | PAY USD 59.13 | no | PAY USD 1,171.39 | reject |
| test-003 | Mixed | PAY USD 1,974.97 | PAY USD 126.94 | PAY USD 129.57 | no | PAY USD 1,974.97 | reject |
| test-004 | Mixed | PAY USD 1,249.80 | PAY USD 138.95 | PAY USD 127.53 | no | PAY USD 1,249.80 | reject |
| test-005 | Dispute | PAY USD 1,274.38 | PAY USD 13.69 | PAY USD 129.73 | no | PAY USD 1,274.38 | reject |
| test-006 | Approval exception | PAY USD 2,595.29 | PAY USD 138.94 | PAY USD 123.75 | no | PAY USD 2,595.29 | reject |
| test-007 | Ordinary | PAY USD 423.97 | PAY USD 329.45 | PAY USD 315.96 | no | PAY USD 423.97 | reject |
| test-008 | Mixed | PAY USD 1,718.51 | PAY USD 136.95 | PAY USD 129.57 | no | PAY USD 1,718.51 | reject |
| test-009 | Mixed | PAY USD 3,654.87 | PAY USD 1,564.87 | PAY USD 2,175.83 | no | PAY USD 3,654.87 | reject |
| test-010 | Mixed | PAY USD 1,750.42 | PAY USD 269.45 | PAY USD 24.59 | no | PAY USD 1,750.42 | reject |
| test-011 | Dispute | PAY USD 2,716.60 | PAY USD 245.67 | PAY USD 245.37 | no | PAY USD 2,716.60 | reject |
| test-012 | Approval exception | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-013 | Ordinary | PAY USD 1,880.94 | PAY USD 1,289.46 | PAY USD 1,295.74 | no | PAY USD 1,880.94 | reject |
| test-014 | Mixed | PAY USD 2,814.50 | PAY USD 269.53 | PAY USD 275.93 | no | PAY USD 2,814.50 | reject |
| test-015 | Mixed | PAY USD 1,429.70 | PAY USD 38.46 | PAY USD 27.39 | no | PAY USD 1,429.70 | reject |
| test-016 | Mixed | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-017 | Dispute | PAY USD 1,173.00 | PAY USD 2.64 | PAY USD 29.53 | no | PAY USD 1,173.00 | reject |
| test-018 | Approval exception | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-019 | Ordinary | PAY USD 1,718.72 | PAY USD 1,365.82 | PAY USD 1,265.84 | no | PAY USD 1,718.72 | reject |
| test-020 | Mixed | PAY USD 1,894.62 | PAY USD 136.95 | PAY USD 137.59 | no | PAY USD 1,894.62 | reject |
| test-021 | Mixed | PAY USD 1,002.25 | PAY USD 369.54 | PAY USD 59.73 | no | PAY USD 1,002.25 | reject |
| test-022 | Mixed | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-023 | Dispute | PAY USD 1,293.73 | PAY USD 14.56 | PAY USD 145.86 | no | PAY USD 1,293.73 | reject |
| test-024 | Approval exception | PAY USD 1,142.73 | PAY USD 16.53 | PAY USD 17.53 | no | PAY USD 1,142.73 | reject |
| test-025 | Ordinary | PAY USD 1,683.95 | PAY USD 1,384.67 | PAY USD 1,397.86 | no | PAY USD 1,683.95 | reject |
| test-026 | Mixed | PAY USD 1,179.88 | PAY USD 13.89 | PAY USD 15.74 | no | PAY USD 1,179.88 | reject |
| test-027 | Mixed | PAY USD 1,914.48 | PAY USD 136.95 | PAY USD 156.38 | no | PAY USD 1,914.48 | reject |
| test-028 | Mixed | PAY USD 1,145.99 | PAY USD 136.95 | PAY USD 315.76 | no | PAY USD 1,145.99 | reject |
| test-029 | Dispute | PAY USD 593.81 | PAY USD 16.45 | PAY USD 17.53 | no | PAY USD 593.81 | reject |
| test-030 | Approval exception | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-031 | Ordinary | PAY USD 706.75 | PAY USD 6.28 | PAY USD 587.49 | no | PAY USD 706.75 | reject |
| test-032 | Mixed | PAY USD 1,559.72 | PAY USD 158.46 | PAY USD 157.84 | no | PAY USD 1,559.72 | reject |
| test-033 | Mixed | PAY USD 2,448.42 | PAY USD 1,289.56 | PAY USD 129.57 | no | PAY USD 2,448.42 | reject |
| test-034 | Mixed | PAY USD 1,674.75 | PAY USD 126.95 | PAY USD 127.58 | no | PAY USD 1,674.75 | reject |
| test-035 | Dispute | PAY USD 764.90 | PAY USD 26.94 | PAY USD 21.78 | no | PAY USD 764.90 | reject |
| test-036 | Approval exception | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-037 | Ordinary | PAY USD 1,143.81 | PAY USD 1,269.54 | PAY USD 1,295.86 | no | PAY USD 1,143.81 | reject |
| test-038 | Mixed | PAY USD 1,068.12 | PAY USD 126.95 | PAY USD 127.54 | no | PAY USD 1,068.12 | reject |
| test-039 | Mixed | PAY USD 2,537.15 | PAY USD 168.45 | PAY USD 215.76 | no | PAY USD 2,537.15 | reject |
| test-040 | Mixed | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-041 | Dispute | PAY USD 1,762.08 | PAY USD 26.95 | PAY USD 29.57 | no | PAY USD 1,762.08 | reject |
| test-042 | Approval exception | PAY USD 2,067.62 | PAY USD 138.95 | PAY USD 137.58 | no | PAY USD 2,067.62 | reject |
| test-043 | Ordinary | PAY USD 865.72 | PAY USD 1,269.58 | PAY USD 1,265.98 | no | PAY USD 865.72 | reject |
| test-044 | Mixed | PAY USD 2,324.91 | PAY USD 138.95 | PAY USD 127.58 | no | PAY USD 2,324.91 | reject |
| test-045 | Mixed | PAY USD 1,784.65 | PAY USD 129.36 | PAY USD 1,297.36 | no | PAY USD 1,784.65 | reject |
| test-046 | Mixed | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-047 | Dispute | PAY USD 1,022.37 | PAY USD 138.95 | PAY USD 126.59 | no | PAY USD 1,022.37 | reject |
| test-048 | Approval exception | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-049 | Ordinary | PAY USD 1,600.95 | PAY USD 1,365.87 | PAY USD 1,578.23 | no | PAY USD 1,600.95 | reject |
| test-050 | Mixed | PAY USD 1,418.17 | PAY USD 136.94 | PAY USD 129.37 | no | PAY USD 1,418.17 | reject |
| test-051 | Mixed | PAY USD 2,106.77 | PAY USD 964.37 | PAY USD 237.96 | no | PAY USD 2,106.77 | reject |
| test-052 | Mixed | PAY USD 1,015.78 | PAY USD 389.46 | PAY USD 148.97 | no | PAY USD 1,015.78 | reject |
| test-053 | Dispute | PAY USD 1,012.65 | PAY USD 124.67 | PAY USD 127.48 | no | PAY USD 1,012.65 | reject |
| test-054 | Approval exception | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-055 | Ordinary | PAY USD 410.25 | PAY USD 346.79 | PAY USD 349.17 | no | PAY USD 410.25 | reject |
| test-056 | Mixed | PAY USD 811.46 | PAY USD 389.17 | PAY USD 217.38 | no | PAY USD 811.46 | reject |
| test-057 | Mixed | PAY USD 764.97 | PAY USD 36.91 | PAY USD 24.91 | no | PAY USD 764.97 | reject |
| test-058 | Mixed | PAY USD 929.69 | PAY USD 143.62 | PAY USD 12.34 | no | PAY USD 929.69 | reject |
| test-059 | Dispute | PAY USD 1,290.00 | PAY USD 136.47 | PAY USD 137.42 | no | PAY USD 1,290.00 | reject |
| test-060 | Approval exception | PAY USD 896.08 | PAY USD 38.95 | PAY USD 25.17 | no | PAY USD 896.08 | reject |
| test-061 | Ordinary | PAY USD 1,472.92 | PAY USD 925.87 | PAY USD 789.52 | no | PAY USD 1,472.92 | reject |
| test-062 | Mixed | PAY USD 1,865.46 | PAY USD 138.54 | PAY USD 157.38 | no | PAY USD 1,865.46 | reject |
| test-063 | Mixed | PAY USD 2,005.18 | PAY USD 128.95 | PAY USD 129.57 | no | PAY USD 2,005.18 | reject |
| test-064 | Mixed | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-065 | Dispute | PAY USD 1,948.96 | PAY USD 138.94 | PAY USD 127.38 | no | PAY USD 1,948.96 | reject |
| test-066 | Approval exception | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-067 | Ordinary | PAY USD 788.43 | PAY USD 528.43 | PAY USD 483.15 | no | PAY USD 788.43 | reject |
| test-068 | Mixed | PAY USD 2,651.36 | PAY USD 2,491.75 | PAY USD 217.59 | no | PAY USD 2,651.36 | reject |
| test-069 | Mixed | PAY USD 2,359.84 | PAY USD 178.53 | PAY USD 215.34 | no | PAY USD 2,359.84 | reject |
| test-070 | Mixed | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
| test-071 | Dispute | PAY USD 1,380.49 | PAY USD 98.45 | PAY USD 29.53 | no | PAY USD 1,380.49 | reject |
| test-072 | Approval exception | HOLD USD 0.00 | HOLD USD 0.00 | HOLD USD 0.00 | yes | HOLD USD 0.00 | accept |
