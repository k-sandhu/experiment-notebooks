# Notebook 26 protocol and run history

This file records how the evidence in this folder was collected, in date order. The reader-facing account is in
[../README.md](../README.md). Every fact below comes from a file in this folder or from the notebook's committed
code and outputs; where a time or setting was not recorded, it says so.

## Fixed settings

- Protocol name `audit26-v1`, stored in every cached request (`request.protocol` in `cache_requests.jsonl`).
- Size knobs in the first code cell: `N_FAMILIES=8`, `N_DRAWS=2`, `BATCH_SIZE=8`,
  `MODELS=['GPT-6.1 Sol', 'Qwen3 30B 2507']`, `MAX_NEW_CALLS=16`, `MAX_OPENROUTER_USD=2.0`, `SEED=20261024`.
- Spend guard: before each OpenRouter call, the notebook reserves the request's byte length times the endpoint's
  prompt price plus 2,200 output tokens at the completion price, and stops if reservations would exceed
  `MAX_OPENROUTER_USD`. This is a collection guard, not a billing guarantee.
- Replay switches: `NB26_LIVE=1` allows new hosted calls; `NB26_LOCAL=1` recomputes the Pythia probes;
  `NB26_DOWNLOAD=1` allows downloading the public Pythia files. With none set, a cache miss stops the notebook.
- The setup cell checks every file listed in `manifest.json` against its SHA-256 before running (`hash_scheme`
  `sha256-file-bytes-v1`).

### GPT-6.1 Sol through Codex

- Model argument `gpt-6.1-sol`; `codex-cli 0.160.1` (field `cli_version` in each cached response). The Codex
  events record no dated model version.
- Command-line options, as recorded in each cached request (`request.cli_options`): `exec --skip-git-repo-check
  --ephemeral --ignore-user-config --sandbox read-only --disable shell_tool --disable unified_exec --disable apps
  --disable plugins --disable multi_agent --disable browser_use --disable computer_use --disable image_generation
  --disable code_mode --disable code_mode_host --disable shell_snapshot -c web_search="disabled"
  -c model_reasoning_effort="low" --json`, run in a new empty temporary folder with a 240-second timeout.
- Each Codex run also emitted an error item saying code mode was unavailable because the code-mode host was
  disabled (first `item.completed` event in each cached response). It did not stop the run.

### Qwen3 30B through OpenRouter

- Model `qwen/qwen3-30b-a3b-instruct-2507` (OpenRouter `canonical_slug`, the same string), temperature 0,
  seed 20261024, `max_tokens` 2200, `allow_fallbacks: false`, `require_parameters: true`.
- Endpoints listed in the frozen catalogue (`model_catalog.json`, collected 2026-10-24T15:19:43Z): DekaLLM
  (quantization unknown), SiliconFlow (`siliconflow/fp8`) and Nebius (`nebius/fp8`).
- Published Hugging Face revision `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe` (`provenance.json`,
  `qwen_published_revision`) is a reference only; the provider did not attest which weights it ran.

### Pythia-14M, local

- `EleutherAI/pythia-14m` at revision `cf967c0a9a04383db6f7b1108d86b2962634b4ac`, Apache-2.0, 14,067,712
  parameters, state SHA-256 `d5f23275dd334c50f4f743c3bed62f912adaea043a679f1bc2a693e7eff63933`
  (`local_probes.json`).
- CPU, float32, one thread, eager attention, `torch.use_deterministic_algorithms(True)`, seed 20261024.
  Python 3.13.5, NumPy 2.2.6, PyTorch 2.9.1+cpu, Transformers 4.57.6, Windows 11 (10.0.26300), 22 logical CPUs.

## Run history

### 2026-10-24: data and sources

- 32 records generated in code from 8 families (`cases.json`, every `created_at` 2026-10-24) and shuffled with
  seed 20261024 into 4 batches of 8 (`batches.json`). No model call was used to write them.
- Model dates frozen in `provenance.json`: GPT-6.1 Sol knowledge cutoff 2026-04-30; Qwen3 30B catalogue
  knowledge cutoff 2025-06-30; Pythia-14M repository created 2026-02-24, used as a release date.
- OpenRouter and Hugging Face catalogue entries saved at 2026-10-24T15:19:43Z (`model_catalog.json`).
- Ten source links fetched between 15:19:44Z and 15:19:49Z, all HTTP 200, with page hashes
  (`source_checks.json`).

### 2026-10-24: hosted collection (times UTC, from `collected_at` in `cache_requests.jsonl`)

- 15:19:49 to 15:21:03: 8 Codex requests for GPT-6.1 Sol, 4 batches in round 1 (draw 0) then round 2 (draw 1),
  all with return code 0. Codex reported 100,914 input and 3,035 output tokens in total.
- 15:21:03 to 15:21:11: 8 OpenRouter requests for Qwen3 30B pinned to DekaLLM (`order: ['dekallm']`, no
  fallback). All 8 returned HTTP 429 with the message that the model was "temporarily rate-limited upstream" and
  `retry_after_seconds` 60. No usage was charged. They remain in the cache and are not scored. The committed
  collection loop stops at the first failed request, yet these eight were made consecutively within about seven
  seconds; the code that made them is not in the repository.
- 15:21:49 to 15:22:08: 8 OpenRouter requests pinned to Nebius (`nebius/fp8`), all HTTP 200, provider
  `Nebius`, returned model `qwen/qwen3-30b-a3b-instruct-2507`. OpenRouter reported $0.0013706 in total.
- Because the provider changed, the Qwen request keys differ from the refused ones; the final comparison uses
  Nebius for both rounds.

### 2026-10-24: scoring and ledger corrections

- Scorer `audit26-score-v2` (`scorer_notes.json`). A first development parser rejected a whole batch when one
  rule code fell outside the five allowed. Qwen used `system_override` in batches 1 and 3 of each round, so that
  parser would have made 16 of 32 Qwen answers per round unreadable, leaving 10 correct and 6 wrong; GPT was
  unaffected at 32 of 32. The corrected scorer reads each entry separately and counts the unknown code as wrong,
  giving Qwen 22 of 32. No raw response was changed. The first-parser counts were recomputed on 2026-10-28 from
  `scored_items.json` by applying the rule stated in `scorer_notes.json`.
- Ledger repair (`scorer_notes.json`, `shared_input_repair`): ledger events now hold their own copies of the input
  facts, so a mutation of one event in a copied ledger no longer affects others.

### 2026-10-24: local probes

- Pythia-14M probes on 8 prompts P01 to P08 (`local_probes.json`, every `created_at` 2026-10-24). The run took
  4.91 seconds (`elapsed_s`). The time of day was not recorded.

### Date not recorded: offline validation

- `validation.json` records a replay in which 10 code cells ran with HTTP and subprocess transports blocked,
  0 external attempts, 0 new hosted calls, and an independent local recomputation of the Pythia probes with
  largest logit difference 0.0.

### Commits

- 2026-10-24: notebook, data and figures added (commit `d10a6b37`).
- 2026-10-24: notebook and README introductions rewritten (commit `9aa82650`).
- 2026-10-28: README and notebook markdown rewritten, and this file added. No code cell, output, figure or data
  file changed, and no model was called.

## Related files

- `scorer_notes.json`: scorer version, the correction and the primary metric.
- `manifest.json`: SHA-256 of every evidence file, protocol and scorer names.
- `validation.json`: the offline validation replay.
- `call_summary.json`: one row per hosted request, with success, provider, time, tokens and reported cost.
