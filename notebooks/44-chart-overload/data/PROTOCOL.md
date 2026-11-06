# Notebook 44 run history

Claim issue: [k-sandhu/experiment-notebooks#116](https://github.com/k-sandhu/experiment-notebooks/issues/116). All times are UTC.

## 2026-11-05: design

The owner asked for a test of whether models overload charts when given more information than one chart should show, with an evolving level of instruction. The owner chose:

- the five-level ladder L0 (bare request), L1 (purpose), L2 (design principles), L3 (priorities), L4 (the L2 chart revised once after the model sees it rendered);
- chart makers Claude Opus 5.5, Muse Wonder Full and one open-weight model picked by smoke test;
- scoring by models only (no human ratings);
- Claude Opus 5.5 in the authoring session to write the code.

Fixed in code before any chart was made: the twelve briefs (seeded generators, frozen in `briefs/`), the roles of every note, the quiz questions, answers and tolerances, the main-message and caveat patterns, the prompts at every level, the output contract (matplotlib, `data.csv`, one 10 by 6 inch figure), one repair call for code that fails, and the judge prompt.

Model choices:

- Open-weight chart maker: DeepSeek V4.1 Flash 1017 (`deepseek/deepseek-v4.1-flash-1017`, permaslug `deepseek/deepseek-v4.1-flash-20261017`, released on Hugging Face 2026-10-17, MIT licence, 763B total parameters), pinned to the DeepSeek first-party provider. On the Artificial Analysis Progress Index page for large open-weight models (checked 2026-11-05) it shared the top place with GLM-5.3, which does not take images on OpenRouter; L4 needs images. Smoke test: it named the tallest bar and its colour in a test chart through both the DeepSeek and DeepInfra endpoints.
- Reader: the claim issue planned GPT-6.1 through `codex exec`. The Codex CLI returned "You've hit your usage limit ... try again at Nov 6th, 2026 7:24 AM" on the first smoke call, so the reader became Kimi K3.1 Pro (`moonshotai/kimi-k3.1-pro`, permaslug `moonshotai/kimi-k3.1-pro-20261023`, Hugging Face repository created 2026-11-02, custom licence, 2.78T total parameters), pinned to Moonshot AI (mxfp4). Qwen3.8 27B was tried as well; both read the title, caveat and two values of a test chart correctly, and Kimi was chosen as the larger model. Moonshot makes no chart in this study.
- Judges: Claude Opus 5.5 and Muse Wonder Full (medium effort), and GPT-6.1 Sol (`codex exec`, medium effort) as a third judge from a vendor that makes no charts. Sol could not run before the Codex quota reset, so the first full run (2026-11-05) used two judges; Sol's 192 judgements were added on 2026-11-06 with the same judge prompt (entry below).

Because the briefs were written for this study, training cutoffs do not affect leakage; release dates are recorded above for completeness.

## 2026-11-05 17:54: smoke test on B01

Nine generation calls (B01 at L0, L2 and L4 for each chart maker). Eight succeeded. Muse Wonder Full's L4 call failed with "agent loop failed: model did not reach a terminal state within 1 step(s)". The same command, run twice by hand, succeeded both times, so the failure was treated as transient: the call layer now retries a failed call up to two more times (5 and 10 s waits) and stops the run on a usage-limit error. The failed call was retried in the full run under the same cache key.

Reader and judge smoke test on three B01 charts (reference, Claude Opus 5.5 L0, DeepSeek V4.1 Flash L2), 12 calls. Claude Opus 5.5 as judge reported that the first draft of the B01 reference chart showed "Price 79to89": the dollar signs had been read as matplotlib maths. The author found the same problem in the B04 and B06 reference charts, escaped the dollar signs in all three, moved one overlapping label in B05, inverted the bar order in B03, and added the before and after averages to B01 (the reader had misread the "after" value from the axis). The four reader and judge calls on the first B01 reference draft remain in the cache but are not used. The other 17 smoke-test calls had exactly the same requests as calls in the full run and were reused.

## 2026-11-05 18:07 to 19:00: full run

Generation: 144 drafts (L0 to L3) and 36 revisions (L4), concurrency 4 for Claude, 4 for Muse and 6 for OpenRouter. All 180 replies contained code. Two needed one repair: DeepSeek V4.1 Flash B08 L3 (`KeyError: 'date'`, the column had been made the index) and Muse Wonder Full B12 L2 (`grid_colour` is not a matplotlib keyword). No call failed after retries.

Scoring: 192 charts (180 plus 12 reference) by the reader (2 calls each) and two judges (1 call each). All 384 reader replies parsed. One of 384 judge replies did not parse (Claude Opus 5.5 on B10, DeepSeek V4.1 Flash, L1); that chart's judge scores use Muse Wonder Full alone.

Langfuse was not running during the run (its health check did not answer), so no calls were traced. Run `python D:\projects\langfuse\backfill\backfill_traces.py --only 44` when it is back.

## 2026-11-05: changes to scoring after the results were seen

Two changes, both reported in the notebook and README with the numbers under the original rule:

1. Range answers. Ten reader answers to one B12 question ("roughly what was the cut in the other districts?") gave the range printed on the chart, "17-27". The first parser read the first number (17, outside the 3-point tolerance of 21.7). The parser now reads a range as its midpoint. Critical score by level, first parser then fixed parser: L0 0.90 and 0.90, L1 0.89 and 0.90, L2 0.81 and 0.81, L3 0.97 and 0.98, L4 0.84 and 0.84. The reference charts went from 0.99 to 1.00.
2. Titles drawn as free text. Some charts draw their title with `fig.text` or `ax.text` instead of `set_title` or `suptitle`, so the counter classed it as an annotation. The label count now treats the topmost text item as the title when it is an annotation at least as large as any proper title. Labels per chart by level, before then after: L0 15.4 and 15.4, L1 12.5 and 12.1, L2 5.6 and 5.3, L3 7.9 and 7.4, L4 6.2 and 5.6. L3 minus L2 changed from +2.3 to +2.1 labels.

Not changed: the main-message and caveat patterns. All reader summaries that missed a pattern were read by the author. Of the seven main-message misses, two would be accepted by a person (B08 Claude Opus 5.5 L2, B12 DeepSeek V4.1 Flash L1). Of the caveat answers, five charts named a harmless secondary caveat where both judges say the critical caveat is on the chart; the notebook reports the judge-based alternative beside the quiz score.

The garbled-dollar measure (text with a pair of unescaped `$` signs whose content starts with a digit) was defined after the charts were seen, as a description of a defect the judges and the author noticed, not as part of the planned scoring.

## 2026-11-06 14:22 to 18:16: GPT-6.1 Sol added as the third judge

Approved by the owner on 2026-11-05 and run by a scheduled task. A one-line `codex exec` call to `gpt-6.1-sol` at 14:22 answered, so the quota had reset. The only change to the notebook code was `JUDGES_USED = ["opus", "sol", "muse"]` in the setup cell; prompts, model settings and images were unchanged, and every other call replayed from the cache.

- First attempt, 14:24. The first six Sol calls (B01 reference and Claude Opus 5.5 L0 to L4) failed after three tries each with `'"node"' is not recognized`. The npm `codex.cmd` launcher runs through `cmd.exe`, and the session's PATH (15,766 characters, 196 entries) was over `cmd.exe`'s 8,191-character limit, so `cmd.exe` saw no PATH. The run was stopped, the six error rows were removed from `cache/calls.jsonl`, and the notebook was run again with a deduplicated PATH (46 entries, 2,004 characters) in the environment.
- Second attempt, 14:29 to 18:16. 192 Sol calls, at most 2 at a time; all succeeded and all 192 replies parsed. The computer slept from about 14:35 to 17:56. Two calls in flight (B03, Muse Wonder Full, L1 and L2) hit the 900 s timeout and succeeded on their first retry; their recorded `elapsed_s` (about 12,100 s each) includes the sleep. Usage reported by the Codex CLI: 3.04 million input tokens, 54,216 output tokens (23,950 of them reasoning). Codex reports no price.
- Langfuse answered its health check, so the 192 Sol calls were traced during the run. The six failed first-attempt calls were traced too, under the same span IDs as the successful calls, so those six traces in Langfuse hold one ERROR and one successful observation each. The 954 calls from 2026-11-05 are still untraced: `backfill_traces.py --only 44` finds no files, because it reads only `.jsonl` files with "cache" in the file name and this notebook's cache is `cache/calls.jsonl`.

What changed in the reported numbers (two judges, then three):

- Judge-based means by level, L0 to L4: secondary notes called out 1.50, 1.19, 0.44, 0.14, 0.50 became 1.58, 1.23, 0.44, 0.14, 0.50; overload 3.06, 2.67, 1.58, 1.88, 1.43 became 2.96, 2.55, 1.57, 1.86, 1.41; clarity 3.64, 4.19, 4.61, 4.64, 4.76 became 3.71, 4.25, 4.51, 4.70, 4.64; overall 5.94, 6.74, 7.49, 7.94, 8.08 became 6.24, 6.99, 7.50, 8.13, 8.00; errors listed per chart 2.19, 2.01, 1.07, 0.83, 0.42 became 1.81, 1.74, 0.89, 0.74, 0.39. Reference charts: overload 1.42 to 1.36, overall 8.63 to 8.67.
- The overall rating no longer rises at every level: L3 (8.13) is now above L4 (8.00). GPT-6.1 Sol rated L3 0.67 above L4 (interval 0.06 to 1.19); Claude Opus 5.5 and Muse Wonder Full did not.
- Overload L0 to L2: difference 1.47 (interval 1.24 to 1.74) became 1.39 (1.12 to 1.69). Rank correlation of labels with overload: 0.56 to 0.57.
- Judge agreement is now reported for three pairs: Opus and Sol 0.75, 0.67, 0.79 (overload, clarity, overall) and 95.1% of note calls; Opus and Muse unchanged (0.81, 0.73, 0.82, 96.5%); Sol and Muse 0.81, 0.57, 0.75, 96.5%.
- Garbled dollar amounts: still noticed by at least one judge on 26 of 40 charts; Sol mentioned them in 28% of its judgements of those charts.
- The caveat rule "most judges say the chart left out the affected data" now means two of three. One chart changed: Claude Opus 5.5's L0 chart for B11, where Sol and Muse say "avoided" and Opus says "missing". Its critical score went from 0.58 to 0.92. Caveat handled at L0: 86% to 89%. Critical score at L0: 0.90 to 0.91 (first parser 0.90 to 0.91); Claude Opus 5.5 at L0: 0.89 to 0.92; L0 to L1 difference -0.00 to -0.01. Caveat by the judges' reading at L0: 92% to 94%. Misses agreed by both caveat measures: five to four. No other reader-based number, label count or level contrast changed.

## Settings

- CLI versions: Claude Code 2.1.296, Muse Code 1.4.14, Codex CLI 0.160.1. Each call ran in an empty temporary folder: `claude -p --tools "" --safe-mode --no-session-persistence --system-prompt "You are a helpful assistant."` with stream-JSON input for images; `muse exec --preset empty --max-model-steps 1` with web, write, shell and user-input tools disabled.
- Efforts: chart makers high (Claude `--effort high`, Muse `--reasoning-effort high`, DeepSeek `reasoning.effort = high`); judges medium; Kimi K3.1 Pro at the provider default.
- OpenRouter: `max_tokens` 32,000, provider pinned with fallbacks off.
- Timeouts: 900 s per model call, 180 s per chart render. Charts saved at 100 dpi with `bbox_inches="tight"`.
- Codex: `codex exec --skip-git-repo-check --ephemeral --ignore-user-config --sandbox read-only -m gpt-6.1-sol -c model_reasoning_effort="medium" -c web_search="disabled" --json` with shell, apps, plugins, browser, computer-use, image-generation and code-mode features disabled, chart image attached with `-i`.
- Spend: 1,146 cached calls; \$18.28 Claude list-price equivalent, \$4.55 on OpenRouter, Muse and Codex unpriced.
