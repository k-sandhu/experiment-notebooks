# handoff-timelines: facts (notebook 07, subagent-handoff-harness)

Source: notebooks/07-subagent-handoff-harness (README.md, data/comparison.csv, data/runs/L0..L6*.json). Numbers below were checked against data.json (wall_s, LLM calls and main-blocked seconds from spans match comparison.csv).

## Question (README "The question")
When a planner agent splits a three-city trip among helper agents, how does each way of coordinating them compare with one agent doing everything, in time to a correct answer, number of model calls and time the planner spends waiting? Do messages between agents reach the agent that needs them in time?

## Setup
Task: plan a May trip Toronto -> Lisbon -> Rome -> Prague -> Toronto, 2 nights per city, 2 travellers; cheapest flights, cheapest hotel rated 4.0+ but prefer a central one if within EUR 10/night. Correct total EUR 3,316 (level 5 is flights only: EUR 2,654). Tools are simulated with fixed delays (flights 3 s, hotels 4 s, backup hotels 5 s, weather 2 s). Planner = Claude Sonnet 5.5, helpers = Claude Haiku 5.5, each agent step is one `claude -p` call. One recorded run per level: a demonstration, not a benchmark (README).

## The 7 coordination patterns (README section 3)
- L0 single agent: one agent does every search itself. Baseline.
- L1 sync handoff: planner hands each city to a helper and waits for it before the next (actions: handoff). Then searches flights.
- L2 async spawn: planner starts all three helpers at once, searches flights meanwhile, collects answers afterwards (spawn, wait, wait_all).
- L3 progress + redirect: helpers send progress reports; Prague hotel search fails once (HTTP 503); planner can send instructions.
- L4 child asks parent: planner is told not to pass on the central-hotel preference, so the Rome helper must ask (ask_parent).
- L5 race + cancel: three helpers search the same flights via providers taking 2, 6, 14 s per search; first answer wins, planner cancels the others (wait_any, cancel). Smaller task, flights only, not comparable on time.
- L6 nested: each city gets a coordinator that starts its own hotel searcher and weather searcher (10 agents).

## Definitions
- Wall-clock = seconds from start to planner's final answer.
- "Main blocked" = time the planner (agent `main`) spent waiting, doing nothing, for a helper (hatched grey bars, spans kind=blocked). Blocked % = blocked / wall-clock. Helper waits are not counted.
- Span kinds: llm (a model call), tool (a simulated search), blocked.

## Headline (data/comparison.csv)
| Level | Wall s | Agents | LLM calls | Tool calls | Main blocked s (%) | Messages |
|---|---|---|---|---|---|---|
| 0 single | 82.06 | 1 | 11 | 10 | 0 (0%) | 0 |
| 1 sync handoff | 120.21 | 4 | 17 | 10 | 66.30 (55%) | 3 |
| 2 async spawn | 56.76 | 4 | 18 | 10 | 0 (0%) | 3 |
| 3 progress+redirect | 68.77 | 4 | 25 | 12 | 0 (0%) | 6 |
| 4 child asks parent | 68.95 | 4 | 21 | 10 | 0 (0%) | 5 |
| 5 race+cancel | 49.27 | 4 | 17 | 9 | 15.73 (32%) | 3 |
| 6 nested | 65.23 | 10 | 35 | 10 | 3.18 (5%) | 9 |
All 7 answers correct (ceiling: correctness does not separate levels). Only L1 was slower than one agent (120 s vs 82 s). Levels 2,3,4,6 finished in 57-69 s while making 18-35 calls instead of 11. Totals: 144 model calls, 71 tool calls.
Why: wall-clock = planner's own model time + own searches + blocked time (to within 0.1 s). Helpers only matter if the planner waits.

## Example items / stories (stable IDs = run file + agent id)
- L1 (L1_sync_handoff): three long blocked bars on main, 25.0, 21.3, 20.0 s waiting for helpers; flights only start at ~83 s.
- L2 (L2_async_spawn): helper answers arrive at 25, 31, 35 s while planner searches flights; wait_all at 43.9 s returns instantly. Never blocked.
- L3 (L3_progress_and_redirect): city_researcher#4 (Prague) search fails 24 s, helper switches to backup, urgent report at 40.0 s; planner sends instruction at ~49.8-50 s; helper's last model call began 46.9 s, so the instruction was never read. This is the one late/unread message in the 7 runs (README says nothing told the planner). No harm since the answer matched.
- L4 (L4_child_asks_parent): Rome helper (city_researcher#3) asks at 32.4 s, blocked 10.8 s, reply 43.1 s (Termini Inn, EUR 104, within EUR 10 of Via Appia Lodge EUR 98); planner never blocked.
- L5 (L5_race_and_cancel): skyscan wins at 34.0 s, planner blocked 15.7 s; cancels at 38 s and 43 s; finish 49.3 s. Figure title "answer WRONG" is a figure bug (applies full-trip check), answer is correct (EUR 2,654).
- L6 (L6_nested): Rome coordinator ran its two searchers one after the other, finishing last at 52.1 s; planner blocked 3.2 s. Answer included weather lows/rainfall no tool returned.

## Caveats (README sections 10, summary)
- One recorded run per level; second run could differ; differences of a few seconds may not repeat.
- Each step is a new `claude -p` process, median 4.5 s per call (3.1-9.6 s).
- Tools simulated; arrangement set by instructions, planner never chose between patterns.
- Blocked share counts only the planner: L4 shows 0% though the Rome helper was blocked 10.8 s; L6 shows 5% though coordinators were blocked 6.6, 17.0, 7.4 s.
- Cost of calls not recorded. No analysis plan recorded before runs.
- Discrepancy note: README text rounds (82 s, 120 s, 57 s); comparison.csv has 82.058, 120.211, 56.761.
