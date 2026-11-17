# forecast-guess: facts (notebook 16, time-series-zero-shot)

Source: notebooks/16-time-series-zero-shot (README.md, data/series.csv, data/cache_hosted/*.json, data/cache_baselines/*.json, data/summary.csv, data/series_scores.csv, data/metrics.csv, data/target_dates.csv, data/origins.csv, data/error_example.json). Per-model point forecasts for the single example origin WERE found in the caches and are in data.json; nothing was invented.

## Question
Given only a series' recent history, does a pretrained forecasting model ("zero-shot": no fitting to that series) make smaller errors than (a) repeating the last cycle ("seasonal naive") and (b) standard methods fitted to that history? And do its 80% intervals contain the truth about 80% of the time?

## Setup
- 6 public series, frozen 2026-10-19; targets only 2026-08-20 to 2026-10-17 (after every model's public weights): Ontario demand (hourly MW, seasonal naive repeats 168 h), Toronto temperature, Toronto wind (hourly, 24 h), Toronto and AI Wikipedia page views (daily, 7 d), USD/CAD (business days, 5).
- 112 origins (20 per series, 12 for USD/CAD) x history 512 or 2,048 values. Hourly horizon 168 h (scored also at 24 h); daily 28 steps (also 7).
- 7 pretrained models via the TSFM.ai hosting service: Chronos-2, Moirai 2, TiRex-2, Toto 2, TimesFM 2.5, TTM R3, Lag-Llama. 5 standard methods: Seasonal naive, AutoETS, AutoARIMA, Theta, Lag boosting. Point forecast of a pretrained model = its median (50th percentile of 9 quantiles).
- Models see only numbers: no dates, holidays, weather.

## Headline metric: relative MAE (summary.csv)
Definition: MAE of a method divided by MAE of seasonal naive on the same forecasts (errors summed per series and horizon, two horizons averaged, six series averaged equally). 1.0 = same as repeating last cycle; 0.86 = 14% less error. skill_percent = (1 - relative MAE) x 100. 95% interval = resample the 6 series 10,000 times (descriptive, not a significance test).
History 512: Chronos-2 0.860 (0.748-0.974), Moirai 2 0.862, TiRex-2 0.869, Toto 2 0.871, TimesFM 2.5 0.911, AutoETS 0.961, Seasonal naive 1.000, AutoARIMA 1.002, Theta 1.086, Lag boosting 1.150, TTM R3 1.258, Lag-Llama 1.334. History 2048: Moirai 2 0.815, TiRex-2 0.835, Toto 2 0.841, Chronos-2 0.844, TimesFM 2.5 0.869, AutoETS 0.900 (TTM R3 and Lag-Llama not served at 2,048).
Top four are within 0.011 of each other: order not a finding. Chronos-2 vs AutoETS: 0.101 lower on average, but 95% interval -0.233 to +0.015 (paired_comparison.json), so a lead over the best fitted method is not established. 24 requests were re-sent; 0 unreadable forecasts (README).
By series (512, series_scores.csv; mean of two horizons): Ontario demand TiRex-2 0.641, Chronos-2 0.666, AutoETS 1.069 (fitted methods all lose); AI page views TiRex-2 1.187, Chronos-2 1.075; USD/CAD TiRex-2 1.015, Chronos-2 1.045, AutoETS 0.989. Pretrained models lose to seasonal naive on the two series without a dependable cycle (AI page views, USD/CAD).
Intervals (README section 6): four leaders' 80% intervals covered only 65.5-70.1% of actual values; TimesFM 2.5's quantiles were unusable (10th above 20th at 23,072 of 23,072 steps).

## The example origin for a "guess before you see it" explainer (data.json -> example)
Case ontario_demand_5544_512: Ontario electricity demand, origin 2026-08-20T00:00; models were given 512 hourly values (data.json holds the last 336 = 14 days, 2026-08-06T00:00 to 2026-08-19T23:00, plus last values 20,564, 19,939, 19,106, 17,758, 16,661, 15,576 MW); forecast the next 168 hours (to 2026-08-26T23:00). This is the README worked example.
- Why seasonal naive overshoots: the week before used more power (average 18,119 MW, peak 22,353) than the week forecast (average 16,571, peak 20,684). Hour 0: actual 14,820, seasonal naive 15,873 (+1,053), Chronos-2 14,917 (+97). Hour 17 (5 p.m.): actual 20,166, Chronos-2 20,389, seasonal naive 22,212. All values recomputed from the data and match the README.
- MAE over 168 h at this origin, MW (recomputed; equals metrics.csv): TimesFM 2.5 572, AutoARIMA 906, TiRex-2 963, Chronos-2 980, Moirai 2 1,015, Toto 2 1,099, Seasonal naive 1,561, AutoETS 1,752, Theta 1,873, TTM R3 2,290, Lag boosting 2,646, Lag-Llama 3,686. Chronos-2 relative MAE here = 980/1,561 = 0.628 (README: 37% less error). Chronos-2 24-hour MAE 227 vs seasonal naive 1,578.
- Take-away worth noting: one origin is one draw. At this origin AutoARIMA (906) beat four of the five leading pretrained models, yet over all Ontario origins AutoARIMA's relative MAE is 1.109 and TimesFM 2.5's 0.732; the average, not any one week, is the evidence. Chronos-2's 80% interval contained the actual in 140 of the 168 hours (README: all 24 of the first 24 hours; computed here 140/168).
- p10/p90 per pretrained model per hour are included (TimesFM 2.5's are unreliable).

## Other examples (README section 7)
- A typical success: the Ontario origin above.
- A failure: when the level drops, models keep old peaks; when it rises they expect a return to normal (AI page views; error_example.json: Chronos-2 on wiki_ai_2816_512, origin 2026-09-17, MAE 4,827.6 vs seasonal naive 2,901.6, relative MAE 1.664).
- A disagreement: on USD/CAD the second-worst model overall, TTM R3, is best (0.887).

## Caveats (README sections 9, summary)
- Six hand-picked series over one two-month window with heavily overlapping forecast windows; intervals treat each series as one unit and are wide.
- The hosting service does not state model versions, hardware, or training cutoffs; the date rule rests on public weight dates (latest bound TiRex-2, 2026-07-02, 49 days before the first target).
- Series downloaded 2026-10-19; electricity data can be revised after release.
- No extra inputs (holidays, weather) for any method; fitted methods use fixed bounded settings (AutoARIMA search capped at 20 models).
- Discrepancy check: none found; README worked-example values (Chronos 97 MW, 14,917; seasonal naive 15,873; MAE 980/1,561; 227/1,578) all reproduce from the cached files.
