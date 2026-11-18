---
name: explainer-director
description: Plan an animated or interactive explainer before building it. Finds the one message, picks the form that teaches it best (step-by-step lesson, replay of a real system run, explorable what-if, every-item-is-a-dot chart, or guess-then-reveal), and writes a storyboard with one idea per step. Use this first whenever someone asks to visualize, animate, explain visually, make an interactive, a GIF, a LinkedIn visual, a Khan Academy style lesson, or "something engaging" from data, an experiment, a process, an agent or a system, even if they do not name a form. Then hand off to the matching skill (stepper-lesson, system-replay, explorable-model, unit-story, predict-reveal) and build with explainer-kit.
---

# Explainer director

A good explainer is decided before a line of code is written. Most weak visuals fail at the plan:
they show everything at once, animate things that do not change, or pick a chart because it is
familiar rather than because it answers the reader's question. This skill turns a request and its
material into a storyboard that a builder can follow. It is short on purpose. Spend the effort here.

## 1. Find the message

Write the takeaway as one plain sentence a newcomer could repeat to a colleague, with the number
that proves it. "In a simple model of one working day, a person who needs 1 minute to load a new
problem finishes about twice as many agent tasks as one who needs 15." (Label a modelled number as modelled.) If you cannot write this sentence, read the material
again; do not start drawing.

Then write down:
- **The reader.** What they already know, where they will see this (phone feed, GIF in a post, an
  artifact page, a slide), and how long they will give it. A LinkedIn reader gives 10 seconds before
  deciding; a lesson reader gives two minutes.
- **The misconception.** What would this reader believe before seeing it? The explainer exists to move
  them from that belief to the message. ("Zero violations means safe." "Deep focus is always best.")
- **The evidence.** Which numbers, items or events prove the message, and the file each comes from.
  Every number on screen must be traceable. Mark anything invented for teaching as illustrative, on
  screen, in the same place as the number.

## 2. Pick the form by what the reader must understand

| The reader must grasp... | Form | Skill | Typical length |
|---|---|---|---|
| How something works, one concept building on another | Step-by-step lesson with hands-on steps | `stepper-lesson` | 5-8 steps |
| What happened over time between several actors: who waited, what flowed where, what broke | Replay of a recorded or simulated run on a scrubbable timeline | `system-replay` | 3-6 chapters |
| How an outcome depends on a choice or an assumption: a price, a threshold, a rate | Live model the reader steers with one or two controls | `explorable-model` | 3-5 steps |
| How many items landed where, and how sure we can be with this many | Every item is a mark that moves between arrangements | `unit-story` | 4-6 steps |
| A number the reader would get wrong if asked | Reader commits a guess, then the data is revealed against it | `predict-reveal` | 3-5 steps |

### The destination decides how it plays

| Where it will be seen | Delivery | Why |
|---|---|---|
| A social feed post (LinkedIn, X), a GIF or MP4 | **Self-playing card**: 30-60 s, plays and loops by itself (`autoplay: 'loop'`), a bold one-line hook in the first frame, no tap needed to get the point; record it with `record.py` | Feed readers do not tap through steps; the first two seconds decide whether they stay |
| An artifact page, a README, a link people open | **Reader-paced**: Next, replay, hands-on steps | The reader chose to be there and will spend minutes |
| A slide or a talk | **Short loop or a few static frames** | The presenter is the pace |
| A chat reply (claude.ai widget) | Reader-paced, compact (3-6 steps) | Sits inline with text |

When the request names a feed ("for a LinkedIn post", "a visual for X"), the deliverable is a postable
card, not a tap-through page:

- **Fixed size.** One fixed-aspect drawing (4:5 portrait, for example a 400 x 500 viewBox, or 1:1) that
  never scrolls and never changes height. Each scene is a slide that would work as a still image in a
  carousel post. Use `--viewbox 400x500` and `autoplay: 'loop'`.
- **Legible when scaled down.** The card is shown about 360 px wide on a phone, so every label, tick and
  tag is at least 13 units in a 400-unit-wide card (about 12 px on screen). If a grid's labels would need
  to be smaller, show fewer columns or put the grid on its own slide. Tiny labels inside a postable card
  were the main complaint against the card that otherwise won.
- **Reads without tapping.** The hook and the number in the first frame; every point made by the scenes
  themselves; no part of the message behind a button. Optional controls go below the card and must
  change something in it, or be left out.
- **Clean pause points.** Hold each scene long enough to read (3-6 s) and make every held frame a finished
  slide, so a reader who pauses or a GIF frame never lands mid-transition.

A reader-paced version can be a second deliverable from the same scene code, but ship the card first.

Forms combine. The strongest lessons usually are a stepper whose middle steps borrow from the others:
one step where the reader plays the model, one where they guess, one that replays the real run. Pick the
primary form from the table, then add at most two borrowed moments.

Do not animate when nothing changes. If the message is one comparison of a few numbers, an annotated
static chart is clearer (use the `dataviz` skill if available). Animation helps when it shows change,
sequence or cause, and when the reader can control it (Tversky, Morrison and Betrancourt, 2002,
"Animation: can it facilitate?").

## 3. Storyboard: one idea per step

Write the storyboard as a numbered list before building. Each step gets:

```
N. <title, 2-5 words, handwritten heading>
   Idea: <the one thing this step adds>
   On screen: <what is drawn, in reveal order; what moves; what is dimmed>
   Reader does: <watch | tap X | drag Y | guess Z> and what changes when they do
   Caption: <one or two sentences, <= 220 characters, says what to look at>
   Evidence: <numbers shown and their source file, or "illustrative">
```

Rules that make storyboards work, with the reason for each:

1. **Name the parts first.** Step 1 draws the cast (actors, boxes, axes, legend) before anything
   moves. Readers cannot follow motion between things they have not met (pre-training principle,
   Mayer, *Multimedia Learning*).
2. **One new idea per step.** If a caption needs "and also", split the step. Learner-paced segments
   beat one long animation (segmenting principle).
3. **Ordinary case, then the complication.** Show the thing working before showing it fail. The failure
   only means something against the normal case.
4. **Keep the same object the same mark.** An invoice that is a dot in step 2 is the same dot in step 5,
   in the same colour. Moving marks keep their identity; new marks fade in (Heer and Robertson, 2007,
   "Animated transitions in statistical data graphics").
5. **One colour, one meaning, everywhere.** Decide the legend in the storyboard. Dim legend entries a
   step does not use.
6. **Ask before you tell, once.** A single guess or hands-on step makes the reader own the conclusion
   and remember it (Kim, Reinecke and Hullman, CHI 2017, "Explaining the gap"). More than two such
   steps turns a lesson into homework.
7. **End on what to do.** The last step is the decision, the habit or the rule the reader should take
   away, not a recap of numbers.
8. **Every frame readable when paused.** A screenshot of any step's final state must make sense with
   its caption. This is also what makes a good GIF.

## 4. Honesty checklist (do this in the storyboard, not after)

- Show counts with their denominator ("3 of 40 answers"), and for small samples show the range the
  data allows (`unit-story` explains how). A rate without its sample size overstates certainty.
- Separate measured from modelled from invented. Use words on screen: "recorded", "simulated from the
  recorded rates", "illustrative numbers".
- When time is compressed, say by how much ("1 s here = 10 s of the real run").
- If the evidence has a ceiling or floor (every method scores 100%), say the test cannot rank them.
- Show the control result when there is one. A clean score on a "should refuse" or "should block" test
  means little if the system also refuses ordinary work. When the source reports how the system did on
  normal cases (ordinary questions answered, legitimate requests allowed, valid invoices paid), put that
  number on screen next to the clean score, so a reader cannot take "0 broken rules" for "refused
  everything". A reviewer chose the other version for exactly this.
- Compute every derived number in code (percentages, chances such as 0.875^29, differences, ratios) and
  print the values you put on screen; do not do the arithmetic in your head or round twice. Check that a
  caption that names a value changes when the reader changes that value.
- Do not let the animation imply a cause the data does not show.
- End with the test's limits in plain words, not only the headline: how many items, how many runs per
  item, what the setup made easy or impossible, and any result at a ceiling or floor. Reviewers preferred the
  less flashy version twice because it named these limits and the flashier one did not.
- When one example carries the story (one week, one run, one invoice), show where it sits in the whole
  result before the end: the average and the spread across all cases, and any aggregate caveat the
  source states (for example, how often stated ranges actually held). A vivid single case read as typical
  is the most common way an engaging explainer misleads.

## 5. Hand off

Pick the form skill from the table and read it, then read `explainer-kit` for the engine, styles and
checks. Default style is `chalkboard` (dark, hand-drawn, pastel ink) unless the destination calls for
another: `paper` for warm light pages, `editorial` for data-dense pieces beside text, `blueprint` for
system diagrams. Default size is a 380-unit-wide drawing, which reads on a phone and records to a
square-ish GIF.

If the user names colours, fonts or a brand, build with a custom theme (`explainer-kit`,
`references/themes.md`) instead of a built-in style. If they did not, but the piece will carry a brand (a
company post, a product page, a client deck) and the user is there to answer, ask once whether they have
colours or fonts to use, alongside the storyboard. When working autonomously, or when the user has no
preference, use the built-in style without asking.

Deliver the storyboard to the user in a few lines when they are present, then build. When working
autonomously, keep the storyboard in your notes and build straight away.

## A worked storyboard: deep work versus parallel agents

This lesson was built with an earlier version of these skills and is the reference for tone and pacing.
Message: "With agents working in parallel, output depends on how fast you can load a new problem, not
on how long you can stay on one." Reader: knowledge workers on a phone. Misconception: "Protect deep focus
at all costs." Form: `stepper-lesson` with two hands-on steps and one simulated comparison.

1. *The old way: go deep* - a person, one task, a focus meter that fills the longer they stay. A minutes counter runs.
2. *Switching was expensive* - two tasks; the reader taps "Switch task" and watches focus drop to zero each time. Lost warm-up minutes add up on screen.
3. *A good day, back then* - a day timeline draws itself: three long blocks, two switches.
4. *Now: agents in parallel* - the person briefs three agents; each works, then turns yellow "waiting on you".
5. *Your turn: keep them moving* - a 30-second game: tap yellow agents to review them. Score: tasks done, switches, % of time agents waited.
6. *What gets rewarded now* - two simulated people, 15-minute and 1-minute switch time, same agents and day. The fast switcher finishes more. Labelled as a simple model.
7. *Getting faster at switching* - three habits the reader toggles; switch time and tasks per day update. Labelled illustrative.

What made it work: every step adds one idea; the two games make the reader feel the cost before the
numbers state it; the legend dims colours a step does not use; the controls never move; the last step
is about what to do.
