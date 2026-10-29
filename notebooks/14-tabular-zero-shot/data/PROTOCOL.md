# Notebook 14 protocol and run history

This file records the settings and run history of notebook 14 for readers who want to check the work. The README and the notebook explain the experiment and its results.

## Settings fixed before scoring

The notebook records these settings in its first code cell and in every saved request. None was changed after the results were seen.

- Protocol name `tabular-zero-shot-v1` (`PROTOCOL`), stored in every cached request.
- Tables: four rules (`MECHANISMS`: `linear`, `smooth`, `threshold`, `range_shift`), two outcome types (`TASKS`: `classification`, `regression`), three seeds (`SEEDS`: 101, 202, 303), eight columns (`N_FEATURES`), a pool of 128 labelled rows (`N_CONTEXT_POOL`) and 128 test rows (`N_TEST`). Labelled-row counts `N_CONTEXT` = 32 and 128; the 32-row set is the first 32 rows of the 128.
- Generator: columns uniform on [−1, 1], rounded to 6 decimals, drawn from `SeedSequence([seed, rule index, 1401])`; out-of-range test rows have x0 = ±U(1.5, 3). Outcomes drawn from `SeedSequence([seed, rule index, task flag, 1402])`: Gaussian noise with standard deviation 0.3 for numbers, Bernoulli with probability 1 / (1 + e^(−f)) for yes/no. Each yes/no table must contain both outcomes in its first 32 labelled rows and in its test rows.
- TabPFN request: `model_path` `v3.5_default`, `model_version` `v3.5`, `n_estimators` 8, `fit_mode` `fit_preprocessors`, `tabpfn_systems` `["preprocessing"]`, `random_state` equal to the table's seed, `output_type` `probas` for yes/no and `median` for numbers. Thinking mode was not requested (`thinking_effort` is null in the saved quotes) and no weights were fine-tuned.
- Fitted models (scikit-learn 1.9.0, one thread): `DummyClassifier(strategy="prior")` and `DummyRegressor(strategy="mean")`; standardised `LogisticRegression(C=1, max_iter=1000)` and `Ridge(alpha=1)`; random forest with 200 trees, `min_samples_leaf=2`, `max_features=1.0`; histogram gradient boosting with `max_iter=100`, `max_leaf_nodes=15`, `min_samples_leaf=5`, `l2_regularization=1`, `learning_rate=0.1`, no early stopping. Each uses the table's seed as `random_state` where it takes one.
- Scoring: a yes/no prediction is "yes" when the probability of yes is at least 0.5. Relative MAE divides by the constant guess's MAE on the same table and labelled-row count. Intervals: 2,000 bootstrap draws over the three per-seed means, random generator seed 1403.
- Spending limits for a live run: `MAX_USAGE_TOKENS` 600,000 and `MAX_LIVE_PREDICTIONS` 48. No automatic retries of a prediction step.

## 2026-10-19: data, collection and checks

- The 24 tables were generated and frozen, with SHA-256 hashes, creation date and licence (MIT) in `fixture_manifest.json`.
- Eight source pages were opened and recorded in `source_checks.json`: the Prior Labs technical reports, REST quickstart, metering and pricing pages, and the four further-reading papers.
- Before collection the account's counters stood at 0 daily and 0 monthly computation tokens, with limits of 5,000,000 daily and 20,000,000 monthly (`provider_preflight.json`, `usage_before_collection`).
- 19:36:02 and 19:36:11 UTC: the two smoke-mode requests, `linear_101_classification` and `linear_101_regression` with 32 labelled rows, were collected first (earliest `collected_at` values in `cache/`). They served as the pilot and were kept as part of the 48.
- 19:36:28 UTC: preflight check. The counters showed 20,000 tokens used, the two pilot requests. The service quoted 10,000 tokens per request for both 32 and 128 labelled rows (`pricing_version` `quota_v3`). Its settings and model limits were saved to `provider_preflight.json`, and the published API schema to `api_schema.json`.
- 19:36:35 to 19:46:00 UTC: the remaining 46 requests were collected. The three slowest were `smooth_202_classification` at 128 rows (82.47 s), `threshold_202_classification` at 32 rows (80.08 s) and `range_shift_202_classification` at 32 rows (31.09 s). No request failed and none was retried.
- After collection the counters stood at 480,000 daily and monthly tokens (`usage_after.json`), equal to the sum of the 48 quotes. The service exposes no charge in dollars, and no paid top-up was made (`spend.json`).
- Every response reported checkpoint `/app/tabpfn_models/tabpfn-v3.5-20260909.safetensors`, server package 9.0.0, 8 estimators, standard execution, device `cuda:0` and `random_state` 0, although the requests asked for 101, 202 and 303. Both values are kept in `model_runtime.json`; no claim is made that the service used the requested seed. The service exposes no checkpoint hash or graphics processor model.
- Redaction: temporary signed upload URLs and the API key are not stored. Only upload IDs, the fit and prediction responses and timings are kept; the code also keeps numeric usage headers, but the service returned none. Error messages from the service have the key replaced by `[redacted]` before they are shown.
- Replay validation (`validation.json`): 24 fixture tables, 48 TabPFN caches and 192 fitted-model caches; 0 HTTP attempts during replay; derived results identical to the collected run; fixture hashes valid; credentials absent; an offline cache miss stops without any HTTP call. Review checks confirmed that a custom seed and rule selection works, custom fixtures replay identically, and derived files use LF line endings.

## Analysis choices made after the results were known

- The error example (`range_shift_101_regression`) was chosen after scoring by a fixed rule: the out-of-range number table at 128 labelled rows with the largest TabPFN-minus-Linear MAE.
- The "best mean baseline" named in the notebook's printed sentences (Random forest for yes/no, Gradient boosting for numbers) was identified after scoring. All four fitted models stay in every table.

## 2026-10-28: rewrite of the README and notebook text

The README and the notebook's markdown cells were rewritten. No code cell, output, figure or data file changed, and no model was called. Some numbers were added to the text, all computed after the results were known from the saved files with read-only scripts that are not part of the repository; the text names the source file and columns for each:

- true-rule scores per table, from `fixtures/*.csv` (`oracle_value`, `target`, `split`);
- the split of wrong yes/no answers into those that agreed and disagreed with the true rule, the distance of combination-rule disagreements from the x0 = 0 and x1 = 0 boundaries, the spread of probabilities on the straight-line tables, the direction of out-of-range errors and the gap between predicted and true probabilities, all from `predictions.csv` and the fixtures;
- the server-reported step timings per request, from `fit_response.timings` and `raw_response.timings` in `cache/tabpfn_*.json`.

Two sources were opened on 2026-10-28: the TabPFN paper by Hollmann et al. (arXiv 2207.01848), added to further reading, and the Prior Labs technical reports page, which lists the TabPFN-3.5 report dated 2026-09-15 and states that the model ranks first on TabArena and BeyondArena.
