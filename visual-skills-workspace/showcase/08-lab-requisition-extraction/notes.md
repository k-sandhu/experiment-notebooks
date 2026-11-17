# Notes: notebook 08, lab requisition extraction

## Message

On 24 synthetic Ontario lab requisitions ordering 102 tests, the three hosted models found 305 of 306
ordered tests (Claude Opus 5.5 all 102, none added), while the four open-weight models found 341 of 408,
missed mostly the tests written on the Other Tests lines (66 of 108 found, against 275 of 300 marked in boxes)
and sometimes listed tests nobody ordered (Gemma 4 31B added 91).

Reader: a curious professional on a phone or an artifact page, who has never seen the notebook.
Misconception to move: "a model that reads forms either reads them or it doesn't; one accuracy number
says it all". The dots show three different failures (missed, added, no answer) and where they sit.

## Form

`unit-story` (built with `explainer-kit`, stepper, style `paper` because the subject is paper forms).
Every ordered test is a dot, one per model, always in the same cell, so a column of rings across models
is a hard test. Tapping any dot opens a card with the real crop of the form where that test is (box or
Other Tests line), a thumbnail of the whole page with the place marked, and the model's outcome. Added
tests (not ordered) show the crop of their empty box on that page when the test is printed on the layout.

## Steps

1. One test, one dot: form-scan-01 thumbnail, its four tests as real crops (2 boxes, 2 written in), four dots.
2. 102 tests, 24 pages: neutral dots in three blocks (10 official-form scans, 8 phone photos, 6 simple-form scans); tap to see any test.
3. Seven models read: 7 rows, same cells, coloured found / missed (hollow red ring) / no answer (grey). Demo taps GPT-6.1's miss and Claude's hit on Vitamin B12, form-photo-02.
4. Tests nobody ordered: amber rows of added tests per model. Demo taps Gemma's added Sodium on form-scan-04 (empty box) and Nemotron's added Potassium on form-photo-02.
5. The Other Tests lines: box tests and adds dim; per-model "written-in found k of n". Demo taps Qwen's missed TSH on form-scan-07.
6. How sure can we be: miss share per model with 95% Wilson intervals; Claude 0 of 102 allows up to 3.6%; hosted intervals overlap.
7. What a lab can do: four checked rules with their evidence, and the synthetic-data caveat in the caption.

## Source of every number

All counts are computed in the page from `DATA`, which `prep_data.py` builds from
`notebooks/08-lab-requisition-extraction/data/`. `prep_data.py` asserts that per-model found, missed and added
counts equal `TP`, `FN`, `FP` in `summary_tests.csv` (they do).

| On screen | Value | Source |
|---|---|---|
| 24 pages, 102 ordered tests, 75 in boxes, 27 written in | 24 / 102 / 75 / 27 | `scored_tests.csv` (gold rows, `source`), `ground_truth/*.json` annotations; README study summary agrees |
| 10 scans, 8 phone photos, 6 simple-form scans; 2 to 7 tests per page | | `manifest.csv` (`doc_id`, `n_tests`) |
| Found / missed per model (102, 101, 102, 92, 95, 86, 68) | | `scored_tests.csv`; equal to `TP`/`FN` in `summary_tests.csv` |
| Hosted 305 of 306, open-weight 341 of 408 | sums | `scored_tests.csv` |
| Added per model (0, 0, 3, 2, 38, 28, 91) | | `scored_tests.csv` (`gold` False); equal to `FP` in `summary_tests.csv` |
| Nemotron: 28 of 38 adds from one photo listing all 31 names | 28 | README sections 4 and 6 (form-photo-02) |
| Muse Spark Open: 6 misses from the one empty reply (form-scan-05) | 6 | README section 3/6; `manifest.csv` n_tests = 6 |
| Gemma blank replies on form-photo-04 and -06, shown as missed | 7 tests | README section 3; counted as misses as in the README table |
| Written-in found: open 66 of 108, boxes 275 of 300, hosted 80 of 81 | | `scored_tests.csv`; README study summary agrees |
| Claude 0 of 102 missed allows up to 3.6% | Wilson 95% upper | computed with `K.wilson(0, 102)`; README section 3 states 3.6% |
| Miss-share intervals for all models | Wilson 95% | computed from the counts above |
| Claude exact list on 24 of 24 pages | 24 | `summary_tests.csv` (`all tests right` x 24) |
| Two replies listed 31 and 24 tests | | README section 6 |
| 1 of 168 replies empty | | README section 3 |
| Crops and thumbnails | | `images/*.jpg`, cut with the ground-truth polygons (`ground_truth/*.json`, `annotations[].polygon`) |

Crops for added tests: an added test has no position on its page in the ground truth. When the test is
printed with a box on that layout and is marked on some scan of the same layout, its polygon is mapped onto
the page with a homography fitted on the shared field polygons (median residual 0.0 px on every page pair, so the
generator uses one exact template geometry per layout; I checked the mapped crops by eye on a contact sheet). 124 of the 162 added tests get a crop this way; the other 38 are tests
not printed on the official form (card says so) or printed but never marked on any page (card says no picture).

README and data agree on every number used. One labelling note: `summary_tests.csv` and `scored_tests.csv`
call GPT-6.1 "GPT-6.1 (Codex)"; the page uses "GPT-6.1" as the README does.

## What I checked

- `render_check.py` at 360 px and 560 px, with and without reduced motion: PASS all checks (after fixing a
  title that wrapped on step 3 and moved the controls, group headings overlapping model names, and the
  Muse Spark Open note crossing its track in step 6).
- Looked at the contact sheets and at full-size frames of steps 1, 3 (demo card), 4 (demo card), 5 and 6:
  each step shows its one idea, dots keep their cells across models, rings and grey dots read apart from
  found dots, and cards show the right crop, page and outcome.
- Looked at sheets of 150 crops: ordered-test crops show the marked box or written line; added-test crops
  show the empty box of the named test (photos included, upright).
- `prep_data.py` asserts per-model found, missed and added counts equal `summary_tests.csv`.
- Recorded with `record.py`: explainer.mp4 (55.6 s, 4.0 MB) and explainer.gif (7.2 MB); checked one frame
  every 5 s on a tile. card.png is step 4 at 380 px wide, 2x, with its idle demo card (Gemma's added Sodium
  on form-scan-04, an empty box).
- HTML is 1.02 MB (crops and thumbnails inlined as JPEG data URIs), under the 3 MB limit.
- Not checked: dark mode (the page sets a light colour scheme), screen-reader reading of the cards, and
  keyboard use of the tap area beyond the kit's Enter/Space handler (keyboard steps through dots in a fixed order).

## Files

- `explainer.html` is assembled from the kit scaffold (`scaffold.py --kind stepper --style paper`), the
  generated data block and the scene script. `prep_data.py` (run as
  `python prep_data.py notebooks/08-lab-requisition-extraction <out>/data.js`) rebuilds the data block.
