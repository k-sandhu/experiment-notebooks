---
name: predict-reveal
description: Build a "guess first, then see the data" interactive - the reader draws a line, drags a bar, places a dot or picks an option to commit to a prediction, then the real data animates in against their guess with the gap explained, followed by how models or methods did. Use when a result is surprising or counterintuitive, when you want readers to remember a number, for forecasting and time series explainers ("draw what you think happens next"), quiz-like engagement for social posts, or when someone asks for something more engaging than a chart about a single key finding.
---

# Predict, then reveal

People remember a number better when they guessed it first, and they notice the gap between what they
expected and what happened (Kim, Reinecke and Hullman, CHI 2017; the New York Times' "You Draw It"
pieces). The guess turns a chart into a question the reader cares about. Use this form for one or two
key numbers, not for every number in a study.

Build with `explainer-kit` (`scaffold.py --kind stepper`).

## The arc

1. *Set the scene* - what the quantity is, its units, and the context the reader needs to guess sensibly
   (the history of a series, the size of the test, what chance would score). Keep it to one step.
2. *Your guess* - the reader commits. The Reveal button stays disabled until they do, with a "skip, just
   show me" link for people who will not guess.
3. *Reveal* - the real value animates in over their guess. Then words: "You guessed 60%. The real figure
   is 34%." Mark the gap with a bracket and its size.
4. *How others did* (optional) - models, methods, or the average reader if you have it, against the same
   truth, in the same picture.
5. *Why* - one step that explains the gap: the mechanism or the base rate that made the result surprising.

## Guess inputs

Pick the one that matches the quantity:

| Quantity | Input | Build |
|---|---|---|
| A path over time (a forecast, a trend) | **Draw your line** across the hidden part of a chart | Transparent rect over the hidden region with `s.drag`; snap each pointer x to a time bin and store the y; draw the guess as a polyline through filled bins; fill gaps by linear interpolation; enable Reveal when 70% of bins are filled. |
| One number (a rate, a count, a price) | **Drag a bar** or a marker on a scale | Handle with `s.drag` constrained to one axis; show the value as text while dragging. |
| Which is bigger / which won | **Pick an option** | Cards with `s.on`; the chosen card stays outlined after reveal. |
| A position in a distribution | **Place a dot** on a strip | Tap to place; a second tap moves it. |

Draw-your-line details that matter: show the visible history in full ink and the hidden region as a
shaded band labelled "your guess here"; start the guess at the last visible point so the line connects;
give the reader a "start over" button; use the real data's scale and units so the guess is comparable.

## The reveal

- Animate the true values drawing in from the guess's start (`s.drawIn` on the true path, or bars
  growing), 900-1500 ms, then pause before the words.
- Lock the guess when the reveal starts (disable the drag, keep a "try again" that resets both). A guess
  that can still be adjusted after the truth is visible is no longer a prediction.
- Score the guess in the units of the data (mean absolute difference, "you were off by 12%"), not a
  made-up points system.
- Comparisons after the reveal use the same axes. Each extra line gets a direct label at its end; dim the
  reader's guess slightly but keep it visible.
- If some methods are close to each other, say whether the difference is real (sample size, intervals)
  before ranking them.

## Demo and recording

`demo()` performs a plausible guess: for a line, programmatically set bins along a reasonable but wrong
path (for example, repeating the last visible stretch) and press Reveal. Label it in the caption as an
example guess when the step is shown in a GIF ("Example guess shown; try your own").

## Example storyboard: model-written digit classifiers (from this repository's notebook 41)

Question: language models wrote every weight of a small digit-recognition network as plain numbers,
with no tools. How many of 1,797 test digits did the networks get right?
1. The task: an 8 x 8 handwritten digit, a tiny network, 6,570 numbers written by a model as text.
2. Guess: drag a bar for "share of digits the best model's network got right" (chance is 10%).
3. Reveal: best first network 91.5% (1,645 of 1,797). Gap to the reader's guess in words.
4. Others: 90.6%, 79.1%, 33.7%, and six models whose first reply gave no usable network, shown as
   empty bars labelled "no usable network" rather than zero.
5. Why it is surprising: the models had no calculator; the numbers came from reasoning about the data in text.

## Honesty

- The guess must never change the data. Store it separately and draw it in a different style (dashed,
  the reader's colour).
- If the "truth" is itself an estimate, show its uncertainty in the reveal.
- If the reveal uses one example (one week, one item), end by showing how that example compares with the
  full result, including any caveat the source gives about the methods' stated ranges or reliability.
- Do not tune the setup to make readers guess wrong. Give them the context a fair guess needs.
