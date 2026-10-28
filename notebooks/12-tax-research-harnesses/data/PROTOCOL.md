# Notebook 12 protocol history

This file records how the data for notebook 12 was collected: the design that was fixed before collection, each
change made during collection, the earlier collections that are kept but not scored, and notes needed to replay or
audit the files. The reader-facing explanation is in `../README.md`. All times are UTC on 17 October 2026 unless
stated otherwise; they come from `frozen_at` in each `design.json` and `collected_at` in each cache.

## Before tax collection: a replaced invoice task

An earlier version of this notebook tested a different task (invoices). The person who commissioned the notebook
chose the US S-Corporation workpaper task instead, and the invoice work was dropped. Its spend is kept in
`preliminary_work_spend.json`: 242 cached model calls (240 unique requests), $0.07739788 of recorded OpenRouter
usage. No invoice result appears in the notebook.

## What was fixed before any tax result was seen

- The 12 test companies and 4 development companies (`cases.json`), the seven-source packet (`sources.json`), the
  rules and checklist, the checker, the scorer and the answer-key function.
- The comparison: two models, two instruction lengths, four setups, at most two calls per run, one sample, the
  primary comparison "custom_feedback minus generic_review within model and prompt", and the rule that a gain is
  supported only when the paired case-bootstrap 95% interval is strictly above zero (2,000 resamples).
- The design is hashed: final design SHA-256 `024fdbe524b28d44e181c004d710724e13f5334afa7d1783a6a8d71e1adfa5fc`;
  the executable protocol (all notebook code, saved in `protocol_source.txt`) SHA-256
  `8416b0f7fdc39a5f2255782f30c6086eecb19e61e70478a6004da83915123368`.

Each design version below records the same cases, prompts, sources, checker and scorer. The changes were to the
output-token limit, the framework adapter and the saving of error messages. Each was recorded, in
`collection_amendments.json` and the `amendment` field of `design.json`, as chosen without inspecting tax accuracy.

## Protocol 1: 1,500 output tokens per call (`budget_pilot/`)

- Design frozen 13:56:30; requests collected 13:56 to 14:13.
- 240 requests, 120 per model. Qwen3.8 Flash stopped at the output limit in 74 of 120 requests and returned empty
  text in 92. Gemma 4 31B never reached the limit; its 24 empty texts are framework tool calls, which carry no text.
- Recorded spend $0.1624296. The collection is complete and kept with its own scores (`budget_pilot/summary.csv`,
  `budget_pilot/effects.csv`), but none of its results is used in the notebook's tables.
- Reason for the change: "Output ceiling frequently exhausted before final text."

## Protocol 2: 6,000 output tokens, framework adapter with automatic tool choice (`transport_pilot/`)

- Design frozen 14:06:20, with the recorded change "Increase output-token cap after observing transport truncation
  in the 1500-token run, before inspecting tax accuracy; preserve the lower-budget run separately."
- Requests collected 14:06 to 14:15. The collection was stopped early after finding that the notebook's adapter for
  the framework had forced automatic tool choice and discarded the framework's stop sequences, so the framework was
  not running with its own defaults.
- 78 returned responses (45 Gemma, 33 Qwen); Qwen reached the output limit in 2. Recorded spend $0.074729694.
  Requests that were in flight when the run stopped may have been charged without a returned cost.
- Not scored and not used in the notebook's tables.

## Protocol 3: framework defaults restored (`protocol_v3/`)

- Design frozen 14:17:39, with the recorded change "Honor framework required tool choice and stop sequences after
  transport inspection, before inspecting tax accuracy. Preserve 1500-token and partial auto-tool pilots separately."
- All 192 runs were collected. The 24 Qwen framework runs failed on their first request with HTTP 400, but this
  version did not save the bodies of HTTP errors, so an offline replay could not reproduce them. The run records
  are kept in `protocol_v3/runs.json`; `protocol_v3/spend.json` records 216 new calls and $0.17299883.

## Protocol 4: error messages saved (final, files in this folder)

- Design frozen 14:28:44, with the recorded change "Persist HTTP error envelopes for exact offline replay. Reuse
  unchanged protocol-3 successful requests; recollect only previously uncached HTTP errors. No tax accuracy
  inspected to choose this correction. Generation options, cases, prompts, sources and scorer unchanged."
- The 192 successful replies are the protocol 3 replies, reused by identical request hash. Only the 24 Qwen
  framework requests were sent again (14:28:46 to 14:28:58). All 24 failed again with HTTP 400 and the same message,
  "The tool_choice parameter does not support being set to required or object in thinking mode". In 3 of the 24
  saved error bodies, OpenRouter's record of earlier attempts shows an upstream 429 (rate limit) before the 400.
- Final cache: 216 entries, 192 model replies and 24 HTTP error bodies. The error bodies report no cost.
  Recorded spend $0.17299883.
- Output-limit hits in the final cache: 5 of 216 requests, all Qwen second calls in the review setups (test-11
  short checker feedback; test-02, test-08 and test-12 detailed self-review; test-09 detailed checker feedback).
  Each stopped after 6,000 reasoning tokens with empty text.

## Redaction

Only one field was removed from the saved HTTP error bodies: `http_error_body.user_id`, an account identifier.
Each such entry records this in `metadata_redactions`. Request hashes and the provider's diagnostic messages are
kept.

## Settings and software

- Every request: temperature 0, at most 6,000 output tokens, one sample, OpenRouter. No provider was pinned.
  Framework requests also carry the framework's own options: `stop: ["Observation:", "Calling tools:"]` and
  `tool_choice: "required"`.
- OpenRouter returned the undated ids `google/gemma-4-31b-it` and `qwen/qwen3.8-flash`; no dated version was
  recorded. Gemma was served by CoreWeave (72 requests), DeepInfra (32), ModelRun (12) and Novita (4); Qwen by
  Alibaba (72 answered requests).
- Python 3.12.5, smolagents 1.24.0, requests 2.34.2 (`versions.json`).
- Runs were collected eight at a time in a fixed random order (seed 1201), so recorded latencies include waiting
  under load.

## Spend across all collections

| Collection | Returned responses | Recorded OpenRouter USD |
|---|---:|---:|
| Final tax comparison (protocols 3 and 4) | 216 | 0.17299883 |
| Protocol 1, 1,500 tokens | 240 | 0.1624296 |
| Protocol 2, automatic tool choice (stopped early) | 78 | 0.074729694 |
| Replaced invoice task | 242 | 0.07739788 |
| Total | | 0.487556004 |

From `all_collection_spend.csv`. These are costs reported in API responses, not an account invoice: HTTP error
bodies and interrupted requests report no cost.

## 28 October 2026: figures redrawn

The plotting code in four cells was changed and the notebook was re-run as an offline replay of the committed
caches, with `NB_LIVE` and `OPENROUTER_API_KEY` unset: zero model calls, $0. No code that loads, parses, scores or
caches a response was changed; every data file and every computed number is unchanged, and the protocol hash check
passed. What changed in each figure:

- `exact_success.png`: one panel per model, stacked vertically. Each bar now splits the 12 companies into fully
  correct, wrong and unreadable, with the counts written beside it, so Gemma's 0 of 12 bars are visible as 12 wrong.
  Qwen's framework rows are marked "not run" (HTTP 400) instead of being drawn as zero. Setup names replace the code
  names. Before, the x-axis was the share fully correct, Gemma's panel was blank and the unreadable replies were not
  shown.
- `cost_and_calls.png`: split by model, leaving out Qwen's 24 framework runs that ended in HTTP 400 (marked "not
  run"). Before, each bar averaged both models, so those failed runs pulled the framework's averages down to 1.5
  calls and $0.0004; the cost axis labels overlapped and the titles did not describe the data. New title: the
  review setups cost 2.0 to 2.7 times the direct call.
- `transport_failures.png`: one panel per model, rows named by setup, each bar labelled with its category and count,
  and rows with no failures labelled. Before, the title read "24 framework runs fail at HTTP transport", which did
  not say that all 24 were Qwen's.
- `error_example.png`: every amount in dollars and the fields named as in the README (business profit, owners'
  shares, review flags). Before, the right table was in cents beside a ledger in dollars.
- `paired_effects.png`, `component_checks.png`, `budget_check.png`: labels only. Setup and component code names and
  OpenRouter model ids were replaced by the README's names; nothing else was changed.
- The printed lines after the paired comparisons no longer end "on this pilot"; each now names the comparison in
  words and says whether its interval lies entirely above zero.

`all_collection_spend.png` was not changed. The framework error logs printed by the run cell come out in a
different order on each replay, because runs execute eight at a time; their content is the same.

## Replay notes

- Replay (`python -m jupyter nbconvert --to notebook --execute --inplace 12_tax_research_harnesses.ipynb`) reads
  every reply from `cache_requests.jsonl`, needs no credentials and stops on a cache miss. It checks the design and
  protocol hashes above.
- New collection needs `NB_LIVE=1` and `OPENROUTER_API_KEY`. A changed design belongs in a new data folder with a
  new design version.
- `NB_SMOKE=1` cuts the case count to two, which changes the design hash, so smoke data must be collected in a
  separate copy of the folder.
