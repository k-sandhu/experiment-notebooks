# Notebook 30 protocol history

Records for someone checking the work. The README and notebook give the parts that change how far to trust
the result.

## Design, fixed before any model call (29 October 2026)

- Claim issue: k-sandhu/experiment-notebooks#87 ("Notebook 30: workbook-to-statements").
- Data: 20 fictional workbooks generated in code (`data/workbooks/`, hashes in `workbook_manifest.json`),
  ground truth and cell logs in `data/ground_truth/`. Two planted source errors (TW-CH01 cash flow gap of
  CHF 37k; TW-KE01 administrative subtotal with two digits swapped).
- The field checks were validated on a perfect conversion built from the cell log before any model ran:
  18 workbooks pass, the two planted errors pass only when declared. An all-zero output originally passed
  every tie-out, so the "not empty" check (`Z`) was added at this stage, before any model output existed.
- The keyword mapper was developed on TW-UK01, TW-KE01 and TW-SE01 until all three were right, then frozen.
- Scoring rule: a statement is right only if all 66 amounts (within half of the workbook's smallest unit) and
  the entity code, currency and both period ends match. Statuses: pass, pass with exceptions, fail, error.

## Models and settings

| Role | Model id | CLI | Settings |
|---|---|---|---|
| writer | `claude-sonnet-5-5` | Claude Code 2.1.296, `claude -p` | `--tools "" --safe-mode --no-session-persistence --effort medium --max-budget-usd 2.00` |
| writer | `gpt-6.1-sol` | codex-cli 0.160.1, `codex exec` | read-only sandbox, shell, apps, plugins, browser, computer use, image generation and web search disabled, `model_reasoning_effort="medium"` |
| reviewer | `claude-opus-5-5` | Claude Code 2.1.296, `claude -p` with stream-json image input | `--tools "" --safe-mode --effort medium` |

The CLIs take model aliases, not dated versions; the cache records the exact request for every call.
Limits: 3 repairs after failed field checks, 1 repair after the visual review, 60 seconds per adapter run,
1,200 seconds per model call, at most 400 new calls and $60 of new Claude spend per run.

## Harness changes made during development

A smoke test (TW-UK02 with Claude Sonnet 5.5) and a test batch of four pipelines (TW-CH01, TW-KE01 and
TW-SG01 with Sonnet; TW-UK02 with GPT-6.1 Sol) ran before the main run. They led to two changes, made before
the main run started:

1. The static check used an allow-list of standard-library modules and rejected GPT-6.1 Sol's harmless
   `import numbers`. It was replaced by a deny-list of risky modules (files, processes, network).
2. The reviewer flagged correctly declared source exceptions as medium issues, which triggered pointless
   repairs. The review prompt now lists the preparer's declared exceptions and asks the reviewer to report
   them again only if the declaration is wrong.

The test runs' folders were deleted and the main run started from scratch, reusing cached responses only
where the request was identical.

## Main run (29 October 2026, 17:27 to 17:57 UTC for the model calls)

- 40 pipelines (20 workbooks x 2 writers), 6 in parallel.
- One pipeline (GPT-6.1 Sol, TW-UK01) crashed the harness: the adapter's error message contained "£", the
  child Python wrote it in the Windows code page, and decoding it as UTF-8 failed. The adapter process now runs
  in UTF-8 mode (`-X utf8`) and tolerates undecodable bytes; the pipeline was re-run with the same cached
  first response and one new repair call.
- During the first notebook execution, Jupyter's `FORCE_COLOR` setting made the adapter process print coloured
  tracebacks, which changed the repair prompts and missed the cache. The adapter process now runs with
  `NO_COLOR=1` and without `FORCE_COLOR`; no result changed.
- Planted-mistakes test, added after the main run showed no wrong number reaching a PDF: 20 mistakes (5 kinds x
  4 workbooks), assigned to workbooks in a fixed table in the notebook, applied to Claude Sonnet 5.5's final
  outputs, 20 new review calls.

## Cache

`cache_cli.jsonl` holds the 110 calls the final notebook replays. Nine calls from development that the replay
does not use (one Codex, eight Claude, $0.67 at list price) were removed; `development_calls.json` records them.
