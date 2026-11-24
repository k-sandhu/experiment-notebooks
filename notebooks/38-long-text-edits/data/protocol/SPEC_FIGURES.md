# Notebook 38, final pass: figure fixes, titles and the worked examples

All model calls are collected. Same constraints: write only in this folder, never write `data/cache_*.jsonl`, never
call a model, never run with `NB_LIVE=1`, keep every request key unchanged. Replays now run without `NB_LIVE`
and without `NB_STOP_BEFORE_CALLS` and must complete from the caches (this writes `data/results/` and `figures/`,
which is now allowed and expected). Verify the final state with a full replay: `python build/nb38.py` from the
notebook folder.

## 1. Figure fixes

- `fig_cost`: the log-scaled token axis has overlapping, mixed-format tick labels (`2x10^3 3x10^4 ...`). Use fixed
  major ticks at 1,000, 2,000, 5,000, 10,000 and 20,000 (only those inside the data range plus margin), labelled
  `1,000` etc., and no minor tick labels.
- `fig_line_numbers`: the symlog axis shows only 0 and 1. Use ticks 0, 1, 2, 5, 10, 20, 50, 100 (up to the data
  maximum), integer labels, and place the `exact; n=` annotation in a fixed right-hand text column outside the
  plotting area so it never overlaps points. Title the x axis "Lines between the stated start and the actual start
  of the hunk".
- Check every figure at 900 px width for overlapping text after the change.

## 2. Titles (pass these exact strings where the analysis cells call the figure functions)

```python
TITLES = {
    'formats': 'Find-and-replace replies most often give the exact document; diffs and patches need a forgiving merge',
    'methods': 'Forgiving merges rescue diffs and patches but not find-and-replace, and a merge model loses edits',
    'cost': 'Find-and-replace replies stay short and fast as documents grow; diffs cost about as much as rewriting',
    'bundles': 'Find-and-replace handles twenty scattered edits but misses renames; rewriting handles renames best',
    'line_numbers': 'Line numbers in diffs were mostly right: every hunk from GPT-6.1 Sol, 78% from Claude Haiku 5.5',
    'collateral': 'Rewriting or merging with a model changes untouched paragraphs more often than code merges do',
    'examples': 'Three silent errors: straightened quotes, a sketch placed on a repeated line, a merge that kept the old year',
}
```

Define `TITLES` once at the top of the first analysis cell.

## 3. Worked examples

Replace the single example cell with a sequence of cells, one case per cell, each preceded by a markdown placeholder
`# %% [markdown]` / `# TODO narrative: case N, <one-line description>`, in this order. Each code cell calls
`show_case(model, fmt, task_id, method)` and, where noted, a short extra display.

1. `('GPT-6.1 Sol', 'udiff', '2026-21949_one', 'git apply + retry')`: show the first reply, `git apply`'s error, the
   retry message the model received (the part after the original prompt), the corrected reply, and the final
   status. Make `show_case` (or a sibling helper) able to show both the first and the retry reply for a
   `+ retry` method.
2. `('GPT-6.1 Sol', 'search_replace', '2026-22093_many20', 'exact')`: also display the reply's length in characters
   and output tokens next to the same model's whole-document reply for the same task.
3. `('Claude Haiku 5.5', 'search_replace', '2026-21949_rename', 'exact')`: also list which original lines with the
   abbreviation the reply had no block for.
4. `('Qwen3.8 27B', 'full', '2026-22093_one', 'as written')`: also count characters changed by kind (curly to
   straight double quote, curly to straight single quote, other) over the whole document.
5. `('GPT-6.1 Sol', 'sketch', '2026-21686_many20', 'anchor merge')`: also show where the segment's first anchor line
   occurs in the original (all line numbers where that exact line appears).
6. `('GPT-6.1 Sol', 'apply_patch', '2026-21949_one', 'reference')`, then the same reply under
   `reference, @@ in context`.
7. `('GPT-6.1 Sol', 'search_replace', '2026-21949_one', 'LLM merge')`: the merge model's document kept "Act of 1995";
   show the reply, the expected line and the merged line.
8. `('DeepSeek V4.1 Flash', 'line_edits', '2026-21949_mixed6', 'as given')`: a near miss that differs only in blank
   lines; show the inserted text with its line breaks made visible.

Then one cell that builds `figures/examples_silent_errors.png` with `fig_case_panel` from cases 4, 5 and 7, labelled
`Whole document (Qwen3.8 27B)`, `Edit sketch, anchor merge (GPT-6.1 Sol)` and `SEARCH/REPLACE, LLM merge (Claude
Haiku 5.5 merging GPT-6.1 Sol's reply)`. For each case fill `input` (the relevant instruction or the reply excerpt
that matters), `reply` (what the model wrote, excerpt), `expected` and `got` (the first differing line pair, trimmed
to about 60 characters around the first difference) from `case()` programmatically, not by hand. Title:
`TITLES['examples']`.

## 4. Check

Run a full replay (`python build/nb38.py`, no `NB_LIVE`), confirm it completes, inspect every figure image for
overlaps, and report the list of narrative placeholders in order (number and TODO line) at the end of your final
message, because the narrative is keyed to that order.
