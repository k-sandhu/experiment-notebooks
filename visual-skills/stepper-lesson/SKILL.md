---
name: stepper-lesson
description: Build a Khan Academy style step-by-step animated lesson that teaches one idea per step, with a Next button, short captions, and one or two steps the reader plays (tap, toggle, mini-game). Use when someone wants to teach how something works or why something changed to a newcomer - a concept, a mechanism, a rule, a workflow, a security trick, a statistics idea - as an interactive explainer, a "lesson", a walkthrough, or a GIF for social media. Pairs with explainer-director (plan) and explainer-kit (engine and checks).
---

# Stepper lesson

A stepper lesson is a short sequence of scenes. Each scene adds one idea, draws itself in, and waits
for the reader to press Next. It works because the reader sets the pace (segmenting), meets the parts
before they move (pre-training), and does something with their hands at the moment the idea needs to be
felt rather than read. It is the right form when the reader needs to understand a mechanism and leave
with a rule.

Build it with `explainer-kit` (`scaffold.py --kind stepper`). Read the kit's `references/api.md` first.

## Shape of a lesson

Five to eight steps. Use these step types, roughly in this order:

| Type | Purpose | Example caption (illustrative) |
|---|---|---|
| Cast | Draw the parts and name them. Nothing fails yet. | "A browser asks a cache first; only a miss goes on to the server." |
| Mechanism | Show the ordinary case working, slowly. | "Watch one request: the cache has the page, so the answer comes back in 5 ms." |
| Complication | Show the case that breaks, against the ordinary one. | "This page changed an hour ago, but the cache still holds the old copy." |
| Hands-on | The reader causes the effect. | "Tap Switch task a few times and watch both tasks crawl." |
| Evidence | Real numbers from the source, with denominators. | "On 300 recorded requests, 41 got a copy older than the page." |
| Takeaway | What to do differently. | "Three habits cut switch time from 15 minutes towards 2." |

Put the first hands-on step by step 2-4, while curiosity is high. Use at most two. Alternate watching
and doing; three watch-only steps in a row lose readers.

## Writing each step

- **Title** (handwritten, 2-5 words, numbered): "3. Climbing out". The number tells readers where they are.
- **Caption** (<= 220 characters): what to look at and what it means. Write it last, after the drawing
  exists, and check it names only things visible on screen.
- **Scene**: reuse positions across steps. If the cache sits at x=190 in step 1 it sits there in step 5.
  Readers track the lesson by places; moving the furniture between steps makes them re-read everything.
- **Highlight**: dim what this step does not use (30% opacity) and set `keys` so the legend dims too.
- **Duration**: 2-6 s of animation. The caption must be readable in the hold time.

## Hands-on patterns

A question step waits for the reader. Mark it `ask: true` so the idle demo never answers for them, keep the
answer buttons until they choose, and say whether they were right and why. A reader who is thinking is not
idle; a quiz that answers itself after five seconds teaches nothing.

The richest hands-on step lets the reader bring their own case: type a path, enter a price, pick any item,
and watch both sides of the comparison judge it with a reason. Prefer that over replaying fixed examples.

Before a complication's reveal, ask the reader what they expect ("Will the gate allow this one?") with two
answer buttons, then reveal. A one-tap prediction before each case teaches more than tapping to watch,
costs nothing, and makes a lesson feel like a conversation. The answer screen says whether they were right.

Choose the smallest interaction that makes the point:

1. **Repeat an action** (a button that triggers the effect each time): switching tasks, sending a
   request, adding an agent. Show a running count of the cost ("3 switches, about 60 min lost").
2. **Pick one of several** (tap a card or a dot): the reader chooses which case to run, and both sides
   of the comparison judge it at once. Cards need hit areas of at least 36 x 36 units.
3. **Toggle conditions** (2-4 toggles): habits, settings, rules. Each toggle visibly changes one bar or
   number; a "Turn all on" button helps readers who do not want to experiment.
4. **Mini-game** (20-30 s, timer visible): the reader plays a role in the system (reviewing agents,
   routing tickets). End with a score in words and numbers, keep a best score while the page is open,
   and put every element in a clean final state when time runs out.

Every hands-on step needs a `demo()` that performs the interaction and `idleDemo: 5000`, so a reader who
only watches (or a GIF) still sees it happen. Handle early taps kindly ("still working").

## Simulations inside a lesson

When a step compares two worlds (slow vs fast switcher, with and without a check), run a small
simulation in code rather than drawing hand-picked outcomes:
- Seed it (`K.rng`) so every replay shows the same day.
- Put its parameters at the top with their source ("review time 6 min: assumed").
- Say on screen that it is a simple model, in the caption or a small note.
- Compute the caption's numbers from the simulation, so text and picture agree.

## Template

```js
K.stepper({ root: '#x', style: 'chalkboard', viewBox: [380, 300],
  title: 'Seven-step lesson on ...',
  legend: [{key: 'you', label: 'You', color: 'amber'}, {key: 'agent', label: 'Agent working', color: 'green'}],
  steps: [
    { title: '1. Meet the parts', keys: ['you', 'agent'], cap: '...',
      draw: () => T(20, 34, 'Heading', {h: 1, z: 26, a: 'start'}) + /* cast, staggered with t */ '',
      duration: 3200 },
    { title: '2. Your turn', keys: ['you'], cap: 'Tap ... and watch ...',
      draw: () => /* same positions as step 1 */ '',
      start(s) { s.btn('play', 'Switch task', () => { /* effect + count */ }, {primary: true}); },
      demo: async s => { for (let i = 0; i < 3; i++) { s.tap(s.act.querySelector('button')); await s.wait(900); } },
      idleDemo: 5000, demoDuration: 2800, duration: 1500 },
  ] });
```

## Pitfalls seen in real lessons (and the fix)

- Next moved because an extra button appeared on some steps: the kit reserves the action row; if you add
  a slider, set `actHeight`.
- A game ended with an agent stuck on "your turn": set every element's final state at the end of a round.
- A long caption pushed the controls: the kit reserves the tallest caption; keep captions under 220 characters anyway.
- The legend showed colours the step did not use: list `keys` per step.
- Headings inside the drawing collided with the title bar: put the numbered title in `title`, and use the
  in-drawing heading for a subtitle only if needed.
- A step tried to teach two ideas because both used the same picture: split it; the second step can reuse
  the drawing with one new element.

## Before you hand it over

Read every caption and on-screen sentence against the data once, looking hardest at words that claim
totality: "only", "all", "never", "every", "none". A lesson that says "only X failed" when Y also failed is
wrong in a way no layout check catches, and it is the error reviewers find first.

Run `render_check.py`, fix every FAIL, look at both contact sheets step by step against the storyboard,
and play every hands-on step yourself (or read its demo frame). Report what you checked.
