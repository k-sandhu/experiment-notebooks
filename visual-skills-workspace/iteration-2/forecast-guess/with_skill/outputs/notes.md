# Notes: "Beat last week" (notebook 16 explainer)

## Message
Repeating last week is a hard bar to clear for Ontario electricity demand. Averaged over 20 Ontario forecasts,
every fitted method made more error than it (relative MAE 1.07 to 1.78). The top four pretrained models made about a
third less error (0.64 to 0.68). Across all six series the best pretrained model's advantage shrinks to 14%
(95% interval 3-25%), its lead over the best fitted method (AutoETS, 4%) is not established, it loses on the two series
without a dependable cycle, and its 80% ranges held only 65.5-70.1% of the time.

Reader: someone opening the notebook or README who has never forecast anything. Misconception to move: "a clever
model or my own eye easily beats copying last week". Delivery: reader-paced page; MP4/GIF for passive viewing.

## Form
predict-reveal (draw-your-line guess) inside an 8-step stepper lesson, chalkboard style, built with explainer-kit
(`scaffold.py --kind stepper`, viewBox 380 x 360). Colours keep one meaning in every step: ink = real demand,
amber dashed = the reader's guess, violet = repeat last week, green = pretrained model, blue = fitted method,
red = a miss.

## Steps
1. **A week of Ontario power**: Aug 13-19 hourly demand draws in; peak 22,353 MW marked; the next week is shaded with "next week: ?".
2. **Your forecast**: the reader drags across the shaded week (hourly bins, gaps filled by straight lines). Reveal unlocks at 70% coverage; Start over clears; Next skips. The guess locks after the reveal. Idle demo (and the GIF) draws a labelled example guess.
3. **The real week**: the actual week draws in over the guess; red lines show the misses; readout gives the guess's average miss in MW. "Try again" resets.
4. **Just repeat last week**: last week's line slides one week right; readout 1,561 MW an hour and the comparison with the guess; Thursday 5 p.m. overshoot (2,046 MW too high) marked.
5. **A pretrained model**: Chronos-2 median plus its 80% band; 980 MW an hour, 37% less; band held 140 of 168 hours.
6. **One week is one draw**: for all 12 methods, a ring at this week's ratio to repeat-last-week and a dot that slides to the 20-forecast Ontario average (AutoARIMA 0.58 → 1.11 annotated). The reader's guess appears as a ring.
7. **Across six series**: headline relative MAE with 95% intervals (history 512); top four within 0.011; Chronos-2 minus AutoETS −0.101, interval −0.233 to +0.015, lead not established.
8. **What to take away**: per series, Chronos-2 vs AutoETS against the 1.0 line, grouped "with a steady cycle" / "without a dependable cycle"; 80% ranges held only 65.5-70.1%. Caption gives the rule: always score against repeating the last cycle.

## Where every number comes from
All arrays and scores are copied by `build/build.py` from `evals/forecast-guess/files/data.json` into `const DATA`,
and every on-screen number is computed from DATA in `build/scene.js`, except two constants from facts.md.

| On screen | Source |
|---|---|
| Aug 13-19 line, peak 22,353 | `example.history`, last 168 values (asserted equal to `example.seasonal_naive`) |
| Real week line, red misses | `example.actual` |
| 16,571 vs 18,119 MW (caption step 3) | means of `actual` and last 168 of `history`, checked in Python; also in facts.md |
| Repeat last week 1,561 MW; Thu 5 p.m. +2,046 | MAE of `seasonal_naive` vs `actual`; hour 17: 22,212 − 20,166 |
| Chronos-2 980 MW, 37% less, 140 of 168 | `forecasts["Chronos-2"]`, `p10_p90["Chronos-2"]`; match `mae_168h_mw` and facts.md |
| Step 6 rings (this week) | each method's 168-h MAE ÷ 1,561 (TimesFM 0.37 ... Lag-Llama 2.36) |
| Step 6 dots (20 forecasts) | `relative_mae_by_series_512[*].ontario_demand` (mean of 24-h and 7-day relative MAE, as the legend says) |
| Step 7 dots, intervals, "0.011", 14% / 4% | `headline_scores` with context 512 (Chronos-2 0.8596 [0.7479, 0.9742], AutoETS 0.9606) |
| Chronos-2 minus AutoETS −0.101 (−0.233 to +0.015) | facts.md (paired_comparison.json), constant `PAIRED` |
| Step 8 per-series dots | `relative_mae_by_series_512` for Chronos-2 and AutoETS |
| 65.5-70.1% coverage | facts.md (README section 6), constant `COVER_RANGE` |
| "512 hours", "20 forecasts", "six series" | facts.md setup |
| Example guess (demo/GIF only) | **Illustrative**: 18,500 + 2,600·cos(2π(hour−17)/24), minus 1,300 on Sat/Sun; mean ≈ last week's level. Labelled "Example guess" on screen. Its error is 1,598 MW, computed live. |

## What I checked
- Recomputed in Python: seasonal naive = last 168 h of history; all 168-h MAEs match `mae_168h_mw`; Chronos-2 band coverage 140/168; 24-h values; week means.
- `render_check.py`: PASS all checks at 360 px and 560 px, plus reduced motion; looked at both contact sheets step by step and fixed cramped day labels (now two-letter) and an annotation that crossed the data lines.
- Drove the real interaction with Playwright (`build/shots.py`): dragged a guess, Reveal unlocked, steps 3-5 showed the reader's error (2,216 MW for that test line) and the comparison with repeat-last-week; no console errors. Screenshots in `qa_reader/`.
- Recorded `explainer.mp4` (43 s, 3.1 MB) and `explainer.gif` (5.2 MB) with `record.py`; looked at frames from every step (`qa_video/`).
- Not checked: real touch devices, screen-reader output beyond the kit's labels. The page loads the Caveat font from Google Fonts; offline it falls back to a cursive system font.
