# Notes: "Can you beat 'same as last week'?" (notebook 16)

## Message

Copying last week hour by hour is a hard forecast to beat. On Ontario electricity demand the best pretrained
models cut its error by about a third with no fitting, while every standard fitted method lost to it. Across all
six series their edge shrinks to about 14%, they lose on the two series without a regular cycle, and one week is
one draw: judge methods on many weeks.

## Form

One self-contained, offline HTML page (`explainer.html`, no libraries, system fonts, hand-drawn SVG, data
inlined from `data.json`). It is a guess-then-reveal interactive: the reader makes a forecast before seeing the
answer. Light and dark themes; at phone width the main chart scrolls inside its own box (no page-level
horizontal scroll). `explainer.gif` is a short walkthrough (slider, reveal, the evidence toggles).

## Structure (steps)

1. **Two weeks of Ontario demand.** 336 hourly values (6 to 19 Aug 2026), weekends shaded, then the empty
   forecast week (20 to 26 Aug). The "copy last week" line is drawn into the forecast week with a "copied forward"
   arrow.
2. **Your forecast.** A slider scales last week's shape up or down (-20% to +10%); the reader can also draw over
   any hours with the mouse or a finger. "Reveal" animates the actual week, shows three score cards (You, Copy
   of last week, Chronos-2: MAE in MW and relative MAE), and four callouts: why copying overshoots, hour 0,
   hour 17, and "the level is the hard part". Scores update live if the reader keeps editing.
3. **Eleven methods, the same week.** Bars of 168-hour MAE for all 12 forecasts (11 methods plus the copy),
   coloured by pretrained / fitted / copy. Clicking a bar shows that method's forecast vs actual with its 80%
   range (pretrained only) and how many of the 168 hours the range held.
4. **One week is one draw.** Diverging bars of relative MAE around 1.00 with a three-way toggle: this one week,
   Ontario over 20 starting points, all 6 series (with 95% resampling ranges). The ranking reshuffles between
   views (AutoARIMA is 2nd in the one week, loses on Ontario overall).
5. **Where "last week" still wins.** Heat table: 12 rows x 6 series of relative MAE, blue < 1 < red.
6. **What to take away** plus source and caveat notes.

Only the forecast week is hidden before the reveal; steps 3 to 6 appear after it.

## Where every on-screen number comes from

All from `data.json` (inlined verbatim) or `facts.md`. Computed values are computed in the page from the
inlined arrays, so they cannot drift from the data.

| On screen | Source |
|---|---|
| History, actual, copy-of-last-week lines | `example.history`, `example.actual`, `example.seasonal_naive` (checked: seasonal_naive == last 168 history values) |
| Chronos-2 and other method lines, 80% bands | `example.forecasts`, `example.p10_p90` |
| Copy MAE 1,561; Chronos-2 980; all bar values (572 ... 3,686) | `example.mae_168h_mw`, rounded |
| Reader's MAE and relative MAE | computed live: mean of abs(reader - actual) over 168 h, divided by 1,561.3 |
| Chronos-2 relative 0.63, "37% less error" | 979.9 / 1,561.3 = 0.628 (facts.md: 0.628, README 37%) |
| Week-before avg 18,119 / peak 22,353; forecast week avg 16,571 / peak 20,684 | computed from history[-168:] and actual; match facts.md |
| Hour 0: 14,820 / 15,873 (+1,053) / Chronos-2 14,917 (+97) | actual[0], seasonal_naive[0], forecasts.Chronos-2[0]; match facts.md |
| Hour 17: 20,166 / 22,212 / 20,389 | index 17 (2026-08-20T17:00); match facts.md |
| "Shrinking by 7% would miss by 720 MW" | computed: seasonal_naive x 0.93 (rounded), MAE vs actual = 719.8. -7% was the best whole-percent scaling (searched -25..+10). Labelled as hindsight |
| Coverage "140 of 168 hours" (Chronos-2) and other models' coverage and mean band width | computed live from p10/p90 vs actual; Chronos-2 140/168 matches facts.md. Lag-Llama 168/168 with a 23,350 MW mean width, flagged as "covers everything only because it is very wide". TimesFM 2.5 band suppressed per facts.md |
| "Five of seven pretrained beat the copy", "six of eleven methods", "AutoARIMA second (906), beat four of five leaders" | counted from mae_168h_mw |
| "This one week" relative values | mae_168h_mw[m] / 1,561.3 (168-hour only; labelled) |
| "Ontario, 20 weeks" values (TiRex-2 0.641 ... Lag-Llama 2.277; AutoARIMA 1.109) | `relative_mae_by_series_512.*.ontario_demand` (mean of 24 h and 168 h horizons; labelled) |
| "27% to 36%" | 1 - 0.732 and 1 - 0.641 |
| "All 6 series" values and 95% ranges | `headline_scores`, context 512 (relative_mae, ci_low, ci_high) |
| 0.860 to 0.871, AutoETS 0.961, lead 0.101 with range -0.233 to +0.015; 2,048-history 0.815 to 0.869 and AutoETS 0.900 | headline_scores and facts.md (paired comparison) |
| Heat table | `relative_mae_by_series_512`, two decimals |
| TTM R3 best on USD/CAD (0.887); leaders all > 1 on AI page views and USD/CAD | relative_mae_by_series_512; checked each of the five leaders |
| 80% ranges held 65.5% to 70.1% | facts.md (README section 6) |
| Dates, 512 values, 168 h, 20 starting points, 6 series, 10,000 resamples, 9 quantiles, TimesFM quantile problem, download date | facts.md / data.json `about` |

Weekday labels are computed from the timestamps (20 Aug 2026 is a Thursday).

## What I checked

- Recomputed every MAE from the arrays in Python: all match `mae_168h_mw` to within 0.1 MW (the arrays are
  integer-rounded); displayed values use the stored figures.
- Recomputed the facts.md worked-example numbers (hour 0, hour 17, weekly averages and peaks, 24-hour MAE 227 vs
  1,578, Chronos-2 coverage 140/168): all reproduce.
- Rendered in headless Chromium (Playwright) at 1100 px light, 1100 px dark and 390 px mobile, before and after
  reveal and with the "All 6 series" view and Lag-Llama selected: no console or page errors, page scroll width
  equals viewport width at every size, labels do not collide after moving the history labels and the
  "copied forward" arrow inside the plot.
- Checked the slider label grammar, that the reader's line no longer hides the copy line before reveal (copy is
  drawn on top), and that the score text reads correctly for beat / tie / lose.
- Searched the page for em dashes (none) and the notebook style list of overused words.
- Did not test on a real touch device; drawing uses pointer events with `touch-action: none` on the forecast
  panel only.
