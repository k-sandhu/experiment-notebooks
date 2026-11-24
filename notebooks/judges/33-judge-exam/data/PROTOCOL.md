# Notebook 33 protocol and run history

This file records how the exam was planned, built, frozen and judged, in date order. The README gives the reader the
parts that change how far to trust the result. Times are UTC on 30 October 2026. The machine-readable record is
[`run_log.jsonl`](run_log.jsonl) (events, hashes, every retry) and [`request_usage.csv`](request_usage.csv) (every
attempt with its time, status, cost and error).

## Plan

The design was set in the claim issue (#94) before any item existed: four families of 60 test pairs (code, worked
calculations, instructions, grounded answers) plus 24 development pairs; exactly one better answer per pair, decided
by code; worse answers written by models that are not judges, with a recorded edit of a passing answer allowed when
no natural failure of the required kind appeared; every pair judged in both orders by six CLI judges, open-weight
judges on OpenRouter and the Decisions API; the eight text judges also solving the 120 code and calculation tasks;
strict and lenient reading rules fixed before the test; and a development rule: if Opus and Sol both scored at least
23 of 24 in both orders on a development draw, make the families harder (whole families, generator settings only)
and draw again. The analysis plan is [`analysis_plan.json`](analysis_plan.json); its first version is
[`initial_analysis_plan.json`](initial_analysis_plan.json).

## Settings fixed before development

| Time | Event |
|---|---|
| 04:49 | Collection started: capability probes and smoke run (a few items per family) |
| 04:54 | First pre-test plan hashed (generator, readers, evaluation, analysis plan) |
| 05:07 | Smoke showed Granite 4.2 8B at its default high reasoning spending the whole output budget with no final text, even at 6,400 tokens. The smoke at that setting was stopped (two requests never returned; 0.02 dollars reserved against the cap) and Granite was set to reasoning off. The large open-weight smoke model, Qwen3 235B (July 2025), was replaced by the more recent DeepSeek V4.1 Flash (17 October 2026) at low reasoning. Qwen's smoke replies stay in the cache and the ledger and are excluded from results |
| 05:13 | Plan text corrected to list all seven instruction-edit categories; no code or data changed |
| 05:21 | A format probe showed that without the provider's JSON mode, Granite with reasoning off wrote long prose that was cut off; with JSON mode it returned JSON in 7 to 9 seconds. JSON mode was switched on for both OpenRouter text judges. Prompt text unchanged; the choice used only format and latency, not correctness |

## Development and the difficulty rule

| Time | Event |
|---|---|
| 05:27 to 05:40 | Draws 1 to 3 (level 1 to 3): Opus and Sol 48 of 48 on each. The three iterations the first plan allowed were used up, and the plan said to report a ceiling |
| 05:42 | Amendment before any test judgment: the iteration limit was extended and all four families made harder (stateful row scan in code tasks, longer calculations, stricter candidate closeness and format rules). A temporary block on the exam output path prevented any freeze or test judgment while development continued |
| 05:46 to 05:59 | In-flight writer requests from an incomplete harder draw were allowed to finish and archived (`pretest_drafts/`); none of them was judged |
| 06:48 | Pre-test validation of 720 generated items passed (generator, checkers, readers, typed-choice payloads) |
| 06:55 | Writers asked to solve and copy in one request often rewrote the supplied reference (9 of 24 fresh pairs failed). A separate copy-only request passed on all 4 probes and was adopted for reference-assisted answers. 15 valid writer-derived pairs were kept. Task text, natural prompts and labels unchanged |
| 07:06 | A development Sol request failed with "Selected model is at capacity", reported only in the CLI's event stream. The transport retry was extended to explicit capacity and temporary-unavailable events; answer text never enters a retry decision |
| 07:06 to 07:29 | Draws 4 to 6 (levels 4 to 6): Opus 48, 48, 47; Sol 48 each. Ceiling rule triggered each time |
| 07:31 | Levels 7 to 9 added: longer instruction messages, signed arithmetic slips, all 12 code templates (development had used 6), common formatting of generated code, writer token budgets scaled to answer length |
| 07:40 | Draw 7b (level 7): Opus 46 of 48 (23 in each order), Sol 48 of 48. Ceiling rule triggered |
| 07:45 | Reading the generated items showed that the fixed arithmetic slip (one ten-thousandth) left a visible pattern in the denominator. The incomplete draw 8b was drained without judging and archived; the slip was changed to one wrong middle digit of the numerator, carried through later steps |
| 08:14 | Two long instruction messages could not be copied whole by the writers. A same-writer chunked copy (pieces of at most 2,200 characters, each verified exactly, joined with recorded whitespace) was added; existing pairs kept |
| 08:16 | Draw 8c (level 8): Opus and Sol 48 of 48. Ceiling rule triggered |
| 08:24 | Reading the items showed repeated clauses that made an edited sentence stand out, and an arithmetic divisibility cue. Draw 9c was drained without judging and archived. Levels 10 to 12 added: distinct generated sentences in 700 to 1,400-word messages (level 10: about 720), plausible one-word edits balanced between insertion and deletion, and the arithmetic slip placed in an operand before the chosen adjustment with balanced sign |
| 08:43 | Draw 10d (level 10): Opus 46 of 48, Sol 44 of 48, Granite 24 of 48. Ceiling rule not triggered |
| 08:57 | Five Granite development replies had been cut off by the token limit after a complete winner and confidence. A conservative prefix reader (an anchored, complete winner and confidence at the start of a reply cut off by the length limit, never a verdict inferred from prose) was added to the lenient rule and tested on the cached development replies with zero new calls: it recovered all five (2 correct, 3 wrong). The complete-JSON-only reading is kept beside it in every table |

Development counts for every draw are in [`development_history.json`](development_history.json) and the
`development_*_judgments.csv` files. No development result used a test pair, and no change was made for one pair.

## Outage before the freeze

| Time | Event |
|---|---|
| about 09:00 | The Codex CLI reported a usage limit ("You've hit your usage limit ... try again at Nov 4th, 2026 1:36 AM"). This blocks every `codex exec` call, including Sol and Luna judgments |
| about 09:06 | A one-word test call outside the notebook returned the same message |
| about 09:07 | The final collector (writing the 240 test pairs) was stopped by hand, because the transport rules at that time did not treat a usage limit as temporary, so Sol and Luna judgments would have been saved as final failures. 60 of 240 test items had been written; no test judgment or solve existed; the exam was not frozen. The last saved attempt is timed 09:07:36. All 280 item files (60 test, 216 development, 4 smoke) were intact |
| 12:24 | A one-word Sol call succeeded |
| 12:28 | Before any further call: every cache and attempt file was searched for usage-limit text (none found, [`quota_cache_audit.json`](quota_cache_audit.json)); usage, quota and credit-limit messages in stdout, stderr or the CLI event stream now stop the collector without saving a reply ([`quota_handling_validation.json`](quota_handling_validation.json), 72 pattern and channel cases, zero network calls); a start-and-return journal of attempts was added ([`attempt_lifecycle.jsonl`](attempt_lifecycle.jsonl)). The stopped collector had no such journal, so up to eight writer calls may have been in flight with unknown charges; 0.08 dollars was reserved against the cap for them |

The outage changed no frozen input: generator, reading rules and evaluation hashes stayed identical to draw 10.

## Freeze and test collection

| Time | Event |
|---|---|
| 12:29 | Final collector resumed from the cache; the 180 remaining test items written |
| 13:34 | Exam frozen at level 10 ([`freeze_record.json`](freeze_record.json), seed 3310302026; SHA-256 of `exam_v1.jsonl`, prompt templates, generator, readers, evaluation and analysis plan, after normalising CRLF to LF). Test judging started |
| 14:18 | Haiku replies on instruction pairs arrived as CLI error envelopes linking Anthropic's usage policy with `Details: [bio]`. Both frozen rules classify them as unreadable (transport error). A descriptive subtype, `provider_safety_block`, was added to the diagnostic table only; no request, reader, retry rule or score changed |
| 14:34 | Every trap pair and every natural error is in the code family (an input-only fact). Code-only summaries for trap and error source were added beside the global ones |
| 15:54 | All 4,320 judgments returned |
| 16:04 | Audit of the 78 unreadable judgments: 73 Haiku policy refusals, 2 Haiku replies with broken JSON (unescaped quotes) that name the right winner, 1 Sonnet reply missing confidence that names the right winner, 1 Decisions API TLS failure, 1 Muse connection failure. Scores stay as the frozen rules give them |
| 16:29 | Review of Muse's only wrong choice (`test-code-002`): the answer it preferred handles row types the hidden tests never send; the answer key and score were kept as frozen |
| 16:58 | All 960 solves returned; collection complete: 9,689 cached attempts in all phases |

Test collection ran from 13:34 to 16:58 (12,219 seconds). Retries were limited to three attempts and triggered only
by rate limits, server errors, explicit capacity or temporary-unavailable errors, and OpenRouter replies cut off by
the token limit (retried with a larger budget). Two connection failures (Decisions API, Muse) matched none of these
and stay as unreadable outcomes.

## Reporting additions after the results

None of these changed an item, a request, a cached reply, a reading rule or a frozen score. Each was checked by an
offline replay with zero new calls and unchanged caches.

1. 17:00 to 17:04: presentation review and final replay (29 figures).
2. After review of the write-up: the number of differing characters between the two answers of each pair
   (`answer_difference.csv`, `answer_difference.png`), calibration in small multiples with a summary of accuracy at
   stated confidence of 90 or more, per-family solve and judge panels, and figure layout and titles. The word-count
   direction split reported in the README (Opus and Sol on messages one word long and one word short) was computed
   after the results were seen and is exploratory.

## Spend

OpenRouter reported 0.87 dollars for writers, open-weight judges and the Decisions API across all phases; with
conservative reservations for attempts that returned no cost and for interrupted requests, the cap accounting is
1.92 dollars of the 5-dollar cap. The CLIs made 4,532 calls, about 90.95 dollars at list prices (Opus 49.00, Sonnet
18.53, Sol 15.89, Muse about 5.45 as a proxy from text length, Haiku 1.75, Luna 0.33). Two early Sol calls returned
no token usage and are left out of the estimate. Per-model figures are in [`spend_by_model.csv`](spend_by_model.csv).

## Environment

Python and package versions, CLI versions and the operating system are in [`environment.json`](environment.json).
Judges and writers ran on provider hardware; local hardware only ran the checkers and the analysis.
