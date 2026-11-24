# Notebook 29 (theory of mind): explainer notes

## Message

Every model knows that a person who missed a change still holds the old belief. The weaker models also give
that old belief to someone who saw, read or heard the change: on twin B (the person took the change in),
Granite 4.2 8B is right on 51% of belief and behaviour answers and GPT-6 Luna on 73%. In twin A every model is at least 90%.
Below the top models, stating a belief correctly does not mean the model uses it.

- Reader: curious professionals on a phone or an artifact page, who have not read the notebook.
- Misconception: "A model that answers 'where does she think the key is?' correctly can keep track of what people know."

## Form and why

`stepper-lesson` (chalkboard style, 380 x 420 drawing, 7 steps), reader-paced for an artifact page. The idea
needs building up: the reader first has to understand twins and pair scoring, so a step-by-step lesson fits better than one chart.
Borrowed moments: one predict-and-reveal step (the reader answers a real pair) and one pick-one step (family
picker). Each has a `demo()` and an idle demo.

Legend (fixed across steps): amber = twin A (missed the change), green = twin B (took it in), blue = stating
the belief (explicit), violet = using it (applied), red = wrong. Model rows keep the README's order in steps 4 to 6.

## Steps

1. **The key moved** (illustrative, labelled on screen): Priya, the drawer, the shelf; the key moves while she is out; her belief bubble says drawer.
2. **One detail flips it** (illustrative): twin A and twin B side by side; the rule of thumb "whoever left has the old idea" gets twin B wrong, so it scores 0 on the pair.
3. **Your turn: Yara's gate** (hands-on, real pair `device-S01`): an event strip of the board, the phone and Yara in each twin. The reader taps the gate she walks to in each twin. The reveal gives the answers (Gate 5 and Gate 3), the reader's pair score, and how the 10 models did on this exact pair.
4. **The errors go one way**: twin A vs twin B accuracy per model (dumbbell); green squares slide left from the amber circles.
5. **Family by family** (hands-on): tap one of 8 family cards; the twin A and twin B detail and each model's explicit (circle) and applied (square) pair accuracy update, with a one-sentence finding per family in the caption.
6. **When the model must tell**: the orchestrator items. For each model, stating what the helper agent knows vs writing the right follow-up (or NONE).
7. **What to test**: two habits (test the told twin; test the action) and where the test stops (ceiling, template stories).

## Source of every number

All files are in `notebooks/29-theory-of-mind/`. "Computed" means I recomputed it from `data/scores.csv` using
the README's definition of pair accuracy (flip questions, answered right in both twins, averaged per pair then over
pairs; unreadable answers count as wrong). Every computed value matches the README to two decimals.

| On screen | Value | Source |
|---|---|---|
| Step 3 story: gate 5 to 3 at 10:00; times 9:00, 10:00, 10:15, 10:30; café, office, Wi-Fi rule | | README "One pair from start to finish" |
| Step 3: 9 of 10 models got both twins; Granite sent twin-A Yara to Gate 3 | behaviour `plan` question | computed from scores.csv rows for `device-S01` (Granite chose Gate 3 in twin A; all others right in both twins) |
| Step 4: 270 answers per twin per model (90 for Muse Wonder) | | computed (classic, uptake, device, machine families; explicit and behaviour flip questions); README "Which twin goes wrong" gives 270 |
| Step 4: twin A / twin B accuracy | Opus, Wonder, Sol 1.00/1.00; DeepSeek 1.00/0.98; Qwen 1.00/0.97; Spark 1.00/0.99; Nemotron 1.00/0.91; Haiku 0.97/0.88; Luna 0.90/0.73; Granite 0.91/0.51 | computed; README gives twin B 0.51, 0.73, 0.88, 0.91 and "at least 90% accurate in twin A" |
| Step 4: Of Granite's 157 wrong answers, 130 gave the old belief | | README "Which twin goes wrong"; computed: 25 twin-A + 132 twin-B non-correct answers, 130 of the twin-B ones chose the twin-A answer |
| Step 5: explicit and applied pair accuracy per family and model | 80 values | computed; identical to README `figures/family_heatmap.png` |
| Step 5 captions: Granite 0.70 / 0.32 classic, all 30 twin-B classic stories | | heat map; README "Which twin goes wrong" |
| Step 5: facing-away pairs, DeepSeek and Qwen 0.67, Nemotron 0.17 (explicit, 6 pairs) | | README "Family by family"; computed level (explicit) and pair count (6) from scores.csv subtype `facing away` |
| Step 5: Granite 0.27 and Luna 0.53 applied on device; Granite 0.07 and Luna 0.90 explicit on partial; Luna 0.97 / 0.31 on machine | | heat map / computed |
| Step 5: Haiku 0.37 and Spark 0.82 nested; strict subset 0.81 and 1.00 | | README "The reading assumption in the nested family" table |
| Step 5: Luna flipped left and right in 14 of 16 stories | | README "Which twin goes wrong" and error case spatial-S00 |
| Step 5: Granite routing 0.90 as water tanks, 0.52 as people | | README "People against cameras, copies and water tanks" (not recomputed) |
| Step 6: follow-up pairs right in both twins | all 1.00 except Luna 0.27, Granite 0.10 | computed from `free` level rows; README orchestrator table |
| Step 6: explicit pair accuracy, machine family | Haiku 0.87, Luna 0.97, Granite 0.77, others 1.00 | computed; README orchestrator table |
| Step 6: "Granite sent updates nobody needed" | 27 of 30 twins needing NONE got a message (3 of 30 right) | computed; README "sent a message in 90% of the twins where none was needed" |
| Step 7: Opus missed 1 of 3,084; Sol 6; Muse Wonder 2 of 1,034 | | README "Study summary" and results table |
| Step 7: 10 models, 240 pairs, 8 families, Muse Wonder 80 pairs (quota) | | README "Study summary" |

### Where the README and the data differ

No number shown on screen differs. One count I did not use differs slightly: the README says GPT-6 Luna made 96
wrong answers in the twin analysis and Nemotron 24, while counting every non-correct answer in scores.csv gives
99 and 25. The difference is probably unreadable answers handled differently. Neither count is on screen.

## What I checked

- `render_check.py`: PASS all checks at 360 px and 560 px, including reduced motion (two FAILs for an axis note
  running off the right edge and two overlap WARNs for the A/B letters were fixed first).
- Looked at both contact sheets and at full-size frames for steps 3 (demo), 4, 5 (demo) and 6 at 360 px. The caption
  matches the drawing in each step. I fixed overlapping event labels in step 3 ("reads the app" and "app not opened") and a tight card label in step 5.
- Read every caption and on-screen sentence against the sources above, especially "all", "only", "every" and
  "at least" (Luna's twin A is exactly 0.900, so "at least 90%" holds).
- No em dashes in the page. Illustrative steps 1 and 2 say so on screen.
- Recording: `record.py` took about 1 min 40 s. explainer.mp4 is 2.7 MB and explainer.gif 5.5 MB. I checked a tile of frames
  sampled every 8 s: each step and both demos appear.
- card.png: step 4 at 380 CSS px wide, 2x (760 x 1366).
- Not checked: keyboard-only play-through by hand, and screen-reader output beyond the kit's aria labels.
