# Invoice checks explorable: notes

## Message

On the 72 test invoices, the cheap model alone was right on only 14. Both checks (ask the cheap model
again, or have Claude review the answer) let those 14 through and sent the other 58 to the expensive
model (GPT), so every check route avoided 14 of 72 GPT calls (19%). Asking the cheap model twice costs
$0.00022 per invoice, so it is cheaper than GPT-on-everything once a GPT call costs more than 0.11 cents.
A Claude review costs $0.0259 per invoice, so it only pays above 13.3 cents a call and never beats the
repeat check. No check route can cost less than 81% of GPT-on-everything, because 58 of 72 invoices still
need GPT.

Reader: finance managers, no AI background. Misconception moved: "a cheap first pass always saves money"
and "a stronger checker is the safer buy". The rule they take away: a check pays when its cost per
invoice is below the expensive price times the share of invoices it safely lets through.

## Form and skills used

explainer-director, then explorable-model (primary form), built with explainer-kit
(`scaffold.py --kind explorable --style editorial`, viewBox 380 x 420). Borrowed moments: a unit chart
(every invoice is a dot, steps 1 and 3) and a one-invoice walkthrough (step 2). Editorial style chosen
for a finance audience. One knob only: the price of one expensive-model call, on a log slider from
0.05 to 50 cents, labelled "assumed". The payment-loss assumptions were left out because losses are
zero for every route shown; the cheap-model-alone and person-review routes are discussed in words
rather than plotted (one is wrong on 58 of 72, the other costs 83 cents per invoice at an assumed $1
per review).

Colour meanings (kept across all steps): green = right answer, red ring = wrong answer, blue = cheap
model (Qwen) and the repeat-check route, violet = Claude check and its route, amber = expensive model
(GPT) and the GPT-on-everything route. Right and wrong dots also differ in shape (filled vs ring).

## Steps

1. The cheap model alone: 72 dots colour in; 14 of 72 right (95% range 12% to 30%), all holds; none of
   58 payment amounts exact; average shortfall $923 per invoice.
2. Two ways to check: invoice test-002 walked through both checks: $145.67, re-ask gives $59.13
   (doubtful); Claude recalculates (doubtful); GPT pays $1,171.39, right. Blind payment would have
   underpaid by $1,025.72.
3. Both checks agree: same dots move into "accepted 14" and "doubtful 58"; GPT re-answers the 58, all
   right; GPT calls 58 instead of 72.
4. What each route costs: stacked bars per 1,000 invoices at the study's running example of 5 cents per
   call, plus a ledger: repeat check +$0.22 cost, -$9.72 saved, net -$9.50; Claude +$25.90, -$9.72,
   net +$16.18.
5. Where the answer flips: the slider sweeps itself from 0.05 to 50 cents, pausing with a ring at each
   break-even; chart of cost as % of GPT-on-everything plus live bars.
6. Your turn: the reader drags the price; verdict line names the cheapest route and the saving per 1,000
   invoices. Idle demo moves the slider if the reader does nothing.
7. What to take away: the rule, the two break-evens worked out, the assumed price band (0.5 to 25 cents)
   and three caveats.

## Where every number comes from

All values sit in `const DATA` at the top of the scene with a source comment; on-screen numbers are
computed from it.

| On screen | Value | Source |
|---|---|---|
| 72 invoices, which are holds, which the cheap model got right | 72; 14 holds; 14 right, all holds | data.json invoice_rows (gold_status, "Qwen direct" correct), recounted |
| 95% range 12% to 30% | 0.1195-0.3003 | summary.csv Wilson interval (data.json summary) |
| Average shortfall $923 per invoice | 922.66 | summary.csv mean_underpayment_exposure_usd |
| test-002 amounts | $145.67, $59.13, $1,171.39, underpaid $1,025.72 | facts.md concrete invoices |
| GPT calls 58 vs 72, 14 saved (19%) | 58/72 | summary.csv gpt_invocations; checked per invoice that both check routes call GPT exactly when Qwen is wrong |
| Cheap model cost per invoice | $0.0001444 (Qwen once), $0.0002176 (twice) | cost_lines known_model_cost_mean |
| Claude check cost per invoice | $0.0259007 total; Claude part = 0.0259007 - 0.0001444 = $0.0257563 | break_even.json extra_known_model_cost; split derived |
| Break-even 0.11 cents and 13.3 cents | $0.0011189, $0.1332038 | break_even.json; recomputed as extra cost / (14/72) |
| Step 4 totals at 5 cents | $50.00, $40.50, $66.18 per 1,000 | model; match cost_scenarios.csv rows 0.05 / 0.0405 / 0.06618 per invoice |
| Net -$9.50 and +$16.18 | | model; match paired differences -0.0095 and +0.01618 in cost_scenario_checkpoints |
| Floor 81% | 58/72 = 0.8056 | slope of every check route's cost line |
| Assumed price range 0.5 to 25 cents | 0.005-0.25 | facts.md caveats |
| Within $1 the repeat check would pay 8 wrong answers | 8 | facts.md caveats |
| Person review route 83 cents per invoice | 0.8315 | cost_lines intercept for Claude screen + review (assumed $1 per review) |

Model used for steps 4-7: cost per invoice = known model cost + (GPT calls per invoice) x price.
GPT on all: price. Repeat: 0.0002176 + 0.8056 x price. Claude: 0.0259007 + 0.8056 x price. This is the
zero-loss line from facts.md, which reproduces all 60 rows of cost_scenarios.csv. "Per 1,000 invoices"
is the 72-invoice average times 1,000, stated on screen.

Labelled on screen as assumed: the GPT price per call (slider label, step 4 heading, step 6 caption,
step 7 band), the $1 person review. The illustrative README example (100 invoices, 30 accepted) is not
used, so no invented numbers appear.

## What I checked

- Recomputed from data.json: 14 right / 58 wrong, all 14 right answers are holds, both check routes call
  GPT on exactly the 58 invoices Qwen got wrong, mean known costs, both break-evens, and the three costs
  at 5 cents (match cost_scenarios.csv).
- Fixed a rounding mismatch: the log slider snapped 5 cents to 5.01 cents, which showed a $9.51 saving
  against $9.50 in step 4. The slider value is now rounded to two significant figures, and both show $9.50.
- `render_check.py` at 360 px and 560 px, plus reduced motion: PASS all checks (no errors, overlaps,
  text outside, moving controls or height changes). Earlier runs flagged and I fixed: a long step 7
  line outside the drawing, the verdict overlapping the axis title, a wrapped heading changing the
  height, and step dots that wrapped and shifted when Next became "Start over".
- Looked at the contact sheets and full-size frames of every step at 360 px: captions match the
  drawing, the chart labels clear the lines, the legend dims colours a step does not use.
- Recorded `invoice-checks.mp4` (65 s, 3.4 MB) and `invoice-checks.gif` (5.2 MB) with `record.py`;
  sampled 12 frames across the video and every step appears, including the sweep and the slider demo.
- Not checked: other browsers than Chromium, screen-reader output beyond the kit's labels, and the
  page offline without the Google Font (it falls back to Georgia).

Files: `explainer.html`, `invoice-checks.mp4`, `invoice-checks.gif`, `qa/` (render-check frames, contact
sheets, report.json, sampled video frames).
