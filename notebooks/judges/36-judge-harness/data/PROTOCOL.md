# Notebook 36 protocol history

This file records how the experiment was run: what was fixed before the results, every change made afterwards, the
interruptions to collection and the spend. The reader-facing explanation is in the [README](../README.md). All times
are UTC. The machine-readable record is [`run_log.jsonl`](run_log.jsonl) (every event, including retries);
[`protocol_milestones.csv`](protocol_milestones.csv) is the same log without retry rows, and
[`attempt_lifecycle.jsonl`](attempt_lifecycle.jsonl) records every request that was started or returned.

## What was fixed before any selection call

- The exam is notebook 33's, unchanged: 240 test pairs and 24 development pairs, copied from the owner-supplied
  commit `cf854303` into [`from_33/`](from_33/). Every copied file was checked against notebook 33's freeze hashes
  after normalising line endings to LF ([`source_manifest.json`](source_manifest.json), [`from_33/SOURCE.md`](from_33/SOURCE.md)).
  No generator setting or item was changed.
- The owner's brief replaced Claude Haiku 5.5 with GPT-6 Luna as the mid-range judge, because Haiku's provider had
  blocked 73 of its 120 instruction judgments in notebook 33. Sol, Luna and Granite keep notebook 33's pins and
  provider. Granite's baseline reasoning setting is "none", so its effort conditions are compared with "none".
- Seed 3610302026 split the test pairs 120 selection / 120 confirmation, 30 per family and 6 traps per half, with the
  better answer shown first in 15 of 30 pairs per family per half ([`split.csv`](split.csv)).
- [`analysis_plan.json`](analysis_plan.json) fixed the conditions, readers, tie and unreadable scoring, bootstrap
  intervals (5,000 item resamples), the single-answer tie-break, the majority rule, the recommendation rule and the
  combination rule. [`prompt_templates.json`](prompt_templates.json), [`pair_schema.json`](pair_schema.json) and
  [`single_schema.json`](single_schema.json) fixed the prompts and native schemas.
- Baseline, both orders and vote 1 of the majority reuse notebook 33's final replies (1,440), and the confirmation
  baseline reuses them too. 27 earlier retry attempts for those replies were recovered from a byte-identical copy of
  notebook 33's archive held in notebook 34 ([`source_retry_manifest.json`](source_retry_manifest.json)); notebook 34
  was only read.
- The freeze at 2026-10-30 17:56:52 ([`freeze_record.json`](freeze_record.json)) hashed the exam, reading rules,
  split, prompts, analysis plan, models, date provenance, schemas and the harness code. The later amendments below
  archived each earlier freeze and code version (`freeze_before_*.json`, `harness_code_before_*.py`); none changed an
  item, prompt, request setting, reader, score or the recommendation rule.

## 2026-10-30: development, freeze and selection start

- 17:19. First full invocation; capability probes for each judge and for the native-schema options.
- 17:19 to 17:52. Development on the four frozen development pairs (one per family), all conditions. Two Granite
  requests stayed open past the 180-second socket timeout and the collector exited twice without an error.
- 17:46:55. Transport amendment ([`transport_amendments.json`](transport_amendments.json)): OpenRouter requests run in
  an isolated Python process with a 180-second socket timeout and a 210-second hard deadline; a timeout is unreadable
  and not retried. 127 completed development outcomes were kept. 17:48:10, a follow-up kept the timeout category when
  the child process reports a socket timeout.
- 17:52:24. Development complete (129 outcomes). The strict reader rejected 23 of 24 analysis-first and solve-first
  development replies; no reader or prompt was changed.
- 17:53:39. Reporting fix before any selection call ([`reporting_amendments.json`](reporting_amendments.json)): the
  logger accepts a timestamp, and NumPy booleans are converted before JSON export.
- 17:56:52. Freeze.
- 18:22:36. A Luna single-answer request (`test-grounded-043`, answer B) ran 754 seconds against a 600-second timeout.
  The notebook's own process tree was stopped by hand so its output could be captured
  ([`manual_timeout_enforcement.json`](manual_timeout_enforcement.json)). The captured error was a Codex client panic:
  the operating system could not start a worker thread (Windows error 1450)
  ([`manual_timeout_reply_audit.json`](manual_timeout_reply_audit.json)). The reply is kept as a failed attempt.
- 18:39:33. Client transport amendment ([`client_transport_amendment.json`](client_transport_amendment.json)): new CLI
  processes get `TOKIO_WORKER_THREADS=2`, file handles instead of pipes, and a hard 600-second wait. Three requests in
  flight were recorded as interrupted with conservative cost reservations. Two tiny transport checks passed
  ([`client_resource_smoke.json`](client_resource_smoke.json)). Single-answer and part of analysis-first selection
  were collected this day.
- 19:04. Descriptive diagnostics code ([`reporting_v1.py`](reporting_v1.py)) created; it never feeds the selection rule.
- 19:07:47. Collection paused at the owner's request. Four requests had no reply (three Granite, one Sol), reserved at
  $0.10 each for OpenRouter. The worktree was later moved from drive C: to D:.

## 2026-11-24: resume, CLI change and the first Sol capacity stop

- 06:05:35. Resume after 25 days ([`resume_record.json`](resume_record.json)). Every data file parsed and the source
  files matched their hashes at the new location ([`resume_integrity_audit.json`](resume_integrity_audit.json),
  [`resume_source_verification.json`](resume_source_verification.json)).
- 06:06:24. Resume transport amendment ([`resume_transport_amendment.json`](resume_transport_amendment.json)): usage
  and quota markers are searched only in error channels, not in successful answer text (19 regression tests,
  [`quota_guard_tests.json`](quota_guard_tests.json)). The `codex` found on the path was an obsolete 0.142.4 that
  failed on an unknown feature flag before reaching a model; the harness now runs the npm package's `codex.exe`,
  codex-cli 0.160.1. Prompts, flags, models and settings are unchanged. The failed local start is kept as a startup
  failure, not an outcome.
- 06:07 to 06:08. One smoke judgment per judge passed ([`resume_transport_checks.json`](resume_transport_checks.json)).
- 06:44:29. The four requests left open at the pause were rebuilt from the frozen inputs and matched their original
  cache keys ([`paused_request_reconstruction.json`](paused_request_reconstruction.json)). They count as sends with no
  reply; later replies with the same keys are separate attempts.
- 06:33 to 07:48. Sol returned "exceeded retry limit, last status: 429 Too Many Requests" repeatedly. The collector
  retried each such component three times instead of stopping. An offline audit found this, and at 07:48:50 the
  notebook's own collector process was stopped ([`cli429_stop_record.json`](cli429_stop_record.json)).
- 07:51:38. Rate-limit amendment ([`cli429_transport_amendment.json`](cli429_transport_amendment.json)): an exhausted
  CLI 429 now stops collection immediately. The 927 exhausted-429 returns were reclassified as non-final records
  (originals preserved in [`cache_before_cli429_stop.jsonl.gz`](cache_before_cli429_stop.jsonl.gz)), and 104
  provisional Sol outcomes built on them (analysis first 38, majority 66) were withdrawn and later collected again.
  No answer-based score changed. Four more requests were in flight; the OpenRouter reservation rose by $0.20.
- 20:50:47. Sol scheduling amendment ([`sol_serial_scheduling_amendment.json`](sol_serial_scheduling_amendment.json)):
  at most one Sol request at a time, because notebooks 34 and 37 were also calling Sol. The owner reported Sol had
  recovered around 09:30. Luna keeps the shared two-request Codex limit and Granite three.
- 20:51:40. Tagged single-request Sol check passed; collection resumed at 20:52.

## 2026-11-25: second stop, completion and replay

- 01:10:09. The first exhausted Sol 429 (native schema, `test-code-002`) stopped collection cleanly
  ([`cli429_stop_20261125T011009.json`](cli429_stop_20261125T011009.json),
  [`sol_serial_stop_validation.json`](sol_serial_stop_validation.json)): 2,522 of 3,870 selection outcomes were
  cached. The 429 reply and three replies that arrived after the stop were kept as non-final records.
- 18:24:04. With notebook 34 finished and Sol available, a fresh single-request Sol check passed and collection
  resumed ([`resume_20261125.json`](resume_20261125.json)).
- 19:33:01. Spend reporting amendment ([`all_attempt_spend_amendment.json`](all_attempt_spend_amendment.json)):
  spend totals include known costs of non-final returns; final-cache-only totals are kept in named fields. The same
  time stamp records that an ignored progress script had a memory error; the collector was unaffected.
- 20:50:54. Recommendation fixed from the selection outcomes alone ([`recommendation.json`](recommendation.json)): no
  change qualified, so the recommended harness is the baseline and confirmation reuses the baseline replies. No
  confirmation request was sent.
- 20:51:07. Collection complete: 3,870 selection, 720 confirmation and 129 development outcomes.
- 20:51:38. Working caches merged losslessly into [`cache_imported.jsonl.gz`](cache_imported.jsonl.gz) (7,110
  records; record equality verified, [`cache_archive_manifest.json`](cache_archive_manifest.json)).
- 20:53:51. Figure title amendment ([`final_figure_label_amendment.json`](final_figure_label_amendment.json)): titles
  state measured findings, and the confirmation title says that no change qualified. Only plot labels changed.
- 20:57:08. Rendering amendment ([`inline_rendering_amendment.json`](inline_rendering_amendment.json)): the 20:54
  replay used a non-interactive plotting backend and embedded no images; the replay now embeds all six figures.
- 21:01:13. Editorial exports (headline tables, eligibility, reader rankings, example selections) moved into the
  notebook's diagnostics cell, with mirrors in [`editorial_exports_v1.py`](editorial_exports_v1.py)
  ([`editorial_export_amendment.json`](editorial_export_amendment.json)).
- 21:01:47. Final zero-call replay passed ([`final_validation.json`](final_validation.json),
  [`replay_audit.json`](replay_audit.json)): 13 code cells, 6 embedded figures, caches unchanged, 9,438 scored reader
  rows checked.
- After the replay, the README, this file and the notebook's markdown cells were written. Only markdown changed; the
  notebook was not executed again.

## Reporting choices made after collection

These are descriptive and did not feed the recommendation rule.

- `fixed` and `broke` in [`paired_comparisons.csv`](paired_comparisons.csv) count any score change, including moves to
  or from an undecided 0.5; `full_corrections` and `full_regressions` count only wrong-to-correct and correct-to-wrong.
- Unary grades are summarised as both pass, both fail, only better passes, only worse passes and unreadable
  ([`unary_pattern_summary.csv`](unary_pattern_summary.csv)). The README's reversed tie-break check (single answer
  would score 85.0%, 60.0% and 52.9%) is arithmetic on these cached grades, done after the results.
- [`reference_copy_audit.csv`](reference_copy_audit.csv) reports exact and parsed-code matches between the code
  reference and the better answer: 46 of 60 exact.
- Collection time is reported as four episodes split by gaps of more than one hour
  ([`collection_episodes.json`](collection_episodes.json)); per-call seconds are summed work, not wall time.

## Calls and spend

| Judge | Origin | Requests sent | Returned | OpenRouter known USD | CLI list-price estimate USD | Records without usage |
|---|---|---|---|---|---|---|
| Granite 8B | notebook 33 (reused) | 507 | 507 | 0.0727 | | 0 |
| Luna | notebook 33 (reused) | 480 | 480 | | 0.2421 | 0 |
| Sol | notebook 33 (reused) | 480 | 480 | | 7.8850 | 0 |
| Granite 8B | this notebook | 2,445 | 2,433 | 0.8728 | | 20 |
| Luna | this notebook | 1,604 | 1,602 | | 0.9202 | 3 |
| Sol | this notebook | 2,542 | 2,539 | | 27.2665 | 932 |

Source: [`physical_spend_by_model.csv`](physical_spend_by_model.csv). This notebook sent 6,591 requests; 6,574
returned, 17 got no reply, and 931 of the returns are non-final (927 reclassified Sol 429s, one later Sol 429, three
replies after a stop). Known OpenRouter cost for this notebook is $0.87275607; with conservative reservations for
interrupted and unpriced requests it is $1.47529402 against the $5 cap ([`spend.json`](spend.json)). The CLI estimate,
$28.19, uses notebook 33's list rates (Sol $2 input, $0.10 cached input, $10 output per million tokens; Luna $0.10,
$0.005, $0.50) and omits the 935 records without usage, so it is a lower bound and not a bill. Notebook 33's costs
are listed for reference and are not new spend.

Collection episodes: 30 October 17:19 to 19:08 (1,057 sends), 24 November 06:07 to 07:49 (1,962), 24 November 20:52
to 25 November 01:11 (1,954), 25 November 18:24 to 20:51 (1,618); 10.3 hours in all, excluding the 25-day pause.
