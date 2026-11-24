# Notebook 37 protocol history

This file records how the study was run: what was fixed before the test, every change made afterwards, the
interruptions, and the spend. The reader-facing explanation is in `../README.md` and the notebook. All times are UTC.
Hashes use SHA-256 after converting CRLF line endings to LF.

## Design fixed before the test

The claim issue is #98. The source is notebook 33 at commit `cf854303` (branch `add-33-judge-exam`). The plan is
`analysis_plan.json` (version `structured-judging-v1.0`); its main points:

- Items: notebook 33's 240 test pairs in four families of 60, copied unchanged with 13 source files into `from_33/`
  (hashes in `source_manifest.json` and `from_33/SOURCE.md`). Notebook 33's 24 development pairs are used only for
  development. No regeneration or difficulty tuning.
- Judges: GPT-6.1 Sol and GPT-6 Luna through `codex exec` at reasoning effort medium; Granite 4.2 8B
  (`ibm-granite/granite-4.2-8b-20260831`, provider `coreweave/bf16`, fallback disabled) through OpenRouter with
  notebook 33's settings: reasoning none, temperature 0, JSON object mode, 1,600 output tokens with escalation to 3,200
  and 6,400 on truncation. Luna replaces Claude Haiku 5.5 under the supplied brief, because 73 of Haiku's 120
  instruction judgments were provider-filtered in notebook 33. No Haiku or Muse calls.
- Checklist author and auditor: Claude Opus 5.5 through `claude -p`, effort medium, no tools.
- Methods: free form, exam prompt, general rubric, item checklist, separate scoring on all 240 pairs; own requirements
  on the 60 instruction pairs. Polished variants of free form, exam prompt and item checklist on 120 pairs.
- Main estimand: accuracy with unreadable and undecided outcomes counted as failures, paired within item, judge and
  displayed order. Exam-prompt baselines on original items reuse notebook 33's final reply for the assigned order (720
  replies); no new baseline calls.
- Order: half better-first within family and trap tag, seed 3710302026 (`order_assignment.json`).
- Polish: 120 items, 30 per family, deterministic worse-only presentation changes; a family is kept only if every
  checker signature is unchanged.
- Checklists: one task-only Opus request per item, 3 to 8 yes-oriented questions, identical task prompts share one
  cache entry (232 unique requests for 240 items), all frozen before judging, no answer-based retries.
- Readers: notebook 33's strict and lenient readers unmodified (including truncated-prefix recovery), plus a
  complete-JSON reader. The rubric keeps the three-field verdict with ten integer scores in a fixed reason prefix
  (`A=[...];B=[...];`), schema failure when absent. Separate scoring takes a boolean array of exactly the checklist
  length; either bad component makes the pair unreadable; equal totals are undecided and count as failures in both
  accuracy and readable-only accuracy.
- Quality: instruction checklists by a deterministic keyword-and-value check of the seven rules; other families by one
  Opus call per item with fixed categories present, partial, absent, unclear against the checker's decisive evidence.
- Intervals: Wilson 95% for accuracy; 5,000-resample paired item bootstrap percentile 95% intervals for differences
  with a fixed seed; exact two-sided sign tests, unadjusted and exploratory. The 12 trap items (all code) are too few
  to rank methods.
- Retries: at most three attempts for HTTP 429, 5xx, capacity, rate-limit or token truncation. Provider safety blocks
  are cached without retry. Usage, quota or credit messages stop the collector without caching a final reply.
- Costs: OpenRouter actual returned usage, capped at 5 dollars with conservative reservations for pending or unpriced
  calls; Claude CLI returned list cost; Codex estimates from returned tokens at Sol 2/10 dollars and Luna 0.10/0.50
  dollars per million input/output tokens, cached input at 5%. Checklist cost is counted once in run totals and charged
  once per item in per-method resources.

## 2026-10-30

- Setup. Source artifacts copied and verified against notebook 33's freeze record; 720 baseline replies imported with
  their original request keys and an origin marker. One capability call each for Sol, Luna, Granite and Opus returned
  readable correct JSON. A fresh OpenRouter catalog request confirmed Granite's pin (`granite_catalog.json`,
  `catalog_snapshot.json`).
- 17:11:29. First logged event of the collection period.
- 17:26:20. Preflight validation (`preflight_validation.json`): the copied checkers and verdict readers are
  AST-identical to notebook 33; reader boundary fixtures pass; no network calls.
- 17:30:25. Design amendment 1 (`design_amendments.json`): the polished selection was rebalanced jointly by
  source-better A/B and displayed-better first/second (fixed 7/8 cells, 15/15 margins per family, selection seed
  3710302063). The initial selection had balanced displayed order only. No model outcome was used; zero model calls;
  checker signatures unchanged. Old and new hashes are recorded.
- 17:34:53. The quota guard stopped the collector on a false positive: the phrase "credit balance" appeared inside a
  valid Opus checklist for a grant calculation (`quota_guard_diagnostic.json`). No provider limit had been reported.
  At that point 188 of 240 test checklists existed from 180 unique calls (`interruption_status.json`). The matched
  reply and one reply completed after the stop are kept as non-final attempts and were re-requested normally.
- 17:49:33 and 17:53:48. Design amendment 2: quota and transient-error matching restricted to error channels (stderr,
  explicit error events, failed CLI channels), never successful model content; temporary storage and source paths moved
  to `D:`. Validated by 12, then 13, guard and cache tests (`transport_amendment_validation.json`), zero model calls.
  Prompts, readers, items and scores unchanged.
- 17:56:39. Design amendment 3: the expanded smoke run raised a KeyError before any judge call because smoke jobs
  looked up the test order index; smoke jobs now use development orders. Three quality audits had already been cached
  normally.
- 18:00:47. Design amendment 4: because the `D:` temporary folders sit inside the repository checkout, Codex calls set
  `project_doc_max_bytes=0` so that no ancestor AGENTS file enters the prompt. Offline inspection showed the default
  prompt at 56,381 bytes with repository instructions and 22,810 bytes without. No test judgments existed. Baseline
  replies collected outside the repository are reused unchanged. Earlier smoke calls keep their original settings as
  history and never supply test verdicts.
- Smoke and development. Smoke used the first development pair in each family under every original condition (63
  pair-condition rows), 36 polished rows and 3 quality audits; all 63 original smoke rows were readable under both
  readers, some Granite smoke calls after token escalation. Development compared free form with the item checklist on
  the 24 development pairs for each judge: Sol 23 and 22 correct, Luna 14 and 16, Granite 13 and 17. No prompt was
  changed after smoke or development.
- 18:13:27. Test freeze (`freeze_record.json`): 16 hashes covering order, polish selection and copies, polish
  validation, checklists, prompt templates, analysis plan, models, date provenance, source manifest, implementation
  and pipeline code, design amendments, environment, preflight and transport validation. Test judging could start only
  after this record existed.
- 18:13 to 19:07. Test collection.
- 17:19 to 19:04. Granite returned 11 HTTP 429 responses across smoke and test requests; each was an intermediate
  retry followed by a final non-429 outcome (`cli429_other_judges_audit.json`).
- 19:07:47. Manual pause. The agent and its runner processes were stopped at the owner's request with
  `taskkill /T /F`. This was not a quota stop or model failure. Five started requests had no return: two Codex calls
  and three OpenRouter calls. None is scored. OpenRouter reservations for them total 0.00339484 dollars
  (`interrupted_attempts.json`); no usage is invented for the two CLI calls. An offline reconstruction on resume found
  1,517 of 4,860 pair-condition verdicts available, including the 720 reused baselines.

Period totals (`collection_periods.json`): 1,716 attempts started and 1,711 returned (Opus 446, Luna 385, Sol 399,
Granite 486 started).

## 2026-10-31 to 2026-11-23

No collection. Calendar gap of 25 days; exact elapsed time from the pause to the resumed collection was 2,113,225
seconds.

## 2026-11-24

- Resume checks (`resume_validation_20261124.json`, `resume_inventory_20261124.json`). All 353 JSON and JSONL files
  under `data/` parsed; no manual repairs. All 16 frozen hashes and all 13 source copies were reverified against the
  moved notebook 33 checkout at `cf854303`.
- 06:06:18. Resume transport amendment (`resume_transport_amendment_20261124.json`). The `codex.exe` found on PATH was
  version 0.142.4; the resolver now selects the native 0.160.1 binary inside the installed npm package. No prompt,
  request key, model setting, item, checklist, reader or score changed. Original code is preserved in
  `frozen_20261030/`; old and new code hashes are recorded. This was the first change after the test freeze.
- 06:06:30. One transport check per model (`resume_transport_checks_20261124.json`). Sol, Luna and Granite returned
  correct JSON with the frozen pins and settings (both Codex calls also logged a fail-closed "code-mode host disabled"
  diagnostic; no tool was used). The Opus check returned "Failed to authenticate: OAuth session expired" with zero
  tokens and zero cost. All 240 checklists and 180 audits were already cached, so no Opus request was needed; no model
  was substituted.
- 06:06 onward. Collection resumed for the missing requests, including the five interrupted ones.
- 06:32:55 to 09:09:58. Sustained, account-wide HTTP 429 "Too Many Requests" errors for Sol through `codex exec`.
  Several notebooks were calling Sol at the same time, and the owner reproduced the same error with a one-call Sol
  check outside this notebook. Under the policy then in force, each request got three attempts, and an exhausted 429
  stream was cached as an unreadable transport outcome. In all 2,928 attempts failed this way, producing 795
  provisional Sol verdict rows with no model reply. Luna had 2 rate-limited attempts at 07:38, both retried
  successfully.
- 08:22:50. Supplementary analysis specified (`post_outage_analysis_record.json`, code `readable_analysis_v1.py`): every
  paired comparison repeated on pairs readable on both sides, for every judge, reader and comparison. Not
  preregistered; primary analyses unchanged; output `readable_paired.csv`.
- 08:44:29, refined 08:45:19. Example selection amendment (`example_selection_amendment_20261124.json`, code
  `worked_examples_readable_v1.py`): diagnostic example patterns require a readable wrong answer instead of "not
  correct", so unreadable and undecided outcomes are not shown as wrong; the missed-check pattern requires audit
  category absent. Display only.
- 09:23:46. Figure display amendment (`figure_display_amendment_20261124.json`): count labels moved above interval bars;
  the own-requirements axis label says instructions only. Display only; primary result hashes before the change are
  recorded.
- 09:36:04. Transport amendment for exhausted CLI 429 errors (`cli429_transport_amendment.json`), authorized by the
  owner and matching notebook 36: an exhausted CLI HTTP 429 error with no model reply is a non-final transport attempt,
  never a scored outcome, and a later returned reply for the same request key becomes final. The rule was fixed before
  any new call and without inspecting any Sol readable verdict. Unchanged: policy refusals, empty replies without an
  exhausted 429, broken JSON, schema failures, and timeouts with a partial reply. Any new exhausted 429 stops collection
  globally. Sol concurrency drops to 1. Code changes are confined to four functions in `implementation_v1.py` and one
  in `pipeline_v1.py` (`cli429_scope_validation.json`); 16 guard tests pass (`cli429_guard_tests.json`).
- 09:36:15. Retirement (`cli429_retirement_manifest.json`, `cli429_affected_outcomes.json`). 2,928 attempts and 795
  Sol verdict rows were retired as non-final, with a full pre-migration copy in `before_cli429_retirement/` and exact
  row hashes. Final cache entries went from 8,584 to 5,656. Retired rows by condition: free form original 141, general
  rubric 140, item checklist original 145, separate scoring 149, own requirements 34, free form polished 64, exam
  prompt polished 62, item checklist polished 60. The 4,065 unaffected verdicts kept their scores.
- 09:39:05 to 09:39:40. One fresh Sol smoke call through `codex exec` 0.160.1 passed (`cli429_smoke_check.json`).
- 09:39:43. Recollection started at Sol concurrency 1: 920 pending logical calls for 795 verdicts.
- 09:40:20. Figure title amendment (`figure_display_recovery_amendment.json`): the accuracy figure title no longer
  refers to the outage. Display only.
- 09:46:47. Resource accounting record (`transport_resource_analysis_record.json`, `transport_resources_v1.py`):
  final-reply resources are reported apart from all attempts including the retired ones
  (`resources_with_transport_overhead.csv`, `transport_attempt_resources.csv`). No score change.
- 09:55:24. Audit of other judges' 429s (`cli429_other_judges_audit.json`): Granite's 11 HTTP 429 responses on 30
  October were intermediate retries, none exhausted or scored; the bounded OpenRouter retry policy is unchanged.
- 14:15:24. Recollection finished: 921 attempts returned 920 non-empty model replies; one attempt returned "Selected
  model is at capacity. Please try a different model." and its bounded retry succeeded. No new exhausted 429 occurred.
  `collection_audit.json` at 14:15:22 records 921 new calls and cache entries 5,657 to 6,578.
- 14:17:03. Zero-call replay verified with 4,860 verdicts (`cli429_recovery_status.json`, `final_qa.json`).
- 14:20:38. Preservation audit (`cli429_preservation_audit.json`): all 2,928 retired request/response rows preserved,
  unretired cache rows unchanged, no exhausted CLI 429 in the final cache.
- 14:21:34. Final replay audit (`replay_audit.json`): zero new calls, 6,578 cache entries unchanged, source and freeze
  verified, seven figures. `final_metadata_sync_verification.json` confirms the study tables and figures are
  byte-identical across the last two replays.

Period totals: 7,077 attempts started and returned (Opus 1, Luna 1,322, Sol 4,246, Granite 1,508). Collector wall
time for the main test across both dates, excluding the pause: 31,292 seconds (8.69 hours), of which the recollection
took 16,541 seconds. Freeze to pause on 30 October was 3,260 seconds; the resumed collector before the recollection ran
11,491 seconds.

The same model names span both dates. The CLIs do not guarantee that a name always maps to the same weights, so a
provider-side change over the gap cannot be ruled out. The design and job order were fixed before either period, and
comparisons between periods are descriptive.

## Write-up, 2026-11-24

The README, notebook prose and this file were written from the frozen outputs with no model calls. Some numbers in
the prose were counted directly from `judgments.csv` as descriptive reporting, not as planned analyses: how often each
judge named the first or second displayed answer per family; how many pairs the four pairwise methods agreed on per
judge; separate-scoring tie patterns (identical yes/no vectors, all-yes and all-no vectors, all-yes ratings of the
better and worse answer alone); gains and losses of the checklist and rubric against free form; mentions of bold
markup in polished-message reasons; finish reasons of Granite's unreadable separate-scoring replies; and the family of
pairs where Sol's free-form and checklist verdicts differ. No interval or test was computed for these. Further-reading
links were opened on 24 November 2026.

## Spend and calls

From `spend.json` and `call_counts.csv`, covering capability, smoke, development, test, audit and transport-check
calls, and the retired attempts:

| Item | Value |
|---|---|
| OpenRouter, actual reported | 0.40290051 dollars |
| OpenRouter, with conservative reservations | 0.45891263 dollars |
| CLI calls returned | 6,797 (Sol 4,643, Luna 1,707, Opus 447) |
| CLI estimated list cost | 44.66 dollars (Sol 27.09, Opus 16.80, Luna 0.77) |
| CLI calls without priced usage | 2,935 (2,928 of them retired 429 attempts) |
| OpenRouter attempts returned | 1,991 |
| Attempts returned, all | 8,788 |
| Attempts started, all | 8,793 (5 interrupted at the pause) |
| Reused notebook 33 replies | 720, no new cost |
| Summed call latency | 70,674 seconds |

CLI estimates are list prices, not subscription charges. Final cache entries: 6,578.

## Settings recorded

- Codex: `codex-cli 0.160.1` native binary from 24 November (0.142.4 was on PATH); prompt on stdin; empty isolated
  working folder; no tools; `project_doc_max_bytes=0`; reasoning effort medium. Concurrency 2 originally, 1 for Sol
  during recollection.
- Claude: `claude -p` headless, effort medium, no tools, empty working folder; concurrency 2.
- OpenRouter: concurrency 3 per model; CoreWeave BF16 endpoint pinned, fallback off; per-key locks prevent duplicate
  in-flight requests.
- Environment (`environment.json`): Python 3.13.5 on Windows 11; numpy 2.2.6, pandas 2.3.1, matplotlib 3.11.2,
  requests 2.33.0, nbformat 5.11.1, nbconvert 7.17.2, ipykernel 7.4.0.
- Model calls in this notebook were not traced to the local Langfuse instance.
