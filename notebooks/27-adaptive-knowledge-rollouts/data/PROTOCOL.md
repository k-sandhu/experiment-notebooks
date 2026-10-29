# Notebook 27: run history

This file records how the collection runs behind notebook 27 were registered, interrupted, changed and recovered, in date order. The README and notebook give the results; this file is for checking how they were produced. All times are UTC. Each entry names the file in `data/` that holds the original record, with its hashes where the file has them.

The files use code names. A "policy" is a tested model, an "allocator" is a collector (uniform or adaptive), an "arm" is one model and collector working through one block (the README calls it a block run), and "frontier" marks the search for tasks that GPT-6.1 Sol sometimes fails. Protocol versions map to the README's comparisons as follows:

| Protocol | README name | Folder |
|---|---|---|
| `27-adaptive-v1` | First run on the office tasks, lost to connection errors | `cache/`, `episodes/`, `schedules/` |
| `27-adaptive-v2` | Office tasks at equal calls | `primary_run/` and top-level tables |
| `27-adaptive-v3-stress` | Five-review calendars at equal calls | `stress_run/`, `stress_*` files |
| `27-adaptive-v4-calibration`, `-v4-comparison` | Six-review ladder and comparison | `frontier_v4/` |
| `27-adaptive-v5-calibration`, `-v5-comparison` | Twelve-review ladder and comparison at equal calls | `frontier_v5/` |
| `27-adaptive-v6-token` and its recovery versions | Twelve-review comparison at equal tokens | `frontier_v6/` |

## Settings shared by every run

- Tested models: `gpt-6.1-sol` and `gpt-6-luna`, called only through `codex exec` (codex-cli 0.160.1, recorded in `environment.json` and the v6 protocols) with medium reasoning effort. The CLI returned no dated model name, so no dated version is recorded. Documented knowledge cutoffs: 30 April 2026 (Sol) and 18 May 2026 (Luna), from the official model pages linked in `environment.json`.
- Each action is a fresh ephemeral CLI process in an empty working directory, given the full visible history. The CLI options (`--ephemeral`, `--ignore-user-config`, `--sandbox read-only`, and `--disable` for the shell, unified exec, apps, plugins, multi-agent, browser, computer use, image generation and code mode, with web search disabled) are saved in every cache entry under `request.cli_options`. Responses are audited for unexpected tool use; a reply after a host-tool call is withheld and scored 0 (`policy_tool_violation`). The CLI exposes no decoding seed, no output-token cap and no attestation of served weights.
- Collector rule, unchanged across all runs: group size 4, probe size 2, a Beta(1,1) prior (uniform over success rates), and an abandonment threshold of 0.45. After two agreeing outcomes the predicted chance of a mixed group of four is (4 − 2)/(4 + 1) = 0.4, so the group is abandoned; a mixed prefix has probability 1 and continues to four. Both collectors share each block's seeded task order, refreshed each cycle.
- Task wording: Claude Opus 5.5 (`claude-opus-5-5`) through `claude -p`, four calls in all, from a different vendor than the tested models. Reported list prices: USD 0.057587 (office tasks, `data_provenance.json`), 0.027507 (five-review calendars, `stress_authoring.json`), 0.0201788 (six-review calendars, `frontier_v4/authoring.json`) and 0.036451 (handoff-charge calendars, `frontier_v5/authoring_fees.json`); total USD 0.1417238. The equal-token tasks reuse the handoff-charge wording (`frontier_v6/authoring.json`, no new call). Every number and answer comes from code.
- Environment: OpenEnv 0.10.0 at commit `21fbb0ecb2a3e74110b59cf38a1b195decc75c88` (BSD-3-Clause). Calendar runs as one loopback HTTP service per worker, because the legacy server keeps mutable request context. FinQA and REPL run locally. No Docker engine and no local model weights are used.
- Interrupted or budget-cut attempts keep a top-level `reward` of null. Their nested `verification.reward` describes the captured partial state and must not be used as a task label.

## 24 October 2026

### Office tasks

- 17:07: `27-adaptive-v1` frozen (`preregistered_protocol.json`). Question: does adaptive collection yield more complete mixed-reward groups at the same policy-call budget? 120 calls per model, collector and block, 960 in all; 10 actions per attempt; 180-second call deadline. Six trial tasks with one attempt per model (64 calls) were excluded from all comparisons and were not used to choose task IDs or thresholds.
- Trial-task finding: pandas stored the ledger's `recorded_at` as SQLite timestamps with a space instead of `T`, which changes same-day ordering against a cutoff containing `T`. The initial observation for the comparison tells both models to compare timestamps as dates, for example with `datetime(...)`. The trial tasks ran before this hint.
- The v1 comparison lost 792 of 960 calls to transport errors, many reading `workspace routing discovery failed`; 168 calls returned. The collector did not stop after repeated failures. One diagnostic call was also made. The data are kept and excluded from every comparison (`original_run_audit.json`).
- A one-call CLI health check succeeded.
- 18:25: `27-adaptive-v2` frozen (`preregistered_primary_protocol.json`) after inspecting the interrupted run: 90 calls per model, collector and block, 720 in all, with a circuit breaker that stops new calls after a transport error. Task IDs, business rules, group size, prior, threshold and ordering were kept from v1. This run supplies the office-task results.
- v2 call statuses: 710 ok, 9 invalid JSON (8 Luna, 1 Sol) and 1 host-tool reply (Luna, `fin-04`), from `calls.csv`.

### Five-review calendars

- 18:38: `27-adaptive-v3-stress` frozen (`preregistered_stress_protocol.json`), registered after v2 left Sol's groups all successes. Two five-review tasks, four calendars, nine allowed starts per review (59,049 combinations; 16 and 33 valid plans after availability and ordering), 15 actions, 64 calls per model and collector (256 in all), 180-second deadline. Both tasks passed a ten-call replay of a known answer through the Calendar tools. The minimum uses a fixed earliest-start tie-break.

### Six-review ladder and comparison

- 19:17: `27-adaptive-v4-calibration` frozen: levels of 6, 7, 8 and 9 reviews, two prepared tasks per level, two attempts per task, two more each when both outcomes appear, stopping when one task has both outcomes; call cap 768; 24 actions (`frontier_v4/calibration_protocol.json`).
- 19:17:56: recorded change before any model call: a missing lower time bound must cover the task day, and every SQL seed is registered (`frontier_v4/calibration_pre_call_amendment.json`).
- 19:18:55: recorded change before any model call: keep the comparison budget at 180 calls per model and collector in two 90-call blocks (`frontier_v4/budget_pre_call_amendment.json`).
- Ladder: only the six-review level ran, 89 calls, all valid actions. `calibration-6-0` gave 1, 1, 1, 0 and `calibration-6-1` four 1s. The levels above were not needed.
- 19:31: level 6 selected (`frontier_v4/selection.json`). Four comparison tasks generated from seeds `2749000 + 100*level + index`, with no tested-model screening.
- 19:32: `27-adaptive-v4-comparison` frozen: four tasks, two blocks, 90 calls per block, 24 actions, 180-second deadline, eight workers (`frontier_v4/comparison_protocol.json`). Call statuses: 699 ok, 19 invalid JSON and 2 host-tool replies, all Luna (`frontier_v4/calls.csv`).

### Twelve-review ladder and comparison at equal calls

- 20:29: `27-adaptive-v5-calibration` frozen, because the six-review comparison gave Sol 29 of 29. New target: two to six successes in eight completed valid-action attempts, with both outcomes on one task; action-horizon endings, host-tool replies and unknown outcomes do not count. Start at eight reviews, move to nine above six successes and to seven below two; call cap 576 (`frontier_v5/calibration_protocol.json`).
- 20:55: eight reviews gave 8 of 8 in 112 calls, so the ladder moved to nine (`frontier_v5/routing_8_to_9.json`).
- The first nine-review cohort stopped when one call reached the 180-second client deadline after its model turn began. The circuit breaker kept seven interrupted or unstarted slots as unknown. A separately logged availability check, the one such check in this stage, succeeded in 4.4 seconds.
- 21:12: recorded change: 600-second deadline and a fresh eight-slot cohort on the same two nine-review inputs; no automatic retries; the earlier cohort kept (`frontier_v5/deadline_recovery_amendment.json`). The new cohort gave 8 of 8.
- 21:48: recorded change: twelve reviews with more independent orderings, and at least 10,000 valid schedules witnessed per task, because full enumeration showed that added reviews can leave very few legal alternatives (`frontier_v5/broader_choices_amendment.json`). The twelve-review cohort gave 8 of 8.
- 22:27: recorded change before new calls: add 12 conditional handoff charges (six of them cross-pair soft orderings) to six mandatory ordering rules; require the movement-only optimum to be at least 60 points worse under the full cost; raise the calibration cap from 576 to 1,152 after 420 calls had been used. The comparison budget stayed at 180 calls per model and collector (`frontier_v5/handoff_costs_amendment.json`). The `objective_minutes` fields hold penalty points from here on; the verifier also writes `objective_penalty_points` and charge breakdowns.
- 22:28: recorded before the first completed handoff-task outcome: start at twelve reviews, go down two reviews below two successes and up two above six, at most three handoff cohorts (`frontier_v5/handoff_ladder_amendment.json`).
- The first handoff cohort gave 0, 0, 0, 0 and 1, 0, 1, 0: two successes in eight, all eight agendas valid. The ladder used 591 calls and gave 33 known outcomes across all cohorts (`frontier_v5/calibration_results.csv`, `calibration_resources.csv`); one call has no usage. The calibration contains 8 API errors, all with the time-zone binding message below.
- 23:00: recorded change before any comparison call: the Calendar binding advertises `timeZone` as optional but rejects a `dateTime`-only edit (HTTP 400 without `timeZone`, HTTP 200 with `timeZone: UTC` on the same event and instant; `frontier_v5/serialization_audit.json`). The comparison schema makes the field required and the initial observation states the rule (`frontier_v5/serialization_pre_comparison_amendment.json`). The calibration used the older schema, so its success rate may not transfer.
- 23:09: recorded change before any comparison call: a completed calibration call took 541.4 seconds, so both comparison collectors get a 1,200-second deadline (`frontier_v5/deadline_pre_comparison_amendment.json`).
- 23:11: twelve reviews with handoff charges selected (`frontier_v5/selection.json`). Four comparison tasks generated afterwards from disjoint seeds; branch-and-bound and an independent MILP agree on every minimum, and all four optimal agendas pass through the Calendar API.
- 23:16: `27-adaptive-v5-comparison` frozen (`frontier_v5/comparison_protocol.json`). Call statuses: 699 ok, 20 invalid JSON and 1 host-tool reply, all Luna. The longest call took 626.7 seconds; 2 calls ran past 600 seconds. The comparison recorded 0 API errors (`frontier_v5/api_error_audit.json`).

## 26 October 2026: equal-token comparison

- 15:22: preparation plan and 15:31: `27-adaptive-v6-token` frozen (`frontier_v6/comparison_protocol.json`). Question: does the earlier tie in complete mixed groups persist on fresh tasks at equal token budgets? 16 tasks (`token6-01` to `-16`, seeds `2026102600 + index`), four blocks of four, 6,000,000 tokens per model, collector and block, 24 actions, 1,200-second deadline, eight workers, safety cap of 400 calls per block run. Primary measure: complete mixed groups summed over four blocks. Secondary measures declared then: paired block differences with all 16 sign flips, curves at 1M-token checkpoints, coverage, rewards, unknown outcomes, exact cost gaps, tokens, time and overrun, and a prefix-matched sensitivity labelled post hoc. Token unit: input plus output tokens as reported, with cached input inside input and reasoning inside output. The first call to cross a block's budget is charged and kept, its action is not run and its attempt is unknown. The controller was tested on synthetic boundary cases without model calls: a finish exactly at the cutoff is eligible, one token past it is not, and missing usage stops collection (`frontier_v6/controller_audit_final.json` and the other `controller_audit*.json` files).
- 15:26: two availability checks, one per model, succeeded (`frontier_v6/health/`).
- First launch (eight workers): 8 calls, 3 of them HTTP 429 rate-limit errors, no known outcome (`frontier_v6/interrupted_launch_audit.json`, folder `comparison/`).
- 15:37: recovery plan with a replacement bank of 16 tasks (`token6r-01` to `-16`, seeds `2026102700 + index`, disjoint from the first bank and every earlier task), four workers and a 2-second gap between call starts (`frontier_v6/recovery_plan.json`, `comparison_recovery_protocol.json`). 15:44: clarification that a numerical proposal whose movement-only search reaches the 2-million-node limit is rejected and the next seed tried; no model outcome involved.
- 15:38 to 15:53: four more availability checks: Sol failed twice (15:38, 15:44) and then succeeded (15:53), Luna succeeded (15:38) (`frontier_v6/health_recovery/`, `health_readiness_frozen.json`). Sol launches were deferred until a Sol check succeeded, so the two models' block runs started at different times.
- Second launch (Luna, four workers): 9 calls, 2 rate-limit errors, no known outcome (`frontier_v6/interrupted_recovery_audit.json`, folder `comparison_recovery/`).
- 15:57: paced plan with two workers and a 6-second gap. Third launch (Sol): 7 calls, 2 rate-limit errors after five successful requests, no known outcome (`frontier_v6/interrupted_paced_audit.json`, folder `comparison_paced/`).
- 16:03: `27-adaptive-v6-token-final` frozen: same replacement bank, unchanged; 15.5-second gap between call starts, at most four starts in any minute and two calls at once (`frontier_v6/comparison_final_protocol.json`). No task or rule was changed after any model outcome. Collection began at 16:03.

## 27 October 2026: interruptions and recovery

- 08:18: Sol returned "Selected model is at capacity." Twelve block runs had reached their token budgets; four had not (`frontier_v6/capacity_interruption_audit.json`):

| Model | Collector | Block (files: 0 to 3) | Calls | Known | Successes | Stop |
|---|---|---|---|---|---|---|
| GPT-6.1 Sol | adaptive | 3 | 5 | 0 | 0 | unknown usage |
| GPT-6 Luna | uniform | 0 | 0 | 0 | 0 | circuit breaker |
| GPT-6.1 Sol | adaptive | 0 | 0 | 0 | 0 | circuit breaker |
| GPT-6.1 Sol | uniform | 0 | 145 | 7 | 5 | circuit breaker |

  The excluded attempts hold 150 calls and 5,139,112 reported tokens, plus one request with unknown usage, and 7 known outcomes (5 successes) that stay outside the comparison.
- 08:18: a Sol availability check succeeded (`frontier_v6/health_capacity/`). 08:21: capacity plan: keep every block run that reached its budget and repeat every other one in full from a fresh calendar with the full 6 million tokens, chosen by completion status, not rewards (`frontier_v6/capacity_plan.json`, `comparison_capacity_protocol.json`). The capacity recovery made 526 calls; three of its four block runs finished.
- 16:13: a local tool-session refresh stopped the collector while the last Sol adaptive block run (block 0 in the files) was unfinished. The collector, watcher, pipeline and last CLI child process were gone; the last raw request (`1727ee8a...`, started 16:05:39) was pending with no usage or outcome. It was kept unchanged and never resubmitted. That block run had 101 calls: 100 completed with 3,576,478 reported tokens, one pending, 4 known outcomes and 0 successes (`frontier_v6/session_interruption_audit.json`).
- 16:13: session plan: keep the 15 finished block runs (12 original, 3 from the capacity recovery) and repeat the unfinished one from a fresh calendar with the full budget, with no availability check because the cause was local (`frontier_v6/session_recovery_plan.json`, `comparison_session_protocol.json`). The repeat made 173 calls and finished at 20:04.
- `frontier_v6/comparison_complete/` holds unchanged copies of the 16 block runs used: 12 from `comparison_final/`, 3 from `comparison_capacity/` and 1 from `comparison_session/`. Its `composite_manifest.json` links each copy to its source and hash. Call statuses in the comparison: 2,036 ok, 23 invalid JSON and 2 host-tool replies, all Luna; one of the two host-tool replies was a crossing call whose attempt is unknown. The included block runs record no Calendar API errors.

## Totals

| Stage | Calls |
|---|---|
| v1 office run 960, trial tasks 64, health check 1, v2 comparison 720 | 1,745 |
| v3 five-review comparison | 256 |
| v4 ladder 89, comparison 720 | 809 |
| v5 ladder 591, availability check 1, comparison 720 | 1,312 |
| v6 comparison 2,061; outside it 282 (three rate-limited launches 24, capacity-stopped block runs 150, session-stopped block run 101, availability checks 7) | 2,343 |
| All tested-model calls | 6,465 |

The v6 comparison reported 96,701,725 tokens against a 96,000,000-token allowance, 701,725 (0.73%) past the cutoffs; its eligible calls end at 95,638,261 because whole calls can leave unused room before a boundary. All 2,343 v6 calls reported at least 106,049,962 tokens; the 282 outside calls account for 9,348,237 of them and for all 11 calls without usage. Copies in `comparison_complete/` are counted once. Billing for the tested models is not reported by the CLI. No OpenRouter request, optimizer step or weight update was made, and every export row is `train_ready=false`.

## Analyses added after the results

- The count of incomplete groups that already hold both outcomes at the token boundary was added after the boundary groups were inspected (`frontier_v6/known_contrast_diagnostic.csv`; summary in `ANALYSES.md`).
- The shared-prefix sensitivity was declared in the v6 protocol and labelled post hoc there (`frontier_v6/shared_eligible_sensitivity.csv`).
- The ledger-query repair audit (`financial_error_audit.json`) and the hindsight checks of uniform groups with an agreeing first pair (`uniform_prefix_audit.*` in `frontier_v4/` and `frontier_v5/`) were computed from saved records after collection.

## How to collect new data

Replay needs only `requirements-replay.txt` and makes no model call. For a separately named new collection, keep the existing data, install `requirements-live.txt` and the three environments from the pinned source:

```powershell
git clone --filter=blob:none https://github.com/meta-pytorch/OpenEnv.git data/tmp/OpenEnv
git -C data/tmp/OpenEnv checkout 21fbb0ecb2a3e74110b59cf38a1b195decc75c88
python -m pip install -e data/tmp/OpenEnv/envs/calendar_env -e data/tmp/OpenEnv/envs/finqa_env -e data/tmp/OpenEnv/envs/repl_env
```

Use an authenticated `codex` CLI. The equal-call collector (section 12 of the notebook) runs only with `NB27_LIVE=1` and a new `FRONTIER_NEW_RUN_ID`; its default of 72 calls per collector, one block and two models caps a run at 288 calls and writes to `frontier_v5/live-<run-id>/`. The equal-token collector (section 13) runs only with `NB27_V6_LIVE=1` and a new `TOKEN_LIVE_RUN_ID`; by default it uses one model, one block and 3 million tokens per collector, keeps the 15.5-second start gap, reuses the frozen task bank and writes to `frontier_v6/live/<run-id>/`. Calendar needs local loopback ports, and nested model calls stay disabled. A paused or pending request needs an audit and must not be resubmitted silently.
