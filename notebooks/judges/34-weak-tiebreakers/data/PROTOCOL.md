# Notebook 34 protocol history

This file records how the collection for notebook 34 ran: what was fixed before results were seen, every change to the
collection code, interruptions, unknown charges and settings. Times are UTC. The reader-facing account is in
[`../README.md`](../README.md). Machine records: `run_log.jsonl` (events), `attempt_lifecycle.jsonl` (every invocation
start and return), `usage_ledger.csv` (every attempt with cost), `freeze_record.json` (frozen design with all
amendments) and `freeze_history/` (the files each amendment replaced, with old and new hashes). Freeze hashes normalise
CRLF to LF.

## Fixed before results

The source exam is notebook 33 at commit `cf854303`, copied with its generator, reading rules, exam, judgments and
caches into `from_33/` (`from_33/SOURCE.md`). All nine source freeze hashes matched after CRLF to LF normalisation.
An offline audit recovered notebook 33's routes exactly (206 agreed, 34 disputed under this notebook's definition, 0
agreed and wrong) with no calls.

When the plan was written, notebook 33's results were already known: which original pairs Opus and Sol disputed and how
the weak models judged them alone. Not yet seen: every reasons and revision reply, all 480 new pairs and their strong
verdicts.

The design was frozen at 2026-10-30 17:25:56 (`freeze_record.json`, version `weak-tiebreakers-v1`), with hashes of
`analysis_plan.json`, `prompt_templates.json`, the setup, transport, design, generator, analysis and run code, the
notebook 33 generator and reading rules, and `models.json`. `analysis_plan.json` fixes:

- Seed 3410302026; generator level 10 with notebook 33's algorithm and parameters unchanged. The only generator-side
  difference is the checker's child Python flags (`-I` became `-X utf8 -E -P`); the checker, labels and hidden tests
  are unchanged.
- Stopping rule: start from the original 240 pairs; add sequential batches of 120 (30 per family), each frozen before
  strong judging; stop after the first complete batch with at least 80 cumulative lenient disputes, or after 480 new
  pairs. Missing strong replies form a separate route sent to a person.
- Selection: no item exclusion, per-item repair or difficulty change based on judge outcomes; lenient reader selects
  disputes; original, new and all cohorts always reported separately.
- Item scoring: two orders; any unreadable reply makes the item unreadable; inconsistent readable verdicts are a split
  with expected half credit; unreadable scored as failure (primary) and as expected coin credit; readable-only accuracy
  excludes items with an unreadable reply.
- Revision: each strong judge gets its own and the peer's original same-order verdict and reason, one independent
  revision per order; settled only if both revised judges agree consistently across all four replies.
- Confidence rule: in each order the verdict with the larger stated confidence; ties or different selected verdicts
  across orders get expected coin credit.
- Strict sensitivity: the unchanged strict reader applied to the same lenient-selected disputes; failed strict gates
  count as unreadable, with no new calls.
- Reasons labels: seeded random Judge 1 and Judge 2 assignment per item and display order, shared across weak models.
- Inference: 5,000 item-cluster percentile bootstrap draws; paired differences on identical items; Wilson bounds for
  observed binary error rates; no multiplicity claims; groups under 10 items flagged sparse; no causal claims about
  persuasive features.
- Limits: OpenRouter 5 dollars; concurrency 2 Claude, 2 Codex, 1 Muse, 3 per OpenRouter model.

The 24 development items from notebook 33 (4 disputed) were reused to exercise both new prompts, readers, scoring,
tables and figures before the first new batch, instead of a new difficulty draw. Development produced 48 context
judgments; all 9 unreadable development replies were Haiku's (8 provider blocks, 4 alone and 4 with reasons, and 1
reasons reply saying it would not reconstruct content cut off by a safety classifier, which the unchanged reader
classes as `no_parseable_json`). No parameter changed as a result (`development_smoke_validation.json`).

## 30 October 2026

- 17:10:55. Capability probes: each of the 9 judges and 2 writers called once; retries cached separately.
- 17:25:56. Design frozen (above).
- 17:31:41. Controlled collector restart, before any new strong test judgment, to replace inflated generic price floors
  in OpenRouter reservations with the verified pinned-endpoint prices (Gemma 3 4B on Parasail 0.04/0.05, Gemma 3 27B on
  DeepInfra 0.08/0.16 dollars per million input/output tokens). Historical over-reservations were kept. 4 requests in
  flight were interrupted; their charges are unknown, reserved at 0.0204516 dollars (`reservation_amendment.json`).
- 17:41:06. When a restart was attempted, the collector process (PID 23216) was already gone, with no exit diagnostic;
  three OpenRouter requests had passed the intended 180 s deadline without returning. A hard 180 s subprocess deadline
  was added before any new strong test judgment. Payloads, settings, prompts, items and readers unchanged. Interrupted
  attempts now 7, reserved 0.02394752 dollars (`deadline_amendment.json`). The cause of the exit is not established.
- 18:24:20. Interval correction, before any new strong test judgment: diagnostic intervals for reasons-feature rates and
  readable-order confidence now resample item clusters and divide summed successes by summed eligible orders, matching
  the reported order-weighted rate; 95% intervals added for readable-only scores. No point estimate, scoring, reading,
  selection, item, prompt, setting or generator change. Checked on 144 development rows with all point estimates
  unchanged and 0 calls (`interval_amendment.json`, `interval_amendment_validation.json`). The running collector kept its
  earlier intermediate export functions; the final offline notebook uses the corrected ones.
- 18:24:31. Batch 1 (`nb34b1`, 120 items) frozen, sha256 `31c4d6a6...`. The first new strong test call followed
  immediately. Opus and Sol judged batch 1 on 30 October (480 calls): 48 cumulative disputes at 360 items.
- 19:07:47. The owner paused the agent and collector manually (`taskkill /T /F`). This was an intentional pause, not a
  quota stop or a failure. The owner reported four OpenRouter requests in flight; the lifecycle log identifies three
  (Gemma 3 27B writer requests for `nb34b2-worked-004`, `-005` and `-007`). Each of the four is reserved at 0.01 dollars
  (0.04 in all); none is an outcome (`resume_record.json`).

Collection in this period: 1,428 returned attempts between 17:10:55 and 19:07:41.

## 24 November 2026

- 06:05:51. Resumed after 25 calendar days. The checkout had moved to `D:/projects/experiment_notebooks/worktrees/`;
  `from_33/SOURCE.md` and `source_manifest.json` were updated to the new source path. All 196 JSON and JSONL files
  (including gzip archives) parsed without repair, and every copied source hash matched commit `cf854303`
  (`resume_integrity_check.json`). The 152 item files written in October (all of batch 1 and 32 of batch 2) keep their
  October creation dates; new task records carry 24 November.
- 06:07:46. Fresh transport check for Opus failed authentication ("OAuth session expired and could not be refreshed").
  No collection calls followed. A local logging error after the failure was saved was fixed offline.
- 06:08:49, 06:10:41, 06:12:34. Resume transport changes, before any resumed collection: the quota guard now inspects
  only error channels, so successful reply text can never trigger quota detection or a retry; Codex resolved to
  `codex.exe` 0.160.1; temporary files moved to the ignored `data/tmp/`; live collection requires every resumed
  transport check to pass. Fifteen positive and negative guard tests and an offline replay of the 960 original strong
  judgments passed with 0 calls. No prompt, model setting, item, reader or score changed
  (`resume_transport_amendment.json`, `freeze_history/resume_20261124/`).
- About 07:00 to 09:30. The owner reported account-wide Codex HTTP 429 responses and an earlier agent turn that ended
  before collection. These are context, not outcomes of this notebook.
- 14:25:31. CLI 429 rule, frozen before the fresh calls: Codex concurrency 1 for all Codex requests, including Sol; a
  CLI 429 that exhausts its retries without a model reply is written only to a non-final log, never scored or cached as
  an outcome, and stops the collector on its first occurrence. Eight offline transport tests passed at 14:37:30 with 0
  calls (`cli429_amendment.json`, `cli429_transport_tests.json`).
- 14:25:46. Opus passed a fresh transport check; the failed 06:07 attempt is linked to it in
  `resume_auth_resolution.json`. Sonnet and Haiku also passed. No 429 occurred in these smoke calls.
- 14:26:01. Sol's transport check failed during CLI option validation ("Unknown feature flag: code_mode_host").
  Collection did not resume. The owner diagnosed PATH shadowing: a different `codex.exe` resolved inside the agent
  environment. The flag is supported by the intended binary.
- 14:31:30 and 14:32:20. Codex path change: the npm vendor `codex.exe` (codex-cli 0.160.1) is called by absolute path.
  Flags (including `--disable code_mode_host`), model pins, reasoning effort, no-tools settings, prompts, items,
  readers, scores and the stopping rule unchanged. Every new Codex attempt records its executable, version and path
  lookup outside the request key, so original baseline requests remain reusable (`codex_path_amendment.json`). Sol,
  Luna, Muse, Granite, DeepSeek, the Decisions API and both writers then passed transport checks; all 11 pinned models
  passed with no substitution.
- 15:03:31. Supplementary export of planned within-item reasons-minus-alone differences by family
  (`paired_family_comparisons.csv`) validated offline on the development items with 0 calls
  (`supplemental_validation_20261124.json`). It was added during batch 2 construction, before batch 2's strong judging,
  and changes no primary score, item, prompt or stopping rule.
- 15:12:22. Controlled restart for context isolation, before any new strong judgment. Moving scratch directories into
  the repository had let headless Codex discover the root `AGENTS.md` (OpenAI documents upward project-instruction
  discovery). A diagnostic Sol prompt used 12,004 input tokens in October, 19,189 from the repository-nested scratch
  directory and 11,963 after the fix. The CLI working directory became the `D:/` volume root, checked to contain no
  `AGENTS.md`, `AGENTS.override.md`, `CLAUDE.md` or `MUSE.md`; tools stay disabled and all scratch files stay under
  `data/tmp/`. 80 verified batch 2 item files were kept. 6 OpenRouter writer requests in flight were interrupted and
  reserved at 0.01 dollars each (0.06), bringing all interrupted unknown-charge attempts to 17 and 0.12394752 dollars
  (`context_isolation_restart.json`, `interrupted_attempts.json`). Contaminated tiny calls were transport checks, never
  test outcomes.
- 15:13:12. Context isolation change frozen (`context_isolation_amendment.json`); all six CLI models passed fresh checks
  by 15:13:58 (`resume_transport_ready.json`).
- 15:15:37. Own `models.json` environment descriptions corrected to match; pins, providers and output settings
  unchanged; the immutable notebook 33 copy unchanged.
- 15:27:10. Batch 2 (`nb34b2`) frozen, sha256 `7fd40756...`.
- 15:39:37. Small reproduction profile repaired: it now prefers one cached original disputed item per family, else an
  agreement control (default 4 items, 2 disputed), never calls tie-breakers on agreed items, and writes to
  `data/smoke_demo` and `figures/smoke_demo`. The running full collector kept the earlier, unused smoke branch; the full
  study is unaffected (`smoke_utility_amendment.json`).
- 17:20:47. Batch 3 (`nb34b3`) frozen, sha256 `601261d5...`.
- 18:18:31. Checkpoint after batch 3: 600 items, 70 disputes, 0 agreed and wrong (`strong_checkpoint_03.json`). Below
  the threshold of 80, so batch 4 was generated.
- About 19:02. Three batch 4 writer requests ran for about 699 s despite the 180 s subprocess deadline; later calls
  completed. Cause unknown (delayed scheduling or machine suspension possible, not confirmed). Retries and deadlines
  were not changed. These writer attempts affect spend and construction history only, never judge scores
  (`delayed_timeouts_20261124.json`).
- 19:22:39. Batch 4 (`nb34b4`) frozen, sha256 `9e062995...`.
- 20:21:53. Checkpoint after batch 4: 720 items, 87 disputes (75 instructions, 10 code, 2 worked), 0 agreed and wrong
  (`strong_checkpoint_04.json`). The stopping rule was met: 87 is at least 80, and batch 4 also reached the 480-pair
  maximum.
- 20:45:54. The monitoring host timed out and its cell was stale. The collector (PID 24852, `data/run34.py`) was
  verified still running and was not restarted. The last attempt event before the check was at 20:38:50 and the next
  at 20:47:57; the cause of that gap is not established. Not a pause and not evidence of a provider outage
  (`monitor_interruption_20261124.json`).
- 23:30:35. Last returned call. Live validation at 23:31:25: 720 items, 87 disputes, 0 missing, 5,142 judgments
  (`live_validation.json`).
- 23:37:30. Presentation-only figure change: visual review found bar labels overlapping the title of
  `disagreement_families.png`; y-axis headroom and a one-row legend were added. Score file hashes were compared before
  and after and are unchanged (`figure_layout_amendment_20261124.json`, `freeze_history/figure_layout_20261124/`).
- 23:38:42. Offline replay of the full notebook: 0 new calls, source hashes valid (`replay_validation.json`). The small
  profile was also replayed offline. Final QA at 23:42:11 (`final_qa.json`).

Collection in this period: one failed sign-in check at 06:07:45 and 5,166 returned attempts between 14:25:38 and
23:30:35 (`collection_periods.csv`).

## After collection

Reader-facing prose (README, notebook markdown, this file) was written after the results. Analyses added at that stage
for reporting, computed from `item_outcomes.csv` and `reasons_alignment.csv` with no new calls and no change to any
score: paired comparisons restricted to items readable in both conditions (Haiku and DeepSeek), counts of pairs meeting
each worked-example criterion, and which strong judge was the more confident in conflicting orders.

## Unknown-charge reservations

| When | Requests | Reason | Reserved (USD) |
|---|---|---|---|
| 30 Oct 17:31 | 4 | Controlled restart to correct reservation prices | 0.0204516 |
| 30 Oct 17:41 | 3 | Collector found absent; requests past deadline | 0.00349592 |
| 30 Oct 19:07 | 4 (3 identified, 1 owner-reported) | Owner's manual pause | 0.04 |
| 24 Nov 15:12 | 6 | Controlled restart for context isolation | 0.06 |
| All | 17 | | 0.12394752 |

None of these requests is a scored outcome. Replies that returned without a cost carry a further 0.97 dollars of
conservative reservations. OpenRouter reported 1.15 dollars returned; the accounted total is 2.24 dollars against the 5
dollar limit.

## Settings

- Strong and CLI judges: Opus, Sonnet, Haiku (`claude -p`), Sol, Luna (`codex exec`, codex-cli 0.160.1), Muse
  (`muse exec`); reasoning effort medium; tools disabled. October: empty temporary working directory. From 24 November:
  `D:/` volume root as working directory, scratch files in `data/tmp/`.
- OpenRouter judges: Granite 4.2 8B on CoreWeave BF16 (reasoning none) and DeepSeek V4.1 Flash on DeepInfra FP8
  (reasoning low); temperature 0; JSON object mode; 1,600 output tokens with length retries up to 6,400. Decisions API
  `openai/gpt-6-luna-decisions-20261006` with notebook 33's state template and both full answers as choices.
- Writers: Gemma 3 4B (Parasail BF16) and Gemma 3 27B (DeepInfra FP8) with notebook 33's temperatures, budgets and
  checked chunked copying.
- Concurrency: October 2 Claude, 2 Codex, 1 Muse, 3 per OpenRouter model; from 24 November Codex 1.
- Retries only for transport failures and truncated OpenRouter replies; provider policy blocks are never retried;
  quota and exhausted CLI 429 replies stop the collector and are never cached as outcomes.
- Reservations use a conservative byte-count input estimate plus 4,096 tokens of overhead at verified pinned-provider
  prices. Imported notebook 33 costs do not count against this notebook's 5 dollar limit.
- Muse reports no usage; its cost is a proxy (characters divided by 4, at 4 and 20 dollars per million tokens).
