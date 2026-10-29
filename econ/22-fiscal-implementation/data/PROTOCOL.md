# Notebook 22 run history

This file records how the study was run, in date order, for readers who want to check the work. The reader-facing explanation is in the [README](../README.md) and the [notebook](../22_fiscal_implementation.ipynb). Times are UTC and come from the timestamp fields of the files named in each entry. All model runs took place on 22 October 2026.

## Files that hold the plan

| File | What it records |
| --- | --- |
| [protocol.json](protocol.json) (top of `data/`) | The synthetic study's plan, `nb22-fiscal-v1.0` |
| [real_v2/protocol_initial_120s.json](real_v2/protocol_initial_120s.json) | The real-report plan as first fixed, with a 120-second time limit (spec hash `5c5fb368...`) |
| [real_v2/request_manifest_initial_120s.json](real_v2/request_manifest_initial_120s.json) | The 150 request hashes under that first plan |
| [real_v2/transport_amendment.json](real_v2/transport_amendment.json) | The change of the test time limit to 300 seconds, with its reason |
| [real_v2/protocol.json](real_v2/protocol.json) | The plan in force for the test questions (spec hash `db65b8da...`) |
| [real_v2/request_manifest.json](real_v2/request_manifest.json) | The 150 request hashes in force for the run |
| [real_v2/runner_validation.json](real_v2/runner_validation.json) | Checks of the runner, parser and calculator made before any model call, and checks that the time-limit change touched nothing else |

These files are kept unchanged.

## 22 October 2026: synthetic study (`nb22-fiscal-v1.0`)

- Python generated 60 fictional spending-programme histories in six recurring patterns (`announcement_only`, `installments_duplicates`, `cuts_cancellation`, `historical_corrections`, `reporting_dates`, `mixed_projects`): 12 development and 48 test histories. All amounts are in fictional "million crowns"; the as-of date for document availability was 30 September 2026. Fixture content is released under CC0-1.0 ([model_metadata.json](model_metadata.json)).
- One OpenRouter call to Qwen3.8 Flash (`qwen/qwen3.8-flash-20260826`, released 26 August 2026) wrote 22 wording templates for 11 event types; Qwen did not produce any amount or answer. Cost USD 0.00052039 ([spend.json](spend.json), [authoring_cache.json](authoring_cache.json)).
- Models: GPT-6.1 Sol through `codex exec` (CLI `codex-cli 0.160.1`) and Claude Opus 5.5 through `claude -p` (CLI 2.1.296), both at low reasoning effort, Claude capped at USD 0.25 per request. 240 CLI requests (120 each), no failed requests, no repair calls. Claude list price USD 3.009032 ([spend.json](spend.json)).
- Scoring: exact three-quarter cash history; strict JSON with no recovery of an object from surrounding text. 5,000 paired bootstrap resamples of histories, seed 22061022.
- Development: 47 of 48 valid outputs; one Claude Direct reply added prose before otherwise correct JSON. The strict output rule was kept for the test run.
- Test: GPT-6.1 Sol 48/48 with both methods; Claude Opus 5.5 47/48 Direct and 48/48 Ledger. The one invalid reply had correct cash, authority and status values but began with prose. All 191 schema-valid test answers had zero cash error ([summary.csv](summary.csv), [validation.json](validation.json)).
- Files: everything at the top of `data/` except this file belongs to this study. The archived write-up is [synthetic_v1_README.md](synthetic_v1_README.md), and its figures are `figures/cash_exact.png`, `figures/cash_error_by_family.png` and `figures/example_cash_paths.png`.
- Committed as `b05e85be` (merged into the repository with notebook 21).

## 22 October 2026: real-report study (`fiscal-real-v2.0`)

### Sources and questions (before any model call)

- 22:00:08. UK and US source discovery by the `fiscal_notebook` agent ([real_v2/discovery_uk_us.json](real_v2/discovery_uk_us.json)); EU discovery by the `methods_literature` agent ([real_v2/discovery_eu.json](real_v2/discovery_eu.json)); annual-report candidates ([real_v2/discovery_annuals.json](real_v2/discovery_annuals.json)). The freshness filter kept target publications dated after 12 October 2026 (Muse Wonder Full's release) and on or before 22 October 2026.
- Extraction ([real_v2/sources.json](real_v2/sources.json), field `extraction_notes`): HTML table cells were kept in order. The UK annual-report PDFs were extracted with Poppler `pdftotext -layout`; the Treasury PDF used pdfplumber. Finance tables were checked against the rendered pages. One Treasury footnote on page 8 was interleaved with a neighbouring note by the extractor; its reading order was repaired without changing words or numbers. Raw PDF and HTML downloads are git-ignored; their URLs, licences and hashes are recorded.
- Answer key review ([real_v2/gold_review.json](real_v2/gold_review.json)): UK and US questions written by `fiscal_notebook` and checked by `methods_literature`; annual-report questions written by `root` and checked by `fiscal_notebook`, which recalculated seven numeric answers and checked two missing disclosures; EU questions written by `methods_literature` and checked by `root`. These are AI agents; there were no independent human coders. All passed with no answer changes.
- Two candidate questions were excluded before collection: `RO_CURRENT_QUARTER_CASH_ONLY` (a Renewables Obligation statement whose unit header conflicted with its figures) and `EU-EUSF-Q03` (redundant with the aggregate same-day storm-aid question).
- Dating qualification ([real_v2/provenance_notes.json](real_v2/provenance_notes.json)): the Horizon publication-history page was first published on 9 February 2026 and updated on 22 October 2026. Its frozen `published_on` field gives the update date and `original_page_published_on` keeps the first date. No scored amount comes from an older entry. The narrative was qualified; prompts and inputs were not changed.
- 22:01:51. Runner checks passed ([real_v2/runner_validation.json](real_v2/runner_validation.json), `base_runner_checks`), including identical input for both methods, no answer key in prompts, the JSON reading rule and a zero-call offline replay.

### Plan fixed, trial run and time-limit change

- 22:04:56. First plan fixed ([real_v2/protocol_initial_120s.json](real_v2/protocol_initial_120s.json)): 25 questions (3 trial, 22 test) in 9 packets from 10 source records; models GPT-6.1 Sol (`codex exec`, CLI 0.160.1), Claude Opus 5.5 (`claude -p`, CLI 2.1.296, at most USD 0.50 per request) and Muse Wonder Full (`muse exec`, CLI 1.4.12, one model step), all at medium reasoning effort; one attempt per request, no retry or repair; 120-second time limit; at most 180 requests and USD 20 of Claude list price; parser `unchanged-json-object-v1`; score `amount-status-separate-grounding-v2`; uncertainty from 10,000 paired whole-packet bootstrap resamples, seed 22061022.
- 22:08:08. Trial run finished ([real_v2/development_results/](real_v2/development_results/run_audit.json)): 18 requests on `EU-RRF-Q01`, `EU-RRF-Q03` and `EU-RRF-Q04`. 17 correct; the Muse Wonder Full Ledger request on `EU-RRF-Q01` timed out at 120 seconds. Claude list price USD 0.1512728.
- 22:08:55. Time-limit change recorded before any test request ([real_v2/transport_amendment.json](real_v2/transport_amendment.json)): the test time limit was raised from 120 to 300 seconds for all three models, because "One development Muse request exceeded two minutes". Trial requests kept their 120-second records and the timed-out trial request was not retried. No question, excerpt, answer, prompt, parser or scoring rule changed. Only the 132 test request hashes changed ([real_v2/runner_validation.json](real_v2/runner_validation.json), `transport_amendment_checks`).
- 22:08:56. Amended plan fixed ([real_v2/protocol.json](real_v2/protocol.json)).

### Test run

- Test requests ran in random order, at most three at a time, each in a fresh empty folder with tools off.
- 22:19:21, 22:26:19 and 22:33:22. The `methods_literature` agent rescored the cache at three points during and after collection (53, 109 and 132 records). The final review ([real_v2/response_review.json](real_v2/response_review.json)) found 130 of 132 correct under the fixed rules, 131 of 131 completed replies correct and in the exact format, and no copied-number failures. It manually checked both invalid runs, both quote failures, 12 passing multi-row ledgers and 4 passing Direct "not disclosed" explanations, and found no further unit, sign, period or measure issue.
- 22:30:58. Test collection finished: 132 requests ([real_v2/test_collection_results/run_audit.json](real_v2/test_collection_results/run_audit.json)). Claude list price for the whole study, trial included, USD 4.284896; Codex and Muse charges per request are not reported.
- Muse Wonder Full internal retries, both on test requests ([real_v2/response_review.json](real_v2/response_review.json), `retry_activity_audit`):
  - `UKFE-02` Direct, request `f7a95273...`: the first model stream returned HTTP 504; the CLI scheduled attempt 2 of 10; the request was stopped at the 300-second limit (295.07 seconds recorded) with no answer.
  - `MTS_DEFENCE_LATEST` Ledger, request `5bf5f323...`: the first stream returned HTTP 504; attempt 2 completed and returned a correct answer (916,836). Usage records 2 calls, 1 failed and 1 completed. The fixed run rule rejects a run with an extra model attempt, so it counts as wrong.
  - The runner itself made no retries or repair calls. The 150 runner requests therefore do not equal the number of provider attempts.
- Model identity: Claude and Muse returned `claude-opus-5-5` and `muse-wonder-full-1.0` on all 50 requests each; Codex returns no model identity, so GPT-6.1 Sol's identity is the requested `gpt-6.1-sol`. No dated model version was recorded for any model.

### Replay, review and commit

- 22:34:29. Offline analysis from the cache ([real_v2/results/run_audit.json](real_v2/results/run_audit.json)): 150 rows, 0 new calls.
- 22:34:31. Offline audit ([real_v2/offline_audit.json](real_v2/offline_audit.json)): source hashes match, both methods received identical input, the answer key was absent from inputs, subprocess and socket calls were blocked during replay, and all 300 cache files were unchanged.
- Render review the same day ([real_v2/publication_validation.json](real_v2/publication_validation.json)): 7 code cells executed with no errors, 0 new calls, 132 test responses rescored.
- Committed as `86f08ec1` ("Rerun fiscal notebook on recent public reports with three frontier CLIs").

## 24 October 2026: narrative edit

- Commit `5923cdbf` gave the notebook and README a gradual introduction. Text only; no code, data or figure changes.

## 28 October 2026: README and notebook rewrite

- The README and the notebook's markdown cells were rewritten to give one answer from all the evidence. The synthetic study and the trial run moved to a "How the study got here" section, and run details moved to this file. Text only: no model calls, no re-run, and no change to code cells, outputs, data files or figures.
- New counts in the text were computed read-only from the committed cache and results files: output-token medians (`usage` in each cache result file), ledger rows and exclusions per reply (`entries` and `exclusions` in each cached Ledger reply), excerpt lengths (`text` in [real_v2/sources.json](real_v2/sources.json)), and the absence of any JSON recovery (`recovered_json` in [real_v2/results/test_case_scores.csv](real_v2/results/test_case_scores.csv)).
- The Further reading links were checked on 28 October 2026.
