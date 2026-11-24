# Checking cheap invoice answers: notes

## Message

In a test on 72 invoices, checking the cheap model's answers let the business skip the expensive model on 14 invoices (19%). Asking the cheap model twice costs so little (0.02¢ per invoice) that it pays once an expensive call costs more than **0.11¢**. Having Claude review each cheap answer costs 2.6¢ per invoice, so that check pays only above **13.3¢** per expensive call.

- **Reader:** finance managers who know invoices and budgets but not model routing. They open the page on purpose and will spend a few minutes on it.
- **Misconception the page corrects:** "A cheap model plus a safety check is always cheaper," or the opposite, "any check costs more than it saves." The answer depends on two things: the price of the expensive call, and what share of invoices the check passes. In this test every saving came from 14 invoices that should be held.
- **Form:** explorable model (`explorable-model`) built as a 7-step stepper with `explainer-kit`. Steps 1 and 2 walk single invoices through the check. Step 3 is a unit chart with one dot per invoice. Step 4 shows the cost arithmetic. Steps 5 and 6 are the live model: a price slider, then a price slider plus a volume slider. Step 7 gives the decision and the limits. Style: `editorial`, chosen because the page is data-dense and aimed at business readers.

## Storyboard

1. **One invoice, asked twice.** A flow diagram: invoice, cheap model asked twice, a box asking "Do both answers match, decision and cents?", then two branches (Match: use the cheap answer; No match: ask the expensive model). Invoice test-012 ($1,785.54, correct answer HOLD) gets HOLD twice, a dot travels to Match, and the page reads "No expensive call needed." The average cost of the two cheap calls (0.02¢) is shown. This is the ordinary case.
2. **When the answers differ.** The same diagram with invoice test-002. The two cheap answers are $145.67 and $59.13, so the invoice goes to the expensive model, which pays the correct $1,171.39. In red: "the first cheap answer would have underpaid by $1,025.72." The caption notes that the Claude check also rejected this invoice.
3. **All 72 test invoices.** 72 dots. Green means the cheap model was right (14, all of them holds) and red means wrong (58). The dots then split into "Check passed: 14 → cheap answer used" and "Check failed: 58 → expensive model", with the failed group turning blue. Final lines: 72 of 72 right with either check; 0 wrong answers let through; 0 right answers sent on anyway; both checks made the same split.
4. **The trade, at 5¢ a call.** Monthly bill for 10,000 invoices as stacked bars, with checking cost in amber and expensive calls in blue: No check $500; Repeat check $2.18 + 8,056 calls × 5¢ = $405; Claude check $259 + 8,056 calls × 5¢ = $662. Then the break-even rule in words, "cost of the checks ÷ calls skipped": $2.18 ÷ 1,944 = 0.11¢ and $259 ÷ 1,944 = 13.3¢. A footnote names the two routes left out: the cheap model alone, and the Claude check plus person review.
5. **Move the price.** A chart of monthly saving against no check, plotted over the expensive-call price on a log scale from 0.05¢ to 50¢. It has one line for each check, a dashed zero line for no check, open circles at the break-even prices, and shading for the 0.5–25¢ range the notebook assumed. The monthly bills sit below the chart. A verdict at the top ("At X a call: … is cheapest" plus the saving or extra cost of each check) updates live. The demo sweeps the slider and pauses at each break-even.
6. **Your price, your volume.** The same view with a second slider for invoices per month (1,000–200,000). The bills and the verdict scale with volume; the break-even prices do not change.
7. **What to take away.** A number line marking where each check starts to pay, followed by five limits (listed below).

## Where every number comes from

All values on screen are computed in the page from the `DATA` block at the top of the scene, and that block is copied from `evals/invoice-checks/files/data.json` and `facts.md`.

| On screen | Value | Source |
|---|---|---|
| 72 invoices, 14 passed, 58 sent on | 72 / 14 / 58 | `summary` (n, gpt_invocations 58 for both check routes); the 14 passed IDs come from `invoice_rows` where gpt_invocations = 0 in both check routes; all 14 are HOLD |
| Cheap model alone 14 of 72 right | 14 | `summary` Qwen direct automatic_correct |
| Check cost per invoice | repeat $0.0002176, Claude $0.0259 | `cost_lines` known_model_cost_mean; I re-derived both from the 72 rows in `invoice_rows` and they match |
| Break-even 0.11¢ and 13.3¢ | 0.0011189 and 0.13320 USD | computed as check cost ÷ (14/72); matches `break_even.recomputed` |
| Monthly bills | vol × (check cost + 58/72 × price) | `cost_lines` straight line in G; zero loss for the check routes and for GPT direct |
| 5¢ example price | 0.05 | README running example, labelled "assumed" on screen |
| $8,315 per 10,000 for Claude + person review | 0.8315 × 10,000 | `cost_lines` intercept (assumes $1 per review) |
| test-012: $1,785.54, HOLD/HOLD | | facts.md |
| test-002: $145.67, $59.13, $1,171.39, underpay $1,025.72 | | facts.md (14567, 5913, 117139 cents; 1,171.39 − 145.67) |
| 94.9% | Wilson 95% lower bound for 72/72 | `K.wilson(72,72)`; matches `summary` correct_ci_low 0.9493 |
| 8 wrong amounts with a $1 tolerance | 8 | facts.md caveats |
| "Half as many passed → 0.22¢ and 26.6¢" | 2 × break-even | derived; illustrative sensitivity, stated as "if" |
| Shaded range 0.5–25¢ | | facts.md: GPT price assumed range 0.005–0.25 |

Measured vs assumed on screen: the expensive-call price is labelled "(assumed)" on the slider and in step 4. The volume slider is labelled "(yours)". The Claude cost appears as list price in the step 7 limits.

## What I checked

- **Model against source:** a Playwright script (`_build/numcheck.py`) loaded the page and evaluated the page's own `model()` at the nine `cost_scenario_checkpoints` rows for the three routes that make no wrong payments (prices 0.5¢, 5¢, 25¢). The largest difference from the source was printed and recorded (see results below). The break-even values were compared with `break_even.recomputed`.
- **Live text follows the controls:** the same script set both sliders on step 6 to three settings. The verdict lines, the bill values and the slider readouts all changed, and they agree with each other because each kind of number goes through a single formatter.
- **Layout:** `render_check.py` at 360 px and 560 px, plus a reduced-motion pass. I fixed every FAIL it reported: a long axis label on step 7, and the controls moving on step 6 (two sliders were taller than the reserved row, so I raised `actHeight` and added a minimum legend height). I looked at the contact sheets and individual frames and fixed what I saw: chart labels that sat on the lines in step 5, invoice amounts rounded to the dollar (they now show cents, which is the point of the check), and an empty gap in step 3.
- **Honesty items:** the control result is on screen (step 3: 0 right answers sent on needlessly, with all 72 final answers right). The ceiling is named (72 of 72 still allows 94.9%). The two excluded routes are named in step 4. The single examples, test-012 and test-002, are placed within the 72-invoice result in step 3.

### Results of the checks

- The page model matches all 9 checkpoint rows to within $0.0000047 per invoice, which is the rounding of the source values to 5 decimals. The break-even prices are $0.0011189 and $0.133204, the same as `break_even.json`. At 5¢ and 10,000 invoices the bills are $500 / $404.95 / $661.78; the source gives 0.0405 and 0.06618 per invoice.
- Settings tried on step 6. At 0.06¢ and 10,000 invoices, "no check is cheapest", and the repeat check costs $0.95 more. At 31.5¢ and 100,000 invoices, the repeat check saves $6,113 and the Claude check saves $3,544. At 0.11¢ and 1,000 invoices, the repeat check "breaks even". No page errors.
- `render_check.py` reports PASS on all checks at 360 px and 560 px, with and without reduced motion. I looked at the contact sheets and at the full-size frames for steps 2, 3, 4, 5, 6 and 7, and at an 8-frame strip of the MP4. One fault was found in the strip: at 30,000 invoices the Claude label sat on the axis. I fixed it by adding padding under the lowest line.
- Recording: `explainer.mp4` (about 57 s, all 7 steps, with the slider demos) and `explainer.gif`, both made with `record.py`.
- The working files in `_build/` are the scene source, the build and number-check scripts, the QA frames and contact sheets, and `mp4_strip.png`.

## Not checked or left out

- Payment-loss assumptions (1% overpay, 0.1% underpay) are not a control. They only affect the cheap-model-alone route, which is excluded as unusable (58 of 72 wrong).
- I did not test the page against other invoice mixes. The share passed is fixed at the measured 14/72, and step 7 states how the break-even scales if that share changes.
