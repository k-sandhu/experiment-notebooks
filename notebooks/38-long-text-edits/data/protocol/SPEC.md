# Notebook 38 implementation spec: how should a model write edits to a long document, and how should they be merged?

You are implementing the code for notebook 38 in this repository. Read `AGENTS.md` at the repository root first:
its rules on self-contained notebooks, caching, size knobs, model access and fresh data apply. The narrative
markdown is NOT your job: another author writes it. Put short placeholder markdown cells where the spec says.

Write only inside `notebooks/38-long-text-edits/`. Do not touch other notebooks, the root README or git state
(no commits, no branch changes). Do not call any LLM (no `claude`, `codex`, `muse` or OpenRouter requests);
the experiment owner runs smoke tests and the live run. Network access is only for the Federal Register
download in step 1.

## Deliverable

1. `notebooks/38-long-text-edits/build/nb38.py`: the notebook's code as a jupytext "percent" script. Code cells
   start with `# %%`, markdown placeholders with `# %% [markdown]` followed by comment lines such as
   `# TODO narrative: explain the seven reply formats`. The final notebook is assembled from this file, so
   every code cell must run top to bottom in a Jupyter kernel whose working directory is
   `notebooks/38-long-text-edits/`, and also as a plain script (`python build/nb38.py` run from that folder;
   use `IPython.display.display`, which works in both).
2. The frozen data that step 1 and step 2 produce under `notebooks/38-long-text-edits/data/` (documents,
   donors, tasks, expected documents, model dates).
3. `notebooks/38-long-text-edits/build/NOTES.md`: what you built, decisions you made where this spec left a
   choice, anything you could not do, and how you tested it (with the oracle test output).

The notebook must replay from `data/` with no network and no model calls once the caches are filled. With
`NB_LIVE` unset, a cache miss raises an error naming the missing request. `NB_LIVE=1` collects missing calls.

## The question

When a model edits a long document, which way of writing the edit (the reply format) gives the most correct
final document, with the fewest unusable replies, the least damage to text that should not change, and the
least output? And for each format, which way of merging the reply into the document (the applier) works best?

## Models and settings (cell: configuration)

```python
MODELS = {  # label -> (backend, model id)
    'GPT-6.1 Sol': ('codex', 'gpt-6.1-sol'),
    'Claude Sonnet 5.5': ('claude', 'claude-sonnet-5-5'),
    'Claude Haiku 5.5': ('claude', 'claude-haiku-5-5'),
    'Qwen3.8 27B': ('openrouter', 'qwen/qwen3.8-27b'),
    'DeepSeek V4.1 Flash': ('openrouter', 'deepseek/deepseek-v4.1-flash-1017'),
}
MERGE_MODEL = ('Claude Haiku 5.5', 'claude', 'claude-haiku-5-5')  # writes the merged document for "LLM merge"
EFFORT = 'medium'        # reasoning effort for the models under test
MERGE_EFFORT = 'low'     # the merge step is mechanical
N_DOCS = 9               # 3 per length bin
FORMATS = ['full', 'search_replace', 'json_replace', 'udiff', 'apply_patch', 'line_edits', 'sketch']
BUNDLES = ['one', 'mixed6', 'rename', 'many20']
MAX_CLI_CALLS = 3000
MAX_CLAUDE_USD = 80.0    # list price reported by claude -p
MAX_OPENROUTER_USD = 15.0
PROTOCOL = 'nb38-v1'     # part of every cache key
```

A size knob may be overridden by environment variables (`NB_N_DOCS`, `NB_MODELS` as a comma list of labels)
so the owner can run a smoke test.

Backends, adapted from notebook 29 (`notebooks/29-theory-of-mind/29_theory_of_mind.ipynb`, the cell that defines
`ALL_MODELS`, `Cache`, `ask_cli` and the OpenRouter caller); read it and reuse its patterns: append-only JSONL
caches keyed by the sha256 of the canonical full request, a per-key lock so two identical concurrent requests
make one call, `NotCollected` for quota and rate limits (not cached), budget guards, an empty temporary working
folder for the CLIs, and provider pinning for open-weight models through a `data/model_catalog.json` (copy the
two relevant entries from notebook 29's `data/model_catalog.json`; keep its pinned providers and permaslugs).

- `claude`: `claude -p --model ID --tools "" --safe-mode --no-session-persistence --output-format json
  --effort E --max-budget-usd 3.00 --system-prompt SYSTEM`, prompt on stdin, UTF-8. Set the environment
  variable `CLAUDE_CODE_MAX_OUTPUT_TOKENS=48000` for the child so full rewrites of 13,000-word documents are not
  cut off. Record `result`, `usage`, `total_cost_usd`, `duration_ms`, `stop_reason` if present.
- `codex`: the `CODEX_OPTIONS` of notebook 29 (read-only sandbox, tools disabled, `--json`, reasoning effort E),
  `-m ID -`, prompt on stdin. Find out from `codex exec --help` and the Codex configuration reference whether a
  config key replaces the base instructions (for example `-c base_instructions=...` or
  `-c model_instructions_file=...`); if one works, pass the same SYSTEM text as for the other models, and if
  none does, leave Codex's own instructions in place and say so in NOTES.md. Parse the last `agent_message`
  and the `turn.completed` usage.
- `openrouter`: `POST https://openrouter.ai/api/v1/chat/completions` with messages `[system, user]`,
  `temperature` 1.0, `max_tokens` 48000, `reasoning: {effort: E}`, `usage: {include: true}`, pinned provider with
  `allow_fallbacks: false`. Record text, usage, cost, provider, finish_reason, latency. A reply cut off by the
  token limit (`finish_reason == 'length'`) is kept as is (it is a result, not a transport error).
- Concurrency: per-model semaphores (claude 4, codex 3, openrouter 6). Order the job list with the model as the
  innermost loop so every provider is busy. Timeout 1,200 s per call. Retry transport errors with backoff;
  a call that fails four times is cached as `{'error': ...}`.
- Write every file with `newline='\n'` and UTF-8 (Windows machine).

SYSTEM text (identical for every model and format):
`You edit documents exactly as instructed. Reply only in the format the user asks for.`

## Step 1: documents (cells: data collection, a look at the data)

Fresh, public-domain text: US Federal Register documents (works of the US government) published from
2026-10-19 to 2026-10-29 inclusive, types RULE and PRORULE. API:
`https://www.federalregister.gov/api/v1/documents.json` with `conditions[publication_date][gte]`,
`[lte]`, `conditions[type][]`, `fields[]` (document_number, title, type, agencies, publication_date, html_url,
full_text_xml_url, page_length), `per_page=100`, following `next_page_url`.

Convert each document's full-text XML into Markdown:

- `# Title` first line. Headings (`HD` elements) become `##`, `###`, `####` by their `SOURCE` level
  (HD1, HD2, HD3 and deeper). Paragraph-like elements (`P`, `FP`, list items, `EXTRACT` paragraphs, `SECTION`
  headings `SECTNO`/`SUBJECT` combined into a heading line, `AMDPAR`) become one line each, with internal
  whitespace collapsed to single spaces. Keep the text's own characters (section signs, em dashes, curly
  quotes) unchanged.
- Drop tables (`GPOTABLE`), math, images (`GPH`), footnote reference markers and the signature/billing blocks;
  keep footnote text as paragraphs where it appears, or drop footnotes entirely (your choice; record it).
- Blocks are separated by exactly one blank line. No trailing spaces. The file ends with one newline.

Length bins by word count of the Markdown: short 1,200 to 2,500 words, medium 4,000 to 6,500, long 9,000 to
13,000. Pick `N_DOCS // 3` per bin deterministically (`random.Random(38)` over candidates sorted by document
number, preferring distinct agencies). Skip documents where fewer than 12 paragraphs qualify as edit targets
(see step 2) or where a long run of the text is a table you dropped.

Donor text: from other documents in the same window that were not selected, collect 60 paragraphs of 30 to 80
words and 60 sentences of 12 to 35 words, without double quotes of any kind. These are inserted or substituted
by edits, so every word in the experiment is human-written government text published after the models'
training cutoffs.

Freeze: `data/docs/{document_number}.md` is git-ignored by the repository; store the frozen Markdown under
`data/documents/{document_number}.md` instead (it is small and public domain). Also `data/documents.csv`
(document_number, title, agency, type, publication_date, html_url, xml sha256, md sha256, words, lines,
paragraphs, length bin) and `data/donors.json` (each donor text with its source document number). On replay,
read the frozen files, check their sha256 against the csv, and never touch the network.

Record `data/model_dates.json`: each model's training cutoff or release date with its source, copied from
`notebooks/29-theory-of-mind/data/model_dates.json` for models listed there; for Claude Sonnet 5.5 look in other
notebooks' data folders (for example notebook 30) and if no source exists say so in the entry. Every document is
dated after 2026-10-17, the latest release date among the models.

## Step 2: edit requests with exact expected documents (cells: task generation, one task shown)

Work on the document as a list of lines. A *paragraph* is a non-blank line that is not a heading (does not
start with `#`) and has at least 20 words. Its *opening words* are its first 8 words; extend up to 14 words if
needed to make the opening unique among all lines; a paragraph whose opening cannot be made unique is not
eligible. No edit may change a paragraph's opening words, so later instructions stay valid. Exclude text that
contains a double quote character (straight or curly) from everything quoted in an instruction.

Edit types (each with an exact effect on the line list):

| type | instruction text | effect |
|---|---|---|
| `replace_phrase` | `In the paragraph that begins "OPENING", change "X" to "Y".` | X is a 3 to 6 word span inside the paragraph, after its first 10 words, unique in the whole document. Y is X with one change: either a number in X altered (add 1 to 9, keep its formatting, e.g. thousands commas), or one word replaced by a plainer one from a fixed dictionary in the code (`shall`->`must`, `approximately`->`about`, `utilize`->`use`, `prior to`->`before`, `pursuant to`->`under`, `in order to`->`to`, `additional`->`more`, `regarding`->`about`, `subsequent to`->`after`, `commence`->`start`, `sufficient`->`enough`, `numerous`->`many`; preserve capitalisation). Aim for half number edits and half word edits. |
| `rewrite_sentence` | `Replace the sentence "S" with this sentence: "T"` | S is a whole sentence (10 to 40 words) of an eligible paragraph, not its first sentence, unique in the document. T is a donor sentence. Split sentences carefully (abbreviations such as U.S., Sec., No., e.g., i.e., et al., Inc., Fed., Reg., CFR section numbers). |
| `delete_paragraph` | `Delete the paragraph that begins "OPENING".` | remove the line and one adjacent blank line |
| `insert_paragraph` | `Immediately after the paragraph that begins "OPENING", insert this new paragraph: "P"` | after the anchor line insert a blank line and P (a donor paragraph) |
| `move_paragraph` | `Move the paragraph that begins "A" so that it comes immediately after the paragraph that begins "B".` | remove A (and one adjacent blank line) and reinsert it, preceded by a blank line, right after B. A and B are not adjacent. |
| `rename` | `Replace every occurrence of the abbreviation "X" with "Y".` | X is an all-capitals abbreviation of 2 to 6 letters that occurs 6 to 40 times as a whole word (case-sensitive, regex `(?<![A-Za-z0-9])X(?![A-Za-z0-9])`); prefer a count near 15. Y is X with its last letter changed to another capital letter such that Y does not occur in the document. If no abbreviation qualifies, fall back to a whole word occurring 6 to 40 times from a fixed pair list (`commenters`->`respondents`, ...) and change the instruction to `Replace every occurrence of the word "X" with "Y".` Headings are included. |

Bundles (one task per document per bundle, so 36 tasks for 9 documents):

- `one`: 1 `replace_phrase`.
- `mixed6`: 2 `replace_phrase`, 1 `rewrite_sentence`, 1 `delete_paragraph`, 1 `insert_paragraph`,
  1 `move_paragraph`.
- `rename`: 1 `rename`.
- `many20`: 20 `replace_phrase` on 20 distinct paragraphs; when a document has fewer eligible paragraphs, allow
  two per paragraph with non-overlapping spans at least 3 words apart, and if still short use as many as fit
  (record `n_edits`).

Within a bundle every paragraph involved (target or anchor) is distinct, and involved paragraphs are separated by
at least one other paragraph. All positions refer to the original document; compute the expected document by
applying the edits in a fixed safe order. Instructions are listed in document order of their target, numbered
`1.`, `2.`, ... Seed with `random.Random(f'{PROTOCOL}:{doc}:{bundle}')`.

For every edit also store a *check* that can be evaluated on any output document independently of the other
edits (normalise both texts as in scoring first):

- `replace_phrase`, `rewrite_sentence`: the output contains the window `left + Y + right` and not `left + X + right`,
  where left/right are up to 25 characters of the expected line around the span, clipped so they do not overlap
  another edit's span.
- `delete_paragraph`: no output line equals the deleted paragraph.
- `insert_paragraph`: the inserted paragraph appears exactly once, and the nearest non-blank line above it starts
  with the anchor's opening words.
- `move_paragraph`: A appears exactly once, and the nearest non-blank line above it starts with B's opening words.
- `rename`: zero whole-word occurrences of X and the expected number of Y.

Save `data/tasks.jsonl` (task_id = `{document_number}_{bundle}`, document, bundle, edits with all fields and
checks, rendered instruction text, n_edits, sha256 of the expected document) and
`data/expected/{task_id}.md`.

## Step 3: the seven reply formats and their prompts (cell: prompt builder; show one prompt)

User prompt for every format:

```
Below is a document and a list of edits. Make exactly these edits and nothing else. Every other character of the document, including punctuation, spacing, line breaks and blank lines, must stay as it is.

<document>
{DOCUMENT_DISPLAY}
</document>

Edits to make:
{NUMBERED_EDITS}

{FORMAT_INSTRUCTIONS}
```

`DOCUMENT_DISPLAY` is the plain document, except for `line_edits`, where it is preceded by the sentence
`Each line below starts with its line number and a | character; that prefix is not part of the document.` and
every line is shown as `{n}| {line}` (blank lines as `{n}|`), n from 1.

FORMAT_INSTRUCTIONS, verbatim:

`full`:
```
Reply with the complete edited document, from its first line to its last, between a line containing only <edited_document> and a line containing only </edited_document>. Write nothing outside those tags.
```

`search_replace`:
```
Reply with one or more edit blocks in this form, and nothing else:

<<<<<<< SEARCH
text copied exactly from the document
=======
the text that replaces it
>>>>>>> REPLACE

Rules: the SEARCH text must be copied character for character from the document and must occur exactly once in it. It may be part of a line or span several lines; keep it as short as it can be while still occurring only once. To delete text, leave the replacement empty. To insert text, search for the text just before the insertion point and repeat it in the replacement followed by the new text. Blocks are applied in order, each to the result of the blocks before it.
```

`json_replace`:
```
Reply with a JSON object in this form, and nothing else:

{"edits": [{"old": "text copied exactly from the document", "new": "the text that replaces it"}]}

Rules: each "old" must be copied character for character from the document and must occur exactly once in it. It may be part of a line or span several lines (write a line break as \n); keep it as short as it can be while still occurring only once. To delete text, use an empty "new". To insert text, set "old" to the text just before the insertion point and repeat it in "new" followed by the new text. Edits are applied in order, each to the result of the edits before it.
```

`udiff`:
```
Reply with a unified diff of your change, in the format produced by diff -u, and nothing else:

--- a/document.md
+++ b/document.md
@@ -12,7 +12,7 @@
 unchanged line
-removed line
+added line
 unchanged line

Rules: line numbers count from 1 at the first line of the document, and blank lines count. Each line in a hunk starts with one character: a space for an unchanged context line, which must match the document exactly, - for a removed line and + for an added line. Give 3 lines of context around each change and use a separate hunk for each region of change, in document order. A line that changes is removed in full and added in full.
```

`apply_patch` (the format OpenAI documents for its apply_patch tool):
```
Reply with a patch in this format, and nothing else:

*** Begin Patch
*** Update File: document.md
@@ a line just before the change, copied from the document
 unchanged line
-removed line
+added line
 unchanged line
*** End Patch

Rules: do not use line numbers. Each line of a change starts with one character: a space for an unchanged context line, - for a removed line and + for an added line; context and removed lines must match the document exactly. Show 3 unchanged lines above and below each change so it can be found, and start each separate change with its own @@ line, in document order. A line that changes is removed in full and added in full.
```

`line_edits`:
```
Reply with a JSON object in this form, and nothing else:

{"edits": [
  {"action": "replace", "start": 12, "end": 12, "text": "the new text of line 12"},
  {"action": "insert_after", "line": 30, "text": "first new line\nsecond new line"},
  {"action": "delete", "start": 40, "end": 41}
]}

Rules: line numbers refer to the document as shown above, before any edit, and a range includes both ends. "replace" replaces lines start to end with text, "insert_after" inserts text after the given line (0 inserts before the first line) and "delete" removes lines start to end. Write a line break inside text as \n and do not include the line-number prefixes. Edits must not overlap.
```

`sketch`:
```
Reply with an edit sketch, and nothing else: write out only the parts of the document that change, in document order, as they should read after your edits. Copy the unchanged paragraph or heading just before and just after each change so its position is clear, and write a line containing only [... unchanged ...] wherever you skip unchanged text, including at the start and the end. Another program will merge your sketch into the document.
```

## Step 4: parsers and merge methods (cell: appliers; cell: oracle self-test)

Every applier is a pure function `(original_text, reply_text) -> ApplyResult` with fields: `text` (the merged
document, or None), `parse_ok`, `n_blocks`, `n_applied`, `failures` (list of `{block, reason, detail}` with
`reason` from a small fixed vocabulary such as `not_found`, `ambiguous`, `bad_json`, `bad_range`, `overlap`,
`corrupt_hunk`, `context_mismatch`, `anchor_not_found`, `no_blocks`, `empty_reply`), and `notes`. Appliers are
best effort: a failed block is skipped and the others are applied. Parsers tolerate a code fence around the
reply and short prose before or after it; record when they had to.

Merge methods per format (names are used in tables, keep them exactly):

- `full`: `as written`: text between `<edited_document>` tags; if the closing tag is missing take everything
  after the opening tag (flag `truncated_or_unclosed`); if no tags, a single fenced block, else the whole reply.
- `search_replace` and `json_replace` (same appliers, different parsers; parse SEARCH/REPLACE blocks leniently, 
  JSON with `json.loads` then `strict=False`, then a repair of unescaped newlines inside strings, recording which
  was needed):
  - `exact`: the old text must occur exactly once in the current text (0 -> `not_found`, >1 -> `ambiguous`).
  - `tolerant`: `exact`, then a unique match after normalising both sides (NFKC, curly quotes to straight,
    en and em dashes to `-` only for matching, non-breaking spaces to spaces, runs of whitespace to one space,
    trailing spaces ignored), mapping the match back to the original span.
  - `fuzzy`: `tolerant`, then the best-matching window with similarity >= 0.90 (difflib ratio on normalised
    text), accepted only when the runner-up is at least 0.05 lower. Must handle 90,000-character documents and
    20 blocks in well under a second per block on a laptop; standard library only.
- `udiff`:
  - `git apply`: write the original to a temporary folder as `document.md` and run
    `git apply --reject --whitespace=nowarn --verbose` on the reply's diff (paths normalised to `document.md`);
    read per-hunk outcomes from its output. Record the git version.
  - `GNU patch`: `patch --forward --batch --fuzz=2 -r <rejfile> document.md < diff` (Git for Windows ships GNU
    patch); per-hunk outcomes from its output. If `patch` is missing, mark the method unavailable.
  - `context search`: ignore line numbers and counts; locate each hunk's old side (context plus removed lines)
    as an exact unique line sequence (if it occurs more than once, take the occurrence nearest the stated line
    number); a line in a hunk with no leading marker that is empty is a blank context line.
  - `fuzzy`: `context search`, then normalised line comparison, then dropping up to 2 context lines at each end,
    then per-line similarity >= 0.90.
- `apply_patch`:
  - `reference`: the rules of OpenAI's reference apply_patch (codex-rs `apply-patch` crate, `seek_sequence`):
    each chunk's `@@` anchor line, if given, is sought from the cursor; then the old lines (context plus removed)
    are sought from the cursor trying exact, then trailing-whitespace-stripped, then fully stripped, then
    unicode-punctuation-normalised comparison; on success the cursor moves past the chunk. Describe in NOTES.md
    any place where you could not match the reference behaviour.
  - `fuzzy`: `reference`, then per-line similarity >= 0.90 and dropping up to 2 context lines at each end.
- `line_edits`: `as given`: validate (integers, in range, no overlap), apply bottom-up to the original lines.
- `sketch`: `anchor merge`: split the reply on marker lines (lenient: `[... unchanged ...]`, `[...]`, `...`,
  `// ... existing text ...` and similar); for each segment (blank edge lines stripped), find its first and last
  non-blank lines in the original, searching forward from the previous segment's end (exact, then normalised,
  then similarity >= 0.90), and replace the original lines between them with the segment. A reply without
  markers that is at least 80% of the original's length is treated as a whole document.

LLM merge (a model call, so it is cached like every other call): `MERGE_MODEL` receives the original and the
reply and writes the whole merged document. Run it for every `sketch`, `search_replace` and `udiff` reply.
Prompt, verbatim:

```
Below is a document and an edit to it, written as {EDIT_KIND}. Apply the edit and write out the complete updated document: make every change the edit shows and copy every other line of the document exactly as it is.

<document>
{ORIGINAL}
</document>

<edit>
{REPLY}
</edit>

Reply with the complete updated document between a line containing only <merged_document> and a line containing only </merged_document>. Write nothing outside those tags.
```

with EDIT_KIND `an edit sketch, in which [... unchanged ...] marks unchanged text that was left out`,
`SEARCH/REPLACE blocks` or `a unified diff`. Its method name is `LLM merge`.

Retry with the error message (a model call): for every reply in `search_replace`, `json_replace`, `udiff`,
`apply_patch`, `line_edits` and `sketch`, run the format's strict applier (`exact`, `exact`, `git apply`,
`reference`, `as given`, `anchor merge`). If it parsed nothing or any block failed, send the same model one
retry: the original user prompt, then

```

Your previous reply was:
<previous_reply>
{REPLY}
</previous_reply>

It could not be applied to the document:
{ERRORS}

Reply again with the complete set of edits in the same format, corrected. The edits will be applied to the original document.
```

ERRORS is one line per failure in plain words (e.g. `Block 3: the SEARCH text was not found in the document.`,
`Block 5: the SEARCH text occurs 4 times in the document.`, `Hunk 2: the context lines do not match the
document.`, git apply's own error lines, `The reply is not valid JSON: <message>.`), written from the strict
applier's failures. At most one retry. Derived pipelines (no further calls):

- `<strict> + retry`: the strict result if it had no failure, else the strict applier on the retry reply.
- `<tolerant> + retry` for `search_replace`/`json_replace` (`fuzzy + retry`), `udiff` (`fuzzy + retry`) and
  `apply_patch` (`fuzzy + retry`): the fuzzy result if it had no failure, else the fuzzy applier on the retry reply.

Oracle self-test (a cell whose output stays in the notebook): for every task build a correct reply in every
format from the ground truth in code (`full` = expected document; `udiff` = `difflib.unified_diff` with 3
context lines; `apply_patch`, `line_edits`, `search_replace`, `json_replace` and `sketch` from the line opcodes,
with search texts extended until unique). Every deterministic applier must reproduce the expected document
exactly from these replies (assert, and print a table of tasks x methods passed). Add a few perturbation checks
that show each method's tolerance: a SEARCH text with curly quotes straightened, a diff with wrong line numbers,
a diff whose blank context lines lost their leading space, an ambiguous SEARCH text, a patch with one context
line slightly misquoted. Print which methods recover each perturbation and which produce a wrong document.

## Step 5: runs (cells: generation, retries, LLM merges)

Jobs: every task x format x model (36 x 7 x 5 = 1,260 calls at the default size), then retries, then LLM
merges. Use thread pools as described above; show a progress line every 50 completed calls; save nothing but the
caches during collection. Missing calls under `NB_LIVE` unset raise a clear error listing how many are missing.

## Step 6: scoring (cell: scoring; results tables saved to `data/results/`)

Normalisation for comparison: `\r\n` to `\n`, trailing spaces removed from each line, runs of blank lines
collapsed to one, leading and trailing blank lines removed. Scores for every (model, format, task, method):

- `exact`: normalised output equals the normalised expected document. Also `exact_strict` (byte-identical apart
  from the final newline).
- `edits_ok`, `n_edits`: number of edit checks passed.
- `collateral_paragraphs`: align the output's non-blank lines with the expected document's non-blank lines
  (difflib on lines). Count expected lines that are untouched originals (identical to a line of the original and
  not involved in any edit) and are not matched equal in the output, plus output lines matched to nothing.
  Also `collateral_chars`: characters changed in those regions (sum of edit distances between aligned pairs,
  plus lengths of unmatched lines; difflib-based approximation is fine), and `dropped_paragraphs` (untouched
  original lines absent from the output entirely).
- `status`: `exact`; `unreadable` (empty reply, transport error, the parser found no edit, or no block applied);
  or `wrong` (something applied, normalised output differs). Also `n_blocks`, `n_failed`, failure reasons.
- Cost per generation call: input and output tokens, output characters, latency, list cost.

Save `data/results/generations.csv` (one row per call, including retries and merges, with tokens, cost, latency,
finish reason, error) and `data/results/merges.csv` (one row per model x format x task x method, with all
scores). Then display summary tables: (a) exact rate by format and model for each format's best pipeline, with
unreadable and wrong counts beside it; (b) exact rate, unreadable, wrong and collateral by format and method;
(c) median output tokens and latency by format and length bin. Figures and the rest of the analysis come in a
second pass; leave a placeholder cell.

Print the spend (Claude list price, OpenRouter USD, call counts by backend) at the end.

## Testing you should do

Run the script from the notebook folder up to the generation step (the generation cell will raise an offline
cache miss, which is expected; provide an environment switch `NB_STOP_BEFORE_CALLS=1` that ends the script
cleanly before the first model call so the owner can check the offline part). The oracle self-test must pass for
every task. Report its output in NOTES.md, along with the selected documents, their word counts, the number of
eligible paragraphs per document and one rendered prompt for each format (for the shortest document, bundle
`mixed6`) in `build/example_prompts.md`.
