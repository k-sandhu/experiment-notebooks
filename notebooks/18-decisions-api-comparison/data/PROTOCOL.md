# Protocol history for notebook 18

This file keeps the run history that the README and the notebook summarise in their limitations: frozen protocols, collection times, failures, amendments and corrections, in date order. Times are UTC from the `started_at` fields of the caches; the local date in Toronto (UTC-4) was 20 October 2026 for every call. Nothing here changes a result reported in the README.

## Broad set (protocol `nb18-v1`)

Frozen in [`protocol.json`](protocol.json) before any primary request (SHA-256 `b6ff5d43cdce3e2398532ff4552c94be2d2af71c829cb98dde1c06e7e712a11a`, also recorded in [`validation.json`](validation.json) and [`manifest.json`](manifest.json)). Main settings:

- Seed 20261020; six families (routing, policy, evidence, tracking, ledger, graph) at four levels; 16 test pairs and 1 pilot pair per family and level (768 test cases, 48 pilot cases), all authored 2026-10-20.
- Models and pins as in [`model_dates.json`](model_dates.json): `openai/gpt-6-luna-decisions-20261006` (provider OpenAI), `typesafe/jev-1.14-20261014` (TypeSafe), `inception/mercury-decide-20260930` (Inception), `cloudflare/clef-flash` (PrimeIntellect; no dated permaslug in the catalog, checkpoint immutability unverified). OpenRouter endpoint `https://openrouter.ai/api/alpha/decisions`, `allow_fallbacks: false`, timeout 60 s.
- One attempt per request, no retry; invalid or failed primary decisions count as wrong.
- Inference: pair bootstrap stratified by family and level (5,000 draws), all models aligned; six sign tests with Holm correction. Calibration on the chosen option's probability in ten fixed bins; review thresholds 0.8, 0.9 and 0.95 fixed in advance, plus a pilot-selected threshold reported separately.
- Size and spend guards: at most 6,500 new calls and USD 5.00 of reported cost plus reservations. The reservation is an estimate, not a billing bound.

Collection, 21 October 2026 UTC:

| Step | Start | End | Attempts |
|---|---|---|---:|
| Endpoint catalog (`model_catalog.json`) | 01:07:34 | 01:07:36 | 4 catalog requests |
| Capability check | 01:07:37 | 01:07:39 | 4 |
| Pilot | 01:07:39 | 01:07:47 | 192 |
| Primary test set | 01:07:47 | 01:09:36 | 3,072 |
| Serial timing and fresh connections | 01:10:25 | 01:11:12 | 144 |
| Throughput waves (concurrency 1 and 4) | 01:11:12 | 01:12:33 | 384 |
| Repeat, reversed options, wording prefix | 01:12:34 | 01:12:58 | 576 |
| Native yes/no type | 01:12:58 | 01:13:41 | 128 |
| Severity, first version (rejected) | 01:13:42 | 01:14:30 | 160 |
| Long input | 01:14:35 | 01:14:42 | 128 |
| Severity, second version | 01:15:50 | 01:16:36 | 160 |

Eight workers collected the primary set. Two primary requests failed with HTTP 502, both Mercury Decide (`test-routing-L4-003-1`, `test-tracking-L3-001-0`), and are counted as wrong.

The first severity diagnostic encoded the correct level in its incident reference, so a model could read the answer from the reference. It was rejected and collected again for every model with opaque 16-character references (`severity_cases_v2.json`). The 160 rejected attempts stay in the cache and in the spend, and are excluded from all results ([`scoring_audit.json`](scoring_audit.json)).

Scoring amendment, made during the scoring audit after one Jev 1.14 probability vector summed to 0.99 and before the final analysis: probability vectors within 0.02 of summing to 1 are normalised for every provider. This affects 133 primary replies. No request was changed and no item removed; raw vectors stay in the cache ([`scoring_audit.json`](scoring_audit.json)).

Spend for this part ([`spend.json`](spend.json)): USD 0.112450732 reported over 4,948 cached attempts; 2 failed attempts unpriced, with a USD 0.002 reservation. An offline replay with the API key removed and network access blocked made no calls ([`offline_network_audit.json`](offline_network_audit.json)). Added to the repository in commit `eeaf932c`.

## Audit, ledger study and harder lookups (protocol `nb18-followup-v1`)

Frozen in [`followup/protocol.json`](followup/protocol.json) before the new calls (SHA-256 `c3a81ab679f15c997d8d7b8a7168137bc76e9f106e86630e34751854111b9b79`). Main settings:

- Seed 2026102002; the same four model pins.
- Ledgers: 24 seeds for each of 4, 8 and 16 rows, small and large amounts, an exact claim and a claim one cent off (288 claims, 72 clusters). Methods: original wording, clarified wording, step instruction, block sums + model, block sums + Python, row labels + Python. Controls: exact block sums + model and exact net + model on 8 large 16-row ledgers. Offsets 0, ±1, ±10, ±100, ±1,000 and ±10,000 cents on the same 8 ledgers.
- Harder lookups: versioned joins, policy precedence and stateful counting at four levels, 6 pilot pairs and 32 test pairs per level.
- Pilot selection rule: pooled pilot accuracy above 0.55 and below 0.95 with a model range of at least 0.08; up to two eligible levels per family closest to 0.75. All held-out levels reported.
- Inference: seed-cluster bootstrap stratified by row count for the ledger and by family and level for the lookups (5,000 draws); a one-sided 95% bound when all 72 clusters succeed.
- One attempt, no retry; invalid decisions count as wrong; a failed intermediate call invalidates its pipeline. Python-assisted methods and exact-intermediate controls are excluded from any ranking of the models alone.
- Guards: at most 12,500 new calls per execution and USD 5.00 of reported cost plus reservations.

The audit of the broad set made no calls. It re-derived all 128 ledger labels from the transmitted text ([`followup/original_ledger_text_audit.csv`](followup/original_ledger_text_audit.csv)), checked 3,072 primary request bodies for answer fields or case IDs and 384 pairs for identical metadata, and confirmed that dictionary equality solves all 128 evidence cases ([`followup/leak_audit.json`](followup/leak_audit.json)).

Collection, 21 October 2026 UTC:

| Step | Start | End | Attempts | Failed |
|---|---|---|---:|---:|
| Ledger direct questions, three wordings | 01:45:54 | 01:52:22 | 3,456 | 9 |
| Block digit calls | 01:54:37 | 01:57:16 | 1,344 | 0 |
| Row-label calls | 01:57:17 | 01:57:58 | 576 | 0 |
| Block final calls | 01:57:58 | 01:59:17 | 1,106 | 0 |
| Exact-block and exact-net controls | 01:59:22 | 01:59:35 | 128 | 0 |
| Offset sweep | 01:59:36 | 01:59:57 | 352 | 0 |
| Lookup pilot, then first held-out collection | 01:59:58 | 03:22:33 | 3,648 | 483 |
| Fact-free control | 03:22:33 | 03:22:36 | 48 | 8 |

Note on the ledger direct questions: the 9 failures are 7 connection errors (Clef Flash 5, Jev 1.14 2) and 2 read time-outs (OpenAI Decisions), counted from [`followup/cache_requests.jsonl`](followup/cache_requests.jsonl). Jev 1.14's block calls returned HTTP 200 throughout, but 13 of its 336 block replies chose a digit that was not its most probable option and fail the parser, which makes 24 of its block-method claims unreadable.

The pilot selection was saved before any held-out call ([`followup/pilot_selection.json`](followup/pilot_selection.json), SHA-256 `4b8569c239690abdc7b3a5d3be385114a716797b00892aa65f9056a2c2176593`). All 576 pilot replies were readable. It chose joins levels 1 and 2, policy levels 1 and 3 and counting levels 1 and 3.

The first held-out collection used eight workers. Of its 3,072 requests, 483 failed: 443 connection errors (OpenAI Decisions 115, Jev 1.14 111, Clef Flash 119, Mercury Decide 98), 38 HTTP 429 rate-limit errors for Clef Flash and 2 HTTP 502 errors for Mercury Decide. Unreadable replies by model: OpenAI Decisions 115, Jev 1.14 111, Mercury Decide 100, Clef Flash 157 ([`followup/benchmark_predictions.json`](followup/benchmark_predictions.json)). On the six selected levels it scored OpenAI Decisions 47.4%, Jev 1.14 59.1%, Mercury Decide 63.0% and Clef Flash 45.3% ([`followup/benchmark_selected_summary.csv`](followup/benchmark_selected_summary.csv)), and only 3 of the 6 selected levels met the selection rule on the held-out cases ([`followup/benchmark_cells.csv`](followup/benchmark_cells.csv)).

The fact-free control sent 12 requests per model with only the reference string and the question. OpenAI Decisions returned HTTP 502 with the message `OpenAI refused to answer question "decision"` for 8 of them.

## Repeat collection of the held-out lookups (protocol `nb18-followup-replication-v1`)

Decided after the first held-out collection's results, including its transport failures, were visible. Frozen in [`followup/replication_protocol.json`](followup/replication_protocol.json): reason "Primary held-out run included fast ConnectionError failures and hosted concurrency 429 responses"; all 768 held-out case IDs; four model streams with at most one request in flight per model; request bodies unchanged from the first collection, with only a different local draw ID that is never transmitted; no retries; a failed connection is closed before the next case and the case is not replaced; the pilot selection file's hash is recorded; no item chosen by outcome. The notebook checks that every repeat request body equals the first collection's body for the same model and case.

Collected 03:27:25 to 03:32:30 UTC: 3,072 requests, 202 failed. Clef Flash returned HTTP 429 ("Too many concurrent hosted model requests. Try again shortly.") to 200 requests, 97 of them on the selected levels. Mercury Decide returned HTTP 502 to 2 requests (`test:versioned joins:3:18:0`, `test:policy precedence:2:24:0`), neither on a selected level. OpenAI Decisions and Jev 1.14 returned 768 readable replies each. On the held-out cases, 4 of the 6 selected levels met the selection rule ([`followup/benchmark_replication_cells.csv`](followup/benchmark_replication_cells.csv)). The README and notebook report this collection in place of the first.

Cache layout: [`followup/cache_requests.jsonl`](followup/cache_requests.jsonl) holds the 10,658 attempts before the repeat collection and [`followup/cache_replication_requests.jsonl`](followup/cache_replication_requests.jsonl) the 3,072 repeat attempts. The split keeps every raw line and request key. No secret header is stored.

Spend for this part ([`followup/spend.json`](followup/spend.json)): USD 0.583295223 reported over 13,730 attempts; 702 failed attempts unpriced, with a reservation estimate of USD 0.7589892 that is not a billing bound. Combined with the broad set, USD 0.695745955 reported. An offline replay of the whole notebook with both live switches and the key removed and sockets blocked made no calls ([`followup/offline_network_audit.json`](followup/offline_network_audit.json)). Added to the repository in commit `f9ec6683`.

## Corrections to the reader text

- An earlier README said all four models scored 50% on the hardest original ledgers. The data show 16 of 32 for OpenAI Decisions, Mercury Decide and Clef Flash and 15 of 32 for Jev 1.14; the cached predictions and scores were already correct ([`followup/ATTRIBUTION.md`](followup/ATTRIBUTION.md)).
- The README before the 28 October 2026 rewrite said Jev 1.14 and Mercury Decide each accepted 25% of claims at every offset. [`followup/offset_sweep_summary.csv`](followup/offset_sweep_summary.csv) shows Jev 1.14 at 0% and only Mercury Decide at 25%.
- The same README said Clef Flash had the two HTTP 502 errors in the repeat collection and the other three models returned 768 of 768 readable replies; notebook text also gave Clef Flash 566 readable replies. The cache shows Clef Flash with 568 readable replies (200 HTTP 429) and the two HTTP 502 errors on Mercury Decide (766 readable).
- The shortcut that counts matching events without keeping the latest update was reported as 56.2%, its average over the four counting levels. It scores 71.9% (46 of 64) at counting level 1, one of the selected levels, and 50.0% to 51.6% at levels 2 to 4 ([`followup/shortcut_baselines.csv`](followup/shortcut_baselines.csv)).

## Text-only rewrite, 28 October 2026

The README and the notebook's markdown cells were rewritten to give one answer from all the evidence. No model was called, no code cell or output changed and no figure was regenerated. Counts added to the reader text (pair scores on the repeat collection, the two ledgers Mercury Decide accepted in the offset sweep, the per-family broad-set counts, unreadable-reply counts by cause) were computed read-only from the files named beside each number.
