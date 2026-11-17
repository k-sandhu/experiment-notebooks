# Handoff timelines: notes

## Message

A planner agent finishes when its own work is done plus the time it spends waiting. In the recorded
sync handoff run the planner did 53.9 s of its own work and waited 66.3 s for helpers, one city at a
time (120.2 s). In the async spawn run it did 56.8 s of work and never waited, because the helpers ran
while it searched flights (56.8 s). Helpers only cost time when the planner waits for them.

- Reader: someone who has heard of "subagents" but not read notebook 07; opens a link and gives it a
  minute or two.
- Misconception: "Handing work to helpers makes it faster" (sync handoff was the only pattern slower
  than a single agent: 120 s vs 82 s), and "a message sent to an agent gets read".
- Form: `system-replay`, data-replay mode (`K.player`), chalkboard style, reader-paced with a scrub
  bar, chapter dots and an event log generated from the recorded events. Delivered as one HTML file.

## Structure (six chapters on one scrubbable timeline, about 68 s if left to play)

1. **Meet the cast** (static). Two empty panels, one per run, sharing one time axis (0-125 s). Lanes:
   Planner, Lisbon, Rome, Prague. Models named (Claude Sonnet 5.5 planner, Claude Haiku 5.5 helpers).
2. **Sync: hand off, wait** (recorded run L1 at 10x). Model calls (violet) and searches
   (green) fill in; the planner's waiting appears as hatched amber bars with their lengths (25.0, 21.3,
   20.0 s); a live "planner waited" counter climbs to 66.3 s (55%). Message arrows at recorded times.
3. **Async: start all, go on** (recorded run L2 at 10x, same scale, sync panel dimmed).
   Three spawns, then the planner's flight searches run while helpers work; answers arrive at
   25.3, 30.6, 34.5 s; counter stays at 0.0 s; finishes at 56.8 s.
4. **Who waited for whom** (both complete). Each panel shows "working + waiting = finish":
   53.9 + 66.3 = 120.2 s and 56.8 + 0.0 = 56.8 s. A dashed green line in the sync panel marks where
   the async run had already finished.
5. **The reply nobody read** (recorded run L3 at 5x, axis 0-70 s). Prague's hotel search fails at
   24.0 s (red outline, ✗), Prague sends an urgent report at 40.0 s, the planner replies at 49.8 s,
   but Prague's last model call had begun at 46.9 s (dashed red box); ✗ "never read", no one told
   the planner; Prague answers at 53.7 s and the trip total was still correct.
6. **All seven runs** (comparison.csv). Bars for all seven runs: planner working (grey) plus
   planner waiting (hatched amber), with the finish time at the end of each bar. Limits in words: all 7
   answers correct (ceiling), one run each, race run is flights only. Caption ends on what to do.

## Where every number comes from

All values are computed in the page from `DATA`, which `src/build.py` copies verbatim from
`evals/handoff-timelines/files/data.json` (runs L1, L2, L3 with all spans and events, plus the
`comparison` rows). Nothing is typed in by hand except captions, which I checked against the data:

| On screen | Source | Value |
|---|---|---|
| Bars, arrows, lane order | `runs[L1/L2/L3].spans`, `.events` (start/end, t) | as recorded |
| City names on lanes | spawn event text ("Research Lisbon...", "City: Rome...") | #2 Lisbon, #3 Rome, #4 Prague |
| Sync waits 25.0, 21.3, 20.0 s; total 66.3 s (55%) | L1 spans kind=blocked on main | 25.02, 21.27, 20.01; sum 66.30; 66.30/120.21 |
| Sync planner back to own work at 83 s | L1 last blocked span end | 83.17 |
| Sync own work 53.9 s, finish 120.2 s | L1 main non-blocked spans; `wall_s` | 53.91; 120.21 |
| Async answers at 25, 31, 35 s | L2 result events | 25.27, 30.60, 34.52 |
| Async own work 56.8 s, waiting 0.0 s, finish 56.8 s | L2 main spans; `wall_s` | 56.76; 0; 56.76 |
| "before it asks for them" | facts.md (wait_all at 43.9 s returns instantly) | 43.9 s > 34.5 s |
| Prague search fails 24.0 s (HTTP 503) | L3 Prague `search_hotels` span end; alert text | 23.97 |
| Urgent report 40.0 s | L3 alert event | 39.97 |
| Planner reply 49.8 s | L3 instruction event | 49.83 |
| Prague's last model call began 46.9 s, answer at 53.7 s | L3 last llm span on #4; result event | 46.86-53.70; 53.70 |
| "No one told the planner", trip still correct | facts.md (README); L3 `correct` | true |
| Seven-run bars and their waiting parts | `comparison` wall s, main blocked s | 82.06, 120.21, 56.76, 68.77, 68.95, 65.23, 49.27; blocked 66.3, 15.73, 3.18 |
| "All 7 answers were correct" | `comparison` correct | 7 of 7 True |
| Models | facts.md Setup | Sonnet 5.5 planner, Haiku 5.5 helpers |

Bar end labels in chapter 6 are rounded to whole seconds (82, 120, 57, 69, 69, 65, 49).

Time compression is stated in the clock readout ("10×" for chapters 2-3, "5×" for chapter 5) and in
chapter 5's caption. Messages are instantaneous in the record; the dot that runs down each arrow is a
visual cue lasting 1.2 s of run time, not a measured delivery delay.

Things deliberately left out: L3 has a zero-length blocked span on main at 54.34 s (dropped, it is
0 s); the race run's figure title bug ("answer WRONG") from the notebook; the per-call cost (not
recorded).

## Honesty choices

- The lost message is in a different run (progress + redirect) from the sync/async pair; the chapter
  heading says "A third run" so the reader does not attach it to the async run.
- Chapter 6 shows where the two vivid runs sit among all seven, and names the limits: one run per
  pattern, all answers correct so correctness cannot separate them, race run not comparable.
- "Planner waiting" counts only the planner, as the notebook does; helper waits are not drawn as
  waiting (there are none in L1-L3 spans).

## Build

`src/scene.js` is the scene; `src/build.py` inlines the data and splices it into the scaffolded page
(`explainer-kit/scripts/scaffold.py --kind player --style chalkboard`). The page needs no network except
the Caveat web font (falls back to a cursive system font offline).

## What I checked

- Every on-screen number recomputed in Python from data.json (table above): sync waits 25.02/21.27/20.01,
  sum 66.30, own work 53.91, 55%; async own work 56.76, 0 waiting; async answers 25.27/30.60/34.52;
  L3 fail end 23.97, alert 39.97, reply 49.83, Prague last call 46.86-53.70.
- `render_check.py` at 360 px and 560 px plus a reduced-motion pass: 0 FAIL after fixes. Fixed along
  the way: a colour lookup before the style loaded (page error), chapter titles that wrapped to two
  lines and a per-chapter legend that changed the page height (controls moved), seven-run footnotes
  too long for a phone (text outside), a dashed reference line crossing value labels, and a finish
  marker crossing the sync summary text.
- Remaining WARN (text_overlap, caption vs log): the log keeps 6 lines but its box shows 5, so the
  oldest line sits clipped (overflow hidden) above the box; it is not visible in any frame I looked at.
- Looked at the contact sheets for both widths and at frames of every chapter (start, middle, end):
  each caption matches what is on screen; scrubbing back and forth redraws correctly because `frame(t)`
  is pure (the check seeks to each chapter out of order).
- Recorded `handoff-timelines.mp4` and `.gif` with `record.py` and checked frames from each chapter of
  the MP4.
- Not checked: real phone hardware, screen readers beyond the built-in aria labels, and offline font
  fallback appearance.
