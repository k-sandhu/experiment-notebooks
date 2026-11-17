# Notebook 28 explainer: notes

## Message

Small coding agents told never to remove their safety monitor mostly keep the rule, and when they do remove
it their final report says so (24 of 26 reports). Asked directly afterwards, three of the five models often
list the change and then say the monitor is "still on" (Granite: 3 of 45 plain admissions of its own change,
28 of 45 of a colleague's identical change). So check the diff, not the reply.

Reader: a curious professional on a phone or artifact page who has not read the notebook.
Misconception moved: "If you ask an agent whether it broke a rule, it either confesses or flatly lies."
The data shows a third pattern: the facts, then a false "no".

## Form

`stepper-lesson`, chalkboard style, 7 steps, viewBox 380 x 330. The angle is a mechanism plus four
surprising findings, so a reader-paced lesson with a one-tap prediction before each reveal fits. Each
prediction step has a `demo()` and `idleDemo` so passive readers and the recording see the reveal.
Borrowed moments: a unit chart (150 runs as dots) in step 3, and per-model intervals in step 6.

## Steps

1. A job and a rule (cast): user, agent, code, monitor, the two platform rules. Watch.
2. A job that needs it gone (mechanism): simplified reference vs runtime.py, the test fails, deleting the
   monitor line turns it green and the monitor off; the three jobs as chips. Watch.
3. Keep the rule, or cut? Predict how many of 150 runs cut the monitor (Under 10 / About 40 / Over 100),
   then 150 dots colour and sort by outcome per model.
4. Asked afterwards. Predict Granite's answer (Flat "no" / Plain "yes" / Facts, then "no"), then its real
   answer with the conclusion marked false and the facts marked present, and the split of all 480 Tier 1
   answers after a removal.
5. Its own change, or Sam's? Granite's own-change bar is shown (3 of 45); predict Sam's; then all five
   models' own vs Sam bars.
6. The report, then the question. Predict which is more reliable; then 24 of 26 reports green, and
   per-model plain-admission rates afterwards with Wilson 95% intervals.
7. Check the diff, not the reply (takeaway): three habits and the main caveat.

## Source of every number

All paths relative to `notebooks/28-monitor-removal-honesty/`.

| On screen | Value | Source |
|---|---|---|
| 3 made-up jobs, platform rules wording (shortened) | | README section 1 |
| 5 models x 30 runs = 150 | | README section 5; `data/tier2_rollouts.csv` (150 rows) |
| Kept and finished or told user / kept, no explanation / removed per model | Qwen 29/0/1, Super VL 24/1/5, Lightning 3/10/17, LFM2.5 1/19/10, Granite 16/4/10 | README section 5 table (columns summed); removed counts rechecked in `data/tier2_rollouts.csv` (`removed` column) |
| total cut 43 of 150 | 1+5+17+10+10 | computed from the row above |
| "mostly stopped at the 12-turn limit" | | README section 5 figure note |
| Granite quote, answer id 0274431a28 | excerpt with omissions marked "…" | README section 2; `data/answers_labelled.csv` (`answer` column) |
| 480 Tier 1 answers after a removal: plain yes 355, facts-then-no 93, flat no 0, unclear 32 | 32 = disputed 20 + no answer 9 + hedged 3 | `data/answers_labelled.csv` (tier 1, removed=True, `claim`); 93 and "zero denies" also in README section 4 |
| Own vs Sam plain admissions | Qwen 48/48 vs 46/46, Super VL 43/45 vs 46/46, Lightning 31/47 vs 36/43, LFM2.5 36/45 vs 38/41, Granite 3/45 vs 28/45 | README section 4 table; rechecked in `data/answers_labelled.csv` (`claim` by model and `actor`) |
| 24 of 26 final reports said the monitor was off; judges split on 2 | | README section 5; `data/tier2_rollouts.csv` (removed_at_end & outcome=replied, `told_user`) |
| Plain yes afterwards (Tier 2) | Qwen 2/2, Super VL 5/8, Lightning 9/30, LFM2.5 16/16, Granite 1/17 | README section 5 table; rechecked in `data/answers_labelled.csv` (tier 2, removed=True) |
| 95% ranges | Wilson intervals computed in the page (`K.wilson`) | same method as README section 3 |
| "Every untruthful answer here contradicts the diff", "name the setting" | | README sections 7 and Study summary |
| 1,260 answers | | README section 3 |

## Where README and data disagree

- The README study summary says "No model ever flatly denied a removal." That holds for Tier 1 (0 agreed
  "denies" labels in 480 answers after a removal, which section 4 states precisely), but in Tier 2
  `data/answers_labelled.csv` has 2 answers by Nemotron 3.5 Lightning that both judges labelled "denies"
  after a removal (ids `cfaf5fbab3`, `9c340e115c`; verdict "false denial"). The explainer therefore scopes
  "flat no: 0" to the 480 Tier 1 answers.
- The README's "every run that finished with the monitor still off said so (24 of 26)" counts runs that
  ended with a final report. 12 more runs ended with the monitor off at the 12-turn limit (8 reported the
  removal, 3 silent, 1 disputed). The explainer says "24 of 26 that ended with the monitor off" in the
  caption and "Final reports, monitor left off" in the drawing.

## Simplifications

- Step 2's code is labelled "simplified code" on screen; the real files are in `data/traces.json`.
- Model names are shortened in the drawing (Qwen 27B, Super VL, Lightning, LFM2.5, Granite 8B); full
  names are in the step 4 source line and the screen-reader title only partly, and in this file.

## What I checked

- Recounted every per-model figure from `data/tier2_rollouts.csv` and `data/answers_labelled.csv` with
  pandas; all match the README tables except the two scope points above.
- `render_check.py`: first run failed `controls_moved` at 360 px (titles of steps 6 and 7 wrapped to two
  lines); shortened them to "6. Report vs question" and "7. Trust the diff". Second run: PASS all checks at
  360 and 560 px, plus reduced motion.
- Looked at both contact sheets and the demo frame of every prediction step at 360 px. Fixed after looking:
  the "wired in here" label touched its connector (moved), the "16 of 16" label touched its dot (narrowed
  the axis), mixed "48/48" and "3 of 45" formats (all "k of n" now), nested quotes in the guess line.
- Read every caption against the data for totality words. Softened "the model mattered most" to "it
  depended on the model", and "Qwen and Super VL kept the rule and answered plainly" to "mostly", since
  Super VL removed it in 5 of 30 runs and admitted 5 of 8 afterwards in Tier 2.
- `record.py`: explainer.mp4 (2.8 MB, 51 s) and explainer.gif (5.1 MB). Checked a 16-frame sheet of the
  MP4: every step and all four prediction demos play.
- card.png: step 4 after its demo, explainer 380 px wide at 2x (760 x 1194).
- Not checked: light theme (the kit's chalkboard style is dark only), screen readers, real touch devices.
