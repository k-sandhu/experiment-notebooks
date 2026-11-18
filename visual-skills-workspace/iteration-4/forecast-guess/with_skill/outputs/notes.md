# Notes: "Beat last week" explainer (notebook 16)

## Message

Copying last week ("seasonal naive") is a hard forecast to beat. On the one Ontario week shown, the pretrained
model Chronos-2 cut the average hourly miss from 1,561 MW to 980 MW (37% less error). Averaged over all six
series in the study, the best pretrained models made only about 14% less error than repeating the last cycle
(95% range 3% to 25%). The gain is large on series with a strong cycle such as Ontario demand (32% to 36% for
the top four) and turns into a loss on series without one (AI page views, USD/CAD).

- Reader: someone opening the notebook README or an artifact page, with no forecasting background.
- Misconception: "A pretrained AI forecasting model will crush a dumb copy of last week."
- Form: `predict-reveal` (two guesses) inside a reader-paced `stepper-lesson`, built with `explainer-kit`,
  chalkboard style, 380 x 330 drawing. Reader-paced because the destination is a notebook page, not a feed.

## Storyboard (8 steps)

1. **Beat "repeat last week"**: 14 days of recorded hourly demand (6-19 Aug 2026) draws in; week averages
   18,908 and 18,119 MW; next week (20-26 Aug) is a hidden grey band.
2. **The rule to beat**: last week lights up blue and slides into the hidden week as a dashed copy
   (seasonal naive). Every method is scored against it.
3. **Your guess** (ask): the reader drags the yellow copy up or down (or uses Lower/Higher) to set next week's
   level; the week average and change from last week update live. Reveal stays disabled until they move it;
   Next skips. Demo (recording only): -750 MW, about last week's drop repeated, labelled "Example guess shown".
4. **The real week**: the real demand draws in over the copy and the guess. Real average 16,571 MW, 1,548 below
   last week; the copy was too high in 163 of 168 hours. Score = average miss per hour: copy 1,561 MW, the
   reader's guess computed live. "Try another guess" returns to step 3.
5. **A pretrained model tries**: zoom to the forecast week. Chronos-2 median (violet) with its 80% band, the
   copy (blue dashed), the real line. Red bracket: copy too high by 2,046 MW at Thu 5 pm. Bars: 1,561 vs 980 MW
   (and the reader's guess). Caption: 37% less error; band held the real value in 140 of 168 hours.
6. **Now guess the big number** (ask): drag a marker on a 0-60% scale for "how much less error than repeating
   the last cycle, over six series". Reveal shows three rows for Chronos-2 at three zoom levels: all six series
   14% (95% range 3-25%), Ontario demand over 20 forecast starts 33%, this one week 37%. The reader's guess is
   marked on each row. Demo (recording only): 40%, labelled as an example.
7. **Every method, scored**: dot plot of relative MAE for all 12 methods (history 512). Filled dot = six-series
   average with its 95% resampling range; ring = Ontario demand alone; dashed line at 1.0 = repeat last cycle.
   Off-scale Ontario rings are labelled (1.78, 1.64, 2.28). Caption: top four within 0.012 of each other.
8. **What to take from it**: 14% overall; 32-36% on Ontario demand (top four); all 5 leading pretrained models
   worse on AI page views and USD/CAD; 80% bands held only 66-70%; this week AutoARIMA beat 4 of 5 leaders but
   lost over all Ontario starts (1.11). Limits line: 6 series, 112 forecast starts, targets 20 Aug to 17 Oct 2026,
   models saw numbers only (no dates, holidays, weather).

Colours: off-white = recorded demand, blue = repeat last week / last cycle, yellow = the reader's guess,
violet = pretrained model, green = standard fitted method, red = a miss. Same meaning in every step.

## Where every number comes from

All values are computed in the page from a `DATA` object that `src/build.py` copies from
`evals/forecast-guess/files/data.json` (no hand-typed series values). `window.NUMBERS` exposes the derived values;
they were printed from the built page and match facts.md.

| On screen | Value | Source / computation |
|---|---|---|
| Hourly demand, 6-19 Aug | 336 values | `example.history` |
| Week averages | 18,908 / 18,119 MW | mean of history[0:168] and history[168:336] |
| Repeat last week | 168 values | history[168:336] (asserted equal to `example.seasonal_naive`) |
| Real week, average | 16,571 MW, 1,548 below last week | `example.actual` mean; 18,119 - 16,571 |
| Copy too high | 163 of 168 hours | count of naive > actual |
| Average miss, copy | 1,561 MW | MAE(naive, actual); equals `mae_168h_mw["Seasonal naive"]` 1,561.3 |
| Average miss, Chronos-2 | 980 MW | MAE(`forecasts["Chronos-2"]`, actual); equals 979.9 |
| 37% less error | 37.2% | 1 - 980/1,561 (facts.md: 0.628) |
| 80% band held real value | 140 of 168 h | `p10_p90["Chronos-2"]`, p10 <= actual <= p90 (facts.md: 140/168) |
| Thu 5 pm miss | 2,046 MW | naive[17] 22,212 - actual[17] 20,166 (facts.md) |
| Reader's guess miss | live | MAE(naive + reader's shift, actual); demo shift -750 gives 944 MW |
| 14% (3-25%) overall | 14.04%, 2.58-25.21% | `headline_scores` Chronos-2, 512: 1 - 0.8596; 1 - ci_high 0.9742; 1 - ci_low 0.7479 |
| 33% Ontario, 20 starts | 33.4% | 1 - `relative_mae_by_series_512["Chronos-2"].ontario_demand` 0.666 |
| Scoreboard dots and ranges | 12 methods | `headline_scores` (context 512): relative_mae, ci_low, ci_high |
| Scoreboard rings | 11 methods | `relative_mae_by_series_512[m].ontario_demand` |
| Top four within 0.012 | 0.0116 | max - min of relative_mae for Chronos-2, Moirai 2, TiRex-2, Toto 2 (facts.md rounds to 0.011 from 3-decimal values) |
| 32-36% on Ontario | 32.2-35.9% | 1 - Ontario relative MAE for the top four |
| All 5 leaders worse on AI page views and USD/CAD | 5 | wiki_ai > 1 and usd_cad > 1 for Chronos-2, Moirai 2, TiRex-2, Toto 2, TimesFM 2.5 |
| AutoARIMA beat 4 of 5 leaders this week; lost overall (1.11) | 906 MW vs 572/963/980/1,015/1,099; 1.109 | `mae_168h_mw`; `relative_mae_by_series_512.AutoARIMA.ontario_demand` |
| 80% bands held only 66-70% | 65.5-70.1% | facts.md (README section 6); not in data.json, so typed as `BAND_COVER` with a comment |
| 6 series, 112 starts, 20 Aug - 17 Oct 2026, 512 hours seen | | facts.md setup |

Nothing is invented. The two demo guesses (-750 MW, 40%) are labelled "Example guess shown" in the caption when
they play.

## What I checked

- `render_check.py` at 360 px and 560 px, plus reduced motion: PASS all checks (no console errors, no
  overlaps, no tiny text, no text outside the drawing, controls do not move, constant height). Earlier runs
  caught a wrapping step-1 title that moved the controls; fixed by shortening it.
- Looked at the contact sheets and individual frames for every step at 360 px. Fixed by eye: week-average
  labels colliding in steps 2-4, the reader's guess line crossing labels in step 6, a cramped range label,
  and a squeezed axis note in step 7.
- Recomputed every derived number in the page and compared with facts.md (980/1,561, 37%, 140/168, 2,046,
  16,571, 14%, 0.748-0.974). All agree; the only difference is 0.012 vs facts.md's 0.011 for the top-four
  spread, a rounding difference explained above.
- Honesty: the guess is stored apart from the data and drawn dashed in its own colour; the reveal locks the
  step-6 guess; the one example week is placed against the Ontario and six-series averages before the end;
  the band coverage caveat and the study's limits are on the final step.
- One thing worth knowing: the example guess (shift last week down by 750 MW) scores 944 MW, slightly better
  than Chronos-2's 980 MW on this week. That is real arithmetic on the data, and it shows that most of the copy's
  error this week was the level drop, but it is one week and one guess, so the explainer does not draw a
  conclusion from it.
- Not checked: real touch devices (drag was tested only through the kit's checks and the demo code path),
  and screen-reader output beyond the kit's aria labels.

## Files

- `explainer.html`: the explainer (self-contained; Caveat font loads from Google Fonts, falls back to cursive offline).
- `explainer.mp4`, `explainer.gif`: recording of all steps with the example guesses.
- `src/scene.js`, `src/build.py`: scene source and the build that injects data.json values.
- `qa/`: render-check frames and contact sheets.
