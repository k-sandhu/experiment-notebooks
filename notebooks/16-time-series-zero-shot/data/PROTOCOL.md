# Notebook 16: run history and settings

This file keeps the records that matter to someone checking the run but not to someone learning from it. Every fact below comes from a file in this folder, from the notebook's committed outputs, or from the GitHub issues named. Times are UTC.

## Plan

- Proposal #13 ("zero-shot time-series foundation models on the last two months of data") planned to run each model locally from a pinned Hugging Face revision, with candidate series including air quality, bike-share trips, GitHub issue counts and Treasury yields, and an optional comparison with a general-purpose language model given the history as text.
- Claim issue #22 ("Notebook 16: time-series-zero-shot") replaced the local route with hosted inference through TSFM.ai at the owner's request, planned six series, about 20 origins per series, horizons of 24/168 hourly steps and 7/28 daily steps, histories of 512 and 2,048 values, a published price of $0.00025 per forecast and a $3 cap. It said hosted execution meant no local CPU, GPU or peak-memory comparison would be claimed.
- As built, the notebook used wind speed instead of air quality and left out the optional language-model comparison. Local setup, GPU memory and hardware comparisons are outside the measured results.

## 2026-10-19: sources, provenance and catalog

- The five source files in `raw/` were downloaded between 20:06:49 and 20:06:51 (`data_manifest.json`, field `retrieved_at`), with their URLs and SHA-256 hashes. The normalized table `series.csv` has its own hash in the manifest. The current public vintage was frozen; historical as-of-origin vintages were not available. The missing-data policy was to stop on any missing or duplicate value, with no filling or clipping.
- Model provenance was checked the same day (`model_provenance.json`, `source_checks.json`). No training cutoff was established for any hosted checkpoint. Availability bounds: last public repository change for Chronos-2, TimesFM 2.5, Moirai 2, Toto 2 and Lag-Llama; the July 2 weight commit `f500c26` for TiRex-2 (its repository changed again on October 7, in other files; weight SHA-256 `184b160f...`); IBM's March 31 announcement for TTM R3, later than its March 24 repository change.
- The provider's catalog (`catalog_snapshot.json`, `catalog_full.json`, 54 models) did not list TimesFM 3 (`google/timesfm-3.0-pytorch`), so TimesFM 2.5 was used. The catalog gives no version, parameter count or licence for the seven models used. The service does not expose or accept an immutable checkpoint revision.
- Account snapshot before any request (`billing_before.json`): free plan, 80,000 credits remaining, usage $0.

## 2026-10-19, 20:06 to 20:09: capability checks

- Eight probe files in `probes/`, sent between 20:06:08 and 20:08:56: one request per model, each with two short synthetic input series, and one request to the batch route carrying two requests. The notebook counts these as 9 forecast requests.
- All returned HTTP 200 with two outputs, nine quantile levels (0.1 to 0.9), the model name asked for and provider `harpoon` (`capability_probes.json`). Wall times ranged from 7.63 s (Moirai 2) to 79.75 s (Toto 2).
- The snapshot `billing_after_probes.json` records usage of $0.00175 (79,993 credits remaining). It has no timestamp.

## 2026-10-19, 20:11 to 20:38: collection

- Protocol tag `ts16-univariate-v1`. 1,344 forecast requests: five models at 224 histories and TTM R3 and Lag-Llama at 112 (the service caps them at 512 and 1,024 values). Each request carried one series' history, the frequency hint, the prediction length, the history length and the nine quantile levels, with no timestamps or covariates.
- Requests went to `/v1/forecast/batch` in batches of up to eight, with a 900-second timeout. The default collector ran up to three batch calls at once; this collection also used separate daily and manual recovery queues, and the peak concurrency derived from cached request times was five batches (`run_manifest.json`). An intent file was written before each live call (177 in `intents/`, created between 20:11:56 and 20:37:54) so that an interrupted call could not be retried silently.
- 177 batch calls in all (`batches/`): 168 of eight requests, 5 of four and 4 of one. Full batches returned between 20:12:12 and 20:38:00.
- Three batches of eight ended without an HTTP status (`ChunkedEncodingError`) at 20:15:15, 20:16:22 and 20:16:44, after 63.2, 61.9 and 66.2 seconds. Together they held 24 forecast requests covering all seven models. Their failure envelopes are kept in `batches/`.
- Usage snapshots taken during collection (no timestamps): $0.03425 (`billing_mid_collection.json`), $0.19625 (`billing_before_recovery.json`) and $0.2535 (`billing_before_lag_recovery.json`).
- Recovery (the notebook's helper runs only by hand, after recorded attempts are reconciled with account usage): 21 requests re-sent at 20:32:27 to 20:32:37 in five batches of four and one single request, then the three Lag-Llama requests one at a time at 20:35:47, 20:36:19 and 20:36:51 (29.1 to 32.0 seconds each). All 24 returned HTTP 200 and parsed. Each recovered entry in `cache_hosted/` lists the failed batch in `previous_batches` (24 entries).
- Final state: 1,344 of 1,344 forecasts cached with `ok: true`, all from provider `harpoon` and naming the requested model; `failures.json` is empty.

## Spend

- After collection (`billing_after_collection.json`): usage $0.34425, 78,623 credits remaining, so 1,377 credits used: 1,368 experiment request attempts (1,344 plus the 24 repeated) and 9 probe requests, at $0.00025 each. The attempt-based estimate is also $0.34425 (`spend.json`).
- The plan stayed `free` with status `inactive`; no top-up or subscription was activated. The account reports a usage cost and a next-invoice estimate of $0.34; this is not a paid-invoice confirmation.
- The published rate was checked at https://tsfm.ai/pricing on 2026-10-19.

## Standard methods

- 1,120 forecasts (five methods at 224 histories), fitted one at a time on Windows, AMD64, an Intel64 Family 6 Model 170 Stepping 4 processor with 22 logical CPUs, Python 3.13.5 (`run_manifest.json`). Total fit-and-predict wall time 1,147.9 seconds (`spend.json`).
- Settings, fixed before scoring: seasonal naive with Gaussian intervals from one-cycle-ago residuals, widened by the square root of one plus the number of completed cycles; AutoETS model `ZZA` with normal errors; AutoARIMA with `max_p` 2, `max_q` 2, `max_P` 1, `max_Q` 1, `max_order` 4, `nmodels` 20, stepwise, approximation on; Theta with additive decomposition; lag boosting with `HistGradientBoostingRegressor`, 100 iterations, 15 leaf nodes, at least 10 samples per leaf, no early stopping, random state 1601.
- Every AutoARIMA record carries warnings: 3,159 "possible convergence problem: minimize gave code 2", 4 with code 1, and 152 "stepwise search was stopped early due to reaching the model number limit: nmodels=20" (`cache_baselines/`, field `warnings`).
- Cache keys include the numpy, scipy, statsforecast and scikit-learn versions, so a different version refits locally.

## Scoring settings

- Seasonal periods 168 (Ontario demand), 24 (weather), 7 (page views) and 5 (USD/CAD), set in the manifest before scoring.
- Up to 20 evenly spaced eligible origins per series, chosen without looking at target values; 12 for USD/CAD, where only 12 were eligible.
- One maximum-length forecast per request, scored at the 24/168 or 7/28 prefixes.
- Bootstrap: 10,000 resamples of the six series, seed 1601; paired comparison of the best pretrained model and best fitted method, seed 1602. Both winners were selected after evaluation; the interval is descriptive, not a corrected significance test.
- Quantile crossings are counted and kept, never sorted or repaired. For AutoETS, AutoARIMA and Theta the point forecast stands in for the 50th percentile.

## 2026-10-19, 20:51: validation

`validation.json` records an offline replay with zero HTTP attempts, identical derived files, verified request and source hashes, the normalized table rebuilt from the raw files, TimesFM 2.5 crossings at 23,072 of 23,072 steps kept unmodified, a credential scan that found no configured credential value, and the guards that reject missing, duplicated or failed comparisons.

## 2026-10-28: text rewrite

The README and the notebook's markdown cells were rewritten for a reader new to forecasting. No model was called, the notebook was not re-run, and no code cell, output or figure changed; spend $0. New counts in the text were computed by read-only scripts from the files in this folder, and the text names the file and field for each. One of them was done after the results were seen: each cached TimesFM 2.5 response's `mean` field equals the value labelled 0.6 at all 23,072 steps (the value labelled 0.5 once), while for Chronos-2, Moirai 2, TiRex-2, Toto 2 and TTM R3 it equals the value labelled 0.5 at every step. Rescoring TimesFM 2.5 with the `mean` field under the notebook's rule gives relative MAE 0.886 at 512 values and 0.844 at 2,048, against the notebook's 0.911 and 0.869. The notebook's tables were left as they are.
