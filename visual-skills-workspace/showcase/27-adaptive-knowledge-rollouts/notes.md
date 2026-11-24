# Notebook 27: stop after two agreeing tries?

## Message

Stopping after two agreeing tries saves attempts, but in a model where every try at a task succeeds with the
same rate it collects fewer mixed groups at every rate (21.9 against 16.7 per 100 attempts at 50%). It wins
only when about 71 to 75% of tasks always give the same result, and then by at most 14%. Measured on Sol at
equal tokens, the two rules tied, 4 mixed groups each: the tasks decided the yield.

Reader: a curious professional on a phone or artifact page who has not read the notebook.
Misconception: "Stopping early on agreeing tries frees budget, so it must find more useful groups."

## Form and why

`explorable-model` (explainer-kit stepper with sliders, chalkboard style, 380 x 400 drawing). The answer
depends on an assumption (the success rate, and how many tasks never change), so the reader moves it and
watches both yields and 100 attempts' worth of groups change. The last step anchors on the measured run.

## Steps

1. Which groups teach: three real Sol groups with leave-one-out scores (✗✓✓✓ gives −1, +1/3, +1/3, +1/3;
   all-fail and all-success give zeros).
2. Two ways to collect: real groups on token6r-16 (always 4: ✗✓✗✗; stop rule: ✗✗ stopped) and token6r-03
   (stop rule: ✗✓ then ✗✗, mixed). Shows the saving and the risk.
3. Same rate on every task (slider: success rate). Curves of mixed groups per 100 attempts for both rules,
   a dot view of 100 attempts per rule, stopped pairs and how many would have turned mixed, live verdict.
   Tick marks Sol's measured 27%.
4. Mix in fixed tasks (sliders: rate on the other tasks, share of tasks that always give the same result).
   Curves against the share; the crossing point is computed and labelled (71% at a 50% rate).
5. What Sol really did: all 24 Sol groups at equal tokens as dots (✓, ✗, ? for budget cut-offs), 4 and 4 mixed,
   6 stopped pairs all on two failures, 4 extra tasks with 0 of 6, and the 111 of 111 ceiling on easier sets.
   Caption ends on the decision: find tasks the model sometimes fails before tuning a stopping rule.

## Model (steps 3 and 4, labelled "model, not measured" on screen)

Each try succeeds independently with rate p; a share e of tasks always gives the same result.
Always 4: 25 groups per 100 attempts, mixed = 25(1−e)(1 − p⁴ − (1−p)⁴).
Stop rule: tries per group = 2e + (1−e)(2 + 4p(1−p)); only groups whose first pair disagrees end mixed.
Crossing share e* = 1 − 2/M + 1/(2p(1−p)), M = 1 − p⁴ − (1−p)⁴: 71.4% at p = 0.5, 74.8% at p = 0.02.
Largest advantage of stopping, as e → 1 at p = 0.5: 4p(1−p)/M = 1.143, i.e. 14%. These are my derivations
from the README's description; the model reproduces the README's two published points.

## Source of every number

| On screen | Value | Source |
|---|---|---|
| Mixed groups per 100 attempts at p = 0.5 | 21.9 and 16.7 | README section 4 (21.875, 16.667; figure probe_tradeoff.png); reproduced by `model()` |
| Leave-one-out scores | −1, +1/3 | README "Teaching a model" and section 2 worked example |
| Step 1 groups | token6r-01 [0,1,1,1], token6r-12 [0,0,0,0] | `data/frontier_v6/groups.csv` (uniform Sol, blocks 0 and 2) |
| Step 1 group | cal-04 [1,1,1,1] | `data/groups.csv`, group `1eb3f7c53370febc9e27-0` (office tasks, uniform Sol) |
| Step 2 groups | token6r-16 uniform [0,1,0,0], adaptive [0,0]; token6r-03 adaptive [0,1,0,0] | `data/frontier_v6/groups.csv` (`3514ff3294564eeacf4a-0`, `0397fdb08bf7c69a9cba-0`, `17b4cde2c3f445661a6d-1`); README section 9 "Stopping after two failures" |
| Sol 27% tick | 16 of 60 known | README section 6 table; `data/frontier_v6/summary.csv` (11 + 5 successes, 30 + 30 known) |
| Step 5 dots, 24 groups | rewards per group | `data/frontier_v6/groups.csv`, Sol rows in file order |
| 4 and 4 mixed; 10 and 14 tasks reached; 6 stopped | | `data/frontier_v6/summary.csv` (mixed_groups, tasks_reached, abandoned); README section 8 |
| 4 extra tasks, 0 successes in 6 | token6r-10, -11, -14, -15 | README section 8; checked in `data/frontier_v6/episodes.csv` (0/1, 0/2, 0/2, 0/1) |
| 111 of 111 | 70 + 12 + 29 | README section 6 and study summary |
| "24M tokens per rule" | 24,000,000 | README study summary; `summary.csv` token_budget |

README and data agree on every number used. One note: the stop-rule row in step 5 shows two groups [0, ?]
(a failure then a cut-off). `groups.csv` marks them `unknown_or_budget`, not `abandon_unanimous_probe`; they are incomplete
and count neither as stopped nor as mixed, matching summary.csv (6 stopped).

## What I checked

- `render_check.py`: PASS all checks at 360 px and 560 px and with reduced motion (first run failed on
  controls moving: step 4's title wrapped and two sliders needed more than the reserved row; fixed by
  shortening the title and raising actHeight to 128).
- Looked at both contact sheets and full-size frames of steps 2 to 5, plus a manual frame at a 20% rate and
  88% fixed tasks (stopping ahead, 2.7 vs 2.6) to check the crossing label and the 47-column dot row fit.
- Recorded explainer.mp4 and explainer.gif (about 42 s, about 1 minute to record) and looked at one frame
  per step.
- Known minor issue: while dragging, the value labels beside the marker can touch the curves near the edges
  or the crossing circle. The same values appear in the row labels and verdict, so nothing is lost.
- Not checked: screen-reader output beyond the kit's aria labels; real touch dragging on a phone.

card.png is step 3 (same rate on every task, at 50%), 2x at 380 CSS px wide.
