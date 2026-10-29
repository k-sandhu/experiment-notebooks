# Run history and settings

This file records how the study was set up and run, in date order, for readers who want to check the work. The README and the notebook give the explanation and the results. All times are UTC. The machine-readable design is in `protocol.json`; this file links to it and does not replace it.

## Design, recorded before any model call (22 October 2026)

`protocol.json` records protocol `verification-costs-v1.0`. Its fields, in plain words:

- Invoices: 12 trial invoices (split `dev`, random seed 20261022) and 72 test invoices (split `test`, seed 20261195), generated in code with exact answers. The trial invoices are called "development" cases in the code and data files.
- Unit: one invoice per request.
- Models: Qwen3.8 Flash through OpenRouter (`qwen/qwen3.8-flash-20260826`), GPT-6.1 Sol through `codex exec` (`gpt-6.1-sol`), Claude Opus 5.5 through `claude -p` (`claude-opus-5-5`). In the code the three roles are `cheap`, `strong` and `verifier`; the second Qwen call is `repeat`.
- Tuning (field `tuning`): "No changes after freezing either split". The trial run checked that calls ran and replies parsed; no prompt, invoice or setting changed after it.
- Retry (field `retry`): one retry only for a transport failure or a reply that does not parse; both attempts are charged. No retry for a wrong answer.
- Selection (field `selection`): all 72 test invoices, no exclusions based on outputs and no inserted errors.
- Scoring (field `scoring`): exact pair of decision and cents, against two separately written rule programs (decimal and whole-number arithmetic).
- Prices (field `price_scenario`): GPT's cost per call is unknown and treated as a parameter; Claude's `total_cost_usd` is a list price, not a bill.
- Escalation (field `evaluation`): escalation routes reuse GPT's standalone answer and are charged a full GPT call and its time each time they use it.
- Hashes: `case_hash` and `gold_hash` in `protocol.json`; SHA-256 of the main data files in `manifest.json`.

Model sources and dates were checked on 22 October 2026 (`provenance.json`, `sources.json`). OpenRouter's catalogue entry for Qwen was saved at 21:11:44 (`model_catalog.json`). The environment was recorded at 21:11:45: Python 3.12.5 on Windows 11, codex-cli 0.160.1, Claude Code 2.1.296 (`environment.json`).

## Settings

- Qwen3.8 Flash: `max_tokens` 1200, `temperature` 0.3, reasoning disabled, `response_format` JSON object. Seed 20261022 for the first call and 20361022 for the second call, plus 1 on a retry. OpenRouter returned the model name `qwen/qwen3.8-flash` and the provider Alibaba on all 168 calls. HTTP timeout 180 seconds.
- GPT-6.1 Sol: `codex exec --skip-git-repo-check --ephemeral --ignore-user-config --sandbox read-only`, with shell, apps, plugins, multi-agent, browser, computer use, image generation and code mode disabled, `web_search="disabled"`, `model_reasoning_effort="low"`, JSON event output. Codex reported no model version. Every one of the 84 event streams contains a notice that Code Mode is unavailable (an item of type `error`); the notebook ignores it and reads the last agent message. Timeout 240 seconds.
- Claude Opus 5.5: `claude -p --tools "" --safe-mode --no-session-persistence --output-format json --effort low --max-budget-usd 0.25 --model claude-opus-5-5`. The CLI reported usage under `claude-opus-5-5`. Timeout 240 seconds.
- Concurrency: at most 3 requests at a time.
- Spending caps (limits, not targets): USD 5 for OpenRouter with USD 0.02 reserved per call in flight; USD 20 of Claude list price with USD 0.25 reserved per call; at most 700 new calls in a full run and 24 in the default live smoke run of 2 trial invoices.

## Trial run, 12 invoices (22 October 2026, 21:10:38 to 21:11:59)

Field `collected_at` in `cache_requests.jsonl`. Results in `evaluations_dev.json`: Qwen's first call was exact on 1 of 12 (`dev-012`, the only hold), its second call on 1 of 12, GPT on 12 of 12, and Claude accepted 1 answer (`dev-012`). No reply needed a retry. The trial calls cost USD 0.002689 on OpenRouter and USD 0.337370 at Claude's list price; both are included in the spend totals. Trial invoices never enter the results.

## Test run, 72 invoices (22 October 2026, 21:12:20 to 21:19:41)

- 288 answers were needed (72 invoices × 4 roles). Three Claude first attempts could not be parsed because Claude wrote its working before the JSON object: `test-013`, `test-025` and `test-061`. Each was retried once and the retry gave the same verdict (reject). The first attempts cost USD 0.0198148, USD 0.0194868 and USD 0.0198548 at list price. Their text is in `prompts.md`.
- No call returned a transport or model error. No invoice was excluded.

## Spend for the whole run (`spend.json`)

- 339 calls: 168 OpenRouter, 84 Codex, 87 Claude (3 of them retries).
- OpenRouter charged USD 0.018353586; no OpenRouter call lacked a price.
- Claude's CLI reported USD 2.1918244 at list price; no Claude call lacked a list price. The subscription charge is unknown.
- GPT's subscription charge is unknown, not zero. Its calls used 1,095,256 input tokens (685,056 cached) and 13,524 output tokens.
- Total measured request time: 1,557.6 seconds.

## Replay checks (22 October 2026)

- 21:25:00: a network-blocked replay executed every code cell with 0 subprocess and 0 HTTP attempts, 0 new model calls and an unchanged cache (`offline_replay_check.json`).
- The notebook's last cell writes `validation.json`: offline cache-miss guard working, request hashes valid, the exact answers absent from every prompt, 336 replies for 336 expected (84 invoices × 4 roles), no exclusions.
- `presentation_validation.json` records the checks made on the first README: contents links, figure files, three visual fixes to the figures (wrapped matrix labels, labelled cost-map regions, a "HOLD" note on the zero-amount example), and, at 21:31:06, the replacement of dollar signs with "USD" in prose so that notebook renderers do not read them as mathematics (170 per file, field `currency_signs_replaced_by_USD_in_each_artifact`).

## Text-only revisions

- 24 October 2026: the README and notebook openings were rewritten to introduce the topic more gradually (commit `5923cdbf`). Markdown only; code, outputs, data and figures unchanged.
- 26 October 2026: merged to `main` with notebook 22 in pull request #41, closing claim issue #39.
- 28 October 2026: the README and notebook markdown were rewritten for readers new to the topic. No model calls, no re-run; code cells, outputs, figures and existing data files unchanged. The full prompts and per-invoice calculation tables moved from the README to `prompts.md` and `worked_examples.md`, which a script generated from `cache_requests.jsonl`, `cases.json`, `gold.json` and `evaluations_all.json`. The old "Collection and scoring details" block at the end of the README was deleted. New counts were computed read-only from the saved data after the results were known: Qwen's results by kind of invoice, its answers between USD 120 and USD 140, the repeat check's outcome under looser agreement rules (within USD 1 and USD 5), the authorised amount appearing in Claude's 58 rejection reasons, and Qwen's reasons that contain figures. The author list of the arbitrage paper was changed to match its arXiv page.

## Figures to change on a future re-run

The figures were left as drawn. Their reading guidance in the README explains these issues:

- `workflow_outcomes.png`: the "58" label on the dotted bar is hard to read, and the title says "gates" for the two checks.
- `payment_exposure.png`: only one route has bars; a scatter of Qwen's answer against the authorised amount for the 58 payable invoices would show the errors.
- `verification_errors.png`: two identical grids under a title that describes the method, not the finding.
- `economic_frontier.png`: the two Claude routes are in the legend but never cheapest, and the title's point about the price of errors applies only to Qwen alone. Lines of cost per invoice against GPT price, one per route, would show the break-even prices directly.
- All figures use the code names (`Qwen direct`, `GPT direct`, `Qwen repeat + GPT`, `Claude screen + GPT`, `Claude screen + review`) rather than the plain route names used in the text.
