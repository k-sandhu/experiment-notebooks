# Notebook 38, amendment 3: an abbreviation inside a link

Same constraints as before: write only in this folder, never write `data/cache_*.jsonl` or `data/results/`, never
call a model, never run with `NB_LIVE=1`. A live collection of the last LLM merges is running from this script; it
loaded the script and data at start, so editing files is safe, but no request key may change.

## Observation

`2026-22093_rename` asks for every occurrence of the abbreviation `FEVS` to become `FEVA`. The document also has
`FEVS` inside a link: `https://www.opm.gov/chcoc/transmittals/2025/Memo%20on%20FEVS%20ReportsFINAL.pdf`. The rename
rule did not count it, because the `0` of the URL escape `%20` sits right before the `F`, so the expected document
keeps the link unchanged. Of the 40 generation replies for this request (8 formats x 5 models, each merged with the
format's last-listed deterministic method), 24 renamed the link's `FEVS` too, and 12 of those would be exact if that
were accepted; only 3 replies are exact under the current answer. Renaming inside the link is literal compliance
with "every occurrence"; leaving it keeps the link working. Both readings are defensible, so both are accepted.

## Change

1. Add accepted alternative expected documents: `data/expected_alt/2026-22093_rename.md` is the current expected
   document with that one link occurrence renamed (`%20FEVS%20` to `%20FEVA%20`). Store the alternatives in the
   frozen manifest and in the task record (`accepted_alternatives`: list of file names and sha256), so the frozen
   inputs still verify. No other task gets an alternative. Instruction text and every request key stay unchanged
   (assert this as in amendment 2).
2. Scoring: `score_result` scores the output against the expected document and each accepted alternative and keeps
   the best (exact first, then `exact_nonblank`, then fewer collateral paragraphs, then the primary expected
   document). The edit checks are unchanged (the link occurrence is not a whole-word occurrence under either
   reading). Record which answer matched in a column `matched_answer` (`primary` or the alternative's file name).
3. Add `link_rule_comparison(merges)`: for `2026-22093_rename`, exact counts per format and method with and without
   the alternative. Make the existing `rename_rule_comparison` and this one available together as a single small
   table of how the two answer corrections (plural `ORVs`, link `FEVS`) change the rename exact counts per format.
4. Extend the oracle test (the alternative must also be reproduced by every method from an oracle reply built from
   it) and the synthetic analysis tests.
5. Append "Amendment 3 (after the generation replies and retries, while the LLM merges were collected)" to
   `data/PROTOCOL.md` with the observation, counts and change, and that results are reported under both rules.
   Update NOTES.md.

Finish by running `NB_STOP_BEFORE_CALLS=1 python build/nb38.py` and report, including the key comparison.
