# Craft: motion, layout, type and colour

Rules for making an explainer feel calm and read clearly, with the reason for each. Most come from
reviewing real explainers frame by frame on a phone; the sources are named where a rule rests on research.

## Motion

- **Animate change, not decoration.** Motion pulls the eye. Spend it on the thing that changes in this
  step: a request travelling, a bar growing, a dot changing group. Nothing else should move.
- **Draw in reading order.** Frame and labels first, connectors next, the moving part last. A reader who
  sees the arrow before the boxes it joins has to look back.
- **Stagger, do not dump.** Related elements appear 100-200 ms apart. Twenty elements appearing at once
  read as one block; appearing one by one, each gets a glance.
- **Pause before the punchline.** Leave 400-800 ms of stillness before the key change (the counter
  ticking, the dot turning red). The pause tells the reader "watch this".
- **Ease in and out.** `inOut` for things that move between places, `out` for things that arrive,
  `linear` only for clocks and progress bars that stand for elapsed time.
- **Speed.** Travelling dots: 300-700 ms per hop. Draw-in of a box: 500-800 ms. A whole step's reveal:
  2-4 s. Captions should be readable in the step's hold time (about 200 words per minute).
- **Keep wobble stable.** Hand-drawn shapes use fixed seeds so they do not shimmer between frames. Redraw
  a shape with the same seed when it must reappear.
- **Pulse sparingly.** One pulse ring per event. A pulsing element that never stops is noise; an element
  that is waiting can pulse every 1.5 s at most.
- **Object constancy.** When data regroups, the same item stays the same mark and moves; marks that
  appear or leave fade (Heer and Robertson 2007). Stage big transitions: move first, then recolour.
- **Give control.** Every step can be replayed; the timeline can be paused and scrubbed. Animation the
  reader controls is understood better than animation that runs past them (Tversky et al. 2002).
- **Time to read.** Autoplay holds each step at least as long as an average reader needs for its caption
  (about 230 ms a word plus a second), and the player pauses at the end of each chapter for the same
  reason and offers 0.5x / 1x / 2x. Do not turn these off for a reader-facing page; set `chapterHold: 0`
  only for a recording that has its own pacing.
- **Overlays.** A callout or tooltip must not cover the marks it explains or the rows the reader is
  comparing: place it in free space or beside the item. Accept taps while it animates (cancel and redraw)
  rather than ignoring them.

## Layout

- **Fixed frame.** The drawing has a fixed size; the caption reserves the tallest caption's height; the
  action row reserves its height. Back, the step dots and Next must sit in the same place on every step.
  A Next button that moves is the most common fault in reviewed explainers.
- **One focal area per step.** Put the thing that changes near the centre. Dim the rest rather than
  hiding it, so the reader keeps the map: shapes to about 30%, text to no less than 50%, so a dimmed label
  can still be read.
- **Labels on the marks.** Put names next to the things they name, not in a distant key (spatial
  contiguity, Mayer). The legend is for colour meanings only.
- **Margins.** 12 units inside the viewBox edge. Text anchored at `'end'` near the right edge must end by
  x = 368.
- **Phone first.** The drawing is about 310 px wide on a 360 px phone. Check that width before any other.
- **Ends cleanly.** When a game or simulation ends, every element shows a final state ("done for today",
  "round over"). Nothing left saying "working..." or "your turn...".

## Typography

- Handwritten font for headings and short labels only (2-5 words). Sans-serif for numbers and anything
  longer. Tabular figures for numbers that change (the kit sets them).
- Minimum 14 units in the drawing (axis ticks included), 15-16 for labels the reader must read, 18-26 for headings.
- Every term on screen is either everyday language or explained the first time it appears. A name like
  "No check" or "the reviewer" must say what it is ("expensive model on every invoice", "a stronger paid
  model that reviews the answer").
- No internal names on screen ("level 3", "L2_async", "cfg_b"). Use the reader's words for each run or option.
- Captions are HTML text at 13.5 px: one or two sentences, 220 characters at most, that say what to look
  at ("Watch the context bar...") rather than restating the title.
- Numbers on screen carry units and denominators: "412 rows", "3 of 40", "2.1 s", "USD 0.02 per call".

## Colour

- Decide the meanings in the storyboard and keep them for the whole piece. The kit's chalkboard default:
  amber = the human, violet = the model, green = a tool call or work in progress, blue = data or a result,
  red = an error or a cost. Change the mapping when the story needs it, but say it in the legend.
- Ink colours (pastels on dark styles) are for strokes and text. Data fills are stronger colours; use
  them for bars, dots and areas that tell categories apart, assigned in the order blue, amber, green,
  violet, red. In the built-in styles every pair of fills stays apart under simulated protan, deutan and
  tritan vision. Custom themes are only required to keep neighbours in that order apart, so
  `scripts/check_theme.py` lists any other pair that comes close; label such marks or add a shape.
- The chalkboard pastels fail a categorical-palette check as data colours (mint and blue are too close,
  all five are too light). That is why the kit has separate fills. Pastel strokes are fine because every
  shape also has a label.
- Never rely on colour alone. Pair it with a label, a position, a shape (✓ ✗) or a pattern.
- Grey is for context. Dimmed, past or irrelevant elements go to `faint` or 30% opacity.

## Interaction

- One obvious thing to do per hands-on step, named in the caption ("Tap Switch task a few times").
- Touch targets at least 36 x 36 units in the drawing (a transparent rect behind small marks) and 40 px
  for HTML buttons.
- Respond within 100 ms: a ring, a floating "+1", a counter change. Silence reads as broken.
- Handle early or wrong taps kindly ("still working", "pick a yellow one").
- Every hands-on step has a `demo()` and an idle trigger so the step still teaches if the reader only
  watches, and so a GIF shows it.
- Keep a score or summary at the end of games, in words, with the numbers ("You finished 4 tasks and your
  agents waited 31% of the time").

## Honesty on screen

- Recorded, simulated and illustrative values look the same, so label them in words where they appear.
- Compressed time is stated ("1 s here = 10 s of the run").
- Small samples show their range (see `unit-story`), not just a percentage.
- Simulations use a seeded random generator (`K.rng`) so every replay shows the same run, and say which
  real numbers they were tuned to.
