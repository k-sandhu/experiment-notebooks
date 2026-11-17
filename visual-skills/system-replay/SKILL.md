---
name: system-replay
description: Build an animated replay of how a system runs - AI agents and subagents, an agent harness with tools and guardrails, a data pipeline, an API request path, a queue, a protocol - from recorded logs or traces (timestamps, spans, events) or from a designed demonstration run. Shows actors, calls travelling between them, waiting and blocking, hidden state like a context window or budget, and a live event log, on a timeline the reader can pause and scrub. Use when someone wants to visualize an agent trace, show who waited for whom, compare coordination patterns, explain how a harness or architecture works in motion, or turn run logs into an animation or GIF.
---

# System replay

Static architecture diagrams show what is connected. They cannot show the thing people actually need to
see in a running system: order, waiting, contention, retries, and the moment something went wrong. A
replay shows the system doing its work, with time under the reader's control.

Two modes, chosen by the material:

| Material | Mode | Engine |
|---|---|---|
| Recorded events with timestamps (spans, logs, traces, call records) | **Data replay**: draw the recorded run on a timeline; time is real, compressed | `K.player` with a pure `frame(t)` |
| A process to explain, no single recorded run (or a run too messy to show) | **Choreographed walkthrough**: a designed run, one mechanism per step | `K.stepper` with `s.travel`, `s.ring`, `s.at` |

Read `explainer-kit/references/api.md` before building. Default style: `blueprint` for engineers,
`chalkboard` for general audiences.

## The parts of a replay

1. **Actors in fixed places.** Boxes (or lanes) for each agent, service, tool or person. They never move.
   Readers learn the map in the first chapter and then watch traffic on it.
2. **Traffic.** Calls, messages and data are dots travelling along connectors (`s.travel`). Colour by
   kind: request vs result vs error. A request and its result travel opposite ways on the same path.
3. **Time lanes** (data replay): one horizontal lane per actor, x = time. Working spans fill in as time
   passes; waiting spans in a different colour; a vertical "now" line moves across. This is a Gantt chart
   that draws itself, and it makes waiting impossible to miss.
4. **Hidden state** as a meter: context window %, tokens used, budget, queue length, retries left. Hidden
   state is usually where the story is (the agent compacts at 87%; the queue backs up).
5. **Event log.** A short terminal-style panel (`log` option) repeating each event in words:
   `→ get_prices(n=412)`, `✗ 429 rate limited`, `← 412 rows · 2.1 s`. Words and motion together help
   readers who look away for a moment, and give exact values the drawing cannot.
6. **Clock.** Show real time and the compression: "41 s into the run (1 s here = 10 s)".

## Data replay recipe (K.player)

1. Load the run into `const RUN = {...}` (spans: agent, kind, start, end; events: t, from, to, kind, text).
   Keep the real seconds; convert with one constant `SPEED` (animation ms per real second).
2. Map actors to lanes in a meaningful order (parent above children, in spawn order).
3. `scene()` draws lane labels, the time axis with real-second ticks, and static boxes.
4. `frame(t, s)` clears `s.dyn` and draws everything with `start < now`: spans clipped at now, messages as
   dots interpolated between sender and receiver lanes at their send/receive times, a "now" line.
   Never keep state between frames; scrubbing backwards must work.
5. Chapters mark the moments worth stopping at: setup, first handoff, the bottleneck, the failure,
   the finish. Each chapter's caption says what to look at in that stretch.
6. Compare runs by showing them with identical layout and the same time scale: either several runs
   stacked (small multiples, shared clock), or chapter buttons that switch runs. Mark each run's finish
   time with a flag and the number ("done at 31.4 s").

Fit the whole timeline into the drawing's width at phone size. A replay that needs sideways scrolling
plays its key moments off-screen, and readers never find them. If the run is too long to fit legibly,
compress quiet stretches (with a visible marker), split it into chapters that each fit, or zoom the time
axis per chapter with a label saying so; never rely on the reader to scroll a timeline.

Long idle stretches: either compress time non-linearly with a visible marker ("⏩ 30 s of waiting
skipped") or let them play, because waiting may be the point. Never hide waiting silently.

## Choreographed walkthrough recipe (K.stepper)

One mechanism per step, using the same diagram throughout:
- Step 1 draws the whole system and names every part (no traffic yet).
- Each later step dims parts it does not use (`focus`), plays one interaction with `s.travel` hops and
  `s.ring` pulses, updates meters, and appends to a log you draw in the action area or the scene.
- Show failure handling explicitly: a red dot comes back (`✗ 429`), a countdown, a retry; a guardrail
  sends the dot back around a loop; a human approval pauses everything with a waiting pulse.
- Time each hop 300-700 ms; leave 400 ms between cause and effect.

### Example storyboard: an agent harness for a finance question (designed run)

Built with an earlier version of these skills; eight steps, 380 x 440, chalkboard.
1. *The harness* - task card, agent loop (Plan, Act, Observe), tool palette (7 tools), data router, four
   sources (cache, warehouse, market API, document store), and three gates (policy check, human sign-off,
   send). Context meter at 18% for instructions and tool specs.
2. *Plan* - the task enters the loop; the plan is written into the log; context grows.
3. *Route the data call* - `get_holdings` travels to the router, which tries the cache (stale, red),
   then the warehouse (412 rows). The model never learns where data lives.
4. *Fan out in parallel* - two calls at once; one hits the cache, one gets HTTP 429, waits, splits the
   batch and retries.
5. *Compute, don't guess* - risk maths runs in a sandbox; only the summary returns to context.
6. *Manage the context window* - notes push context to 87%; older results are compacted to files.
7. *Guardrails push back* - the draft fails a sourcing check, loops back, passes on revision.
8. *A human signs off* - the loop pauses, waiting pulses, approval, the note is sent. "Eight turns."

What made it work: one diagram for all eight steps, a log that narrates every hop, a context meter that
makes hidden state visible, and failure paths drawn in red rather than described.

## Honesty

- Data replay: every span and message on screen comes from the record. If you smooth or drop events,
  say so in a note. Show the real total time at the end.
- Walkthrough: it is a designed run. Say "an illustrative run" in the first caption or the title.
- Do not draw parallelism the system did not have, or waiting it did not do.

## Checks specific to replays

- Scrub to 0, the middle and the end: the picture must be right each time (proves `frame` is pure).
- Each chapter's caption matches what is visible in that chapter's stretch.
- Lane labels and log text stay legible at 360 px (13 units for lane labels).
- Late or lost messages are shown arriving after the receiver stopped reading, with a ✗ and words.
