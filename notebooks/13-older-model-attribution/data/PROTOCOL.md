# Protocol history: notebook 13

This file records how the run was planned, collected and reviewed, in date order. The reader-facing account is in the notebook's [README](../README.md). Every fact below comes from a file in this folder or from the notebook's committed markdown and outputs before the 2026-10-28 text rewrite.

## Scope, before collection

- The study is the small version of [proposal #14](https://github.com/k-sandhu/experiment-notebooks/issues/14). The proposal asked for eight generators and 120 prompts; this run uses four generators and 25 prompts. It keeps two sizes within each of two families, all five tasks, both attribution conditions (zero-shot and few-shot), both proposed trained baselines and all proposed text ablations.
- Closed-weight predecessors were left out because the sources are open-weight models. Claude and GPT therefore have no own-family source in the corpus.
- Proposal #14 asks whether a vendor's newer model recognises its own older models, so the overlap between source and attributor vendors (Meta: Llama 3.1 and Muse Wonder; Alibaba: Qwen 2.5 and Qwen 3.6 27B) is intentional (`date_provenance.json`, field `same_vendor_exception`).
- The 25 prompts and fictional source passages were drafted by GPT-based Codex (OpenAI) on 2026-10-19 (`date_provenance.json`, field `prompt_author`). This differs from the repository's default advice to have a different vendor from the models under test write evaluation data. The note in `date_provenance.json` gives the reasons: prompts are identical across sources, and gold labels are recorded endpoint identities rather than model-written judgements.

## Protocol version 1, frozen 2026-10-19 before collection

`protocol.json` was saved before any generated text was read and is checked on every replay. Its hash, as recorded in `validation.json` and `review_audit.json` (field `protocol_sha256`), is `37189c3f44167d8b21989d93e486d1cf35f405db0bfba202749493f59b42a7a9`.

- Seed 20261019.
- Generators and pinned providers: Llama 3.1 8B (`deepinfra/fp8`), Llama 3.1 70B (`deepinfra/turbo`), Qwen 2.5 7B (`phala`), Qwen 2.5 72B (`deepinfra/fp8`). Generation system prompt "Follow the writing request. Return only the requested content."; temperature 0.7, top_p 1.0, seed 20261019, max_tokens 1100.
- Attributors: Claude Opus 5.5 (`claude-opus-5-5`, `claude -p`), GPT-6.1 (`gpt-6.1-sol`, `codex exec`), Muse Wonder (`muse-wonder-full-1.0`, `muse exec`), Qwen 3.6 27B (`qwen/qwen3.6-27b`, OpenRouter, `chutes/fp8`), Decisions (`openai/gpt-6-luna-decisions`, OpenRouter).
- Split: three training prompts (about 80, 180 and 450 words) and two test prompts (about 180 and 450 words) per task, five tasks.
- Few-shot examples: three per generator, from prompts explain-1, email-2 and opinion-3, capped at 100 words. Batches of five texts.
- Primary measurement: exact-model accuracy on all held-out prompts, clustered by `prompt_id`.
- Baselines: logistic regression with fixed C=1, no test tuning, trained on 12 and 60 examples. Embedding model `qwen/qwen3-embedding-8b`.
- Ablations: GPT-6.1 zero-shot was fixed before collection as the ablation attributor. Word caps 50, 100, 200 and 400. Paraphraser `mistralai/mistral-small-3.2-24b-instruct`.
- Order check: GPT zero-shot on all 40 items with reversed candidate order. Single-item check: GPT zero-shot on the four explain-4 outputs individually.
- Resampling: 5,000 prompt resamples; 499 label permutations. The original protocol specified resampling whole test prompts to give 95% intervals (changed in interpretation by the review below).
- Protocol note: "10 test prompt clusters; descriptive secondary comparisons; no claim about unseen source models".
- Notebook size knobs: at most 350 new calls, an estimated OpenRouter limit of USD 10.0 (applied to reservations, not to billed charges), 3 workers.

## Collection, 2026-10-19 (times UTC)

- Collection environment (`collection_environment.json`): Claude Code 2.1.296, codex-cli 0.160.1, Muse Code 1.4.11 (1.4.11-R6667.1), Windows 11 (10.0.26300), base commit `3c12928fb5100608ff9b767d4723682606bddbac`. CLI version checks do not call a model.
- 19:20:43: OpenRouter catalogue snapshot saved (`model_catalog.json`).
- 19:20:44 to 19:27:48: 100 source texts generated (`item_creation_dates.csv`, `corpus.csv`). No response hit the token cap and none was excluded.
- Qwen 2.5 72B returned HTTP 429 on five attempts across two requests: one request failed at 19:20:46, 19:20:48 and 19:21:28 and succeeded at 19:22:35; the other failed at 19:21:28 and 19:21:39 and succeeded at 19:22:41. The cache file keeps each intermediate state as a separate line with the same key (305 lines, 300 unique keys). Transient errors allowed at most four attempts per request.
- 19:23:07: while Qwen 2.5 72B returned 429s, catalogue entries for alternative models were looked up (`availability_checks.json`). These lookups are not inference calls. Qwen recovered and no generator or attributor was changed.
- Attribution and checks: Claude 19:28:43 to 19:29:18; GPT-6.1 19:29:57 to 19:49:06 (main calls, ablations, reversed order, repeat and single-item checks); Muse Wonder 19:33:10 to 19:37:16; Qwen 3.6 27B 19:37:00 to 19:38:27; Decisions 19:38:19 to 19:38:27; embeddings 19:38:37 to 19:39:14; Mistral paraphrases 19:39:19 to 19:41:12.
- CLI attributors ran in empty temporary directories with tools disabled and no corpus files. Request text included no gold labels, source filenames or generator metadata for test items.
- Development requests: eight GPT-6.1 requests used an early identity-removal rule that changed line breaks even when no identity cue was present. The corrected rule leaves those inputs unchanged and reuses the raw-response cache. The eight development requests remain in the cache and are marked `used_in_final_analysis = False` in `request_usage.csv`.

## Checks added after seeing results, 2026-10-19

- Same-order repeat (`posthoc_controls.json`): the planned reversed-order check changed 16 of 40 GPT zero-shot predictions, so one identical-prompt repeat was added to measure run-to-run variation. The cache key adds a replicate number that is not transmitted to the model. The repeat changed 13 of 40 predictions and is never substituted for a primary answer.
- One-brace formatting diagnostic: after strict parse failures, exactly one closing brace is appended, only if that produces a complete, valid set of unchanged guesses. The rule was applied to every attributor; only Qwen 3.6 27B needed it (10 responses, 50 items). Strict scores remain the primary measurement.

## Review, 2026-10-19

- Cache-only review (`review_audit.json`): verified 100 raw source responses, 400 main attribution items and 15 metric rows, and recalculated both calibration conditions; normalised train-test overlap 0; scoring fixtures cover perfect guesses, wholly invalid guesses, a mixed invalid and wrong-size case, and repeated item IDs across inference draws.
- The review found that the ten test prompts and eight shared calls per condition form one connected dependence component (`dependence_audit.json`): the same prompt links four calls, and each call links five prompts. Prompt-resampling ranges therefore cannot give 95% confidence coverage.
- Change of interpretation: the headline chart shows point scores without whiskers; the resampling ranges are kept only as descriptive reweightings (columns `resample_low` and `resample_high`); a dependence audit and leave-one-prompt and leave-one-call deletion ranges were added (`deletion_sensitivity.csv`). The protocol, prompts, source texts, model responses and primary point scores did not change.
- A request-format confound was recorded: Decisions receives the shared attribution state, including the generative JSON-output instruction, beside its native choice questions. A replication should remove the output-format instruction from the Decisions state.

## Evidence handling

- Raw responses, usage, provider and collection time are stored before parsing. Every attempt is retained, including HTTP errors and malformed responses. Account identifiers in HTTP error envelopes were redacted before committing; request payloads and model content were kept.
- `manifest.json` lists SHA-256 hashes of every evidence file under the scheme `sha256-text-lf-v1`, which normalises CRLF to LF so Git line-ending conversion does not change the hashes. Escaped newlines and spaces inside cached JSON strings are part of the content and are preserved.
- Replay is strict and offline: it fails on any cache miss. The committed outputs were executed top to bottom and the final replay made zero new calls (`validation.json`, fields `successful_replay_new_calls` and `offline_cache_miss_guard_verified`). Analysis environment: Python 3.13.5, numpy 2.2.6, pandas 2.3.1, scikit-learn 1.9.0, matplotlib 3.11.2 (`environment.json`).

## Spend

From `spend.json`: 300 unique cached requests, 305 transport attempts, 0 new calls on replay. OpenRouter reported USD 0.042325715 in charges. The five failed attempts have no reported cost. Estimated OpenRouter reservations total USD 0.99634869; reservations are a collection heuristic, not a billing bound. Claude Opus 5.5 reported a list-price equivalent of USD 0.7797214. GPT-6.1 (Codex subscription) used 1,247,244 input tokens, of which 302,336 were cached, and 25,853 output tokens. Muse Wonder ran on a subscription that exposes neither tokens nor dollars.

## Links

- Further-reading links were checked on 2026-10-19 and again on 2026-10-28.

## 2026-10-28: text rewrite

- The README and the notebook's markdown cells were rewritten for readers new to the topic, and run history was moved into this file. No model was called, the notebook was not re-run, and no code cell, output, figure or other data file changed.
