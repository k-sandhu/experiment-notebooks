# Notebook 41: networks written as text

Source: `notebooks/41-direct-weight-mlps` (README.md and data/), read-only.

## Message

Language models wrote all 6,570 weights of a small digit classifier as plain numbers, with no tools or training
run. The best network (GPT-6 Astra) labelled 1,645 of 1,797 test digits correctly (91.5%). But 6 of 13 first
replies gave no usable network at all, mostly because the list was cut short or miscounted. The open-weight
networks ran but scored near chance because one digit's score wins almost every image.

Reader: curious professionals on a phone or artifact page, reader-paced. Misconception targeted: "a model can't
write a working network without training", or the opposite, "they all can". The reader guesses first.

## Form and why

`predict-reveal` (primary form), built with `explainer-kit` as a 7-step stepper in `chalkboard` style, 380x400 viewBox.
The headline is a single number most readers would get wrong, so the reader commits a guess before seeing it.
I borrowed from `unit-story` for the reveal: each of the 1,797 test digits is a dot, and the dots are recoloured
using Astra's real per-item results. The predict-reveal skill has a sample storyboard for this notebook. I did
not reuse its counts. I re-read every number from the README and data, and the counts on screen follow the
current README (13 first requests, 10 networks scored in all, 11 submissions with no network).

## Steps

1. **Digits, typed as numbers.** The page shows four real 8x8 visible digits (0, 6, 1, 7) and the 0 written out
   as the model read it. That is one CSV line of 64 ink counts plus its label, wrapped by row on screen. Below it: "× 2,048 labelled digits".
2. **6,570 numbers to write.** A 64-64-32-10 network, with the numbers per layer (4,160 / 2,080 / 330), the
   real start of Astra's reply, and a counter that climbs to 6,570. A line says "no calculator · no code · no training run".
3. **Your guess.** The 1,797 test digits are dots. The reader drags a marker on a 0 to 1,797 scale, with
   random guessing (about 180) marked. Reveal stays disabled until the reader drags; a "Skip, just show me"
   button is there for readers who won't guess. On reveal the guess locks, the dots turn blue (right) or grey
   (wrong) in test order, a blue marker appears at 1,645, a bracket shows "off by N", and the caption puts the
   guess and the truth side by side. "Try again" resets the step. The demo guesses 1,000, and its caption says
   it is an example guess.
4. **Every first reply.** A chart of the 13 first requests on the same scale: 7 blue bars, then 6 rows marked
   "no usable network" with the reason in red. It has reference lines for guessing (about 180) and the
   nearest-sample lookup (1,750), and the reader's guess as an amber dashed line.
5. **A second try, numbered.** The same chart. Violet bars appear for the numbered retries: Opus 5.5 high
   1,580, Sonnet 5.5 1,214, Gemini 1,091. The other three rows change to their retry outcomes: Opus xhigh's
   continuation was refused, Haiku declined, and Nemotron got 3 provider timeouts. Ten networks ran in all,
   and 11 submissions gave none.
6. **Right idea, wrong count.** Sonnet 5.5's flat reply drawn line by line next to the layout the format
   requires. It has an extra line of 56 zeros (line 66) and a b2 line with 30 of 32 values, for 6,624
   numbers in all, so the reply is unusable. With numbered entries, the same design scored 1,214.
7. **It ran, but one digit wins.** GLM-5.3's predicted-digit histogram: 1,670 answers of "0" (178 of them
   right) and 127 of "3", against about 180 real images per digit. DeepSeek answered "1" 1,388 times and
   MiMo 1,546 times. Takeaway: "check the count, then the idea", with the caveat "one network per model,
   on 1998 data: not a ranking".

Colour legend, used the same way in every step: amber = your guess; blue = digits right; violet = right after a
numbered retry; red = no usable network; grey = wrong digits (labelled on screen).

## Source of every number

| On screen | Value | Source |
|---|---|---|
| Digits in the training sample | 2,048 | README §1; `data/dataset.npz` `visible` (2048 rows) |
| Test digits | 1,797 | README study summary; `data/study_summary.json` `n_test` |
| Parameters | 6,570; per layer 4,096+64, 2,048+32, 320+10 | README §2 tensor table |
| Four digits shown | official training rows 2136 (0), 541 (6), 1525 (1), 60 (7) | `data/dataset.npz` `visible` + `visible_indices`, first visible image of each label; matches line 8 of `data/visible_sample.csv` for the 0 |
| Ink counts 0 to 16 | | README §1 |
| Reply start `{"weights":[0,0,1,0,0,0,0,0,0,0,2,-1,0,0,…` | | `data/responses/astra/weights_output.json` |
| Random guessing about 180 | | README §5 ("about 180 expected from guessing") |
| Nearest-sample lookup 1,750 | | README study summary; `data/nearest_neighbour_baseline.json` |
| Astra 1,645 (91.5%), 152 mistakes | | README §5 table; `data/study_summary.json`; per-item dots from `data/responses/astra/predictions.npz` `test_pred` vs `dataset.npz` test labels (recomputed: 1,645 right, 152 wrong) |
| Fable 5.1 1,628; Sol 1,422; Muse Wonder 606; DeepSeek V4.1 Flash 379; MiMo-V2.6-Pro 335; GLM-5.3 194 | | README §5 table; `data/study_summary.json` results |
| First-request failures and reasons | Opus xhigh (reasoning used whole allowance), Opus high 6,378 values, Sonnet 6,624, Haiku zeros to the output cap, Gemini schema rejected, Nemotron output limit during reasoning | README §5 "no network" table; `study_summary.json` `failure_category` |
| Retries | Opus high numbered 1,580; Sonnet numbered 1,214; Gemini numbered 1,091; Opus continuation refusal; Haiku declined; Nemotron 3 provider errors | README §5 tables |
| 13 first requests, 12 models, 10 networks scored, 11 submissions without one | | README study summary; `study_summary.json` (`readable_submissions` 10, `unreadable_submissions` 11) |
| Sonnet flat-reply layout (line 66: 56 zeros; b2 30 of 32; 6,624) | | README §6 "Replies that failed the count" table |
| GLM predictions 1,670 "0", 127 "3"; 178 and 16 right | | README §6 collapse table (1,670, 127); per-class rights recomputed from `data/open_models/glm/predictions.npz` (178 + 16 = 194, matches README) |
| Real count about 180 per digit | test labels per digit 174 to 183 | `dataset.npz` test labels |
| DeepSeek "1" 1,388; MiMo "1" 1,546 | | README §6 table; recomputed from `data/open_models/*/predictions.npz` |
| 1998 data, one network per model | | README §8 limits |

No disagreements were found between the README and the data files for any number shown. One note: the
predict-reveal skill's built-in example storyboard for this notebook says "six models whose first reply gave no
usable network" and lists 90.6% as a second value. Both match the current README: 6 of 13 first requests, and
Fable 5.1 at 90.60%. The explainer also adds the numbered retries, which that storyboard predates.

## Simplifications

- The model names are short ("Opus 5.5 xhigh", "Nemotron 3.5"). Effort settings were not matched across
  models (README §8). The page doesn't explain this; the final caveat line and the "not a ranking" wording
  cover it.
- Gemini's three unusable recovery replies before its numbered reply are collapsed into "another try".
- Opus xhigh's second try was a continuation, not a numbered request, so the step 5 caption says "mostly with
  every number tagged".
- Step 6 draws each reply line as a bar whose length is proportional to the number of values on that line.

## What I checked

- `render_check.py`: PASS all checks at 360 px and 560 px, including reduced motion and the step 3 demo, after each round of fixes.
- I looked at both contact sheets and the individual frames at 360 px (steps 1, 3 demo, 5, 6, 7). Fixes from
  looking:
  - The idle demo and the check's demo ran twice, which left the readout at 314 while the caption said 1,000.
    The guess now locks after the reveal.
  - "Try again" wrapped to a second row on phones. Skip is now hidden after the reveal.
  - Red reasons crossed the reference lines. They now have a background halo.
  - The step 1 caption said "below"; it now says "above".
  - The bottom reference labels ran together. I spaced them out.
- Recording: `record.py` wrote explainer.mp4 (about 3 MB, 45 s) and explainer.gif (about 5 MB) in about 1
  minute. I checked a frame tile from the MP4 every 5 s.
- card.png is a 2x screenshot of step 5 (every model, with the retries) at 380 px CSS width (760 px image).
- Not checked: real touch dragging on a phone (the drag was tested only through the scripted demo), and
  screen-reader output beyond the kit's aria labels.
