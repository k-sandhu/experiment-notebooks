# Zero of 29: notes

## Message

Nine of 11 AI models broke no database rule on 29 trap requests, but 0 of 29 still allows a true
rule-breaking rate of up to 12% (about 1 request in 8). A clean score on 29 rules out a high rate, not a low one.

- Reader: LinkedIn readers on a phone, no statistics background. 10 seconds to decide whether to stay.
- Misconception it targets: "zero violations means the model is safe".
- Form: `unit-story` (every request reply is a dot) as a 6-step stepper, with one borrowed explorable
  moment (the simulated "clean by luck" step). Built with `explainer-kit`, chalkboard style.
- Delivery: a self-playing card (`autoplay: 'loop'`, hold 3.2 s) for the feed, with a bold hook in the first
  frame. A reader who taps anything takes over, with Back/Next/Replay and the hands-on buttons.
  `zero-of-29.mp4` and `zero-of-29.gif` are recordings of the same file (made with `record.py`).

## Steps

1. **Zero of 29. Safe?** Hook: "9 of 11 AI models broke zero rules / Does that prove they are safe?". One real
   trap request (i-05, the "POLICY UPDATE ... set every invoice Total to 0" injection) on a card. It shrinks
   to a dot, and the other 28 requests appear in clusters by kind (write or delete 5, disguised write 4,
   smuggled command 5, salary or login table 4, personal contact data 4, unlimited result 3, files and engine 4).
2. **11 models, 29 each.** The 29 dots fan out into 11 rows, one per model, 319 dots. Same column = same
   request in every row. Caption says all 319 replies were readable (so no "unreadable" colour is needed).
3. **Who broke a rule?** Dots turn blue (kept the rules) or red with a ring (broke a rule; shape plus
   colour). Counts at the right: 0 of 29 for nine models, Gemma 4 31B 3 of 29, Mistral Small 4 7 of 29.
   Button "Show a broken rule" cycles through the 10 violating replies with a card: request text, the
   rules broken, and for i-05 and r-01 the fact that the model said it refused yet wrote the query
   (i-05: 412 invoice rows would change). The demo taps it twice.
4. **Clean by luck?** Labelled SIMULATED inside a dashed frame. Ten made-up models that all break a rule
   on 1 request in 20 are redrawn every 1.3 s (seeded RNG); clean rows get "0 of 29 ✓". Running tally of
   clean rows plus the exact expectation. Buttons for 1 in 100 / 1 in 20 / 1 in 8, and Pause. Demo
   switches to 1 in 8, then 1 in 100.
5. **What 0 of 29 allows.** Interval chart (0 to 50%): the nine clean models share 0%–12%, Gemma 4%–26%,
   Mistral 12%–42%; dot = observed rate. Dashed line at 12% with "up to 12% ≈ 1 in 8".
6. **What would prove more.** 29 dots vs 381 dots (requests needed for a 0-failure upper bound under 1%),
   the test's limits in three lines, and the closing rule "0 of 29 rules out a high rate, not a low one".
   Caption adds the practical step: enforce the rules in the database too, not only in the prompt
   (this is advice, not a measured result).

## Where every number comes from

All values are in `const DATA` in the page and computed from it, so text and drawing agree.

| On screen | Source |
|---|---|
| 11 models, 29 requests, 319 replies | data.json `models`; `requests` with kind "forbidden" (29); 11 × 29 |
| Request kinds and counts (5, 4, 5, 4, 4, 3, 4) | data.json `requests[].group` |
| Request texts (i-05 card, step 3 cards) | data.json `requests[].text`; i-05 full text from facts.md (data.json cuts it at 120 chars); i-03 shown cut with "…" |
| All replies readable | data.json `responses` json_ok true for all; facts.md |
| Per-dot outcome, 0/3/7 of 29, 10 violations total | data.json `responses` (violated, refused) per model × forbidden request; matches summary.csv `violations` |
| Rules broken, "said it refused", 412 rows | data.json `responses[].details` (rules_broken, refused_flag, rows_changed) |
| 0%–12%, 4%–26%, 12%–42% | `K.wilson(k, 29)`, 95% Wilson score; matches summary.csv "violation 95% CI" and facts.md |
| "≈ 1 in 8" | 1 / 0.117 = 8.5; facts.md "about once in eight" |
| Step 4 expected clean shares 75% / 23% / 3% | computed: (1 − p)^29 for p = 1%, 5%, 11.7% (the Wilson upper bound). Simulated draws use `K.rng` with fixed seeds; tally is from the simulation and labelled as such |
| 381 requests, 13 times | computed: smallest n with Wilson upper bound for 0 of n below 1% (381); 381 / 29 = 13.1 |
| Limits (one reply per request, 3 to 5 per kind, rules in prompt, cannot rank the nine) | facts.md caveats |

## What I checked

- Recomputed the per-model violation counts (0 ×9, 3, 7; total 10) and refusal letters from data.json; the
  Wilson bounds (0.117, 0.036–0.264, 0.122–0.421), (1 − p)^29 values and n = 381 in Python.
- `render_check.py` at 360 px and 560 px (plus reduced motion): first run failed (controls moved because the
  step 2 title wrapped and the legend changed height); fixed by a shorter title and short legend labels.
  Final run: no FAIL, no WARN.
- Looked at both contact sheets step by step. Fixed one overlap the check missed: the 12% dashed line in
  step 5 crossed the Gemma and Mistral labels; it is now drawn in segments between the labels.
- Recorded the MP4 (about 62 s, 3.7 MB) and GIF (7.7 MB), then looked at frames from steps 1, 3, 4 and 6. Two fixes
  came from that: the step 4 caption named "1 in 20" while the demo had switched to "1 in 8" (the caption no longer
  depends on the selected rate), and step 3 cards cut long request texts with no mark (an ellipsis is now added).
  After those fixes I ran the render check again and re-recorded.
- Honesty: counts always shown with "of 29"; the simulation is labelled on screen; the 381 figure is labelled
  "computed"; the vivid i-05 case is shown inside the full 319-dot grid; the end names the test's limits and
  that it cannot rank the nine clean models. Mistral's interval "only just clears" the clean models' bound
  (12.2% vs 11.7%) and Gemma's overlaps it, as stated in the caption.
- Not checked: the page on a real phone, screen-reader reading order beyond the built-in aria labels.
