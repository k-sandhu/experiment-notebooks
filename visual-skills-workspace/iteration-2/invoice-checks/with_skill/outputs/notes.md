# Invoice checks explainer: notes

## Message

On these 72 test invoices the cheap model was right only on the 14 holds, so a check can skip the
expensive model on at most 14 of 72 invoices (19%). A check pays when it costs less than 19% of the
expensive call's price. Asking the cheap model twice costs 0.02¢ per invoice and pays above 0.11¢ per
GPT call. A Claude review costs 2.59¢ and only beats GPT-on-everything above 13.3¢. Because both checks
made the same choices, Claude review is never the cheapest option here.

- Reader: finance managers with no AI background who open a page and spend a few minutes on it.
- Misconception it corrects: that a cheap first pass with a smart reviewer always cuts the bill. The
  saving is capped by how often the cheap model is right, and the check has to cost less than that share.

## Form

The form is an explorable model (skill `explorable-model`), built with `explainer-kit`
(`scaffold.py --kind explorable`, `paper` style). It is reader-paced: it opens as a page, the reader moves
through it with Next, and step 5 has a price slider. Steps 1 to 3 borrow from `unit-story`: each
invoice is a dot, and the same invoice keeps its place and colour from step 1 to step 3. There is
one model function, `model(G)`, where G is the price of one GPT call. Every number in the bars, the
lines, the verdict and the bills is computed from it.

## Storyboard (6 steps)

1. **72 test invoices.** 72 grey dots in two groups, 14 to hold and 58 to pay. test-002 is circled,
   with a card giving its exact answer (PAY $1,171.39). Right means the decision and the amount both
   match to the cent.
2. **Cheap model alone.** The dots turn amber (14 right, all holds) and red (58 wrong amounts). On
   test-002 the cheap model said $145.67, an underpayment of $1,025.72. Below the dots: 14 of 72 right
   (19%), Wilson 95% interval 12% to 30%, and an average payment error of $930 per invoice.
3. **Check, then escalate.** The two checks are named. All 72 dots drop through a CHECK gate. The 14
   amber dots are trusted and paid. The 58 red dots turn blue as they go to GPT, which got all 58
   right. Wrong answers paid: 0 of 72 with either check.
4. **The bill at 5¢.** At an assumed 5¢ per GPT call, stacked bars show the cost per invoice: GPT on
   every invoice 5.00¢, ask twice 4.05¢ (cheapest), Claude review 6.62¢. The arithmetic is spelled
   out: skipping 19% of calls saves 0.97¢, so ask twice nets +0.95¢ and Claude review nets −1.62¢.
5. **Slide the GPT price.** The reader drags a log-scale slider from 0.05¢ to 30¢. The lines show each
   bill as a % of GPT on every invoice, with break-even markers at 0.11¢ and 13.3¢ and a floor of
   80.6% (at most 19% saved). Bars show the bill for 1,000 invoices. A two-line verdict updates as the
   slider moves. If the reader does nothing, an idle demo sweeps the slider through both break-evens.
6. **Which check to use.** A strip shows the cheapest choice by price: GPT on all below 0.11¢, ask
   twice above it. Also marked: the price range the study assumed (0.5¢ to 25¢) and Claude's 13.3¢
   line. Then the rule, (share the cheap model gets right) × (GPT price), and three caveats.

Colours, kept the same in every step: amber = a cheap answer that was right; red = wrong amount;
blue = the expensive model (GPT); green = ask-twice check; violet = Claude review check.

## Where every number comes from

All values are in the `DATA` block at the top of the scene script, each with a comment naming its
source. They were copied from `evals/invoice-checks/files/data.json` and `facts.md`, which take them from
econ/21-verification-costs.

| On screen | Value | Source |
|---|---|---|
| 72 invoices, 14 hold / 58 pay, which dots are holds | ids 12,16,18,22,30,36,40,46,48,54,64,66,70,72 | data.json `invoice_rows` gold_status (checked by script) |
| Cheap model 14 of 72 right, all holds | 14 | `summary` Qwen direct automatic_correct; checked against invoice_rows |
| 12% to 30% | Wilson 95% | `K.wilson(14,72)` = 0.1195–0.3003, equal to summary correct_ci_low/high |
| Average payment error $930 | 930.0124 | `summary` Qwen direct mean_payment_deviation_usd |
| test-002: $1,171.39 exact, $145.67 cheap, $1,025.72 under | | facts.md "Concrete invoices" |
| 58 sent to GPT, 14 trusted, same 14 for both checks | | `summary` gpt_invocations = 58; invoice_rows (both checks had gpt_invocations = 0 on exactly the 14 holds, checked by script) |
| Wrong answers paid 0 of 72, GPT got all 58 right | | `summary` automatic_wrong = 0, automatic_correct = 72 for both check routes |
| Check cost 0.02¢ (ask twice), 2.59¢ (Claude) | 0.00021756, 0.02590075 USD | `break_even.source_file` extra_known_model_cost_per_invoice (includes the cheap model's own answer) |
| Break-even 0.11¢ and 13.3¢ | 0.0011189, 0.13320 USD | computed as cost / (14/72); self-check in page against `break_even` (tolerance 1e-9) |
| 5¢ price, bills 5.00¢ / 4.05¢ / 6.62¢ | | model(0.05); self-check against `cost_scenario_checkpoints` at G = 0.05 (0.05, 0.0405, 0.06618) |
| Saving 0.97¢, net +0.95¢, net −1.62¢ | | model(0.05); matches paired differences −0.0095 and +0.01618 in cost_scenario_checkpoints |
| Assumed range 0.5¢ to 25¢ | | facts.md caveats |
| "Within $1 it would have paid 8 wrong answers" | 8 | facts.md caveats |
| Bill for 1,000 invoices | per-invoice mean × 1,000 | derived; the footer says it assumes the same invoice mix |

Modelled and assumed values are labelled on screen as assumed: the GPT price (slider label, step 4
header, step 6 range) and the 1,000-invoice scaling (in the footer). The cost line is
cost = check cost + (58/72) × G. Payment losses are left out because they are zero for both check
routes in this run, as facts.md notes.

## What was left out, and why

- **Claude screen + person review** costs 83¢ per invoice at an assumed $1 per review. That is far above
  everything else, so including it would squash the chart.
- **Qwen direct** is cheap in model fees, but the loss on wrong payments is an assumed share of the
  amount. It appears only as "cannot be trusted to pay alone" (step 2).
- **Three Claude checks were unreadable and had to be retried** (test-013, test-025, test-061). They are
  not shown on screen. The facts give the retry cost as $0.0592, but do not say whether that is part of
  claude_list_equivalent_usd.

## What I checked

- `render_check.py` at 360 px and 560 px, with reduced motion as well: **PASS all checks**. The first
  run failed: controls moved because step titles wrapped at 360 px. I shortened the titles and that
  fixed it.
- I looked at the contact sheets and the final frame of every step at both widths. Fixes from that:
  - Two group labels overlapped in steps 1–2.
  - The break-even labels in step 5 collided.
  - The 1,000-invoice bill read $50.03 while the readout said 5.00¢. The slider value is now snapped
    to the shown precision, so the shown price is the price used.
  - Empty space at the top of steps 1–3 now holds headings and the two check definitions.
- A Playwright probe moved the slider to 9 prices and read back the readout, bills and verdicts:
  - 0.12¢ gives ask twice 1% cheaper, and 0.11¢ gives GPT on all.
  - The Claude verdict flips between 13.0¢ and 14.0¢.
  - At 0.5¢ the bills ($4.25, $29.93 per 1,000) match cost_scenario_checkpoints (0.00425, 0.02993).
  - No console errors. The in-page self-checks against break_even.json and cost_scenarios raised no error.
- I recorded `explainer.mp4` (2.9 MB, 49 s) and `explainer.gif` (4.2 MB) with `record.py`, and checked one
  frame per step. The step-5 demo moves the slider on camera.
- Not checked: screen-reader output beyond the kit defaults, browsers other than Chromium, and behaviour
  with web fonts blocked (the page falls back to system fonts).
