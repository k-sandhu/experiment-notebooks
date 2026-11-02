# Notebook 17 run history

This file records the settings, changes and incidents behind notebook 17, in date order, for readers who want to
check the work. The README and the notebook give the results. Times are UTC unless a commit time is quoted with its
own offset. The rewrite of the README and notebook text in October 2026 changed text only and made no model calls.

## Inputs from the earlier study

- The earlier study is notebook 15 (protocol `nb15-v1`, collected 2026-10-19). Its cases, drafts, judgments, flags,
  catalogue, model dates, prompts and the 276 cache entries behind the 108 sampled drafts were copied into
  [`legacy/`](legacy/), with SHA-256 hashes and the source commit `b5305ace` in
  [`legacy_provenance.json`](legacy_provenance.json).
- Its charged-or-reserved OpenRouter bound, $4.4500, was reserved before any new paid request, so the two studies
  share one $10 cap ([`protocol.json`](protocol.json), `budget`).

## Protocol and cases frozen before collection (commit `3b26cf04`, 2026-10-20 20:53 -04:00)

Saved before any draft or score was collected: [`protocol.json`](protocol.json), [`cases.json`](cases.json),
[`tasks.json`](tasks.json), [`legacy_sample.json`](legacy_sample.json), [`passage_sample.json`](passage_sample.json)
and the model catalogue.

- Protocol version `nb17-v1`, seed 20261020, `created_before_collection: true`.
- 24 cases: six decision types (value threshold, procurement, case mix, capacity, uncertain scenarios, trial with a
  guardrail) × 4 parameter draws, generated at 2026-10-21 00:53:13 UTC, each assigned one document type in rotation.
  Exact answers computed in code; all 24 passed an independent arithmetic and rule check
  ([`fixture_checks.json`](fixture_checks.json)). Packets leave out the licence and session metadata that writers in
  notebook 15 copied into their drafts.
- Document lengths: email 180 to 280 words, six-slide text 200 to 320, web article 700 to 1,000, academic-style report
  1,000 to 1,400.
- Writers: Claude Haiku 5.5, Claude Sonnet 5.5, Claude Opus 5.5, GPT-6 Astra, Muse Wonder Full, DeepSeek V4 Pro; two
  drafts per case from identical prompts in fresh sessions; no regeneration for length.
- Judges and passage judges: Claude Opus 5.5, GPT-6 Astra, GPT-6.1 Sol. All new judges were limited to models called
  through the Codex and Claude Code command-line tools at the repository owner's request; this is recorded in the
  protocol and checked in [`validation.json`](validation.json) (`judges_only_codex_claude`).
- Earlier-study sample: one available draft per writer and document type, picked by a seeded hash without scores
  (108 drafts); one outside-company audit flag per draft where at least two eligible fresh judges remained (96) and
  one unflagged sentence of 30 to 260 characters per draft (108).
- Warning test: one draft per case picked by a seeded hash, each scored alone under the neutral review (`baseline`),
  the habit list (`rubric`) and the habit list plus the AI-slop warning (`warning`), paired by draft and judge.
- Main analysis: outside-company clarity, concern types and passage opinions; average the two drafts within case and
  writer; bootstrap the 24 cases; a six-decision-type sensitivity; judge-specific comparisons. The common panel is
  not named in the protocol.
- Human study: pending by the repository owner's request; no synthetic participant responses.
- Failures and malformed replies are kept as missing; only transport retries; no exclusion by score.
- Command-line options are listed in `protocol.json` (tools off, ephemeral sessions, low reasoning effort). Codex
  0.160.1, Claude Code 2.1.296 and `muse exec` 1.4.11. Every call ran in a new empty temporary folder; on 2026-10-20
  there was no global Codex instruction file, no parent instruction file and no Claude user instruction file
  ([`instruction_context_audit.json`](instruction_context_audit.json)). Model access was rechecked on 2026-10-20
  ([`model_dates.csv`](model_dates.csv)).
- DeepSeek V4 Pro was pinned to Sail Research (`sail-research/us`, FP4) with fallback off and low reasoning; the
  endpoint's dated name is `deepseek/deepseek-v4-pro-20260813` ([`model_catalog.json`](model_catalog.json), refreshed
  for prices at 2026-10-21 00:50:34).

## Parser amendment (2026-10-21 01:43:23)

Recorded in [`parser_amendment.json`](parser_amendment.json) during collection:

- Trigger: 44 completed Codex judge replies had complete records but left off only the outer `]}`; no other JSON
  defect.
- Change: add exactly `]}` only when the open structure is `{[`, outside any string, after a closed record, and only if
  every expected ID, count, numeric bound and field type then validates.
- Raw replies are unchanged. No draft was regenerated and no prompt changed.
- Final effect: 51 main scoring replies (GPT-6 Astra 37, GPT-6.1 Sol 14) and 27 warning-test replies (Astra 17, Sol
  10) were repaired; no passage re-check reply needed it. Strict-only results are saved in
  [`strict_json_writer_sensitivity.csv`](strict_json_writer_sensitivity.csv),
  [`strict_json_adjudication_sensitivity.csv`](strict_json_adjudication_sensitivity.csv) and
  [`strict_json_instruction_sensitivity.csv`](strict_json_instruction_sensitivity.csv). With the amendment the study
  is an amended exploratory study, not a confirmatory one.

## Collection results (commit `d59218ce`, 2026-10-20 23:46 -04:00)

- Drafts: 288 of 288 usable ([`drafts.json`](drafts.json), [`generation_coverage.csv`](generation_coverage.csv)).
  None of the 396 documents in the study names a model ([`authorship_mentions.json`](authorship_mentions.json)).
- Main scoring: 432 requests, two drafts each; 429 readable. The 3 unreadable replies, read from
  [`reviews.json`](reviews.json) in the October 2026 rewrite: two GPT-6.1 Sol replies used the concern type
  `grounding`, outside the allowed four, and one GPT-6 Astra reply returned one of its two records. 282 drafts have
  all three judges' scores.
- Passage re-check: 140 requests, 140 readable; 554 opinions on 204 passages, every passage with at least two.
- Warning test: 216 requests, 216 readable; 55 outside-company judge-and-draft pairs with all three instructions.
- The common-panel sensitivity ([`common_panel_sensitivity.csv`](common_panel_sensitivity.csv)) and the equal
  company weighting within the outside-company panel
  ([`vendor_balance_sensitivity.csv`](vendor_balance_sensitivity.csv)) were computed in this commit, alongside the
  first results.
- Human materials: 64 reader schedules of 8 documents covering 396 documents, 34 editor booklets covering 204
  passages, administrator keys kept apart; human status `pending`, 0 responses
  ([`human_protocol.json`](human_protocol.json), [`human_status.json`](human_status.json)).

## Explanatory additions (commit `641fc02e`, 2026-10-22 10:46 -04:00)

Added after the results, from the frozen replies, with no new model calls:

- the breakdown of each writer's score by judge company ([`judge_panel_components.csv`](judge_panel_components.csv))
  and the per-draft strictness gap ([`same_text_judge_scores.csv`](same_text_judge_scores.csv)), with the figures
  `judge_panels.png` and `same_text_examples.png`;
- six worked examples with prompts, drafts and judge replies ([`explanation_examples.json`](explanation_examples.json))
  and arithmetic checks on them ([`explanation_checks.json`](explanation_checks.json));
- further-reading links checked on 2026-10-22.

## Spend

From [`spend.json`](spend.json):

| Item | USD |
|---|---:|
| Earlier study's charged-or-reserved bound, reserved first | 4.4500 |
| This study's OpenRouter cost reported on replies | 0.1816 |
| This study's OpenRouter replies without a reported cost | 0 |
| Combined charged-or-reserved bound | 4.6316 |
| Shared cap | 10.00 |

Command-line calls ran on subscriptions. Claude Code reported a list-price equivalent of $16.93 for this study's
calls ([`request_usage.csv`](request_usage.csv)).

## Cache

[`cache_requests.jsonl`](cache_requests.jsonl) holds 1,076 requests and 1,081 attempts. Redundant journal snapshots
(2,162 versions, 34.6 MB) were removed, keeping every recorded attempt (24.8 MB)
([`cache_storage.json`](cache_storage.json)). [`manifest.json`](manifest.json) holds the evidence hashes checked on
replay.

## Text rewrite (2026-10-28)

README and notebook text rewritten for new readers. Counts added from existing files: concern types on flagged
passages, passages with at least one or every judge raising a concern, the warning test's unchanged, lower and higher
pairs, the per-draft strictness gap's range, and the kinds of unreadable replies. No code, output or figure changed.
