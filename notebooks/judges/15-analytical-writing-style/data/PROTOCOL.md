# Notebook 15 run history

This file records the settings, changes and incidents behind notebook 15, in date order, for readers who want to
check the work. The README and the notebook give the results. Times are UTC as written in the data files. Nothing
here involves new model calls: the rewrite of the README and notebook text in October 2026 changed text only.

## Settings fixed at the start (2026-10-19)

- Protocol version `nb15-v1`, seed 20261019, saved in [`protocol.json`](protocol.json).
- 2 cases × 4 document types = 8 tasks; 27 writers; 30 judges; 216 planned drafts; batches of up to 4 drafts per
  judge request; 2,000 bootstrap resamples over the 8 tasks.
- Primary measure: outside-company clarity under the neutral review with the author hidden; slop-audit flag
  counts reported separately (`primary` in `protocol.json`).
- Planned contrasts: slop audit minus neutral review (author hidden); author named minus hidden under each
  instruction; the difference between the two naming effects.
- Judge panel per draft: the writer itself, one top outside judge (GPT-6 Astra, Claude Opus 5.5 or Muse Wonder
  Full) and one rotating outside judge, assigned by load and a hash ([`panel.json`](panel.json)).
- Failures and malformed replies are missing, never zero; no reply is rewritten; no completed draft is regenerated.
- OpenRouter spending cap $10, including probes and retries, enforced by reserving a byte-based input bound plus the
  output cap at the frozen provider price before each paid call.
- Command-line options for `codex exec`, `claude -p` and `muse exec` (tools off, ephemeral sessions, low effort) are
  listed in `protocol.json`. Every call ran in a new empty temporary folder. Claude Code was version 2.1.296, the
  Codex tool 0.160.1 and `muse exec` 1.4.11 ([`model_catalog.json`](model_catalog.json), `versions`).

## Model access (2026-10-19, about 20:06 to 20:08)

- The Codex model list was fetched at 20:06:18 and the OpenRouter catalogue at 20:07:21.
- Candidates: every visible Codex catalogue entry except hidden reserve and approval models; all 14 versions in
  Claude Code's supported-model list; Muse Spark 1.2 and 1.3, Muse Wonder and Wonder Full; four open-weight writers
  and three open-weight judge-only models.
- Each candidate was asked "What is 2 + 3?" once ([`availability.csv`](availability.csv)). 30 of 32 answered. Claude Fable 5
  and Fable 5.1 returned "API Error: ... safeguards flagged this message" and were left out.
- Pinned OpenRouter providers, with fallback off (`selected` in `model_catalog.json`): DeepSeek V4 Pro on Baidu
  (FP8), Qwen3.8 2.4T on Novita, GLM-5.3 on Wafer (FP4), Kimi K3 on Sail Research (FP4), Mistral Large 4 on Mistral,
  Gemma 4 31B on Parasail (FP8), Nemotron 3.5 Super VL on DeepInfra (FP4).
- Source pages opened on 2026-10-19: the Codex models page, Claude Code model configuration, the Muse release post
  and OpenRouter provider routing. Training cutoffs were not published for the command-line models; open-weight
  catalogue creation dates are recorded as release proxies in [`model_dates.csv`](model_dates.csv).

## Cases and drafts (2026-10-19, 20:08 to 20:16)

- The two cases were generated at 20:08:26 ([`cases.json`](cases.json)), after the access probes.
- Drafting began at about 20:08. 23 open-weight requests stopped at the initial 1,800-token output limit, mostly
  inside the model's reasoning, and returned no usable text.
- GPT-5.6 Sol's command-line tool exited with an error on every attempt (4 or 5 each) for C1 academic, C1 email and
  C2 slides. Those three drafts are missing; 213 of 216 drafts are usable.

## Amendment: truncated drafts and judge output limit (2026-10-19 20:16:25)

Recorded in [`protocol_amendment.json`](protocol_amendment.json), after the first draft collection and before any
judge call:

- Retry only requests that ended with `finish_reason=length`, once, with the identical prompt, model, provider and
  sampling defaults and `max_tokens=16000`. Keep the first complete output. Never regenerate a complete draft.
- Set judge `max_tokens=16000` before any judging.
- The 23 initial truncations and their costs stay in the cache. 23 drafts in `drafts.json` carry
  `length_recovery=True`.

## Collection changes before the reading check (2026-10-19)

From [`collection_events.json`](collection_events.json):

- 20:25:19. The shared worker queue was replaced by one queue per backend. Prompts and judge assignments were
  unchanged. Requests dispatched but not yet recorded at the interruption keep their reserved cost; their upper
  bound is $0.169 over 19 requests ([`interruption_bounds.json`](interruption_bounds.json)).
- 20:28:48. Before reader collection: one draft per reading request, to stop facts leaking between drafts in one
  request.
- 20:34:15. Before reader collection: the "was a cause established" question, whose answer is "no" in both cases, is
  left out of the aggregate reading accuracy and reported on its own.

## Correction: open-weight judge reasoning (2026-10-19 20:44:04)

Recorded in [`judge_protocol_correction.json`](judge_protocol_correction.json), with the providers' reasoning
options saved at 20:43:26 in [`judge_reasoning_catalogue.json`](judge_reasoning_catalogue.json):

- Open-weight judges had kept the providers' high or maximum default reasoning while command-line judges used low
  effort. Transport review found frequent cut-offs at 16,000 tokens, especially for Qwen and Nemotron.
- New rule for every open-weight judge request and every instruction: low reasoning for DeepSeek, Qwen, GLM and Kimi;
  none for Mistral; reasoning disabled for Gemma and Nemotron, which offer no low setting.
- The earlier default-reasoning reviews, including successful ones, stay in the cache as diagnostics and count
  toward spend. Command-line reviews and all drafts were unchanged.
- The correction states that no writing-score comparison was used to choose it. With it, the study is an amended
  exploratory pilot, not a preregistered confirmatory test.

## Reviews and checks

- 672 main judge requests (213 drafts, 3 judges, 4 instructions, up to 4 drafts per request); 637 readable. The 35
  unreadable replies: 6 empty from GPT-5.6 Sol (tool exit code 1), 3 empty from Mistral Large 4 (HTTP 429 rate
  limit), 12 complete ratings missing only the closing `]}` (GPT-6 Astra 11, GPT-6.1 Sol 1), and 14 with text around
  the JSON or other JSON errors. Counted in the October 2026 rewrite from [`ratings.json`](ratings.json) and the cache.
- 60 planted-phrase control requests (58 readable): Gemma 4 31B's neutral control reply had an invalid control
  character, and Kimi K3's audit reply failed the schema check. Nemotron 3.5 Super VL's audit reply parsed but repeated
  keys inside each flag object, so only the last flag per object survived; its raw text quotes all eight planted
  phrases under the intended habits.
- 30 repeat-review requests (28 readable; one Mistral Large 4 and one Nemotron reply did not parse).
- 458 reading-check requests (419 readable). All 39 unreadable replies are Claude Opus 5.5's, each with a line of
  arithmetic before the JSON. Re-read in the October 2026 rewrite with a parser that starts at `{"answers"`, all 39
  are correct on all four questions; the notebook keeps the strict result.

## Spend

From [`spend.json`](spend.json):

| Item | USD |
|---|---:|
| OpenRouter cost reported on replies | 3.1877 |
| Upper bound for OpenRouter replies without a reported cost | 1.0933 |
| Upper bound for requests interrupted before their reply was recorded | 0.1690 |
| Charged-or-reserved total | 4.4500 |
| Cap | 10.00 |

Command-line calls ran on subscriptions. Claude Code reported a list-price equivalent of $22.59 for its calls; the
Codex and Muse tools report tokens only ([`request_usage.csv`](request_usage.csv)). The later notebook 17 reserved
this $4.4500 bound before making its own calls.

## Cache and evidence files

- [`cache_requests.jsonl`](cache_requests.jsonl): one row per request with every recorded attempt. 1,550 requests and
  1,606 attempts. Journal snapshots were compacted from 3,064 versions (60.6 MB) to the latest row per request
  (43.0 MB) without dropping any attempt ([`cache_storage.json`](cache_storage.json)).
- [`manifest.json`](manifest.json): SHA-256 hashes of the evidence files; replay stops if any differs.
- [`validation.json`](validation.json): replay checks, including no new calls, distinct outside-company judges and no
  style terms in writer prompts.

## Commits

- 2026-10-19, commit `b5305ace`: notebook, data and README added.
- 2026-10-22, commit `2e40aed8`: worked examples added to the README and notebook, with
  [`reading_guide_examples.json`](reading_guide_examples.json) copied from existing evidence. No new judging or
  generation. Further-reading links checked on 2026-10-22.
- 2026-10-28: README and notebook text rewritten for new readers; counts of unreadable replies, judge agreement and
  control-text strictness added from existing files. No code, output or figure changed.
