---
name: explorable-model
description: Build an explorable explanation - a live model the reader steers with one or two sliders or toggles while linked views show the outcome change - for questions where the answer depends on a choice or an assumption, such as a price, a threshold, a rate, a budget, an error cost, a break-even point or a tradeoff between options. Use when someone wants an interactive "what if" calculator that teaches, a break-even or crossover explainer, a sensitivity visual, or asks to let readers "play with the numbers", "see when it pays off" or "find where the answer flips", from data or a cost model.
---

# Explorable model

Some answers are not a number but a rule: "checking pays off when a mistake costs more than X", "stop early when the first two tries agree, unless success is rarer than Y". A table of scenarios
states the rule; an explorable lets the reader find it. When the reader drags a price and watches the
winner change, the threshold stops being a fact they were told and becomes something they discovered
(Bret Victor, "Explorable Explanations", 2011).

Build with `explainer-kit` (`scaffold.py --kind explorable`, which is a stepper with a slider row).

## Design the model before the picture

1. **Write the model as one pure function** `model(params) → outputs`, in plain JavaScript, at the top
   of the scene. Every number and every mark is computed from its output. If the drawing and the
   caption ever disagree, the model is not the single source.
2. **Separate measured inputs from assumptions.** Measured: counts and rates from the data (with the
   file they come from). Assumed: prices, costs of a mistake, volumes. The reader may move assumptions;
   measured inputs stay fixed unless the point is sensitivity to them, and then show their uncertainty.
3. **Choose one or two knobs.** The ones that flip the answer. Five sliders is a spreadsheet, not an
   explanation. Hide the rest as fixed values listed in a small note.
4. **Find the flip.** Solve for the threshold in code (break-even, crossover, where the best option
   changes). It becomes a labelled marker the reader can see coming as they drag.

## Layout: knob, outcome, and a concrete view

Use linked views so the reader sees both the rule and the things it is about:

- **Outcome chart** (top): outcome against the knob for every option, e.g. cost per item against price,
  one line per option. A vertical marker at the knob's current value; the winning line drawn thicker;
  the crossover marked with its value ("break-even 42 cents").
- **Concrete view** (middle): the items themselves at the current setting, e.g. 200 orders as dots
  coloured by where each one went, or a stacked bar of where the money goes. This answers "what does
  this mean for my 200 orders?"
- **The reader's units.** State the outcome the way the audience budgets it: dollars per month at a volume
  they can type in, hours per week, errors per thousand. A per-item cost in fractions of a cent, or a share on
  a log scale, is correct but makes a finance reader do arithmetic before they can decide.
- **Verdict line** (caption or a big number): "At 30 cents per review, checking every order by hand is
  cheapest." Update the words, not just the picture.
- **Knob** (action row, `K.slider` in `s.act`, set `actHeight: 76`): label with units, readable value,
  sensible step, a tick or note at the measured or typical value.

## Steps

1. *The decision* - the options and what each costs or risks, at one fixed sensible setting. No knob yet.
2. *What moves the answer* - show the knob moving by itself (`demo` sweeping the slider) while the lines
   and dots respond; pause at the flip and label it.
3. *Your turn* - the reader drags; the verdict updates live. Optionally a second knob or a toggle for an
   assumption (cost of a mistake).
4. *Where we really are* - jump to the measured or realistic setting and state the conclusion, with the
   caveat about the assumptions.

Every step with a slider has `demo()` that sweeps it and `idleDemo` so GIFs and passive readers see the
response.

## Make it responsive and readable

- Format each number once: one function turns the knob's value into text, and the slider readout, the
  verdict sentence and the chart label all call it. Two roundings of the same value ("14.1 cents" beside
  "At 14.0 cents") make readers distrust everything else.
- Recompute and redraw on every `input` event; keep it under 16 ms (no heavy work, no layout thrash).
- Move marks with short transitions (150 ms) or directly; long easing while dragging feels laggy.
- Use one axis per chart. Two measures of different units get two charts, not a dual axis.
- Log scale when the knob spans orders of magnitude (prices from 0.1 cent to 100 cents), and say "log scale".
- Label lines directly at their right end; keep a legend too when there are more than two.

## Example: when to stop repeating a task (illustrative numbers)

A team collects several attempts per task to train a model, and wants to stop after two attempts when
they agree. Knob: the model's success rate p on a task (0 to 1). Model: probability that two attempts
agree = p² + (1-p)²; probability that four attempts would have shown both outcomes = 1 - p⁴ - (1-p)⁴.
Outcome chart: "groups that would have taught something" with and without early stopping, against p.
Concrete view: 100 task groups as small rows of four dots, greyed when stopped early. Flip: the p at
which early stopping throws away more useful groups than it saves calls. Verdict line updates with p.

## Honesty

- Label assumed values as assumptions on screen, next to the control that changes them.
- Do not let the slider range suggest values the data rules out; mark the measured value.
- If the data has uncertainty (a small sample), draw the outcome as a band, or say the threshold is
  approximate and why.
