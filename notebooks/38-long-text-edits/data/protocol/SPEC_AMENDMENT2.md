# Notebook 38, amendment 2: native diff tools, plural renames, a blank-line measure

Read this after `SPEC_PATCH_WORDING.md` (amendment 1), which is already implemented. Same constraints as before:
write only in this folder, never write `data/cache_*.jsonl` or `data/results/`, never call a model, never run with
`NB_LIVE=1`. No change here may alter a generation or merge request key. Retry requests have not been collected
yet, so the strict `git apply` failure messages that feed retry prompts may change.

## 1. Let `git apply` and GNU `patch` judge the model's diff themselves

Observation (1,260 generation replies collected so far): models often drop the last line of a hunk when it is a
blank context line, so the hunk has one line fewer than its `@@` header says. `apply_external_diff` currently
removes such hunks in Python (`Hunk line counts do not match its header.`) before calling the tool. That matches
`git apply`, which rejects the diff (`error: corrupt patch at line 11` on GPT-6.1 Sol's reply to
`2026-21949_one`), but not GNU `patch`, which applies that same diff, nor `git apply --recount`, which also applies
it. The pre-filter and the re-serialisation of parsed hunks (which also restores lost blank-line markers) make the
native methods measure our parser rather than the tools.

Change `apply_external_diff` so that the tool receives the model's diff text as written, with only these
changes: the reply is unwrapped from a code fence and surrounding prose (as now), the `---`/`+++` file lines are
replaced by `--- a/document.md` and `+++ b/document.md` (added if missing), and `diff --git`/`index` lines are
dropped. Hunk bodies are passed byte for byte (do not restore markers, do not drop trailing lines, do not
re-serialise). Per-hunk outcomes come from the tool's own output (`--reject` for git, the reject file and messages
for patch). When the tool rejects the whole diff without per-hunk results (a fatal parse error such as
`corrupt patch`), fall back to invoking the tool once per hunk, each hunk passed as its own raw text (from its
`@@` line up to the next `@@` line or the end), applied cumulatively, so a valid hunk still gets its chance and
every per-hunk verdict is the tool's. Failure details are the tool's own error lines (trimmed), so the retry
prompt quotes what the tool said.

Add the method `git apply --recount` (same as `git apply` plus `--recount`), placed after `git apply` in the
method order. Keep `git apply` as the strict method for udiff retries.

Add perturbation checks: a diff whose final blank context line is missing (header count one too high), and a diff
whose blank context lines lost their leading space. Report, for each native method and the Python methods, whether
it recovers, rejects or produces a wrong document. Record the observed native behaviour in NOTES.md.

## 2. Plural forms count as occurrences in a rename

Observation: in `2026-21300_rename` (`ORV` to `ORA`) the document also contains `ORVs` 23 times. Every model,
including every full rewrite by GPT-6.1 Sol, Claude Sonnet 5.5 and Claude Haiku 5.5, changed `ORVs` to `ORAs`;
the expected document did not, so seven untouched-looking paragraphs counted as collateral. "Every occurrence of the
abbreviation" includes its plural. No other rename task has a suffixed form (checked: COTP, RB, IRS, DOE, RFA, FR,
FEVS, ACF have none; `IRFA`, `FRFA`, `CFR` and a `%20FEVS%20` inside a URL are other words or not whole words and
stay unchanged).

Change the rename rule so that an occurrence is `X` as a whole word or `X` immediately followed by a lowercase
`s` and then a non-alphanumeric character or the end (`(?<![A-Za-z0-9])X(?=s?(?![A-Za-z0-9]))`), replaced by `Y`
with the `s` kept. Regenerate the expected document, check and hash for `2026-21300_rename` only (all other
expected documents must stay byte-identical; assert this), and update `data/tasks.jsonl`, `data/expected/` and the
frozen manifest. The instruction text does not change, so no prompt changes; assert that every generation request
key is unchanged. Keep the previous expected document as `data/expected_v1/2026-21300_rename.md` and add
`rename_rule_comparison(merges)`: for that task, the exact count per format and method under the old and the new
expected document.

## 3. A secondary measure that ignores blank lines

Some wrong documents differ from the expected one only in blank lines: an inserted or moved paragraph with no blank
line before it, so in Markdown it runs into the paragraph above. Add `exact_nonblank` to `score_result`: the
normalised documents compared after dropping blank lines entirely. Keep `exact` as the main measure. Add the
column to `results_by_format` and the methods summary, and add `near_misses(merges)`: per format and pipeline, the
number of wrong documents that are `exact_nonblank`.

## 4. Record it

Append "Amendment 2 (after all 1,260 generation replies, before retries and merges)" to `data/PROTOCOL.md` with the
observations and counts above, what changed, and that results are reported under both expected documents for the
rename task and both with and without blank lines. Update NOTES.md. Extend the oracle self-test and the synthetic
analysis tests to cover the new method, rule and measure. Finish by running `NB_STOP_BEFORE_CALLS=1 python
build/nb38.py` and report, including the key comparison.
