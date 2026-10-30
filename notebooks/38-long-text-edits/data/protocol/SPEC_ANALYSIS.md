# Notebook 38, second pass: analysis, figures and example helpers

Read `build/SPEC.md`, `build/NOTES.md` and `build/nb38.py` first. This pass adds the analysis cells. The live
collection is running right now in another process and is appending to `data/cache_cli.jsonl` and
`data/cache_openrouter.jsonl`: never write, move or rewrite those files, never write `data/results/`, and do not
call any model. Edit only `build/nb38.py` (and `build/NOTES.md`, a short new section at the end).

Because the real results are not ready, develop and test against synthetic frames built in memory the way
`run_pipeline_table_tests` does (oracle replies with deliberate corruptions so every status occurs). Keep that
test, extended to cover the new functions, so the notebook shows it passed. The owner will run the real data
through your functions and choose the figure titles, so every figure function takes `title` as an argument with
a neutral default.

## Changes to scoring

1. `score_result` also returns `edit_checks`: a JSON list of booleans, one per edit in task order, so results can
   be broken down by edit type. Keep `edits_ok` as their sum.
2. Collateral measures for an unreadable output are `NaN`, not counts against an empty document. Summary tables
   average collateral over readable outputs only and say so in the column name (`collateral_paragraphs_readable`).
3. Add `MAIN_PIPELINES`, a fixed dictionary, declared before results are seen (do not pick by score):

```python
MAIN_PIPELINES = {   # format -> (strict pipeline, forgiving pipeline)
    'full': ('as written', 'as written'),
    'search_replace': ('exact', 'fuzzy + retry'),
    'json_replace': ('exact', 'fuzzy + retry'),
    'udiff': ('git apply', 'fuzzy + retry'),
    'apply_patch': ('reference', 'fuzzy + retry'),
    'line_edits': ('as given', 'as given + retry'),
    'sketch': ('anchor merge', 'anchor merge + retry'),
}
FORMAT_LABELS = {'full': 'Whole document', 'search_replace': 'SEARCH/REPLACE blocks',
                 'json_replace': 'JSON find-and-replace', 'udiff': 'Unified diff',
                 'apply_patch': 'OpenAI patch', 'line_edits': 'Line-number edits', 'sketch': 'Edit sketch'}
```

   The existing "best pipeline" table may stay, but label it as selected on the same data.

## Analysis cells (after the scoring cell; each runs only when results exist)

Each analysis cell starts by building what it needs from `MERGES`, `GENERATIONS`, `TASKS`, `DOCUMENTS`,
`EXPECTED`, `GEN_RESPONSES`, `RETRY_RESPONSES`, `MERGE_RESPONSES`. Put a `# %% [markdown]` placeholder before
each with a one-line `# TODO narrative:` describing what the prose must explain.

1. **Results table by format** (`results_by_format(merges)`): one row per format and pipeline in
   `MAIN_PIPELINES` (strict and forgiving), pooled over models and tasks: n, exact count and rate with a 95%
   Wilson interval, wrong, unreadable, exact rate on readable replies, share of edits done, mean collateral
   paragraphs on readable outputs, extra calls made (retries). Display formatted (percentages as text).
2. **Headline figure** `fig_formats(merges, title)`, saved as `figures/formats_by_model.png`: two panels side by
   side sharing the y axis (formats in a fixed order, top to bottom as in `FORMATS`): left the strict pipeline,
   right the forgiving pipeline. In each panel a light horizontal bar for the pooled exact rate with its Wilson
   interval as a thin line, and one marker per model (five distinct marker shapes and colours, same in every
   figure, legend below the panels). x axis "Share of requests merged into the exact expected document", 0 to 1.
   Annotate each pooled bar with `k/n`.
3. **Merge methods figure** `fig_methods(merges, title)`, saved as `figures/merge_methods.png`: one small panel per
   format that has more than one method (search_replace, json_replace, udiff, apply_patch, line_edits, sketch),
   each a horizontal 100% stacked bar per method in a fixed order (strict first, then tolerant, fuzzy, native
   tools, retry variants, `LLM merge` last): exact (green), wrong (red), unreadable (grey), with counts written in
   the segments when wide enough. Hatching or text labels must distinguish the three statuses without colour.
4. **Cost figure** `fig_cost(generations, title)`, saved as `figures/output_and_time.png`: two panels: median output
   tokens per generation reply by format, grouped by length bin (short, medium, long), log x scale with plain tick
   labels; and median latency in seconds by format and length bin. Generation stage only (exclude retries and
   merges), and a separate small table of the total extra calls, tokens and time that retries and LLM merges add.
5. **Bundle heatmap** `fig_bundles(merges, title)`, saved as `figures/bundles.png`: formats x bundles (one, mixed6,
   rename, many20), cell = exact rate of the forgiving pipeline pooled over models (n = 45 per cell), annotated
   with the percentage and `k/n`; a second heatmap panel for the strict pipeline. Sequential single-hue colormap,
   colorbar labelled.
6. **Edit type table** `edit_type_table(merges)`: share of edits done by edit type (number phrase, word phrase,
   sentence, delete, insert, move, rename) and format, forgiving pipeline, readable outputs; with counts.
7. **Failure reasons** `failure_table(merges)`: for each format's strict method, count failed blocks by reason and
   by model; and the share of replies with at least one failed block.
8. **Line-number accuracy** `line_number_accuracy()`: for every unified diff reply, every hunk that the
   `context search` method could place: the stated old start line versus the line where the hunk's old side
   actually is in the original (both 1-based, before any other hunk is applied). Per model: hunks, share exactly
   right, share within 3 lines, median absolute offset. Also, for `line_edits` replies: for each edit object,
   whether its line range covers exactly the line(s) of the requested edit it corresponds to (match an edit
   object to a requested edit by the target line's original text or by the inserted text), share right per model.
   Save `figures/line_numbers.png`: per model, the distribution of absolute offsets for udiff hunks (strip or box
   plot, symlog x axis) with the share exactly right annotated.
9. **Collateral figure** `fig_collateral(merges, title)`, saved as `figures/collateral.png`: for readable outputs,
   the share with at least one collateral paragraph and the mean number of collateral paragraphs when there is
   any, for: whole document (as written), each format's `LLM merge`, and the deterministic forgiving pipelines
   pooled. Bars by method, split by length bin.
10. **Example helpers** (no fixed examples; the owner picks them):
   - `case(model, fmt, task_id, method)` returns a dict with the instructions, the raw reply (and retry/merge
     replies used), the ApplyResult failures and notes, the score row, and a unified diff between the expected
     and merged documents (3 lines of context, at most 60 lines, long lines wrapped at 110 characters).
   - `show_case(...)` displays it as Markdown (instructions as a numbered list, raw reply in a fenced block
     truncated to 2,500 characters with a note of the full length, the status line, the diff in a ```diff block).
   - `fig_case_panel(cases, path, title)`: a matplotlib figure with one row per case and three columns of
     monospace text boxes (the instruction or relevant input excerpt, what the model wrote, what the merged
     document contains versus the expected text), with the mismatching span highlighted (a coloured background
     on the differing characters plus an underline, so it does not rely on colour alone). Each case is a dict
     with `label`, `input`, `reply`, `expected`, `got` strings that the owner fills from `case()`; wrap text to fit.
   - `find_cases(**filters)` returns rows of `MERGES` matching filters (status, format, method, model, bundle,
     reason substring in failures, collateral > 0) sorted by task id, to help pick examples.
11. **Spend table** `spend_table(generations)`: calls, input and output tokens, list cost and total latency by
   model and stage (generation, retry, merge).

## Plot style

Keep the notebook's single style block (add one in the configuration cell if there is none, copied from notebook
29: same rcParams). Titles state a finding (passed in by the owner), axes labelled with units, no dual y axes,
legible at 900 px width, `savefig` to `figures/` at 150 dpi. Use a fixed colour per model and per status across
figures. Model order everywhere: GPT-6.1 Sol, Claude Sonnet 5.5, Claude Haiku 5.5, DeepSeek V4.1 Flash,
Qwen3.8 27B.

## Testing

Run `NB_STOP_BEFORE_CALLS=1 python build/nb38.py` (no calls); your synthetic test must exercise every new
function, write its figures only to a temporary folder (not `figures/`), and pass. Do not run the script with
`NB_LIVE=1`. Finish with a short summary of what you added and the test output.
