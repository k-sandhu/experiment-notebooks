# Notes: "Beat last week" (notebook 16, Ontario electricity demand)

## Message

Copying last week is a hard forecast to beat. For one week of Ontario electricity demand, Chronos-2
missed by 980 MW an hour against 1,561 MW for "copy last week", which is 37% less error. Across 20
forecast starts on Ontario power, the four leading pretrained models missed about a third less
(relative error 0.64 to 0.68), and every fitted method did worse than copying. Across all six series
the best model cut the miss by only 14%, and that lead over AutoETS is not established.

- Reader: a notebook or README reader who does not know forecasting. They view it on an artifact page
  or in the browser and set their own pace.
- Misconception: "A big pretrained model will easily beat a rule as dumb as copying last week", or
  the reverse, "one great week proves the model is better".
- Form: `predict-reveal` (draw your line) inside an 8-step `stepper-lesson`. One step borrows from
  `explorable-model`: a three-way toggle that switches between this week, 20 starts and 6 series.
  Built with `explainer-kit` in the chalkboard style, 380 x 310 viewBox.

## Storyboard (as built)

1. **A week of Ontario power.** The last 7 days of hourly demand (Aug 13-19) draw in, with day
   letters and the hidden next week shaded with a "?".
2. **The rule to beat.** A dot travels from last Thursday 5 p.m. to next Thursday 5 p.m., then the
   whole week slides forward as a blue dashed copy. This is seasonal naive, the scoring baseline.
3. **Your turn: draw next week** (`ask: true`). The reader drags across the shaded week to draw a
   forecast. Reveal unlocks at 70% drawn, gaps are filled by linear interpolation, and the guess
   locks once it is revealed. Clear resets the drawing. "Example" draws an illustrative guess (last
   week's average day repeated seven times, labelled as not a model). The recording uses the same
   example as its demo.
4. **What happened.** The actual week draws in over the guess (amber) and the copy (blue). It shows
   both errors in MW an hour and a verdict ("Copying last week beat you by N%"). A red bracket marks
   Thursday 5 p.m., where copying was +2,046 MW too high. The caption gives the cause: the week
   averaged 16,571 MW against 18,119 MW the week before. "Draw again" goes back to step 3.
5. **A pretrained model tries.** Chronos-2's 80% range (shaded) and its median line. Its error counts
   down from 1,561 to 980 MW an hour, then "37% less error than copying last week" appears. The
   caption says the range held the actual in 140 of 168 hours.
6. **One week is one draw.** Bars for 12 methods, each as miss ÷ copy-last-week miss, with a
   reference line at 1. A toggle switches between this week, Ontario over 20 starts and all 6 series
   with 95% whiskers. Rows keep their positions, the bars morph between views and the caption
   changes with each view. Takeaways: this week AutoARIMA (0.58) beat four of the five leading
   pretrained models. Over 20 Ontario starts the leaders scored 0.64-0.68 and every fitted method
   scored above 1. Over 6 series Chronos-2 scored 0.86 against AutoETS 0.96, and the lead is not
   clearly established.
7. **Where it helps.** Chronos-2 per series. Series with a steady cycle (power, temperature, wind,
   Toronto page views) come in below 1. Series without one (AI page views 1.07, USD/CAD 1.04) lose
   to copying the last cycle.
8. **What to take away.** Four habits: score against copying first, expect about a third less error
   on steady cycles, expect 14% overall, and treat the 80% ranges as too narrow (65.5-70.1%
   coverage). The caption gives the limits: 6 hand-picked series, one two-month window with
   overlapping forecast weeks, and no holiday or weather inputs.

Colours (legend, dimmed per step): ink = actual demand, blue = copy last week, amber = your guess,
violet = pretrained model, green = fitted method, red = the error bracket only.

## Where every number comes from

`build/build.py` reads `evals/forecast-guess/files/data.json` and writes the values into `const DATA`
in the page. All on-screen numbers are computed in the page from DATA, unless marked otherwise below.

| On screen | Value | Source |
|---|---|---|
| Last week's curve, Aug 13-19 | 168 hourly MW | `example.history[168:]` (last 7 of the 14 days provided) |
| Actual next week, Aug 20-26 | 168 hourly MW | `example.actual` |
| Copy last week | = last week | `example.seasonal_naive` (build asserts equality with history[168:]) |
| Copy last week error | 1,561 MW an hour | recomputed MAE; equals `mae_168h_mw["Seasonal naive"]` 1561.3 (asserted) |
| Chronos-2 line, band | median, p10/p90 | `example.forecasts["Chronos-2"]`, `p10_p90["Chronos-2"]` |
| Chronos-2 error | 980 MW an hour | recomputed MAE; equals `mae_168h_mw["Chronos-2"]` 979.9 (asserted) |
| 37% less error | 1 - 980/1,561 | computed; facts.md: relative 0.628, README "37% less error" |
| 80% range held 140 of 168 hours | count p10 <= actual <= p90 | computed; facts.md: 140/168 |
| Week averages 16,571 vs 18,119 MW | means | computed; facts.md: 16,571 and 18,119 |
| Thu 5 p.m. overshoot +2,046 MW | 22,212 - 20,166 | computed from hour 17; facts.md values |
| Example guess error 1,548 MW (1% better than copying) | MAE | computed; the guess is illustrative and labelled so on screen |
| Reader's error and verdict | MAE of their drawing | computed live |
| Step 6 "This week" bars | MAE ÷ 1,561.3 | `mae_168h_mw` (AutoARIMA 905.7 → 0.58, TimesFM 2.5 → 0.37, Lag-Llama → 2.36) |
| Step 6 "20 starts" bars | 0.641 ... 2.277 | `relative_mae_by_series_512[*].ontario_demand` (mean of 24 h and 168 h horizons) |
| Step 6 "6 series" bars and whiskers | 0.86 ... 1.33, ci_low-ci_high | `headline_scores` with context 512 |
| 14% (Chronos-2), AutoETS 4% less | 1-0.8596, 1-0.9606 | `headline_scores` |
| Step 7 per-series bars | 0.67, 0.78, 0.79, 0.80, 1.07, 1.04 | `relative_mae_by_series_512["Chronos-2"]` |
| 20 starts per series, 112 starts in all | counts | facts.md Setup (20 per series, 12 for USD/CAD) |
| 80% ranges held 65.5-70.1% | text | facts.md, Intervals (four leaders, README section 6) |
| "not clearly ahead of AutoETS" | text | facts.md: paired 95% interval -0.233 to +0.015 |
| Window Aug 20 to Oct 17, 2026; limits | text | facts.md Setup and Caveats |

The example guess, "last week's average day, repeated seven times", is the only invented series. It
is labelled illustrative on screen whenever it appears ("Example guess: off by", and the step 3
caption after drawing). It scores 1,548 MW, about the same as copying. That is not tuned; it is what
the profile gives.

## What I checked

- `render_check.py` passes all checks at 360 px and 560 px and with reduced motion. An earlier
  version failed `controls_moved` because three step-3 buttons wrapped at 360 px. The labels are now
  shorter (Clear / Example / Reveal).
- I read both contact sheets and full-size frames for steps 4, 6 (demo, all-series state), 7 and 8.
  Because value labels crossed the reference lines, I added a dark text halo to all chart text.
- A real drawing interaction, tested with Playwright at 360 px: a sine-shaped drag across the pad
  reached 92% drawn and enabled Reveal. Step 4 then showed "Your line: off by 2,071 MW an hour ...
  Copying last week beat you by 33%".
- I checked statements that claim totality against the data. "All four fitted methods missed more
  than copying" holds on Ontario: AutoETS 1.069, AutoARIMA 1.109, Theta 1.78, Lag boosting 1.322.
  "Beat four of the five leading pretrained models" holds: AutoARIMA 906 against TiRex-2 963,
  Chronos-2 980, Moirai 2 1,015, Toto 2 1,099, with TimesFM 2.5 at 572 ahead. "Leaders 0.64-0.68" is
  TiRex-2 0.641, Chronos-2 0.666, Toto 2 0.671 and Moirai 2 0.678.
- The build script asserts that the recomputed MAEs match `mae_168h_mw` and that seasonal naive
  equals last week.
- Not checked: how readable the drawing is on a real touch phone. It was only tested with a mouse in
  Playwright. Each day is about 19 px wide at 360 px, so readers will draw a rough wave rather than
  exact hours. The whiskers in step 6 come from resampling the 6 series and are descriptive (facts.md).

## Files

- `explainer.html`: the explainer. It works offline except for the Caveat web font, which falls back
  to cursive.
- `explainer.mp4` (54 s, 2.9 MB) and `explainer.gif` (5.9 MB): recordings made with `record.py`. I checked one frame per step in `qa/mp4_strip.png`. Step 3 shows the example guess,
  labelled on screen.
- `build/`: `scene.js` (the scene source), `build.py` (data injection and asserts), `scaffold.html`
  (the unmodified kit scaffold) and `drag_test.py`.
- `qa/`: render-check frames, contact sheets and `report.json`.
