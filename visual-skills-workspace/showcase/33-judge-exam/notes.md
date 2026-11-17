# Notebook 33, judge exam: build notes

Source folder: `notebooks/judges/33-judge-exam/` (README.md, data/). All paths below are relative to it.

## Message

When code decides which of two answers is better, the four strong judge models picked it in 95% to 99.6% of
240 pairs (both answer orders), the five cheaper ones in 59% to 81%. The strong judges' remaining misses sit almost
entirely on exact word counts, and the cheaper judges' "right" answers often just followed the answer order.
No pair beat all nine judges. The ranking among Opus, Sonnet and Sol is not resolvable, and the exam is mostly
one-edit pairs, so it says little about answers that differ everywhere.

Reader: curious professional on a phone or an artifact page, has not read the notebook.
Misconception moved: "A judge that is right 70% of the time is 70% good" (amber dots show many of those right
answers came from picking the same slot both times), and "a few points apart means a ranking".

## Form and why

`unit-story` (explainer-kit stepper, chalkboard, 380 x 448). The question is "how many of 240 landed where, per
judge, and how sure are we", which is what the unit form is for. Every pair is a dot; the same pair keeps the same
cell in all nine grids, so a hard pair shows up as a vertical pattern across judges and the families form bands.
One hands-on moment (tap a dot in the hard-pairs stack), with a demo for passive viewers and the recording.

## Steps

1. One pair, one dot: test-code-000 (`gap >= 8` fails 2 of 64 tests, `gap > 8` passes all 64); the dot joins 240 in four family bands.
2. Every judge, asked twice: the nine verdicts on code-000 in both orders; defines the four colours (Granite picked the second slot twice, so amber).
3. Nine judges, 240 pairs: the pile splits into nine waffles, then colours; "right in both orders" count per judge.
4. Misses cluster by task: toggle (auto, with buttons) between the instructions band (strong judges' misses) and the calculations band (cheaper judges right in one order only).
5. The hardest pairs: the 2,160 judge-dots merge into 240 pair-dots stacked by how many judges were right both times; violet = word-count pair; tap a dot for a card. Demo opens instructions-008, code-041, code-022.
6. How sure can we be?: accuracy per judge over 480 verdicts with the README's 95% bootstrap intervals; Opus, Sonnet, Sol boxed as unrankable; Muse vs Opus paired difference.
7. The catch: one-edit pairs: only the 13 natural code pairs stay bright; each judge's accuracy on them.
8. What to do with a judge: ask in both orders, let code count, strong judges for small diffs.

## Where every number comes from

| On screen | Value | Source |
|---|---|---|
| Per-pair outcome colours (all dots, steps 2-5, 7) | computed per item and judge | `data/judgments.csv` (`correct`, `unreadable_type`, two orders per pair); script below |
| Family of each pair, natural vs planted | | `data/exam_v1.jsonl` (`family`, `error_source`) |
| Card notes (tests failed, word count vs target, distractor type) | | `data/exam_v1.jsonl` (`tags.subtlety`, `rules`) |
| 240 pairs, 4 families of 60, 64 hidden tests | | README "The question", "The exam" |
| code-000: `gap >= 8` fails 2 of 64, `gap > 8` passes all 64; B is better | | README "One pair from start to finish" |
| code-000 verdicts (8 right both orders, Granite right once) | | `data/judgments.csv` item test-code-000 |
| Right in both orders: Muse 238, Opus 224, Sonnet 222, Sol 221, Haiku 188, DeepSeek 142, Luna 118, Decisions 101, Granite 55 (of 240) | computed from PAIRS | matches README results table and `data/summary.csv` `both_orders_correct` |
| Opus and Sonnet: every non-blue dot is in instructions; Sol 15 of 19 (4 in code) | computed from PAIRS | `data/judgments.csv`; consistent with `data/family_summary.csv` |
| "about 720 words", "one word over or under" | | README "Where judges go wrong" |
| Luna 60/60, Decisions 58/60, Granite 59/60 calculation pairs right in one order only | computed | `data/judgments.csv` (Granite's 60th is wrong in both orders) |
| Histogram columns 2..9: 1, 15, 30, 61, 23, 23, 45, 42 pairs; none at 0 or 1 | computed | `data/judgments.csv`; README "No pair defeated every judge" |
| instructions-008: worse message 722 words, rule 723; only Muse and Opus right both times | | `data/exam_v1.jsonl` tags, `data/judgments.csv` |
| Accuracy and 95% interval per judge (99.6, 95.8, 95.0, 95.0, 81.0, 75.6, 71.5, 69.2, 59.4) | | `data/summary.csv` (`accuracy`, `ci_low`, `ci_high`), README results table |
| Muse vs Opus +3.8 points (1.9 to 5.8) | | README "Which judges pick the better answer" |
| 227 of 240 planted, 13 natural code pairs | | README "The exam" table |
| Natural-pair accuracy: Muse 96, Opus 100, Sonnet 100, Sol 85, Haiku 54, DeepSeek 65, Luna 42, Decisions 65, Granite 27 (% of 26) | | `data/code_error_source_summary.csv` rows `natural`; README "The exam" (Muse's 96% is only in the CSV) |
| "95% to 99.6%" (step 8) | | README study summary |

The per-pair table was built with `extract.py` (scratchpad, not delivered): it groups `judgments.csv` by item and
judge and classifies the two orders as right-both / right-once / wrong-both / any-unreadable.

## Disagreements and choices to know about

- The angle asked for "hard pairs that trip every judge". The data has none: README says no pair defeated every
  judge, and the computed minimum is 2 of 9 judges right in both orders (instructions-008). The explainer says
  "No pair beat all nine" and shows the hardest end instead.
- Haiku's 73 blocked replies are labelled `transport_error` in `judgments.csv`; the README describes them as usage
  filter refusals returned as CLI errors. I show them as "no readable reply" (grey), which matches both.
- A dot counts as grey if either of its two replies was unreadable, even when the other was right (Haiku 4, Muse 1,
  Sonnet 1, Decisions 1 pairs). That keeps format failures apart from wrong answers, as the README does.
- The waffle counts are pairs right in both orders (of 240); step 6 shows the README's headline accuracy over 480
  single verdicts. The caption says which is which.

## What I checked

- Every on-screen count computed in the page from PAIRS was cross-checked in Python against the README table
  (both-orders counts 238/224/222/221/188/142/118/101/55 match exactly).
- `render_check.py` at 360 and 560 px plus reduced motion. The first run gave 4 text-overlap WARNs (step 5 "no pair
  beat / all nine" line spacing, step 7 "Granite 8B" against "27% on 13"); fixed. The second run reported PASS on all checks.
- Looked at the 360 px contact sheet and full-size frames of steps 1, 5 (demo with card open), 6 and 7. After that
  I made the uncoloured dots light parchment (#c9c2b2), so they no longer look like the grey "no readable reply"
  dots, turned on the outcome legend in step 5 (the card uses those colours) and shortened the step 7 labels.
- `record.py`: explainer.mp4 (74 s, 7.5 MB). The recorder's GIF was 13.0 MB, so I rebuilt explainer.gif from the
  MP4 with ffmpeg (400 px wide, 10 fps, 96 colours): 8.3 MB. I checked frames from every step in the MP4
  (`qa_rec/strip.png`, `qa_rec/strip2.png`), including the step 4 toggle and the step 5 demo opening code-041 and code-022.
- card.png: step 3 (nine coloured waffles) at a 380 px viewport, 2x. The explainer element is 348 CSS px wide
  inside the body padding, so the image is 696 x 1382.
- Not checked: real touch devices, screen-reader reading order.
- Known quirk: the 50% "coin flip" line in step 6 is drawn solid, not dashed, because the draw-in animation
  overrides the dash pattern. The label still marks it.
