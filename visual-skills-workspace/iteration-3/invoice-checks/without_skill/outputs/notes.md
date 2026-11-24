# Invoice checks explainer: notes

Files: `explainer.html` (self-contained; Inter from Google Fonts, falls back to system fonts offline; no JS libraries), `explainer.gif` (the five story steps, then a price sweep from $0.0005 to $0.50 in the calculator).

## Message

Letting a cheap model answer first and checking it saves money only when the expensive calls avoided are worth more than the check. On the 72 test invoices, both checks avoided the same 14 expensive calls (0.194 per invoice). Asking the cheap model twice costs almost nothing, so it is cheapest whenever an expensive call costs more than about $0.0011. A Claude review costs $0.0259 per invoice, so it only pays above about $0.133 per expensive call, and even then asking twice is cheaper. Caveat: the checks never met a hard case and the cheap model was right only on holds.

## Structure

1. Header: the question in plain words for a finance manager.
2. "Three ways to get every invoice right": cards for expensive model on every invoice, cheap + ask-twice check, cheap + reviewer check, with the right-answer rule (decision and amount to the cent).
3. Stepped story (Back/Next, 5 steps) beside a 12x6 grid, one square per invoice (test-001..072), with tooltips and a running case (test-002):
   1. 58 to pay, 14 to hold.
   2. Cheap model alone: 14 right (all holds), 58 wrong; average error $930.02 per invoice.
   3. Checks: both accept the same 14, flag the 58, 0 mistakes let through.
   4. Expensive model answers the 58: 72/72 right, 58 calls instead of 72.
   5. Break-even: $0.0011 (ask twice) and $0.133 (review).
4. Break-even cards with the arithmetic.
5. Calculator: log slider for the expensive-model price ($0.0005 to $0.50) with presets ($0.005, $0.05, $0.25 from the study, and both break-evens), invoices per month (default 10,000). Outputs: a verdict sentence naming the cheapest route, stacked bars (measured cheap/check cost + expensive calls at your price) with two off-scale reference routes, and a savings-vs-price line chart with break-even markers (clickable to set the price).
6. Caveats. 7. Source footer.

## Where every number comes from

All computed in the page from `data.json` (embedded verbatim subset) unless noted.

- 72 invoices, 58 PAY / 14 HOLD, cheap model right on 14, 58 escalations: counted from `invoice_rows` (gold_status, Qwen direct `correct`, Qwen repeat + GPT `gpt_invocations`). Both check routes have identical escalation sets (verified in Python).
- Average error $930.02: mean of Qwen direct `payment_deviation_usd` (matches summary `mean_payment_deviation_usd` 930.0124). Range $63 to $2,545: min/max of the same column (test-055, test-014).
- Split of holds (6 duplicate/blocked, 8 expired or unsigned exception), two rules programs agree, "within $1 would have paid 8 wrong answers", "no calculator, reasoning off": facts.md.
- test-002 figures ($1,171.39 exact; $145.67 and $59.13 from Qwen; short $1,025.72; GPT exact; Claude rejected with recalculation): facts.md. $0.028 for cheap answer + review on test-002: `known_model_cost` 0.02822 in the Claude screen + GPT row.
- Cheap model about $0.00014 per invoice: cost_lines Qwen direct known_model_cost_mean 0.0001444.
- Check costs $0.000218 and $0.0259 per invoice, slope 0.8056: `cost_lines`. 0.194 calls saved = 14/72.
- Break-evens $0.0011 and $0.133: `break_even.source_file` zero_loss_break_even_gpt_price (0.0011189, 0.1332038); recomputed from rows (0.0011189, 0.1332036). "About 120 times": 0.0259/0.0002176 = 119.
- Calculator cost = known + G x gpt_invocations_mean + H x review_fraction + a x overpayment + b x underpayment, with H = $1, a = 1%, b = 0.1% (notebook's running example). Cheap model alone and reviewer + person use the same formula; their costs are dominated by those assumptions and are labelled so.
- Price range $0.005 to $0.25 described as the study's assumption: facts.md.

## What I checked

- Recomputed counts, means, escalation sets and break-evens from the 360 invoice rows in Python; all match `summary`, `cost_lines` and `break_even`.
- Calculator against `cost_scenario_checkpoints`: at $0.05 and 10,000 invoices the page shows $500 / $405 / $662 (checkpoints 0.0500, 0.0405, 0.06618 per invoice), at $0.25 $2,016 and a $227 reviewer saving (0.20161, 0.22729), cheap model alone $9,964 (0.99636), reviewer + person $8,315 (0.83146).
- Verdict switches at the right prices: $0.0010 expensive-only cheapest, $0.0012 ask-twice cheapest; reviewer costs more at $0.130 and saves at $0.140.
- Headless Chromium (Playwright): no console or page errors; no horizontal scroll at 1280 px or 390 px; light and dark themes rendered and inspected; all five steps screenshotted and read; chart label overlaps and a clipped off-scale label on phone fixed after inspection.
- Not checked: screen-reader pass, browsers other than Chromium.
