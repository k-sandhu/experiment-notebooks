# Handoff timing replay: notes

## Message

A planner agent's finish time is its own model calls, plus its own searches, plus the time it sits waiting
for helpers. In the recorded runs the helpers did about the same work either way (19-25 s each). The
synchronous planner waited 66.3 s of its 120.2 s (55%). The async planner started all three helpers, searched
flights while they worked, never waited, and finished at 56.8 s. In a third run (level 3), the planner's one
instruction to the Prague helper arrived at 49.8 s, after the helper's last model call had started (46.9 s),
so the helper never read it. That was the only unread message in the 7 runs.

- Reader: someone who builds or reads about agent harnesses; sees it as an artifact page or a README link.
- Misconception it targets: "More helper agents in parallel means faster". Helpers only help if the planner
  keeps working instead of waiting; handing off and waiting was slower than one agent alone (82.1 s).

## Form

`system-replay` in data-replay mode: one `K.player` timeline (explainer-kit, blueprint style, 380 x 300 drawing),
pausable and scrubbable, with 9 chapters, an event log and a clock that states the time compression.
Reader-paced page (autoplays once, about 78 s), plus an MP4/GIF recording.

Fixed map: one lane per agent (planner, Lisbon, Rome, Prague helpers), x = real seconds on a 0-125 s axis
shared by both runs. Colours, kept throughout and listed in the legend: violet = model call, green = search
(tool), amber hatched = planner waiting, blue arrow = message to the planner (answer, progress, alert),
white arrow = handoff / instruction from the planner, red = the unread instruction. A hidden-state meter
under the lanes shows each planner's time ledger (model + searches + waiting) growing with the clock.

## Chapters (scenes)

| # | Title | Real time shown | What is on screen |
|---|---|---|---|
| 1 | Same trip, two ways | 0 s (hold) | Empty lanes for both runs; names the cast and the two methods |
| 2 | Hand off, then wait | 0-16.5 s (1 s = 4.5 s) | Sync hands Lisbon over at 5.6 s and starts a hatched wait; async starts helpers at 5.0, 10.5, 15.1 s |
| 3 | Work while they work | 16.5-44.2 s (1 s = 5 s) | Async searches flights from 19.3 s; answers arrive 25.3, 30.6, 34.5 s; sync's first wait ends 30.6 s (25.0 s), second starts 36.5 s |
| 4 | Async done at 56.8 s | 44.2-56.8 s (1 s = 4.5 s) | wait_all at 43.9 s finds all answers in; async done flag; sync still waiting for Rome |
| 5 | A third wait | 56.8-87.6 s (1 s = 5 s) | Sync waits 20.0 s for Prague; dashed line at 82.1 s = one agent alone; flights start 87.6 s |
| 6 | Sync done at 120.2 s | 87.6-120.2 s (1 s = 5 s) | Ledger: sync 120.2 s total, 66.3 s waiting (55%); async 56.8 s, 0 s waiting |
| 7 | Helpers report back | level 3 run, 0-41 s (1 s = 6.5 s) | Progress reports; Prague hotel search fails at 24.0 s (503), backup search 27.6 s, alert 40.0 s; zoom box 38-56 s |
| 8 | A reply too late | 41-68.8 s (1 s = 4 s) | Zoom: last model call began 46.9 s (bracket), instruction 49.8 s (red arrow), Prague answers 53.7 s, "never read"; done 68.8 s |
| 9 | Keep planners busy | all 7 runs | Bars of finish time per level, waiting hatched; 7 of 7 correct; one run each; level 5 flights only |

Each chapter holds 1.6-10 s at its end so the caption can be read; the clock reads "paused" during holds.

## Where every number comes from

All values are copied unchanged from `files/data.json` by `_build/make_data.py` into `const DATA` in the page,
and every on-screen number, caption number and log time is computed from DATA in the page script.

| On screen | Source in data.json | Computation |
|---|---|---|
| 120.2 s, 56.8 s, 68.8 s, 82.1 s finish times | `runs[L1/L2/L3/L0].wall_s` (120.21, 56.76, 68.77, 82.06) | 1 decimal |
| Bars on every lane | `runs[].spans` [agent, kind, start, end] | drawn as recorded, clipped at the clock |
| Waits 25.0 / 21.3 / 20.0 s | L1 spans kind=blocked on main (5.57-30.59, 36.46-57.73, 63.16-83.17) | end - start |
| 66.3 s waiting, 55% | sum of L1 blocked spans = 66.30 (= `main_blocked_s_from_spans`, = comparison.csv 66.3, 0.55) | sum / wall |
| Ledger "s so far / total" | main spans by kind | L1: 41.89 model + 12.02 search + 66.30 wait = 120.21; L2: 44.72 + 12.04 + 0 = 56.76 (checked in Python) |
| Handoff / spawn / answer times (5.6, 30.6, 36.5, 57.7, 63.2, 83.2; 5.0, 10.5, 15.1, 25.3, 30.6, 34.5) | `runs[].events` t | 1 decimal |
| Async flights from 19.3 s; wait_all 43.9 s | L2 first search_flights start 19.25; last search_flights end 43.94 (facts.md: wait_all at 43.9 s returns instantly; no blocked span is recorded) | |
| Sync flights at 87.6 s | L1 first main search_flights start 87.64 | |
| Helpers worked about 19-25 s each | sum of helper span lengths: L1 25.02, 21.27, 20.00; L2 20.24, 20.10, 19.38 | floor of min, round of max |
| Prague search failed 24.0 s (503) | L3 Prague search_hotels span end 23.97; "HTTP 503" from the alert text summarised in facts.md | |
| Backup search 27.6 s | L3 search_hotels_backup start 27.58 | |
| Alert 40.0 s, instruction 49.8 s, Prague answer 53.7 s | L3 events alert 39.97, instruction 49.83, result from #4 53.70 | |
| Last model call began 46.9 s | L3 Prague llm span 46.86-53.70, the last one starting before the instruction | |
| Only unread message in all 7 runs; "nothing told the planner"; answer still correct | facts.md (README) | text |
| Chapter 9 bars and labels | `comparison` rows: wall s, main blocked s, correct | waiting drawn as the hatched end of each bar (its position within the run is not shown) |
| 57-69 s for levels 2, 3, 4, 6 | comparison wall s 56.76, 68.77, 68.95, 65.23 | rounded min-max |

Wording that is not a measured number: "planner model", "helper model" (facts.md: Sonnet 5.5 planner, Haiku 5.5
helpers), the HTTP 503 label, and "the answer was still correct" (facts.md / comparison.csv correct = True).

Simplifications, stated here because the page does not show them: messages are recorded with one timestamp
(send = receive), so they are drawn as vertical arrows at that time with a short pulse, not as travelling
dots. Level 3 has a zero-length blocked span at 54.34 s on the planner; it has no width and is not drawn
(comparison.csv reports 0 s blocked). The level-1 handoff events have kind "spawn" in the data; the page calls them "handed off" as facts.md
does.

## What I checked

- `render_check.py` (explainer-kit) at 360 px and 560 px plus reduced motion (`_build/qa/`). Final run: no FAIL
  (no errors, no blank frames, no sideways scroll, no text outside the drawing, controls fixed). First runs
  failed on wrapping chapter titles that moved the controls at 360 px; titles were shortened to one line.
  Remaining WARNs are text_overlap between a caption and the 6th log line: the kit's log keeps 6 entries in a
  box that shows 5, and the hidden top line sits under the caption box edge. Looked at the frames: nothing
  visible overlaps.
- Looked at frames at the end of every chapter at 360 px and 400 px (`_build/frames/`, contact sheet
  `_build/frames/sheet360.png`): one idea per chapter visible, captions match what is drawn, no clipped text.
- Scrubbing: frames are a pure function of time (each view redraws everything from DATA and the clock);
  seeking backwards from the end to chapter 3 gave the same picture as seeking there directly.
- Sums recomputed in Python from data.json (ledger identity above; blocked 66.30 s; helper busy times).
- Caveats shown on screen in chapter 9: one recorded run per level, 7 of 7 answers correct (correctness
  cannot rank them), level 5 is a smaller task.

Not checked: the original notebook files (only data.json and facts.md were allowed); colour-blind
simulation of this specific page (the kit's fills were validated by the kit authors, and every colour is
paired with a label, arrow or hatch).

## Files

- `explainer.html`: the page (self-contained; only the IBM Plex Mono web font is loaded from Google Fonts).
- `explainer.mp4`, `explainer.gif`: recordings made with `record.py`.
- `_build/`: `make_data.py` (data copy), `scene.js` (scene source), `build.py`, `grab.py` (frame grabs), QA output.
