# Beat last week: notes

## Message

Copying last week is hard to beat for Ontario electricity demand. In the study it beat every standard fitted
method (relative error 1.07 to 1.78). The top pretrained models made about a third less error than the copy
(0.64 to 0.68, averaged over 20 Ontario forecasts). Across all six series the best of them made only 14% less
error (0.86, range 0.75 to 0.97), and they lost to the copy on the two series with no steady rhythm.

- Reader: someone opening notebook 16 or its README, with no forecasting background.
- Misconception to move: "a simple copy of last week is a strawman, and any real model beats it easily."
- Form: `predict-reveal` (draw-your-line) inside an 8-step `stepper-lesson`, built with `explainer-kit`
  (chalkboard style, 380 x 340 drawing). One hands-on guess step and one toggle step.

## Storyboard (as built)

1. **A week of Ontario demand.** This step draws last week's hourly demand (Aug 13-19). Next week is hidden behind a "?". Above the chart: peak 22,353 MW and low 13,608 MW.
2. **The lazy forecast.** Last week's line slides right into the hidden week as a dashed blue copy. The caption names it seasonal naive and calls it the yardstick.
3. **Your turn: draw next week.** The reader drags across the shaded week to draw a forecast in 84 two-hour bins. The dashed copy stays faint for comparison. Reveal unlocks at 70% drawn. The step also has Start over and Skip. The demo (shown in the GIF and MP4, and after 6 s idle) draws an *example guess*: last week averaged per two hours, minus 600 MW. It is labelled "Example guess" on screen and in the score rows.
4. **What really happened.** The real week draws in. The gap between the copy and reality is shaded, because that gap is the error. Score rows show the reader's average miss next to the copy's 1,561 MW. The copy was too high in 163 of 168 hours, and the week averaged 16,571 MW against 18,119 the week before.
5. **A pretrained model tries.** Chronos-2's median forecast and its 80% band appear. It missed by 980 MW, 37% less error than the copy, and its band held the real value in 140 of 168 hours.
6. **One week is one draw.** Bars show relative error (1.0 = copy) for all 12 methods. In this one week AutoARIMA scored 0.58 and beat four of the five leading pretrained models. The "All 20 forecasts" toggle animates the bars to the Ontario average over 20 forecasts. There all four fitted methods sit above 1.0, and the top pretrained models are at 0.64 to 0.73.
7. **Beyond electricity.** A dot plot of Chronos-2 and AutoETS on the six series, plus the six-series average with Chronos-2's 95% resampling range.
8. **What to take from it.** Three cards: always race the copy; rhythm is where the models win; one week proves little. The caption gives the caveat: six series in one two-month window, and the lead over AutoETS (0.86 vs 0.96) is not established.

Colours: real demand = off-white ink; your guess = amber; repeat last week = blue (dashed); pretrained = violet;
fitted = green. These are the same in every step and in the legend. Unused legend entries dim.

## Where every number comes from

All values are read from the eval input `evals/forecast-guess/files/data.json` by `src/build.py`. The page computes every number it shows from that DATA, in `src/scene.js`.

| On screen | Value | Source / computation |
|---|---|---|
| Hourly lines, Aug 13-19 | 168 values | `example.history[-168:]` (equals `example.seasonal_naive`, asserted in build.py) |
| Hourly lines, Aug 20-26 | 168 values | `example.actual` |
| Peak / low last week | 22,353 / 13,608 MW | max/min of the above |
| Week averages | 16,571 vs 18,119 MW | mean of actual / last week (facts.md agrees) |
| Copy too high | 163 of 168 hours | count of last week > actual |
| Copy's average miss | 1,561 MW | MAE(seasonal naive, actual); equals `mae_168h_mw["Seasonal naive"]` 1561.3 |
| Chronos-2 line and band | 168 values each | `forecasts["Chronos-2"]`, `p10_p90["Chronos-2"]` |
| Chronos-2 average miss | 980 MW | MAE recomputed; equals `mae_168h_mw` 979.9 |
| 37% less error | 1 - 980/1,561 | facts.md: README "37% less error" |
| Band held truth | 140 of 168 hours | p10 <= actual <= p90 count; facts.md: 140/168 |
| Example guess miss | 1,028 MW | computed live from the example guess (illustrative, labelled "Example guess") |
| Step 6 "this week" bars | e.g. AutoARIMA 0.58, TimesFM 2.5 0.37, Lag-Llama 2.36 | `mae_168h_mw[m] / mae_168h_mw["Seasonal naive"]` (168 h only) |
| Step 6 "20 forecasts" bars | TiRex-2 0.64 ... Lag-Llama 2.28 | `relative_mae_by_series_512[m].ontario_demand` (mean of 24 h and 168 h), noted on screen |
| Step 7 dots | e.g. Ontario 0.67 / 1.07, AI page views 1.08 / 0.99 | `relative_mae_by_series_512` for Chronos-2 and AutoETS |
| Six-series average | 0.86 (0.75-0.97), AutoETS 0.96 | `headline_scores`, context 512 (`relative_mae`, `ci_low`, `ci_high`) |
| "14% less error" | 14.04 | `headline_scores` skill_percent for Chronos-2 |
| Lead over AutoETS not established | interval -0.233 to +0.015 | facts.md (paired_comparison.json); stated in words only |
| "20 forecasts" | 20 Ontario origins | facts.md: 20 origins per series |
| "512 hourly numbers" | 512 | `example.context_values` |

The only invented values are in the example guess. It is labelled on screen wherever it appears. A reader who draws their own line gets their own score.

## Choices and honesty notes

- I chose Chronos-2 for steps 5 and 7 because it is the README's worked example and the top model at history 512. The top four are within 0.011 of each other. Step 8 groups them as "top pretrained models" and does not rank them.
- Step 6 says "20 forecasts", not "20 weeks", because the forecast windows overlap heavily (facts.md caveat).
- TimesFM 2.5 had the best score this week (0.37). Its point forecast is valid, so it is shown. Its bands are unusable, so the explainer shows no TimesFM bands.
- The "this week" bars use the 168 h error only. The 20-forecast bars average the 24 h and 168 h errors, and a note on screen says so.

## What I checked

- `render_check.py`: **PASS all checks** at 360 px and 560 px, plus reduced motion. The first run flagged a text overlap between the week label and the score panel title in steps 4 and 5; I moved the panel down.
- I looked at the contact sheets and at individual frames (steps 3 demo, 4, 5, 6 demo, 7) at 360 and 560 px, then fixed what I saw:
  - Leaving step 3 during the demo kept half a guess, which scored 2,079 MW. The demo now sets the whole example at once and animates only the line.
  - The 0.96 label crossed the 1.0 line in step 7, so I moved it.
  - The step 6 caption understated AutoARIMA's result; it now says it beat "four of the five leading".
- I recomputed the example numbers in Python against facts.md: 1,561, 980, 572 (TimesFM 2.5), 906 (AutoARIMA), 140/168, 163/168, 16,571 and 18,119. They all match.
- I recorded `explainer.mp4` (42 s, 2.9 MB) and `explainer.gif` (5.5 MB) with `record.py` and looked at a tile of frames every 2 s. Every step appears, the demo guess and the toggle play, and the final step holds.
- Not checked: drawing by touch on a real phone. The drag handler uses pointer events with `touch-action: none` and was exercised only through the scripted demo, not by a person drawing.
- Remaining minor issue: in step 6 the "0.73" value label touches the dashed 1.0 line.

## Files

- `explainer.html`: the explainer, one self-contained file. The only network request is the optional Google Font.
- `explainer.mp4`, `explainer.gif`: recordings, with the example guess.
- `src/scene.js`, `src/build.py`, `src/scaffold.html`: the source. `python src/build.py` rebuilds the page from data.json.
- `qa_explainer/`: render-check frames, contact sheets and the recording tiles.
