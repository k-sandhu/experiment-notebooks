# Notebook 35 protocol and run history

This file records how the study was planned, frozen and run, in date order. The README gives the reader the parts
that change how far to trust the result. Times are UTC on 30 October 2026 unless stated.

## Plan

The design was set in the claim issue (#96) before any data was mined: mine earlier and accepted README paragraphs
from the rewrite merges of 27 to 30 October 2026, split them by document into training and test halves, and compare
six kinds of guidance (no guidance M0, written rules M1, 8 random past choices M2, 8 similar past choices M3, a rubric
distilled once by a top model M4, rules plus random choices M5) for four judges in both orders, with a mechanical rule
checker as a non-model baseline. The planned test size was at least 120 pairs, and the planned analysis included a
split into "mechanical" pairs (the rule checker prefers the accepted version) and "substantive" pairs.

Fixed before any test call: the pair file, the split, the example draws, the rubric, every prompt, the model settings,
the strict and lenient reading rules and the analysis plan (`analysis_plan.json`). The freeze record is
`freeze.json`; its SHA-256 is `d060f6ca813de39b91e9899abcb7f362a4bc21ebfcef2d17575bf1897373de1e` after the
pre-test provenance additions listed below.

## Data extraction and amendments before the freeze

All of these changes were made from the text alone, before any test-pair judgment existed. The development source
documents stayed in the training half throughout.

1. Initial extraction matched single paragraphs one to one and found 75 eligible pairs. Matching was widened to
   groups of one to three neighbouring paragraphs, because rewrites often split or merged paragraphs; 126 eligible.
2. A text audit found groups that crossed section headings and quoted model prompts (blockquotes) that were never
   rewritten. Groups were restricted to one section and blockquotes excluded; 108 eligible.
3. A second text audit found that the three pairs the rule checker preferred were false positives: "harness" used as
   a noun, which AGENTS.md allows, and weak alignments. The checker was changed to count "harness" only as a verb
   followed by a determiner, and pairs now also need sequence similarity of at least 0.20; 88 eligible (46 training,
   42 test), none mechanical.
4. Sample allocation: the strict content checks left too few pairs for 120 tests. All 42 eligible test pairs were
   kept; 6 training pairs became the development slice and 40 the pool for examples and the rubric.

Filter counts are in `filter_counts.json`; the archived intermediate extractions are in `pre_freeze_v0/` and
`pre_freeze_v1/`.

## Development and smoke checks

| Time | Event |
|---|---|
| 04:54 | Design recorded before development (126-pair version; later superseded by amendment 3) |
| 05:02 | Smoke run finished: 96 calls on training-only notebooks, 91 strictly readable; data and first rubric archived in `pre_freeze_v0/` |
| 05:03 to 05:12 | Development run: 128 requests on the 6-pair development slice, 125 strictly readable; no judge near 100% with no guidance |
| 05:13 | Test design frozen: 2,016 test requests |
| 05:13 | Pre-test provenance manifest: hashes added for parser fixtures, amendments, environment, data audit, authorship records and display adapter; no test calls yet |

Development showed Qwen3.5-9B often spending its 4,096-token output allowance on hidden reasoning and returning
empty content. Its allowance was raised to 8,192 tokens, with 16,384 on a retry, at medium effort, before the freeze.
Every earlier attempt is kept and charged in `request_usage.csv`.

The rubric was distilled once by Claude Opus 5.5 (`claude -p`) from the 40 example-pool pairs. It came back at 740
words against a 650-word instruction and was kept unchanged (`rubric_v1.md`, prompt in `rubric_prompt.txt`).

## Test collection

| Time | Event |
|---|---|
| 05:14 | Test collection started, 2,016 requests |
| 05:43 | CLI isolation audited during collection: Claude `--safe-mode` disables CLAUDE.md and customisations; Codex ignores user configuration with `project_doc_max_bytes=0`; no request settings changed |
| 07:37 | Test collection finished: 2,016 judgments, 2,174 new attempts in this phase |

Wall time from first start to last finish of test collection was 8,615 seconds. Retries were bounded (at most three
attempts) and triggered only by transport failures or Qwen's empty, length-truncated replies, never by the content
of an answer.

### Outage

One GPT-6.1 Sol request (method M1, pair `p35_b8827a3556adf4e8`, Sol shown the accepted version first) failed with
"Selected model is at capacity. Please try a different model." The CLI reported this only in its JSON event stream
with an empty stderr, so the harness's transient-error detector did not retry. The request stays cached and counted
as unreadable (a failed request); it was not recovered or re-scored. Its largest possible effect is one judgment of
84 (1.2 points) for Sol under M1. Details are in `collection_outages.json`; the token usage of this attempt is
unknown, so it is left out of the cost estimate rather than counted as zero.

## Reporting-only amendments after the results

No change below altered a frozen input, a prompt, a model setting, a cached reply, a reading rule or a frozen
agreement score. Each was checked by an offline replay with zero new calls.

1. 07:44 (`reporting_amendment.json`): sort the usage ledger by request key and attempt (the first replay differed
   only in row order); mark the attempt without usage data as unpriced; add Wilson intervals for order consistency,
   bootstrap intervals for reason shares, parser rankings, both-order outcomes and samples of unreadable replies by
   type; enlarge example text and size panels to content; label the empty mechanical group; show retry loops in the
   call graph. 07:49: an axis and annotation fix on the substantive panel after visual checking. Replays at 07:47 and
   07:51 reproduced every table and figure.
2. 08:01 (`reporting_amendment_2.json`): plain names for the six kinds of guidance in every displayed table and
   figure (codes M0 to M5 kept in the data); each figure displayed in its own section; progress printed only during
   live collection; the empty mechanical/substantive figure replaced by four text baselines and a split by whether the
   accepted version is longer or shorter; agreement without notebook 26; prompt tokens, time and cost per kind of
   guidance; figure titles that state the finding; the position panel plotted as the share choosing the second
   version (one minus the unchanged share choosing A).
3. 08:20 (`reporting_amendment_3.json`): an audit of the paragraph matching, prompted by a worked example in which
   the accepted README still contained a paragraph the pair showed as deleted. Rule: split each side of a pair on
   blank lines, normalise spaces, and flag a paragraph longer than 40 characters that appears in the other version's
   whole frozen README but not on the other side of the pair. Every flagged pair was read to decide whether a real
   rewrite remained. Result: 2 of 42 test pairs flagged (`p35_b8827a3556adf4e8`, `p35_3d5a56a387bc192a`, neither a
   real rewrite) and 11 of 46 training pairs (9 not real rewrites; 10 from notebook 28, 1 from economics notebook 21).
   All 11 are among the rubric's 40 source pairs; 37 of 42 test pairs had at least one among their similar past
   choices and 35 of 42 among their random ones. Added: agreement on the 40 unflagged test pairs, gains over no
   guidance on them, and example-exposure tables (`alignment_audit.csv`, `sensitivity_clean_test.csv`,
   `flagged_examples_in_prompts.csv`, `agreement_by_flagged_examples.csv`, `rubric_alignment_audit.json`). The frozen
   test, example draws and rubric were not changed, and the main results stay on all 42 pairs.

The text baselines in amendment 2 (pick the shorter version, the version with shorter sentences, or the version with
fewer words of three or more syllables), the split without notebook 26 and the alignment audit in amendment 3 were
added after the results were seen, during the review of the write-up. They are reported as exploratory.

## Environment

Python 3.13.5 on Windows 11; numpy 2.2.6, pandas 2.3.1, scipy 1.17.1, scikit-learn 1.9.0, matplotlib 3.11.2; Claude
Code 2.1.296; codex-cli 0.160.1 (`environment.json`).
