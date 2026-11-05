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
- Judges: GPT-6.1 Sol (`codex exec`, medium effort) was planned as a third judge from a vendor that makes no charts. It could not run before the quota reset. The study was completed with Claude Opus 5.5 and Muse Wonder Full as judges; adding `"sol"` to `JUDGES_USED` and running with `NB44_LIVE=1` would add it.

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

## Settings

- CLI versions: Claude Code 2.1.296, Muse Code 1.4.14, Codex CLI 0.160.1. Each call ran in an empty temporary folder: `claude -p --tools "" --safe-mode --no-session-persistence --system-prompt "You are a helpful assistant."` with stream-JSON input for images; `muse exec --preset empty --max-model-steps 1` with web, write, shell and user-input tools disabled.
- Efforts: chart makers high (Claude `--effort high`, Muse `--reasoning-effort high`, DeepSeek `reasoning.effort = high`); judges medium; Kimi K3.1 Pro at the provider default.
- OpenRouter: `max_tokens` 32,000, provider pinned with fallbacks off.
- Timeouts: 900 s per model call, 180 s per chart render. Charts saved at 100 dpi with `bbox_inches="tight"`.
- Spend: 954 cached calls; \$18.28 Claude list-price equivalent, \$4.55 on OpenRouter, Muse unpriced.
