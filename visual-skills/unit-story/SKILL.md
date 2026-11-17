---
name: unit-story
description: Build an animated unit visualization where every item is its own mark - each test question, request, invoice, user or sample is a dot - and the dots move between arrangements (one pile, split by model, coloured by outcome, sorted) to tell a story about counts, composition and uncertainty. Includes showing small-sample uncertainty honestly with intervals and hypothetical outcome animations. Use when someone wants to visualize evaluation or benchmark results per item, compare models on a test set, show how many of N failed, explain why "0 out of N" or a small sample does not prove much, or make results tangible for a LinkedIn post, slide or README.
---

# Unit story

"The model failed 18% of the time" is abstract. Forty dots with seven of them red is a thing you can
see and count. Unit charts show the denominator, keep each item identifiable, and make
proportions concrete (natural frequencies are easier to reason with than percentages: Gigerenzer and
Hoffrage, 1995). Moving the same dots between arrangements lets one picture answer several questions
in sequence without the reader losing track of what a dot is.

Build with `explainer-kit` (`scaffold.py --kind stepper`) using `s.units` and `s.arrange`.

## The arc

1. *One dot is one item* - show a single item large: its input, its expected answer, what a model did.
   Then shrink it into a dot and let the rest of the set appear around it. The reader now knows what a
   dot means. Say the count ("Each dot is one of 120 questions").
2. *Split* - arrange the dots by group (model, method, category) into small waffles side by side, same
   cell positions in every group so groups are comparable.
3. *Colour by outcome* - recolour in place (correct, wrong, unreadable). Keep the unreadable or failed-
   format items a separate colour from wrong answers; they mean different things.
4. *Sort or regroup* - pull outcomes together within each group so the counts can be read, and write the
   count beside each group ("7 of 40").
5. *How sure can we be?* - for each group, the range of true rates consistent with this count (see below).
6. *What it means* - the decision or caveat, in words, with one highlighted dot as an example.

Give readers a way into individual items: tapping a dot shows a small card with that item's input and
outcome (`s.on` on the dot, a card in the dynamic layer). Pick two or three dots for the `demo()`.

## Layout

- Dot radius 3.5-5 units, gap 9-12 units. A 380-wide drawing holds about 30 dots per row.
- Waffle per group: fixed columns (5 or 10 make counting easy), fill row by row, groups in a row or
  column with their label and count on the same line.
- Same item, same place across groups when items are shared (question 17 is always the 17th cell), so
  the reader can compare groups item by item: a column of red across all models is a hard item.
- Large sets (over ~600 items): use smaller dots, or one dot per 10 items and say so on screen.
- Order of motion: stagger by item (`stagger` 3-8 ms) so the transition reads as a flow, and use the
  `order` field to move the interesting items last.

## Showing uncertainty from small samples

A count from a small sample is consistent with a range of true rates. Show it three ways, in this order:

1. **Words with the count**: "0 of 40 wrong" (never "0%" alone).
2. **The interval**: a horizontal rate axis (0-50% is often enough), one row per group, a dot at the
   observed rate and a bar for the 95% interval (`K.wilson(k, n)`). Zero failures in 40 still allows a
   true failure rate up to about 9%.
3. **Hypothetical outcomes** (HOPs; Hullman, Resnick and Adar, 2015): animate what other samples of the
   same size would look like if the true rate were a plausible value. Redraw the waffle every 600-900 ms
   with `K.rng`-seeded draws from that rate and keep a tally: "If the true rate were 5%, a set of 40
   would show zero failures in 13% of samples" (the chance of zero is (1 - p)^n). Let the reader pick
   the true rate with buttons or a slider. Seeing a clean sample come up again and again from a model
   that does fail is what moves the misconception.

Keep this calm: HOP animations flicker by nature, so use a slow cadence, a fade between draws, and a
pause button.

## Example storyboard (illustrative numbers)

A judge model compares two answers and must pick the better one; each test pair is shown in both
orders. 40 pairs, three judges.
1. One pair, large: question, two answers, which one is better and why. Shrinks to a dot.
2. 40 dots per judge, three waffles, same cell per pair.
3. Colour: picked the better answer in both orders (blue), in one order only (amber), in neither (red).
4. Count beside each judge: "33 of 40 both orders". The amber dots line up across judges on four pairs:
   those pairs are hard, not the judges.
5. Interval rows for "both orders" rate per judge; the intervals overlap, so this test cannot rank the
   top two.
6. Takeaway: show each pair in both orders; a judge that agrees with itself only one way is guessing.

## Honesty

- Unreadable or refused replies are their own colour and count, not merged into "wrong".
- When all groups are at the ceiling or the floor, say the test cannot separate them, and how many items
  did ("all three judges missed the same 2 of 40").
- If a dot stands for more than one item, say so in the legend.
- Simulated draws in HOPs are labelled "simulated" and use the stated true rate, not the observed one
  dressed up as truth.
