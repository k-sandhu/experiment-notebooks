# Protocol and run record: notebook 07, subagent handoff harness

This file holds the settings and run history behind the notebook. The reader-facing account is in `../README.md`
and the notebook. Everything here is taken from the notebook's code and outputs, the files in `data/`, or the
repository's git history; nothing was re-run when this file was written.

## Plan

No analysis plan was written down before the runs. The seven levels, the measures (wall-clock time, model calls,
tool calls, planner blocked time and share, correctness) and the correctness check were defined in the notebook
together with the harness. `data/runs/` holds one run per level.

## Dates

- The run records carry no timestamps. They were added to the repository on 17 October 2026 at 02:32 (UTC-4) in
  commit `2901f83d` ("Add eight self-contained LLM experiment notebooks"), together with the notebook,
  `data/comparison.csv` and the eight figures.
- 17 October 2026, commit `1cf89c87`: Contents, workflow diagram, agent-loop diagram and per-level sequence
  diagrams added to the notebook; README extended. No data or figure changed.
- 17 October 2026, commit `5630274b`: Future work and further reading section added; links checked that day.
- 28 October 2026: README and notebook markdown rewritten for the repository's writing rules, and this file added.
  No code cell, output, figure or data file changed, and nothing was re-run. The Anthropic research-system post
  was opened again that day to confirm the figures the README cites from it.

## Models and how they were called

- Planner: `claude-sonnet-5-5`. Every helper: `claude-haiku-5-5`. These are the names passed to `--model`; the
  field `model` of every agent in `data/runs/*.json` holds one of the two.
- Each agent step is one stateless call: `claude -p --model <model> --tools "" --safe-mode --no-session-persistence
  --effort low --output-format json`, prompt on standard input, 600 s timeout, run in a fresh temporary directory.
  The harness keeps only the `result` text of the JSON output, so the served model version, token counts and cost
  were not recorded.
- The notebook also defines `codex exec` (`gpt-6.1-sol`) and `muse exec` (`muse-wonder-full-1.0`) backends behind
  `BACKEND`. They were not used for the recorded runs.

## Harness settings

- `MAX_STEPS = 18` model calls per agent; an agent that reaches it finishes with "gave up after 18 steps". No agent
  reached it.
- Prompt: role instructions, task, allowed actions (from the action docstrings), the agent's subagents and their
  status, the last 12 history entries (each action cut to 300 characters and each result to 2,500 characters,
  `HISTORY_CHARS`), new messages (each cut to 2,500 characters), and the reply-format line.
- A code comment records that a first version of the harness cut each history entry to 700 characters, which cut
  off combined `wait_all` results. The notebook's code uses 2,500. No run made with the first version is in `data/`.
- A reply that does not parse becomes the action `invalid` and the agent tries again; a failed CLI call becomes the
  text "LLM call failed: ..." and is handled the same way. Neither occurred in the kept runs.
- Waits: `handoff` and `ask_parent` wait up to 600 s; `wait`, `wait_all`, `wait_any` and `wait_for_message` use
  the `timeout_s` the agent passes (default 300 s). Each level has a 900 s overall timeout. All seven runs
  finished (`finished: true`).
- Logging: every model call, tool call and blocked interval is a span with start and end seconds; every message is
  an event with a time, cut to 300 characters; the call log keeps the prompt length and the first 600 characters
  of each reply.
- `max_depth` is 1 for planners that may spawn and 2 for the level 6 city coordinators.

## Simulated world

- Tool delays: `search_flights` 3 s, `search_hotels` 4 s, `search_hotels_backup` 5 s, `get_weather` 2 s.
- Level 3: the first `search_hotels` call for Prague raises "hotel search service unavailable (HTTP 503)".
- Level 5: `search_flights_provider` waits 2 s (skyscan), 6 s (farefinder) or 14 s (airdeal), chosen by the
  provider name in the helper's task.
- Correct answer: €3,316 with Baixa Rooms, Termini Inn and Old Town Loft (€3,310 without the central preference);
  flights only, €2,654.

## Kept runs

| Run file | Wall-clock (s) | Agents | Model calls | Tool calls | Planner blocked (s) | Correct |
|---|---:|---:|---:|---:|---:|---|
| `L0_single_agent.json` | 82.1 | 1 | 11 | 10 | 0.0 | yes |
| `L1_sync_handoff.json` | 120.2 | 4 | 17 | 10 | 66.3 | yes |
| `L2_async_spawn.json` | 56.8 | 4 | 18 | 10 | 0.0 | yes |
| `L3_progress_and_redirect.json` | 68.8 | 4 | 25 | 12 | 0.0 | yes |
| `L4_child_asks_parent.json` | 68.9 | 4 | 21 | 10 | 0.0 | yes |
| `L5_race_and_cancel.json` | 49.3 | 4 | 17 | 9 | 15.7 | yes (flights only) |
| `L6_nested.json` | 65.2 | 10 | 35 | 10 | 3.2 | yes |

Totals: 144 model calls (67 Claude Sonnet 5.5, 77 Claude Haiku 5.5) and 71 tool calls. Prompts sent by the harness
total 311,950 characters (204,501 to Sonnet, 107,449 to Haiku; field `prompt_chars` in `llm_log`).

## Events during the runs

These are behaviours of the agents, recorded in the run files, not changes to the protocol.

- Level 3: the Prague helper switched to `search_hotels_backup` after the planned failure without first reporting
  and waiting; its urgent report arrived at 39.97 s. The planner's instruction (49.83 s) arrived during the helper's
  last model call (46.86 to 53.70 s) and was never read. The Rome helper called `search_hotels` twice.
- Level 5: the planner cancelled farefinder at 38.41 s and airdeal at 43.34 s; both returned
  "[cancelled before finishing]".
- Level 5 timeline: `figures/L5.png` is titled "answer WRONG" because the timeline title applies the full-trip
  check. The comparison table applies the flights-only check and marks the run correct.

## Spend

Not recorded. The harness did not keep the cost field of the CLI's JSON output. The notebook estimates a full live
pass at about 150 CLI calls and 10 to 15 minutes.
