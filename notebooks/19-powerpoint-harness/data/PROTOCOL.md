# Protocol history: notebook 19

Records for someone checking the work: plan versions and when they were frozen, amendments, the storage
incident, collection settings, superseded intermediate results and spend. The reader-facing account is in
`../README.md` and the notebook. Entries are in date order; times are UTC unless marked. The frozen plans are
kept unchanged in their own files:

- [`protocol.json`](protocol.json): four-slide first run (`ppt-harness-1`)
- [`harder/protocol.json`](harder/protocol.json): eight-slide study, generation and individual scoring (`ppt-harness-2`)
- [`harder/paired_protocol.json`](harder/paired_protocol.json): first 18 head-to-head pairs (`ppt-pairs-1`)
- [`harder/paired_full/protocol.json`](harder/paired_full/protocol.json): all 48 head-to-head pairs (`ppt-pairs-full-1`)
- [`runtime.json`](runtime.json) and [`harder/runtime.json`](harder/runtime.json): CLI versions, renderer and the amendment log

Code names used in the data: `primitive` = basic tools, `helpers` = layout helpers, `text` = text review,
`vision` = screenshot review; `pilot-00` = Aster task, `pilot-01` = Cedar task, `dev-02` = development case
(Birch service network, never scored). The helper code names are `header` (title block), `kpi` (key-number
card), `flow` (row of connected steps) and `columns`. "Expansion rule" in the data files is the rule for
adopting a feature that the README describes.

## 2026-10-21: four-slide first run (`ppt-harness-1`)

- Plan frozen at 19:09:16 (`protocol.json`), seed 20261021, two scored briefs plus the development case,
  all created 2026-10-21 by a seeded Python generator from fixed templates. The case file hash is recorded in
  the protocol (`cases_sha256`).
- Deck makers: GPT-6.1 Sol (`codex exec`, requested `gpt-6.1-sol`), Claude Opus 5.5 (`claude -p`,
  `claude-opus-5-5`), Muse Wonder Full (`muse exec`, `muse-wonder-full-1.0`). Judges: GPT-6 Astra
  (`gpt-6-astra`), Claude Opus 5.5 and Muse Wonder Full. One repetition per cell.
- Settings: 150-call cap, medium effort, generation output capped at 38,000 characters, $3 cap per Claude
  call, at most three concurrent CLI requests, tools disabled, each call in an empty temporary folder.
  Renderer: Microsoft PowerPoint 16.0 on Windows, 1440 x 810 PNG exports; fonts Arial, Georgia, Calibri.
  CLI versions: codex 0.160.1, claude 2.1.296, muse 1.4.11-R6667.1. Python 3.13.5, python-pptx 1.0.2.
- Design: 2 x 2 crossed (basic tools or helpers, text or screenshot review), one shared draft per
  model, brief and tool set, revised independently under both review modes with an identical change request.
- Primary measure: mean of five 0-5 judge ratings scaled to 0-100, averaged over the three judges; a failed
  generation scores 0. Sensitivity: exclude same-vendor judges; report every dimension, judge and brief.
- Inference rule: "Two briefs are a descriptive pilot. No population CIs, p-values or global winner."
- Image gate: every judge must read a code from an image and prefer a clean over a damaged slide in both
  orders. All 6 control calls passed (`controls.json`).
- Expansion rule: validity at least 90%, positive effects on both briefs and no cross-vendor reversal. Both
  features failed it (`expansion_decision.json`).
- Amendments recorded in `runtime.json`: (1) before generation, after the freeze, the self-test's expected
  connector count was corrected from four to five (test assertion only); (2) after generation, during judge
  collection, `init --seed`, brief-count validation and UTC creation dates were added for future runs;
  (3) at packaging, derived tables were written with LF line endings. None changed a prompt, image or score.
- Calls: 132 (6 image controls, 12 drafts, 24 revisions, 72 individual ratings, 18 order-audit calls).
  Known Claude list-price equivalent $5.68; dollar cost of the other 88 calls unknown (`spend.json`).
- Results, now design history only: all 24 decks rendered; judges marked all 864 requirement checks met;
  mean scores GPT 94.5, Claude 88.8, Muse 88.7, with three GPT setups tied at 94.7; helpers -2.9 points,
  screenshots +0.2, interaction +2.7; the order audit kept the same preference in 9 of 9 checks; mean
  spread between the highest and lowest judge score per deck 8.0 points. Lowest deck
  `artifacts/85f6a9f3611d0a54` (Claude, helpers + text review, Aster), 74.7, titles overlapping subtitles on
  slides 2 and 4.
- Commit `11a62ac` (15:39 -0400, local time).

## 2026-10-21: title helper repair (development check)

- The `header` helper was rewritten to measure text with the installed font, insert safe line breaks, place
  a 24-27 pt title in a two-line band at (0.55, 0.22, 12.2, 0.91) inches, a single-line 10-12 pt subtitle
  at y = 1.18, an accent rule at y = 1.48, and leave the body from y = 1.7. It keeps a 6% width allowance
  and raises an error for text that still does not fit.
- Check: the four headers of `artifacts/85f6a9f3611d0a54` rebuilt in Arial, Calibri and Georgia with each
  helper version. Overlaps: old 6 (Arial 2, Georgia 4), repaired 0 (`harder/validation.json`,
  `header_geometry`; images in `harder/header_regression/`).
- Basic tools unchanged: 18 four-slide decks rebuilt with identical expanded scenes, slide XML, chart XML and
  embedded workbook contents against commit `11a62ac`, ZIP timestamps excluded (`primitive_compatibility`).
  The other three helpers were not changed.

## 2026-10-21: eight-slide study (`ppt-harness-2`)

- Plan frozen at 20:29:25 (`harder/protocol.json`), seed 20261022, collector snapshot
  `harder/harness_at_freeze.py`. Briefs `pilot-00` and `pilot-01` created 2026-10-21, MIT licence.
- Changes from the first run: eight slides, 24 requirement checks, three task-card images per judge request,
  generation cap 75,000 characters, 600 s timeout, planned 132 calls with a $132 Claude ceiling.
  Unchanged: basic-tools compiler, the other three helpers, model IDs, effort, one draft and one revision per
  final deck, the rubric and the three judges.
- Primary contrast: helpers minus basic tools, averaged over models and review modes; screenshot effect and
  interaction also reported. The expansion rule added "no requirement loss" and "checklist no longer at
  ceiling".
- Calls: 6 image controls (all passed, `harder/controls.json`), 36 generation calls, 72 individual ratings.
  All 12 drafts and 24 final decks built and rendered.
- Amendment (`harder/runtime.json`), after absolute collection and before aggregate analysis: one Muse
  rating of deck `180b0686bfd85db8` (request key `15621b036ca1...`) returned 25 identical `true` checks
  instead of 24. Replay drops one; every possible deletion gives the same vector; the raw reply, the original
  parse failure and the five quality ratings are kept (`harder/parse_normalizations.json`). No other rating
  needed repair.
- Expansion rule outcome (`harder/expansion_decision.json`): helpers failed (not positive on both briefs,
  not positive with other-vendor judges, requirement loss); screenshots were positive on both briefs with all
  judges but not with other-vendor judges, and showed a requirement loss.
- Post-collection engineering check (`harder/native_audit.json`), no rescoring or repair: 24 decks, 192
  slides, 48 native charts, 108 native tables; all 156 fitted header text objects clear the next header
  band; 34 title boxes have font bounds 0.72 pt below the nominal box.

## 2026-10-21: head-to-head comparisons, first 18 pairs (`ppt-pairs-1`)

- Added at the owner's request after generation, while individual ratings were being collected. The plan was
  frozen at 21:11:24 (`harder/paired_protocol.json`, collector snapshot `harder/paired_harness_at_freeze.py`)
  before any paired call and before aggregate individual scores were inspected. Pair selection did not use
  scores.
- 18 pairs: the three model matchups under basic tools + text review and helpers + screenshot review on both
  briefs (12), and helpers against basic tools under screenshot review (6). Every judge saw every pair in both
  orders: 108 calls, cumulative cap 240 calls, Claude ceiling $108, no retries. The first-brief helper pairs
  also served as the planned order audit, so no separate audit calls were made.
- Storage incident: after 107 paired replies were cached, one GPT-6 Astra reply was lost when the disk filled
  during a cache append. The identical request was sent once more within the cap; no earlier answer existed
  to compare or select. Recorded at 21:46:09 in `harder/collection_failure.json`. Totals to this point: 223
  attempts, 222 cached replies.
- Results on these 18 pairs, superseded by the 48-pair set that contains them unchanged: order consistency
  43 of 54, 8 tie votes, score order agreed with head-to-head preference in 15 of 17 untied pairs, helpers
  under screenshot review 27.8% win credit (other-vendor 27.1%, score -1.8 points); with other-vendor judges
  only, GPT and Claude tied at 75.0% model win credit (`harder/paired_summary.json`,
  `harder/paired_models.csv`).
- Spend to this point: 223 attempts, $23.31 known Claude list-price equivalent, 149 calls without a dollar
  figure (`harder/spend.json`).
- Commit `951dc63e` (17:50 -0400, local time).

## 2026-10-21: head-to-head comparisons, all 48 pairs (`ppt-pairs-full-1`)

- The owner chose to complete every model and tool comparison after the 18-pair results were available. The
  plan was frozen at 22:02:06 (`harder/paired_full/protocol.json`), listing every remaining pair before any
  new call, with no subset chosen on outcomes. It is not an independent replication: decks, task cards,
  prompts, judges, effort and ordering rule are unchanged.
- 48 pairs, 288 judgments: the 108 earlier judgments reused byte for byte, 180 new calls. Cumulative cap 430
  calls, additional Claude ceiling $180, no model retries.
- Cache-write change for this run: retry a local `ENOSPC` write up to five times after truncating any
  partial append, and require 256 MiB free before each missing call; no model call is repeated. After
  collection the active writer was changed to unbuffered writes that handle short writes; local tests checked
  it, and the frozen collector snapshot was kept.
- Spend: 180 new calls, $19.66 known Claude list-price equivalent, 120 without a dollar figure. Eight-slide
  study total 403 attempts, $42.97, 269 without a dollar figure (`harder/paired_full/spend.json`). Both runs
  together: 535 attempts, $48.65, 357 without a dollar figure. A fresh full run without the storage incident
  needs 402 attempts.
- Commit `8d5acb7d` (18:38 -0400, local time).

## 2026-10-22: README and notebook text revisions

- Commits `43147ce0`, `dd37533f`, `070a40ad` and `386a3e6d` changed only the README; `b7691ef4` changed the
  notebook's explanatory text. No data changed. Research links in `research.json` were checked on 2026-10-21
  and the notebook's further reading on 2026-10-22.

## 2026-10-28: text rewrite

- README and notebook markdown rewritten into one account; no model calls, no re-run, no data or figure
  changes. Further-reading links re-checked on 2026-10-28.
- New observations computed read-only from the saved data during the rewrite: the 36 generation prompts in
  `harder/cache.jsonl` do not contain the judges' 24-item list, the task card's "likelihood on x, impact on y"
  or a request for the yearly saving on slide 8; both Claude Cedar drafts (`ed5008f41aa1aeda`,
  `b2d6cfcbb7c3a2cb`) already lacked the saving on slide 8; six of the eight Muse risk charts put likelihood
  on the vertical axis (slide 7 of each `scene.json`).
