# Handoff timelines: notes

## Message

In the recorded runs, the sync handoff took 120.2 s because the planner waited 66.3 s (55%) for helpers, one at a time.
That made it slower than one agent working alone (82.1 s). The async spawn started all three helpers by 15 s and
searched flights while they worked, so it never waited and finished in 56.8 s. Separately, in the progress-report run
one planner instruction (sent at 49.8 s) reached the Prague helper after its last step had already begun (46.9 s).
That instruction was never read.

Reader: someone who opens the artifact page from the notebook README. They do not know the harness.
Misconception: "more agents in parallel is faster". The speed-up only appears when the planner does not wait for helpers.

## Form

A system replay (data replay with `K.player`, chalkboard style, 380 x 300). It runs in the reader's own time: Play/Pause,
a scrub bar, chapter dots with Next/Back, and an event log under the caption. Each `frame(t)` is a pure function of t,
so scrubbing backwards works. The two runs share one layout and one real-seconds clock (a stacked small multiple),
and every bar or arrow on screen is a recorded span or message.

## Chapters (7)

1. **Same trip, two ways.** Introduces the cast first: a planner and Lisbon, Rome and Prague helpers, in two panels
   (Sync handoff, Async spawn). Shows the time axis and a dashed "one agent alone: 82.1 s" reference line. Nothing moves yet.
2. **Hand off, or start all (5 to 19 s).** The sync planner hands Lisbon over and its lane turns to amber stripes
   labelled "waiting". The async planner starts all three helpers (5.0, 10.5 and 15.1 s), and blue arrows show the handoffs.
3. **Work while helpers work (19 to 56.8 s).** The async planner searches flights while its helpers' answers arrive at
   25, 31 and 35 s. Its "planner waited" counter stays at 0.0 s and it finishes at 56.8 s, marked with a finish line.
   Over the same stretch the sync counter climbs as its waits pile up.
4. **Waiting, one by one (56.8 to 120.2 s).** Sync gets Rome back at 57.7 s and Prague at 83.2 s, and only then
   searches flights. It finishes at 120.2 s, to the right of the 82.1 s single-agent line. The counter ends at 66.3 s,
   which is 55%.
5. **A helper hits an error.** Zooms into the progress-report run (16 to 58 s of 68.8 s; Lisbon and Rome are dimmed).
   Prague's hotel search is drawn in red with "✗ 503", followed by the backup search and an urgent report (red arrow) at 40.0 s.
6. **The reply nobody read.** Prague's last model call starts at 46.9 s (outlined). The planner's instruction is sent at
   49.8 s and waits as an envelope in Prague's inbox. When the helper answers at 53.7 s the envelope turns red:
   "✗ never read". Callouts give the three times. The caption says nobody told the planner and that there was no harm.
7. **All seven runs.** The wall-clock of each of the 7 recorded runs, split into the planner's model time, its search
   time and its waiting. Sync and async are highlighted. Footnotes say that race + cancel was a flights-only task, that
   there was one run per pattern, and that 7 of 7 answers were correct. This shows where the two featured runs sit
   and that correctness does not separate the patterns.

Time compression is shown in the clock readout: 8x speed in chapters 1 to 4, 4x speed in the zoom, and holds at key
moments. The scrub bar always shows recorded seconds.

## Where every number comes from

All numbers are computed in the page from `DATA`, a verbatim copy of `evals/handoff-timelines/files/data.json`
(which holds notebook 07's `data/runs/*.json` and `data/comparison.csv`). None are typed in by hand.

| On screen | Computation | Value |
|---|---|---|
| done 120.2 s / 56.8 s / one agent alone 82.1 s | `runs[].wall_s` for L1, L2, L0 | 120.21, 56.76, 82.06 |
| planner waited (live counter) | sum of `main` spans with kind=blocked, clipped at the current time | ends at 66.3 (L1), 0.0 (L2) |
| 55% | 66.30 / 120.21 | 0.5515 |
| waits of 25.0, 21.3, 20.0 s (log) | the three L1 blocked spans | 25.02, 21.27, 20.01 |
| helpers started by 15 s | L2 spawn event times | 5.03, 10.50, 15.13 |
| answers at 25, 31, 35 s | L2 result event times | 25.27, 30.60, 34.52 |
| Rome back 57.7 s, Prague 83.2 s, flights from 87.6 s | L1 result events; first L1 `search_flights` span | 57.73, 83.17, 87.64 |
| "collects 3 answers: no wait" at 43.9 s | facts.md: wait_all at 43.9 s returned at once (no blocked span in L2) | 43.94 |
| ✗ 503 at 20 to 24 s, backup at 27.6 s | L3 Prague `search_hotels` span (failed, per facts.md and the alert text) and `search_hotels_backup` span | 19.97 to 23.97, 27.58 |
| urgent report 40.0 s | L3 alert event | 39.97 |
| last step 46.9 s, answer 53.7 s | last L3 Prague llm span start; L3 Prague result event | 46.86, 53.70 |
| instruction 49.8 s, "use the backup data" | L3 instruction event (text paraphrased from "Proceed with the backup data…") | 49.83 |
| 16 to 58 s of 68.8 s | chosen zoom window; L3 `wall_s` | 68.77 |
| summary bars and values 82, 120, 57, 69, 69, 49, 65 s | per run: `main` llm + tool + blocked span sums; label is `wall_s` | sums match `wall_s` within 0.01 s for all 7 |
| waited 66 s (summary) | L1 `main` blocked sum | 66.30 |
| 7 of 7 answers correct | `runs[].correct` | all true |

Claims taken from facts.md, not from spans: each agent step is a fresh `claude -p` call; the instruction was never
read and nothing told the planner; no harm because the answer matched; the race task was flights only. The red colour
on the failed search span is an interpretation, supported by facts.md ("Prague hotel search fails ... 24 s") and the
alert text ("search_hotels failed ... HTTP 503").

Simplifications: messages are drawn as instant vertical arrows at their recorded time, animated over 0.45 s of
animation time. The zero-length L3 blocked span (54.34 to 54.34 s) is not drawn. Hotel names are left out.

## What I checked

- I recomputed every derived number in Python from data.json, separately from the page. Planner llm + tool + blocked
  equals wall_s for all 7 runs, the L1 waits are 25.02, 21.27 and 20.01, and 66.3/120.21 = 55.2%. The page also logs
  its own derived values to the console.
- I ran `render_check.py` at 360 and 560 px plus a reduced-motion pass. It found no console errors, no blank frames,
  no sideways scroll, no text outside the drawing, and the controls stay fixed. The first run failed `controls_moved`
  because two chapter titles wrapped; I shortened them. The remaining `text_overlap` WARNs pair the caption with the
  top log line, which is clipped out of view by the log box (overflow hidden), so they are harmless. The latest result
  is in `qa_check.txt`.
- I looked at the end frame of every chapter at 380 px (`qa_me/sheet.png`, `qa/sheet_w360.png`) and fixed four
  problems: the envelope label crossed the alert arrow (now on a background chip), "done" labels sat on the dashed
  line, the summary title repeated the chapter title, and one caption said "flights at 88 s", which was ambiguous
  (it now gives the Prague return at 83.2 s and then the flight search).
- Captions are 172 to 246 characters in source, and the longest fits its reserved height at 360 px.
- Not checked: screen-reader output beyond the aria labels the kit sets, and Safari or Firefox (Chromium only).

## Files

- `explainer.html`: the replay, one self-contained file. Only the Caveat font loads from Google Fonts; text falls
  back to a cursive font offline.
- `handoff_replay.mp4` (62.6 s, 1.9 MB) and `handoff_replay.gif` (3.8 MB): recordings of the full timeline made with
  `record.py`. I spot-checked frames at 20 s and 58 s (chapter 4 end and the summary).
- `scene.js`, `build.py`, `template.html`: the source (`python build.py` rebuilds explainer.html).
- `qa/`, `qa_me/`, `qa_check.txt`: frames, contact sheets and check output.
