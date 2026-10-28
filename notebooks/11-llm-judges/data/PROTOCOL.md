# Notebook 11 protocol history

Run history for the LLM-judge experiment, in date order. The README and notebook give the reader only the parts
that change how far to trust the result. Times are UTC. Every number here comes from a file in this folder.

## 2026-10-17: first version (12 hand-written pairs)

- Twelve authored candidate pairs: a plain error, a "stress" error and an equivalent-answer tie for each of four
  task families (arithmetic, extraction, grounding, policy). The stress cases included an evaluator-directed
  instruction inside a candidate, an invented breach, and a refusal followed by the forbidden action. Candidates
  were authored, so no judge graded its own output.
- Judges: Claude Opus 5.5 (`claude -p`, model `claude-opus-5-5`, `--effort low`, `--max-budget-usd 0.50`) and
  GPT-6.1 Sol (`codex exec`, model `gpt-6.1-sol`). Two prompts: "quick" and an "evidence rubric". Both answer
  orders. Three pairs per call, so 32 calls produced 96 ratings.
- Result: both judges matched the gold choice in 96 of 96 ratings, with no order change, invalid output or
  abstention (`summary.csv`, `order_checks.csv`, `judgments.csv`). The original README reported a Wilson 95%
  interval of 75.7% to 100% over 12 pairs, treating pairs as independent; the three pairs per family share one
  scenario, so that interval overstates the evidence.
- The evidence-rubric prompt supplied answer-specific criteria as well as instructions, so it changed the
  information available to the judge, not only the method.
- Spend: Claude list-price equivalent $0.2590728; Codex subscription, incremental dollars not exposed; OpenRouter
  $0 (`spend.json`). `model_catalog.json` lists three OpenRouter models, but no OpenRouter call was made.

## 2026-10-22: second design (protocol `nb11-extension-v2.0`)

The first version could not separate the judges, so the study was rebuilt. Files are in `extension_v2/`; the
folder name, the protocol identifier and the `extension_` prefix on figure files are historical names from when
this design was added to the first one. It is the current study.

- Design changes: seeded generators (seed 20261022) for 144 fresh tasks (24 development, 120 test) across the
  same four families, six answer relationships per family including both-good, both-bad and missing-source
  cases; opaque case IDs; condition labels hidden from judges; helper references separated from the prompt
  method; malformed outputs reported separately; three prompts (`direct`, `rubric`, `evidence`).
- 14:36:21: one authoring call to Muse Wonder (`muse exec`, model `muse-wonder-full-1.0`, `--reasoning-effort
  low`, `--max-model-steps 1`, shell, write and web tools disabled), 183.7 s, for scene-setting sentences and
  style text (`language_templates.json`). No model generated records, candidate values or labels.
- 14:38:57 onward: development collection, 288 single-item ratings (24 tasks x 2 judges x 3 prompts x 2 orders).
  The strict parser rejected 12 of 288, all Claude (direct 8, evidence 2, rubric 2; 9 of the 12 on policy tasks),
  each a prose note before a correct JSON object (`development.csv`).
- After development and before any test call, a secondary parser was specified: recover exactly one `ratings`
  object from surrounding prose, then apply the same schema and ID checks; multiple or conflicting objects fail.
  The strict parser stays primary. No model prompt was changed after development: the contract and method prompt
  hashes are identical in `protocol_development_draft.json` and `protocol_published.json`. The published
  protocol adds the parsing rule, the stress-subset rule and case IDs, the cache-reuse note and the
  score-shopping rule.
- Stress subset, chosen before test collection: one unique-winner test case from generator configurations 0, 2,
  4 and 5 per family (16 cases).
- Confidence thresholds: grid 0, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99, 1.01; choose on development only the lowest
  threshold with at most 5% observed error and at least ten automatic decisions. Both judges were assigned 0
  (Claude 19 development decisions, GPT 20, no errors; Wilson upper bounds 16.8% and 16.1%;
  `thresholds_published.json`).
- 14:46:51: protocol frozen after the 288 development calls (`freeze_record.json`: protocol hash
  `40f63282...`, cases hash `d029d7f6...`). The validation check `test_collected_after_protocol_freeze` passed.
- 15:05:16: environment recorded (`environment.json`): Windows 11 (10.0.26300), Python 3.13.5, codex-cli
  0.160.1, Claude Code 2.1.296, Muse Code 1.4.11. Libraries at replay: pandas 2.3.1, numpy 2.2.6, matplotlib
  3.11.2.
- Test, stress, batch, single-answer and ranking collection followed; the last request completed at 15:25:49.
- CLI settings: Claude `-p --tools '' --safe-mode --no-session-persistence --output-format json --effort low
  --max-budget-usd 0.3`; Codex `exec --skip-git-repo-check --ephemeral --ignore-user-config --sandbox read-only`
  with shell, apps, plugins, multi-agent, browser, computer use, image generation and code mode disabled,
  `web_search="disabled"` and `model_reasoning_effort="low"`. The CLIs returned no dated model snapshot; Claude's
  usage record names `claude-opus-5-5`, and Codex returns no model ID.
- Every one of the 986 Codex replies has a "Code Mode is unavailable because code-mode host is disabled" notice
  in its raw event log, a consequence of disabling code mode; the agent message followed normally in every case.
  All 1,973 requests returned exit code 0; none was marked failed.
- Calls: 2,152 evaluation jobs (288 development, 1,440 test, 320 stress, 8 batch jobs of four ratings, 64
  single-answer, 32 ranking) and 1 authoring job; 1,973 distinct cached requests (986 Claude, 986 Codex, 1 Muse).
  The cache key is the full request: prompt, model ID, CLI options and replicate number. Identical requests,
  such as swapped identical candidates, share one reply; the repeat variant uses a new replicate. Failures would
  be cached too; there are no hidden retries or replacement models.
- Spend: Claude list-price equivalent $28.0508114, not the subscription invoice; Codex and Muse incremental
  dollars are not exposed; no OpenRouter calls (`spend.json`).

## 2026-10-22: preserving the first version

- The first version's notebook and README were copied to `pilot_v1/` (`11_llm_judges_original.ipynb`,
  `README_original.md`), with copies of its data and figures. The original files directly under `data/` and the
  original three figures (`gold_agreement.png`, `order_and_tasks.png`, `error_example.png`) were left unchanged.
  Their hashes are in `pilot_v1/preserved_files.json` and `extension_v2/manifest.json`; the notebook's checks
  `original_pilot_unchanged` and `original_96_ratings_preserved` passed (`extension_v2/validation.json`).
- The archived README refers to the notebook's former file name; the archived notebook is
  `11_llm_judges_original.ipynb`. Copy the folder before re-running it so the preserved outputs stay unchanged.

## 2026-10-27: reader text rewritten, no data changed

- The README and notebook markdown were rewritten to the repository's writing rules. No code cell, output,
  figure or data file changed, and no model was called.
- Earlier text said that, after recovery, Claude made one wrong choice in the formatted stress variant and one
  with a corrupted reference. Both are the same task (`0bfa48d9d0e7`), and both replies remain unreadable after
  recovery: each contains a first grade choosing A, a correction line, and a second grade choosing B, and the
  recovery parser rejects two grade objects (`extension_v2/stress_recovered.csv`, column `failure`). No readable
  stress reply was wrong.
- New counts in the rewritten text were computed read-only from saved files: readable-rating accuracy from
  `test.csv` (`valid`, `correct`); the shape of the 85 distinct unreadable test replies and of Claude's 19
  unreadable single-answer and 10 unreadable ranking replies from `cache_requests.jsonl` (`response.text`);
  unreadable counts by family and by development run from `test.csv` and `development.csv`; and the recovery
  columns of the routing and answer-selection tables by applying the notebook's rules to `test_recovered.csv`.

## 2026-10-28: figures redrawn by an offline replay, no data changed

- Only plotting and display code changed: a shared block of figure labels, colours and drawing helpers in the
  setup cell, and the plotting lines of nine other cells. No line that loads, parses, scores or caches a reply changed.
  The notebook was re-run with `NB_LIVE` unset and no API key in the environment: every reply came from
  `extension_v2/cache_requests.jsonl`, with zero model calls and $0 spent.
- A replay of the unchanged notebook first reproduced every data file and every text output. The only
  differences were the Python, pandas and numpy versions that `extension_v2/validation.json` and the last
  code cell record (this replay used Python 3.12.5, pandas 3.0.6, numpy 2.5.4 and matplotlib 3.11.2). The
  committed `validation.json` was kept; the notebook's printed validation record shows the replay versions.
  After the plotting changes, every data file was again unchanged.
- Every figure now uses the names in the text (direct, checklist and quotation prompts; GPT-6.1 Sol; plain
  names for kinds of work, presentation variants and decision rules) and one colour scheme: blue for Claude,
  orange for GPT, grey hatching for unreadable replies and red cross-hatching for readable wrong answers. The
  figures were renamed from the historical `extension_` prefix; the old files were removed. The data folder
  keeps its name.
- `accuracy_by_parser.png` (was `extension_accuracy.png`): showed strict scores only, with a title that read as
  the headline. It now shows both parsers side by side, splitting each judge and prompt's 120 tasks into
  correct, unreadable and wrong, and the kind-of-work heat map under both parsers. The recovery counts come from
  re-reading the same cached replies inside the plotting cell.
- `parser_rescoring.png` (was `extension_parser.png`): its x labels printed as raw tuples. It now counts the 240
  ratings per judge and prompt under each parser, split the same way, with readable labels.
- `presentation_tests.png` (was `extension_stress.png`): showed changes from the baseline, so the two replies of
  task `0bfa48d9d0e7` that stay unreadable after recovery looked like wrong grades. It now shows each
  condition's 16 tasks as correct, unreadable or wrong, with the baseline as the first bar.
- `review_workload.png` (was `extension_review.png`): the left title named the axis. It now states the finding
  and labels each point with its cutoffs; the right panel uses plain rule names and colours rules by judge.
- `answer_selection.png` (was `extension_utility.png`): the right panel, for score shopping, was empty because
  both counts were zero. It was removed, and the remaining panel adds Claude's picks under the recovery parser
  (60 of 100, from the notebook's selection rule applied to the recovery-parser grades).
- `development_by_parser.png`, `formats_by_outcome.png`, `confidence_check.png`, `latency_by_prompt.png`,
  `acceptance_error_card.png` and `policy_error_grid.png` (were `extension_development.png`,
  `extension_formats.png`, `extension_calibration.png`, `extension_cost_latency.png`,
  `extension_error_example.png` and `extension_policy_error.png`): renamed, relabelled and recoloured as above;
  the development figure uses the same split as the parser figure, the latency figure adds rings for the
  recovery parser, and the calibration and error-grid titles state their findings.
- The README and notebook text around each figure was rewritten to describe the new images, and the sentences
  warning about the old figures' flaws were removed.
