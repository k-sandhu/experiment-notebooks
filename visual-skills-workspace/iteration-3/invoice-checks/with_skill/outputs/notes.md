# Invoice checks explainer: notes

## Message

On the 72 test invoices, letting the cheap model answer and checking it before payment saves money once one
expensive call costs more than **$0.0011** with the "ask twice" check, but only above **$0.133** with Claude review.
Even then the saving is at most **19%** of the expensive bill, because the cheap model got only the 14 holds right and
the other 58 invoices still had to go to the expensive model.

- Reader: finance managers on an artifact page, reader-paced, a couple of minutes.
- Misconception it addresses: "a cheap model plus a check is always cheaper", or "any check pays".
- Form: `explorable-model` (primary) in a 7-step stepper built with `explainer-kit`. Style `editorial`
  (light, crisp, data next to prose). Steps 1-3 borrow from `unit-story` (each invoice is one dot that keeps its identity).

## Storyboard (steps)

1. **72 test invoices.** 72 dots, 58 grey (should be paid an exact amount) and 14 amber (should be held). Example card: test-002, right answer PAY $1,171.39. The rule: right only if the decision and the amount match to the cent.
2. **Cheap model alone.** The same dots recolour: 14 green (all holds), 58 red. test-002: cheap model paid $145.67. Average underpayment $923 per invoice. Cost about $0.00014 per invoice.
3. **Check, then escalate.** The two checks are explained in one line each. The dots split into 14 accepted (paid on the cheap answer) and 58 sent to GPT-6.1 Sol, all then right. test-002: $145.67, then $59.13, no match, so expensive model answered $1,171.39.
4. **Bill at 5 cents a call.** Monthly bill bars at 10,000 invoices a month (labelled as an example) and an assumed $0.05 per call: Expensive only $500, Ask twice $405 (✓ cheapest), Claude review $662. The red part of each bar is the checking cost. The note explains the two routes left out: the cheap model alone, and Claude review with a person.
5. **Where it flips.** Chart: monthly saving compared with "Expensive only" against the price of one expensive call, with one line per check. The zero line is "Expensive only". A marker sweeps the price by itself and pauses at Claude's break-even ($0.133). Ask twice's break-even ($0.0011) is marked at the origin.
6. **Your turn.** A price slider ($0.0005 to $0.30, assumed) and volume buttons (1,000 / 10,000 / 100,000 invoices a month). The chart marker, the monthly bill bars and a two-line verdict ("Cheapest at $X a call: ..., $Y a month / It saves $Z a month vs Expensive only") all update live. There is an idle demo after 5 s.
7. **What to take away.** Ask twice pays from $0.0011 per call, as long as it keeps the to-the-cent rule. Claude review pays only above $0.133. The saving tops out at 19%. Limits: with 72 invoices the share skipped could be 12-30% (Wilson 95%), which puts Claude's break-even between $0.086 and $0.217. The expensive price is assumed and Claude's cost is its list price. Within a $1 match, Ask twice would have paid 8 wrong amounts. Caption: both checks scored 72 of 72 and chose the same way on every invoice, so the test cannot rank them on harder mistakes. The cheap model ran without reasoning.

Colour meanings, kept for the whole piece: grey = should be paid, amber = should be held, green = cheap answer right, red = cheap answer wrong
(and checking cost in bars), ink/black = Expensive only, blue = Ask twice, violet = Claude review.

## Where every number comes from

All inputs come from `evals/invoice-checks/files/data.json`. They sit in a `DATA` block at the top of the scene, and every number on
screen is computed from it by one `model(g, v)` function.

| On screen | Value | Source |
|---|---|---|
| 72 invoices, 58 pay, 14 hold | 72/58/14 | `invoice_rows` gold_status; `summary.n`; facts.md |
| Hold invoice ids | test-012, -016, ... -072 | `invoice_rows` (gold_status HOLD); identical to Qwen-correct and no-GPT ids for both check routes |
| Cheap model right 14 of 72, all holds | 14 | `summary` Qwen direct automatic_correct; recomputed from invoice_rows |
| Cheap model cost ~$0.00014/invoice | 0.0001444 | `cost_lines` Qwen direct known_model_cost_mean |
| Underpays $923 per invoice on average | 922.66 | `summary` mean_underpayment_exposure_usd (922.6569) |
| test-002: $1,171.39 right, $145.67 / $59.13 cheap | | facts.md concrete invoices (14567 and 5913 cents) |
| 58 sent to expensive model, 14 accepted, 72/72 right | 58 | `summary` gpt_escalations for both check routes; invoice_rows |
| Check cost per invoice: Ask twice $0.0002176, Claude $0.0259 | | `cost_lines` known_model_cost_mean |
| Expensive calls per invoice 58/72 = 0.8056 | | `cost_lines` gpt_invocations_mean |
| Monthly bill = volume x (check cost + 0.8056 x price) | | cost line formula in `about.cost_lines` (losses are 0 for these three routes) |
| $500 / $405 / $662 at $0.05, 10,000 invoices | | model; equals `cost_scenario_checkpoints` 0.0500 / 0.0405 / 0.0662 per invoice x 10,000 |
| 8,056 expensive calls | 10,000 x 58/72 | model |
| Break-even $0.0011 and $0.133 | 0.0011189, 0.1332 | `break_even.recomputed`; model recomputes check cost / (1 - 0.8056) = 0.0011191 and 0.1332 |
| 19% cap | 14/72 = 0.194 | `break_even.gpt_invocations_saved_per_invoice` |
| 12-30% range | Wilson 95% for 14/72 = 0.1195-0.3003 | `summary` correct_ci_low/high (also K.wilson) |
| Claude break-even $0.086-$0.217 | 0.0259/0.3003, 0.0259/0.1195 | **derived here** from the above; labelled as a range on similar invoices |
| Claude + person: $0.83 per invoice, $8,315 a month | 0.8315 | `cost_lines` Claude screen + review intercept (assumes $1 per person review) |
| Within $1 Ask twice would pay 8 wrong amounts | 8 | facts.md caveats |
| Model names (Qwen3.8 Flash, GPT-6.1 Sol, Claude Opus 5.5), reasoning off | | facts.md |

Assumptions that are shown as assumptions on screen: the expensive model's price per call (the slider is labelled "assumed", as are the
step 4 heading and the chart axis), the monthly volume (labelled as an example), and Claude's cost at list price. The 10,000 invoices and
the $0.05 price in step 4 are the study's running example price combined with an example volume.

## What I checked

- `render_check.py` passes at 360 px and 560 px, and with reduced motion: no errors, overflow, text overlap, tiny text, moving controls
  or height changes. (Earlier runs failed on the step 6 action row being 3 px too tall and on titles wrapping at 360 px. Both are fixed.)
- I looked at the contact sheets and the individual frames for steps 3, 5, 6 and 7. I fixed the step 3 text overlapping the dots,
  the step 5 break-even labels crossing the lines, and the marker value labels sitting on the line labels.
- A Playwright sweep of step 6 drove the slider through 121 prices at each of the 3 volumes (363 states). It found 0 SVG text
  overlaps and 0 texts outside the drawing. Marker labels switch sides, or dim the fixed label they would cover.
- Model values match `cost_scenario_checkpoints` at $0.005, $0.05 and $0.25 (for example Ask twice 0.004245 / 0.0405 / 0.2016, Claude
  0.02993 / 0.06618 / 0.22729 per invoice). The break-evens recomputed in the page are 0.0011191 and 0.1332. The verdict flips from
  "Expensive only" to "Ask twice" between $0.0010 and $0.0015. Claude review is never the cheapest, because it has the same slope
  as Ask twice and a higher check cost.
- Recorded `explainer.mp4` (46 s, 2.9 MB) and `explainer.gif` (4.8 MB) with `record.py`. I checked one frame every 5 s of the MP4.
- Not checked: dark mode (the editorial style is light only), and screen-reader reading of the live verdict.

Files: `explainer.html` (self-contained; loads only the Source Serif 4 web font), `explainer.mp4`, `explainer.gif`, `qa/` (render-check frames and sheets).
