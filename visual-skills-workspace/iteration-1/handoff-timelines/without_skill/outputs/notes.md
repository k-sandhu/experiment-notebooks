# Handoff timelines: notes

## Message

Handing work to helpers only saves time if the planner keeps working while they run. In the sync handoff run the planner waited 25.0, 21.3 and 20.0 s (66.3 s, 55% of the run) for one helper at a time and finished at 120.2 s, slower than one agent alone (82.1 s). In the async spawn run the same three helpers ran at the same time as the planner's own flight searches, the planner never waited, and it finished at 56.8 s. Messages are read only when an agent starts its next model call, so the planner's instruction to the Prague helper (49.8 s), sent after that helper's last call had begun (46.9 s), was never read.

## Form

One self-contained HTML page (`explainer.html`, no network needed; system fonts, no libraries). It is a step-through animated replay: a swimlane timeline (one lane per agent) drawn from the recorded spans and messages, with a playhead that sweeps the recorded seconds at 10x (5x and 20x selectable). Controls: play/pause, restart, a scrubber, clickable dots under the axis that jump to each captioned moment, Back/Next and arrow keys between scenes. Each lane shows a live status ("model call", "searching flights", "waiting for Rome helper", "finished"), and the lane the planner is waiting on is highlighted, so "who waits for whom" is visible at every moment. Hover any bar or arrow for its exact times and the (truncated) message text. Light and dark themes; with reduced motion the scenes open at their end state. On narrow screens the chart scrolls sideways inside its box (page width stays 390 px at phone size).

`explainer.mp4` (39 s, 12 fps) and `explainer.gif` (760 px wide, 8 fps) record scenes 2 to 5 from the page.

## Scenes

1. The setup: the task, the cast (planner Sonnet 5.5, helpers Haiku 5.5), and the single-agent run (L0) replayed as the time to beat, 82.1 s.
2. Sync handoff (L1, 0 to 120.2 s): three hatched waiting bars on the planner lane, labelled "waited 25.0 s for Lisbon" and so on; flights only start at 87.6 s. Live chips: planner waiting so far, share of time waiting (ends at 66.3 s, 55%). Dashed line marks 82.1 s.
3. Async spawn (L2, 0 to 56.8 s), with the finished L1 run faded above on the same axis: helpers start at 5.0, 10.5, 15.1 s, answers arrive at 25.3, 30.6, 34.5 s while the planner searches flights; chip "helpers working at once" reaches 3 of 3; planner waiting stays 0.0 s.
4. Where the time went: stacked bars per run of planner model time + planner searches + planner waiting, which add up to the wall-clock (L0 51.9 + 30.1 = 82.1; L1 41.9 + 12.0 + 66.3 = 120.2; L2 44.7 + 12.0 = 56.8), with a dashed outline for all agents' model time summed (52.0, 90.1, 86.4 s).
5. The late message (L3, axis 0 to 70 s): Prague hotel search fails at 24.0 s, backup search 27.6 to 32.6 s, urgent report at 40.0 s, last model call starts 46.9 s (outlined, "input fixed at 46.9 s"), instruction at 49.8 s, helper answers and stops at 53.7 s; envelope marked "never read". Final answer 68.8 s, still correct.
6. What it shows: two lessons, a table of all 7 patterns (seconds, planner waiting), and the caveats.

## Where every number comes from

All from the two input files; nothing typed in by hand for the timelines.

- Bars, arrows, playhead times, lane statuses and the live chips: computed in the page from `runs[].spans` and `runs[].events` of `data.json` (L0 to L3), embedded verbatim by a build script (only change: the replacement character `�` in two L2 message texts, a garbled euro sign, is shown as "EUR"; those texts appear only in hover tooltips).
- Wall-clock times (82.06, 120.21, 56.76, 68.77): `runs[].wall_s`, shown rounded to 0.1 s.
- Waits 25.0, 21.3, 20.0, total 66.3 s: L1 blocked spans 5.57 to 30.59, 36.46 to 57.73, 63.16 to 83.17; matches `main_blocked_s_from_spans` 66.3 and comparison.csv 66.30 / 55%.
- Scene 4 segments: sums of the planner's (`agent: main`) llm, tool and blocked spans per run. All agents' model time: comparison `LLM s (summed)` (51.95, 90.13, 86.41). Agent and model-call counts: `agents` length and `calls.llm`.
- "63.5 s sooner" = 120.21 - 56.76 = 63.45; "25.3 s sooner than one agent" = 82.06 - 56.76 = 25.30; "2.9 s longer" = (44.72 + 12.04) - (41.89 + 12.02) = 2.85.
- L3 times: Prague `search_hotels` span 19.97 to 23.97 (the failure; the HTTP 503 itself comes from the alert text and facts.md, the spans have no error flag, so the build marks that one span as failed by its start time), `search_hotels_backup` 27.58 to 32.59, alert event 39.97, last llm span of city_researcher#4 46.86 to 53.70, instruction event 49.83, result event 53.70. "9.9 s after the report" = 49.83 - 39.97. Quoted instruction text is from the event's `text`.
- Scene 6 table: `comparison` rows (wall s, main blocked s, main blocked %). "Median model call 4.5 s, range 3.1 to 9.6 s": recomputed from all 144 llm spans (median 4.46, min 3.10, max 9.59), as in facts.md. "Rome helper waited 10.8 s": L4 blocked span of city_researcher#3, 32.35 to 43.14. "Only unread message in the 7 runs", "all 7 correct", "one run per level", "tools simulated": facts.md.
- City names for helpers (#2 Lisbon, #3 Rome, #4 Prague): from the spawn/handoff message texts in each run.

## What I checked

- Planner time decomposition from spans: own model time + own searches + waiting equals wall_s to 0.01 s for every run (L0 82.06, L1 120.21, L2 56.76, L3 68.77; L4 off by 0.01).
- Every captioned moment (34 captions across scenes 1, 2, 3, 5) is matched by script to a span boundary or event time in the right run, within 0.005 s.
- Rendered every scene in headless Chromium (light and dark) at end states and mid-play times, read the screenshots, and fixed what I saw: a clipped "= 120.2 s" label, wrong "messages 10 of 6" chip (see below), legend items that did not apply to a scene. No console errors. At 390 px width the page has no horizontal scroll.
- Watched extracted frames of the GIF; the first palette shifted the red and purple legend colours, so the GIF was re-encoded with a full 256-colour palette.

## Choices and open points

- Messages count: the L3 run has 10 message events (3 task starts, 2 progress, 1 alert, 3 answers, 1 instruction), but comparison.csv says 6 messages; its definition is not given in the inputs. The page shows the event count without a total and does not use the 6.
- facts.md says wait_all in L2 happens at 43.9 s; the spans only show that the last flight search ends at 43.94 and that there is no blocked span. The caption says only what the spans show: the answers were already in at 43.9 s and collecting them cost 0 s of waiting.
- "Never read" follows facts.md/README: the instruction arrived during the helper's last model call and the helper made no later call. The data has no explicit read flag.
- The facts.md wording "search fails 24 s" and "alert 40.0 s" match the span end 23.97 and event 39.97 after rounding.
- Speeds: replay at 10x by default, so the 120 s run plays in 12 s. Times on screen are always recorded seconds.
