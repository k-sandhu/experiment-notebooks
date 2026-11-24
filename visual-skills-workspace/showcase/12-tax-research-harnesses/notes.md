# Notes: notebook 12, tax research harnesses

## Message
Extra steps around a model only help if they can catch the error. Gemma 4 31B wrote test-01's profit as
$3,400 instead of $4,400, and the checklist, self-review, checker feedback and agent framework all left it
there, because none of them redoes the sum. Gemma got 0 of 96 workpapers fully correct. Qwen3.8 Flash was
right in one call (24 of 24 direct calls), so for Qwen the extra steps only added cost and 5 empty replies.

Reader: curious professionals on a phone or an artifact page. Misconception: "adding review, feedback or an
agent loop makes model output more correct".

## Form and why
`system-replay`, choreographed walkthrough (K.stepper), blueprint style, 380 x 460, 8 steps. The question is
about what each harness does around one model call, so one fixed diagram (books, model, workpaper, checklist,
review loop, checker) carries every step, with traffic dots for requests and feedback and a two-line event log.
Each step replays the recorded test-01 run for that setup. A per-setup tracker fills in row by row. The last
step widens from one company to all 192 runs (one mark per run) so the single example is placed in the whole
result, including the ceiling/floor caveat.

## Steps
1. Job and harness: test-01 books, $8,100 - $3,700 = $4,400 (green, the key); model, workpaper (9 fields); add-ons shown then dimmed.
2. Direct call: Gemma returns 3,400 / 2,040 / 1,360; 7 of 9 right, not fully correct. Tracker row 1.
3. A longer checklist: same call plus the 868-character checklist; same 340,000 cents.
4. Self-review: draft goes back with the review prompt; identical reply (42 of 48 Gemma review runs).
5. Checker feedback: checker ticks format, year, sources, A + B = profit; "no profit recheck"; returns []; same draft.
6. Agent framework: tool call to validate_workpaper, Observation [], final_answer 3,400. Qwen: HTTP 400 on all 24.
7. The other model: Qwen thinks 1,930 tokens, writes 4,400, 9 of 9. Tracker Qwen column fills (4 x correct, HTTP 400).
8. What to change: all 192 runs as marks (correct, wrong, empty reply, not run) by model x setup x instruction length; Gemma 0 of 96, Qwen 67 of 96 (67 of 67 readable); no room to show a gain; a step must be able to catch the error (recomputing profit, labelled not tested).

## Source of every number (notebook folder notebooks/12-tax-research-harnesses/)
- Books lines 8,100 / -200 / -1,000 / -800 / -200 / -1,500 and profit 4,400: data/cases.json (test-01 ledger, cents) and README section 3; answer key profit 4,400, shares 2,640 / 1,760: data/gold.json.
- Gemma test-01 draft 340,000 / 204,000 / 136,000 cents, 7 of 9 fields right: data/runs.json (all 8 Gemma test-01 runs give 340,000; checked) and README section 3.
- "168 tokens": data/cache_requests.jsonl, Gemma direct short (completion_tokens 168, reasoning 0); README section 3.
- "+868 characters" and the checklist quote "Cash draws are not wage deductions": README section 2 (design.checklist).
- Self-review prompt text and checker message "[]": data/cache_requests.jsonl (last user message of the second request), README section 2.
- 42 of 48 identical Gemma review replies: README section 9; recomputed from cache_requests.jsonl (42 / 48).
- Checker checks (format, year, sources, shares add up; no recompute): README "Models, and the steps teams add around them".
- Agent framework trace (validate_workpaper call, "Observation:\n[]", final_answer with 340,000): data/cache_requests.jsonl, Gemma smolagents short test-01.
- Calls per setup (1, 1, 2, 2, 2): data/scored.csv `calls` for test-01.
- Qwen HTTP 400 on all 24 framework runs: data/scored.csv (24 invalid with error) and README section 9.
- Qwen 1,930 reasoning tokens, 440,000 profit: data/cache_requests.jsonl (Qwen direct short test-01) and README section 3.
- Qwen cost 2.4 to 2.7 times, 5 of 48 empty second calls: README study summary and section 8.
- Step 8 per-company outcomes: data/scored.csv (correct, valid, error), ordered test-01..test-12; matches README section 6 table (Qwen 12/12, 12/9, 11/11, 0/0; Gemma 0 everywhere), 67 correct of 96, 67 of 67 readable.
- "profit wrong in 96 of 96": README section 7 table.

README and data agreed on every number checked; no disagreement found.

Labelled on screen: "Replay of recorded runs" (step 1 caption); the recompute-profit checker is "not tested" (step 8).
The "+ checklist" tracker row is the direct call with detailed instructions; for test-01 every instruction
length gave the same result for both models, so one row per setup is exact.

## What I checked
- render_check.py at 360 and 560 px plus reduced motion: first run FAILed (two titles wrapped at 360 px and moved the controls) and showed label/value collisions ("Owner A 60%", "Goods sold"); shortened titles and labels; second run PASS all checks.
- Looked at the contact sheets and single frames for steps 1, 2 (560 px), 5, 6, 7, 8: one idea per step visible, active tracker row highlighted, captions match the drawing, no cramped text after the fixes. Changed the "empty reply" mark from amber to ink so amber means only checker feedback.
- Recorded with record.py in under 2 minutes: explainer.mp4 (3.3 MB, 55 s) and explainer.gif (8.3 MB); checked a tiled frame per ~6 s of the MP4.
- card.png: step 5 (checker passes a wrong profit), 380 px viewport at 2x.
- Not checked: real phone hardware, screen-reader reading order beyond the kit's aria labels.
- One kit observation: at 360 px there is a ~100 px gap between caption and legend (reserved caption height plus the empty action row); harmless but loose.
