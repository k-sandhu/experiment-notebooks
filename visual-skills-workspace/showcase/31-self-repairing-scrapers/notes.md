# Notebook 31, self-repairing scrapers: explainer notes

## Message

A capable model can write the 20 scrapers once. Free automatic rules then catch every break when sites are
redesigned, so Claude Haiku 5.5's programs delivered 80 of 80 correct source-weeks for $0.28. The paid Opus
review only matters when the writer is weak: with Granite 4.2 8B it cut unnoticed wrong source-weeks from 22 to 1.

- Reader: curious professionals on a phone or an artifact page, who have not read the notebook.
- Misconception: "A model that writes its own code needs an expensive model checking it every week", or the
  opposite, "Cheap checks are enough for any writer."

## Form and why

The form is system-replay, played as a choreographed walkthrough of the recorded run (`K.stepper`, chalkboard
style, 380 x 432). The story is a loop working over time: writer, program, rules, review, tracker, and a red
report path back to the writer. The same diagram stays on screen for steps 1-6 and 9. Below it, a 20-source by
4-week grid fills week by week, and a terminal-style log prints the recorded events in words. Every event, cell and
cost comes from the run records, but the timing is designed (the real run's timestamps are not replayed), so I
used the stepper rather than `K.player`. Two moments are borrowed from other forms: one hands-on toggle (step 6)
and two comparison charts (steps 7 and 8).

Colour meanings stay fixed throughout. Green means correct with no model call, blue means correct after a
repair, amber means flagged for a person, and red means wrong with nobody noticing. Violet marks a model call
(the writer, the Opus review and cost). Cells also carry letters (R, F, ✗), so colour is never the only cue.

## Steps

1. Watching 20 news pages: the cast (pages, program, rules, review off, tracker, writer, report path), with an empty grid and a log of the setup.
2. Week 1, write once: Haiku writes 20 programs. 19 cells turn green and Harrow & Finch shows "!". Spend counts to $0.19.
3. Check, report, repair: the Harrow & Finch date rule fails (`published_at` is in milliseconds), the report goes back, Haiku repairs it for $0.013, the cell turns blue R, and spend reaches $0.21.
4. Week 2, reuse for free: 20 of 20 green, the writer is dimmed, $0.00.
5. Week 3, six redesigns: ▲ marks appear over 6 columns. 4 breaks are logged with their rule messages and repaired (+$0.07). The two quiet redesigns stay correct. Week 4 is all green. "80 of 80 source-weeks correct for $0.28". Sonnet 5.5 managed the same for $1.76 (caption).
6. A weak writer (hands-on): the grid morphs to Granite 4.2 8B with rules only (22 ✗, 10 of 20 correct in week 4, 21 flagged, $0.06). Tapping "Add the Opus review" shows 1 ✗, 16 of 20, 27 flagged and $4.87. A demo taps it for passive viewers and the recording.
7. Which check catches what: planted errors, with bars for rules and review per error kind, 48 of 135 against 135 of 135, and 0 false alarms on 20 controls.
8. Or read every page?: 9 methods, share of 593 release-weeks right and 4-week cost.
9. What to do: the diagram with the review on and three rules, plus a caveat box (made-up tidy sites; rules flagged 48 of 135 planted errors).

## Source of every number

All paths are relative to `notebooks/31-self-repairing-scrapers/`.

| On screen | Value | Source |
|---|---|---|
| 20 organisations, 4 weekly runs 5-26 Oct 2026, fields | | README §1 "Why the data is new", §2 "What the writer is asked to do" |
| Six redesigned sites (kso, krs, ksc, hfb, lhr, cvp) | | README §1 table |
| Haiku grid (19 first-try correct, hfb repaired wk 1; kso, krs, hfb, lhr repaired wk 3; all else correct) | | `data/attempts.jsonl`, writer Claude Haiku 5.5, mode `static`, last attempt per source-week; matches README §4 and §5 tables |
| Granite grids, rules only and rules + review | | `data/attempts.jsonl`, writer Granite 4.2 8B, modes `static` and `static+review`; same derivation |
| 22 and 1 wrong unnoticed; 10 and 16 of 20 correct in week 4 | | computed from those grids; equal to README §5 table and text (22 source-weeks; 9/9/9/10 and 9/14/14/16) |
| 21 and 27 flagged source-weeks | | computed from the same grids (not stated in the README) |
| Week-1 spend before the repair, $0.19 | 0.1931 | `data/attempts.jsonl` (week-1 Haiku static write_cost 0.2057 minus hfb repair 0.0126) |
| Repair cost $0.013, 15 requests, ms read as seconds, `date: None`, 24 of 24 fields | | README §3; repair write_cost 0.01263 and fetches 15 in `data/attempts.jsonl` |
| `published_at` 1790602200000, true date 2026-09-28 | | README §3 JSON excerpt; `data/ground_truth.csv` (hfb week 1) |
| Rule message `date must be a "YYYY-MM-DD" string, got None` | | `data/attempts.jsonl` static_problems (shortened on screen) |
| Week-3 break messages (0 records; 5 vs 8 last week; 410 Gone; "Words by Daren Pell") | | README §5 and §8; `data/attempts.jsonl` static_problems |
| Spend $0.21 (week 1), +$0.07 (week 3), $0.28 total; Sonnet $1.76 | | README §5 and §7 tables |
| Granite spend $0.06 / $4.87 | | README §7 table; `data/attempts.jsonl` sums to 0.065 and 4.875 |
| Planted errors per kind, 48 of 135, 135 of 135, controls 0 | | README §6 table; checked against `data/planted_errors.csv` (same counts) |
| Methods: release-weeks right of 593, 4-week cost | | README §7 table |
| "10 to 50 times larger" real pages | | README §7 |
| Caveat text | | README study summary "The main caveat" |

### Disagreements between the README and the data

- Haiku rules-only total: the README gives $0.28 (weekly $0.21 + $0.07). The write costs in `data/attempts.jsonl`
  sum to $0.273 (0.2057 + 0.0674). The README's total is the sum of rounded weekly figures. I show the README's
  $0.21 and $0.28 so the screen agrees with the published table. The $0.19 week-1 figure before the repair comes
  from the data.
- No other disagreements found. The grid counts, the 22/1 silent source-weeks, the week-4 correct counts and the
  planted-error counts all match.

## What I checked

- `render_check.py`: PASS all checks at 360 px and 560 px and with reduced motion, after fixes. The first run
  warned that "20 news" and "pages" overlapped; I relabelled the box "Pages / 20 sites".
- I looked at the contact sheets (w360, w560, w360_rm) and at single frames of steps 3, 5, 6, 7, 8 and 9. After
  looking I made these changes:
  - Planted-error bars now scale to each row's case count, so 15 of 15 reads as full.
  - Amber and red no longer mark method names or costs in step 8, so each colour keeps one meaning.
  - The step-5 log is merged so all four breaks fit on screen.
  - The step-8 caption is hedged to the README's claim.
- Step 6 toggle: tested in Playwright (click, then the caption, the counts 1 / 16 of 20 / 27 and $4.87 update,
  with no console errors). The recording also shows the demo tap.
- `record.py`: explainer.mp4 (4.0 MB, 62 s) and explainer.gif (7.4 MB). I sampled frames at 20, 40, 43, 45, 47,
  50 and 62 s.
- card.png: step 5 final state (80 of 80 for $0.28), 380 px viewport at 2x (760 x 1416).
- Not checked: screen-reader reading order beyond the kit's defaults, and pages in a real phone browser.
