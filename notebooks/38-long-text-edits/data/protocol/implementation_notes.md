> Implementation notes written by GPT-6.1 Sol while building the code. File names refer to the build folder it worked in; `nb38.py` became the notebook's code cells.

# Notebook 38 implementation notes

Implemented from `SPEC.md`, after reading the repository AGENTS.md and notebook 29's code, model catalogue and date records. Only this notebook folder was written. No branch, commit or repository index was changed. No LLM was called. The only HTTP downloads were the Federal Register API listing and its Federal Register full-text XML URLs.

## Deliverables

- `nb38.py` is a self-contained percent-format notebook script. Narrative cells are placeholders for the separate author. It runs from the notebook folder.
- `data/documents/`, `documents.csv`, `donors.json`, `tasks.jsonl` and `expected/` hold the frozen inputs, exact answers and independent edit checks. `source_manifest.json` records the API listing and every candidate decision; `frozen_manifest.json` checks 51 input files byte for byte before replay.
- `data/model_catalog.json` copies only Qwen and DeepSeek from notebook 29, retaining providers, permaslugs, weights, precision, pricing and source notes. `model_dates.json` copies available dates and marks the Sonnet gap.
- `example_prompts.md` contains all seven complete prompts for the shortest document, task `2026-21949_mixed6` (1,842 words).
- Production collection writes append-only model caches. Results CSVs and summaries are built only after the generation, single-retry and merge stages finish. Tests using fake replies write no experimental cache or results files.

## Selected documents

Word counts include the title and headings. A paragraph here is a non-heading line with at least 20 words; eligible paragraphs additionally pass the quote and unique-opening rules.

| Document | Bin | Words | Paragraphs | Eligible targets | many20 edits | Agency |
|---|---|---:|---:|---:|---:|---|
| [2026-21949](https://www.federalregister.gov/documents/2026/10/28/2026-21949/special-local-regulation-port-miami-main-shipping-channel-miami-fl) | short | 1,842 | 27 | 23 | 12 | Homeland Security Department; Coast Guard |
| [2026-21686](https://www.federalregister.gov/documents/2026/10/23/2026-21686/airworthiness-directives-the-boeing-company-airplanes-correction) | short | 2,292 | 37 | 30 | 20 | Transportation Department; Federal Aviation Administration |
| [2026-21267](https://www.federalregister.gov/documents/2026/10/19/2026-21267/regulations-regarding-payment-of-tax-by-commercially-acceptable-means) | short | 2,478 | 27 | 24 | 17 | Treasury Department; Internal Revenue Service |
| [2026-21801](https://www.federalregister.gov/documents/2026/10/26/2026-21801/nrc-reviews-of-reactor-designs-previously-authorized-by-us-department-of-energy-or-department-of-war) | medium | 4,565 | 47 | 31 | 20 | Nuclear Regulatory Commission |
| [2026-21300](https://www.federalregister.gov/documents/2026/10/19/2026-21300/gates-of-the-arctic-national-park-and-preserve-use-of-off-road-vehicles-for-subsistence-purposes-by) | medium | 5,936 | 65 | 42 | 20 | Interior Department; National Park Service |
| [2026-21821](https://www.federalregister.gov/documents/2026/10/26/2026-21821/enhancing-the-ability-of-consumers-to-control-the-robocalls) | medium | 5,065 | 44 | 35 | 20 | Federal Communications Commission |
| [2026-21622](https://www.federalregister.gov/documents/2026/10/22/2026-21622/virginia-approval-of-state-coal-combustion-residuals-permit-program) | long | 9,184 | 127 | 96 | 20 | Environmental Protection Agency |
| [2026-22093](https://www.federalregister.gov/documents/2026/10/29/2026-22093/personnel-management-in-agencies-strategic-human-capital-management) | long | 12,762 | 129 | 98 | 20 | Personnel Management Office |
| [2026-22116](https://www.federalregister.gov/documents/2026/10/29/2026-22116/reducing-bureaucracy-and-burden-for-child-support-enforcement-programs) | long | 10,777 | 104 | 81 | 20 | Health and Human Services Department; Children and Families Administration |

## Data and task choices

1. Drop footnotes entirely, including reference markers. Preserve inline emphasis text, punctuation and Unicode. Collapse internal whitespace, use blank lines between blocks and finish with one newline. XML heading levels deeper than HD3 are capped at four Markdown heading marks. Combine section number and subject into one level-three heading. Drop tables, images, math and signature/billing blocks. A dropped table of at least 500 words disqualifies its document.
2. Sort candidates by document number, shuffle with `random.Random(38)` per the specified shared generator, then prefer agencies not yet selected across all bins. Check all bundle constraints before sampling. The audit has 43 eligible candidates, 88 outside the length bins, five with too few targets and one with a long dropped table. Donors are deduplicated, shuffled deterministically and frozen, 60 paragraphs and 60 sentences from unselected documents. Each records its date, source number and URL.
3. Conservatively exclude an entire target paragraph if it contains any straight, curly, low/reversed, guillemet, double-prime or full-width double quote. Opening uniqueness uses literal line prefixes. Paragraph spacing is measured among all non-heading paragraphs of at least 20 words, including ineligible ones. Global rename is the specified exception to opening preservation.
4. Use a conservative offset-preserving sentence splitter with legal abbreviations, dotted initials and decimal section references. Reject an unfinished fragment as a sentence target. Donor sentences must end with terminal punctuation. Phrase-number changes use integers, retaining comma grouping and zero padding; word replacements retain initial or all-capital case. The fixed fallback rename pairs are in the script.
5. For mixed6, allocate seven separated paragraphs (the move has its own destination anchor) with a deterministic seeded search; prefer a number edit and a word edit. For many20, dynamic programming maximises the count under spacing rules, then minimises departure from half word edits. Try distinct paragraphs first; allow two separated spans per paragraph only when fewer than 20 fit. A three-word gap is mandatory. There are 126 number edits and 70 word edits; short documents have too few dictionary-bearing paragraphs for a 50/50 split. No constraints were relaxed to force 20.
6. Compute replacements using descending character offsets, then remove source lines/adjacent blanks and emit insertions at original anchors in one pass. Instructions sort by original target and character position. Independent replacement windows are clipped at neighbouring spans. Frozen expected hashes are checked, ground truth is recomputed, and every check must fail on the original and pass on the expected text.
7. `NB_N_DOCS` must be a positive multiple of three; smoke size is three (one per bin). Existing nine-document input files are never rewritten by a smoke run. `NB_MODELS` takes exact comma-separated labels. Inputs with mismatched hashes fail before collection, rather than silently being regenerated.

## Applier and scoring choices

- There are 15 deterministic format/method combinations and 28 pipelines after retries and LLM merges. Parsers record removed fences/prose, repairs and matching fallbacks. Invalid blocks are skipped while valid ones are applied. Empty, invalid, overlapping and ambiguous blocks have fixed failure codes.
- Replacement normalisation maps each normalised character to its original span, including combining marks and NFKC expansions. It preserves surrounding document text. Leading/trailing SEARCH whitespace consumes only the requested boundary whitespace, avoiding an extra blank-line change. Fuzzy matching uses rare word anchors, with character-seed fallback for short or fully misspelled queries. Ratios use `difflib.SequenceMatcher(autojunk=False)`, a 0.90 floor and a 0.05 margin over a different non-overlapping locus. Overlapping alternative boundary windows at the same locus are treated as one candidate. This is an efficient candidate search, not exhaustive enumeration of every substring.
- Unified diff parsers restore missing blank-line context markers. Context search ignores hunk counts and locates repeated context nearest the stated original position, adjusted for prior applied line deltas. Fuzzy diff matching tries full normalised context, then up to two trimmed context lines at each edge, then per-line similarity. It preserves actual original context lines when splicing a hunk.
- Native methods use git apply with `--reject --whitespace=nowarn --verbose` and GNU patch with `--forward --batch --fuzz=2`. Paths are replaced with `document.md`; no model-supplied path or file operation is executed. Structurally corrupt hunks are removed and reported first. Valid hunks are sent together, with failures mapped from native hunk diagnostics. A fatal whole-diff error falls back to isolated hunk invocations to preserve best effort. GNU patch is found on PATH or under Git for Windows; an absent tool is marked unavailable. Versions on this machine: git 2.45.1.windows.1; GNU patch 2.7.6.
- Reference apply_patch implements the specified forward cursor, optional anchor, exact/rstrip/strip/punctuation matching, end-of-file preference and chunk splicing. Context included in an applied reference chunk is written from the reply, as in reference replacement construction; tolerant context can therefore cause collateral edits. Its fuzzy variant tries context dropping before per-line similarity. A small context typo at an outer edge can be skipped, while a typo next to the changed line can be copied into the output.
- Reference limitations: the upstream codex-rs source and online configuration reference could not be fetched under the Federal-Register-only network rule. This is a local implementation of the requested rules, not a differential test against a particular upstream crate build. Unicode comparison uses an explicit punctuation/space mapping. Additional specified best-effort behaviour skips malformed chunks; short prose/fences are tolerated. Unanchored insertion-only chunks use the cursor. No support for model-requested add/delete/move-file operations is included.
- Sketches split on the requested marker variants. First and last nonblank anchors are found forward, exact then punctuation/space normalised then at least 0.90 similar. The complete segment, including its supplied anchors, replaces that region. Short prose outside edge markers is ignored when it contains no original anchor. Correct oracle sketches extend to unique unchanged anchors; a changed boundary without an anchor uses the specified whole-document fallback.
- Full replies retain document line endings for strict scoring. Main comparison only changes CRLF to LF, strips trailing whitespace, collapses blank lines and removes blank edges. `exact_strict` ignores one terminal newline only. Unreadable status includes transport/empty/unparsed/no-applied-block outcomes; a parsed applied wrong document is wrong. An exact document can still have an extra rejected block, so failure counts remain separate.
- Collateral alignment uses nonblank expected/output lines and excludes every original target or anchor line from the untouched set; global rename excludes all original lines containing the renamed token. Replaced lines are paired in order inside non-equal difflib regions. Count missing/changed untouched expected lines plus excess unpaired output lines. Character changes use difflib approximations for those pairs and unmatched lengths. Dropped paragraphs are untouched expected lines absent anywhere in the output. A changed paragraph therefore also counts as dropped when its exact original line has disappeared. An unreadable output is treated as an empty document for collateral counts, and has zero successful edit checks.
- The best pipeline is selected once per format over all tested models on this same sample, with ties broken by fewer unreadables, lower collateral, then method name. This is a descriptive, optimistically selected result, not held-out validation. Summaries also show readable-only accuracy and strict accuracy. Unknown subscription cost is blank, not zero, in the generation table.

## Model calls, caching and budgets

- One full canonical request hash covers protocol, backend/model, system text, prompt, effort, options, child settings, provider pin and task/stage context. CLI and OpenRouter caches are append-only JSONL with locked appends and per-key locks. Identical concurrent requests within the notebook process make one call. Cross-process distributed locking is not implemented.
- CLI working directories are new empty tempfile directories. Claude uses the exact safe/tool-free options and 48,000 output-token environment setting. Codex retains notebook 29 options and replaces its base instructions using `model_instructions_file` containing exactly SYSTEM, outside the empty working folder. The temporary path is a stable placeholder in the key; its contents are included in the canonical request.
- Verified only local CLI configuration, with codex-cli 0.160.1: `codex exec --help` documents `-c`; a missing instruction-file configuration is rejected with a specific file-read error, and the same setting with a real SYSTEM file succeeds under `codex -c ... features list`. These commands made no model request. The online configuration reference was not accessed. Live instruction delivery and model availability remain for the owner smoke run.
- OpenRouter uses dated permaslugs, the copied provider tags (`near-ai/fp8`, `deepinfra/fp8`), fallback disabled, system/user messages, temperature 1, 48,000 max tokens, medium reasoning and returned usage. Length-finished replies remain results. Merge calls use Haiku at low effort. Strict failure triggers one corrective retry; all derived pipelines apply the chosen reply to the original, never the partially changed document.
- Per-model concurrency is Claude 4, Codex 3, OpenRouter 6. The job list has model innermost. Timeout is 1,200 seconds; transport failures back off and cache an error after four attempts. Rate/quota and budget stops raise NotCollected without caching an answer. Cached terminal errors are replayed unchanged, including in live mode.
- Monetary guards include existing protocol caches, actual reported cost and reservations for in-flight calls. Reserve $3 per Claude attempt and a conservative OpenRouter upper bound using UTF-8 input bytes, framing allowance and maximum output tokens at pinned provider pricing. Failed attempts without cost reports, and successful paid calls missing cost, retain a conservative upper bound in memory and the terminal cache record when one is written. NotCollected has no terminal cache record, so unknown costs for a partially completed interrupted request cannot be recovered after process restart.
- Counts and latency describe logical generation/retry/merge requests; transport attempts are recorded in the attempts column and backend spend counts. CLI/API usage and reported cost refer to the reported terminal response; unreported transport spend is explicitly bounded rather than invented. Per-key locks are in-process, matching notebook 29.

## Open issues and owner handoff

- No verified Sonnet 5.5 release/cutoff date was found. Sibling model_dates files, including notebook 30, had no entry. Notebook 17 has an availability/model-configuration source but explicitly null dates. This is recorded in model_dates.json; freshness for that model needs owner verification.
- No live calls were authorised here. Availability, provider acceptance of the dated IDs, live output envelopes and cost reporting still need the owner smoke test. Pure wrapper parsing, command construction and cache behaviour have local-fake coverage.
- Upstream reference apply_patch differential validation and online Codex config reference verification were unavailable under the network restriction. The implementation follows the specified rules with the differences recorded above.
- No final ipynb, reader README, figures or root README edits are included; the spec assigns narrative and final assembly to another author, and forbids writes outside this folder. No measured model results or experimental response caches exist.

## Reproduction

From `notebooks/38-long-text-edits/`, use Python with pandas, requests and IPython, plus git and optionally GNU patch.

```powershell
$env:NB_STOP_BEFORE_CALLS = "1"
python build/nb38.py
```

If system temporary directories are sandboxed, set TMP and TEMP to an existing absolute `build/tmp/` path in the testing shell. The notebook itself uses tempfile normally and has no hard-coded temporary folder. With STOP unset and LIVE unset, the script fails at a counted, identified offline cache miss. NB_LIVE=1 explicitly permits actual collection for the owner.

## Validation output

`NB_STOP_BEFORE_CALLS=1 python build/nb38.py` completed with exit 0 on 2026-10-30. The recorded full run took 28.39 seconds. All persistent unit tests are folded into notebook cells; no separate test implementation remains. The complete output is `test_output.txt`.

The oracle table and perturbation/unit-test output from that run follow. Timings vary between runs.

```text
             task  edits full/as written search_replace/exact search_replace/tolerant search_replace/fuzzy json_replace/exact json_replace/tolerant json_replace/fuzzy udiff/git apply udiff/GNU patch udiff/context search udiff/fuzzy apply_patch/reference apply_patch/fuzzy line_edits/as given sketch/anchor merge
   2026-21949_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21949_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21949_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21949_many20     12            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
   2026-21686_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21686_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21686_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21686_many20     20            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
   2026-21267_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21267_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21267_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21267_many20     17            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
   2026-21801_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21801_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21801_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21801_many20     20            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
   2026-21300_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21300_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21300_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21300_many20     20            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
   2026-21821_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21821_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21821_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21821_many20     20            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
   2026-21622_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21622_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21622_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-21622_many20     20            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
   2026-22093_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-22093_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-22093_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-22093_many20     20            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
   2026-22116_one      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-22116_mixed6      6            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-22116_rename      1            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
2026-22116_many20     20            pass                 pass                    pass                 pass               pass                  pass               pass            pass            pass                 pass        pass                  pass              pass                pass                pass
Oracle: 36 tasks x 15 methods; 540 exact reproductions.
                 perturbation         format         method        outcome         failures
   straightened SEARCH quotes search_replace          exact       rejected        not_found
   straightened SEARCH quotes search_replace       tolerant      recovered                 
   straightened SEARCH quotes search_replace          fuzzy      recovered                 
      wrong diff line numbers          udiff      git apply      recovered                 
      wrong diff line numbers          udiff      GNU patch      recovered                 
      wrong diff line numbers          udiff context search      recovered                 
      wrong diff line numbers          udiff          fuzzy      recovered                 
blank context lost its marker          udiff      git apply      recovered                 
blank context lost its marker          udiff      GNU patch      recovered                 
blank context lost its marker          udiff context search      recovered                 
blank context lost its marker          udiff          fuzzy      recovered                 
             ambiguous SEARCH search_replace          exact       rejected        ambiguous
             ambiguous SEARCH search_replace       tolerant       rejected        ambiguous
             ambiguous SEARCH search_replace          fuzzy       rejected        ambiguous
       one patch context typo    apply_patch      reference       rejected context_mismatch
       one patch context typo    apply_patch          fuzzy      recovered                 
  interior patch context typo    apply_patch      reference       rejected context_mismatch
  interior patch context typo    apply_patch          fuzzy wrong_document                 
Instrument unit checks: 569 passed. Fuzzy 90,000 chars / 20 blocks: median 0.152s, maximum 0.231s per block.
```

Additional local-fake checks: 24 cache/wrapper checks and 10 pipeline/result-table checks passed. Claude list price and OpenRouter spend were both $0.0000; there are no experimental model calls. A guarded three-document, one-model offline smoke reported 84/84 missing requests and named their request hashes before stopping, with zero network attempts and zero model-process attempts.

## Analysis pass (2026-10-30)

Implemented `SPEC_ANALYSIS.md` in `nb38.py`: fixed strict/forgiving pipelines; JSON per-edit checks;
readable-only collateral measures; format, edit-type, failure and spend tables; seven plotting helpers; original-line
diagnostics; and `find_cases`, `case`, `show_case` and `fig_case_panel`. Analysis cells have narrative placeholders and
run only when results exist. Plot titles have neutral defaults and accept the author's finding. The single style
block copies notebook 29's rcParams, with fixed model markers/colours and status hatches. These scoring choices
replace the earlier unreadable-as-empty collateral description above. The best-pipeline table remains explicitly
labelled as selected on the same data.

`extra_calls` counts retries actually collected for a retry pipeline; `retries_used` separately counts those whose
reply was used. Spend and extra-call totals count actual requests once, rather than repeated scoring rows. Unknown
cost or usage totals remain missing. Wilson intervals use observed request counts; they do not account for shared
documents or tasks.

Line-number diagnostics default to generation replies; `line_number_accuracy(('generation', 'retry'))` provides
separate stage summaries. Hunk locations are found independently in the original, with unplaceable hunks reported
outside the offset denominator. Unmatched line-edit objects remain in the all-object denominator. Ranges may include
adjacent blank separators but no additional nonblank original lines; off-range deletions without identifying text
are unmatched. Example panels highlight differing characters with both background and underline, using measured
monospace spacing and literal punctuation.

Final validation: `NB_STOP_BEFORE_CALLS=1 python build/nb38.py` completed with exit 0, with `NB_LIVE` disabled:

```text
Oracle: 36 tasks x 15 methods; 540 exact reproductions.
Instrument unit checks: 569 passed.
Cache and wrapper local-fake checks: 24 passed; zero model/network calls.
Pipeline/scoring/analysis local-fake checks: 97 passed; 9 figures tested in a temporary folder;
no experimental data/results or production figures written.
```

The expanded synthetic test covers all five models, formats, bundles and length bins, including wrong, unreadable,
retry and collateral cases. A separate audited analysis run rejected any data/production-figure write, network
connection or model process and passed. Plots were visually inspected in temporary storage. SHA256 comparisons
confirmed the protected source sections unchanged, excluding the permitted plot style addition. No model was called
and no experimental data or production figure was written. Spend printed by the script reflects the separate live
collection's existing caches, not these tests. Only `build/nb38.py` and this notes section were edited.

## Patch wording amendment (2026-10-30)

Implemented `SPEC_PATCH_WORDING.md`. `apply_patch_openai` is appended as the eighth format,
with its instructions copied verbatim, the same user prompt template, parser and appliers as `apply_patch`,
`reference` for corrective retries, and fixed pipelines `reference` and `fuzzy + retry`. Neither patch format
uses LLM merge. The two labels distinguish the short wording from OpenAI's wording. The eight complete prompts
are regenerated in `example_prompts.md`.

Both patch formats now have `reference, @@ in context`, immediately after `reference` and before `fuzzy`.
This merge method was added after partial results were seen, as recorded in
`data/PROTOCOL.md`. It preserves the forward reference search and only retries placement
when that fails and the anchor itself occurs in the old lines. The fallback starts at the anchor position
minus the index of its first occurrence in those old lines, never before the current cursor. Splicing still
writes supplied context, including any differences accepted by reference normalisation. It does not add a new
model call or change the retry trigger. The original prompt and reference results remain in the comparison.

Consecutive `@@` headers now form one chunk with anchors searched in order. Single-anchor bodies, block numbers,
failure messages and placement remain unchanged. The oracle and perturbation tests cover both formats and the
new method. Boundary tests cover context and removed anchors, repeated old-side anchors, forward-match priority,
the cursor limit, supplied-context splicing, three stacked anchors, and best-effort continuation after a missing
stacked anchor. Synthetic analysis covers the added format, recovery and retries, example helpers, tables and
all eight formats in figures. The methods figure grows to seven visible panels. There are now 19 deterministic
format/method combinations and 34 total pipelines.

Before editing the script, `check_patch_wording.py` froze its source and request hashes
under `build/.patch_wording/`. The check reads complete records from both live caches without writing them;
the frozen set makes a comparison independent of later appends. It loads only definitions and constants from
the script, without running collection cells. It constructs all 36 x 7 x 5 original generation requests, plus
every retry and merge request implied by those cached generation replies. It also reconstructs each stored
request, verifies any collected retry/merge against its derived prompt, compares existing strict applications,
and checks the new instructions against the specification verbatim. Re-run the comparison with
`NB_LIVE=0 python build/check_patch_wording.py compare`; do not replace the before-edit snapshot.

The key comparison reports:

```text
Request-key comparison: {'generation': 1260, 'merge': 326, 'retry': 167}; all identical before/after.
Cached request reconstruction: 781 identical keys.
Existing strict results: 664 identical before/after.
```

Final offline validation uses `NB_STOP_BEFORE_CALLS=1 python build/nb38.py`, with `NB_LIVE=0`, all nine documents
and five models selected, and temporary files confined to `build/.patch_wording/`. Output is saved in
`patch_wording_test_output.txt`:

```text
Oracle: 36 tasks x 19 methods; 684 exact reproductions.
Instrument unit checks: 635 passed.
Cache and wrapper local-fake checks: 24 passed; zero model/network calls.
Pipeline/scoring/analysis local-fake checks: 113 passed; 9 figures tested in a temporary folder;
no experimental data/results or production figures written.
```

For both patch formats, `anchor repeated in context` is rejected by `reference` and recovered exactly by
`reference, @@ in context`. These are deterministic test outcomes, not a measured advantage for the new wording.
The final command also loads a local Python audit guard from `build/.patch_wording/sitecustomize.py`, which
rejects network access, model processes, writes under `data/`, and writes outside this notebook folder.
No model was called and neither the collection caches nor `data/results/` was written. Any spend printed at the
end comes from the separate live collection's existing caches.

## Native diffs, plural renames and blank lines (Amendment 2, 2026-10-30)

Implemented `SPEC_AMENDMENT2.md`. The protocol entry is
`Amendment 2`, after the original 1,260 generation replies and before
retry and merge collection. There are now 20 deterministic format/method combinations and
35 total pipelines. The generation and merge collection cells, prompt builders, instruction
strings, model settings and strict udiff retry method are unchanged.

`apply_external_diff` no longer calls `parse_udiff`, checks hunk counts in Python or serialises
parsed hunks. It unwraps the reply, fixes the file headers to `a/document.md` and `b/document.md`,
and drops `diff --git`/`index` lines. Raw hunk text retains its original header, line endings,
blank markers (including missing markers), missing final lines and trailing blank lines.
Native diagnostics and reject files supply per-hunk verdicts. A fatal whole-diff failure
restores the original and invokes the same tool cumulatively on each individual raw hunk.
Failures quote trimmed native error lines, which feed the prospective corrective prompts.
`git apply --recount` follows `git apply` in both method orders. `git apply` remains strict
for udiff retries. The Python context-search and fuzzy methods retain their defined parser
leniencies.

Observed perturbation outcomes on git 2.45.1.windows.1 and GNU patch 2.7.6:

| Method | Final blank context line missing, header count one too high | Blank context lines lack their space marker |
|---|---|---|
| `git apply` | Rejected, native `corrupt patch` error | Recovered exactly |
| `git apply --recount` | Recovered exactly | Recovered exactly |
| `GNU patch` | Recovered exactly | Recovered exactly |
| Python `context search` | Recovered exactly | Recovered exactly |
| Python `fuzzy` | Recovered exactly | Recovered exactly |

None of these ten perturbation outcomes produced a wrong document. These are deterministic
fixture results, not measured model success rates. Raw-byte interception tests check what
each native process actually receives, including fixed paths and unmodified missing context.
A three-hunk fixture includes an insertion, a corrupt middle hunk and a valid final hunk:
strict git applies the first and third cumulatively, rejects only the second with its own
parse error and receives each fallback hunk byte for byte. Recount and GNU patch recover all
three. A separate non-matching removed line checks ordinary native per-hunk rejects without
triggering fatal fallback.

`rename_pattern` implements `(?<![A-Za-z0-9])X(?=s?(?![A-Za-z0-9]))`: only the base is
replaced, so its lowercase plural `s` remains. Expected-document generation, edit checks,
collateral target identification and line-edit diagnostics all use this rule. Candidate
selection retains the frozen base-abbreviation choice, so no instruction changes. For
`2026-21300_rename`, 16 singular and 23 plural occurrences now give 39 occurrences in both
the task metadata and the check. This corrects the old treatment of seven paragraphs as
collateral. Other abbreviations and the excluded larger words/URL forms are covered by
boundary tests.

`migrate_amendment2.py` regenerates the expected text from the saved
edits, changes only that task's count/check/hash, and asserts that the other 35 expected
documents and task records remain unchanged. The old answer is preserved byte for byte at
`expected_v1/2026-21300_rename.md`. The frozen
manifest covers both answers. `rename_rule_comparison(merges)` reapplies the selected saved
reply locally and reports the exact count per format/method against each answer, including
generation, retry and LLM-merge reply provenance. It makes no model calls. Synthetic tests
check known old/new counts, every format/method and exclusion of unrelated tasks.

`exact_nonblank` compares normalised documents after dropping every blank line. `exact`
and the three primary statuses remain unchanged. Both format and method summaries include
the secondary count and rate. `near_misses(merges)` reports the number of readable wrong
documents that pass the secondary measure for each fixed format/pipeline. Tests cover a
blank-line-only mismatch, preserved nonblank line boundaries, changed text, unreadable
replies, denominator reconciliation and percentage display. The analysis cells display both
new comparison tables when real results exist.

Before editing, `check_amendment2.py` froze the current source, input
texts and request hashes under `build/.amendment2/`. Its fixed cache-key set contains 993
complete records, independent of later live appends. It constructs all 36 x 8 x 5 generation
requests and every merge request implied by that snapshot, reconstructs all stored requests,
and compares the before/after hashes. It also asserts that the actual collection cells,
prompt builders and settings are unchanged, so later collected replies use the same merge
request construction. The amendment permits strict native failure messages, and therefore
uncollected retry prompts, to change; strict results and retry keys are deliberately outside
this amendment's equality comparison. The older amendment-1 comparison remains its historical
record; use `NB_LIVE=0 python build/check_amendment2.py compare` for the current source.

`amendment2_key_comparison.txt` reports:

```text
Request-key comparison: {'generation': 1440, 'merge': 414}; all identical before/after.
Cached request reconstruction: 993 identical keys.
Prompt builders/settings unchanged, including merges for later collection appends.
Expected documents: 35 byte-identical; only 2026-21300_rename changed; old version preserved.
Task instructions unchanged; rename check includes 23 plural occurrences; frozen manifest verified.
```

Final offline validation ran `NB_STOP_BEFORE_CALLS=1 python build/nb38.py` with `NB_LIVE=0`,
all nine documents and five models. Temporary files and matplotlib configuration were confined
to `build/.amendment2/`; the existing `build/.patch_wording/sitecustomize.py` audit guard
blocked model processes, network access, all data writes and writes outside the notebook
folder. Full output is saved as UTF-8 in
`amendment2_test_output.txt`:

```text
Oracle: 36 tasks x 20 methods; 720 exact reproductions.
Instrument unit checks: 740 passed.
Cache and wrapper local-fake checks: 24 passed; zero model/network calls.
Pipeline/scoring/analysis local-fake checks: 132 passed; 9 figures tested in a temporary folder;
no experimental data/results or production figures written.
Offline audit: {'model_processes': 0, 'network_attempts': 0, 'data_writes': 0, 'outside_writes': 0}
```

The command completed with exit 0. No model was called and no collection cache or
`data/results/` file was written. Spend printed at the end reflects the separate collection's
existing caches, not these tests.

## An abbreviation inside a link (Amendment 3, 2026-10-30)

Implemented `SPEC_AMENDMENT3.md`. The new
`protocol entry` records that this correction was specified after
generation replies and retries, while LLM merges were being collected. Of the 40 generation
replies for `2026-22093_rename` (eight formats and five models, each with its last-listed
deterministic method), 24 also renamed the URL's `%20FEVS%20` occurrence, and 12 of those
were otherwise exact. The primary answer gave three exact replies. Accepting either link
reading therefore gives 15 exact replies for that comparison. This observation motivated
the answer correction; it is not a rule fixed before the outputs were seen.

The only alternative is
`expected_alt/2026-22093_rename.md`. It changes
that one URL occurrence to `%20FEVA%20`. The task's `accepted_alternatives` list records its
data-relative `file` and `sha256`; the frozen manifest covers it and the updated task file.
`migrate_amendment3.py` uses the before-edit snapshot and changes
only those authorised inputs. All 36 primary expected documents remain byte-identical,
and the other 35 task records are unchanged. Instruction text, rename counts and individual
edit checks are unchanged for every task. The script loads and verifies alternative hashes
alongside the primary answers.

`score_result` chooses exact first, then `exact_nonblank`, then fewer collateral paragraphs,
then the primary answer on a tie. `matched_answer` is `primary` or the alternative's
data-relative file name. Strict exactness, collateral characters and dropped paragraphs
come from that same selected answer; they do not influence selection. Shared edit checks
are still evaluated once against the output. Unreadable replies select the primary answer
and keep their false exact scores and undefined collateral measures. The case helper shows
the selected expected text so that an accepted link change does not appear as an error.

`link_rule_comparison(merges)` reports exact counts with and without the alternative for
every available format/method, reconstructing generation, retry or merge output locally.
`rename_rule_comparison(merges)` keeps the plural correction's previous/current comparison.
`rename_corrections_comparison(merges)` combines them into eight rows, one per format for
the existing fixed forgiving pipeline, across all rename tasks. It reports the exact count
before both corrections, each correction's gain and the current exact count, with the
method and denominator visible. Pass `pipeline='strict'` for the other fixed pipeline.
The analysis cell displays this compact table; the two detailed helpers remain available.
Neither helper calls a model or changes the chosen pipeline.

Oracle replies are now built separately from both accepted FEVS answers in every format.
Every deterministic method must reproduce each answer exactly and record its correct
`matched_answer`. Synthetic fixtures distinguish all four selection priorities, including
a primary answer that wins a normalised tie despite the alternative's strict byte match.
Link fixtures cover both exact readings, blank-line-only near misses, extra paragraphs,
unreadable replies, every format/method, retry and LLM-merge provenance, and the compact
table's reconciliation with all rename scores. The URL lies on a paragraph already
involved in the rename: with an unrelated extra paragraph, both expected answers can have
equal collateral, so the specified tie rule chooses the primary. The test asserts this
rather than assuming the URL alone determines the selected answer.

Before source or input changes, `check_amendment3.py` saved the source,
all frozen primary answers and a fixed set of complete live-cache records by key under
`build/.amendment3/`. It constructs every 36 x 8 x 5 generation request, plus every retry
and merge request implied by the frozen generation replies. Comparison reconstructs all
stored requests, checks every request hash and strict result, and verifies that all existing
functions except the authorised scoring, oracle, analysis-test, comparison and case helpers
are unchanged. Assignments and collection cells are also protected. In particular, the
owner's Claude concurrency of 12, native patch final newline and $0.50 Haiku reservation
are preserved. Later cache appends cannot change this comparison's fixed key set.

`amendment3_key_comparison.txt` reports:

```text
Request-key comparison: {'generation': 1440, 'merge': 525, 'retry': 439}; all identical before/after.
Cached request reconstruction: 1971 identical keys.
Existing strict results: 1260 identical before/after.
All 36 primary expected documents byte-identical; only FEVS task metadata gained an alternative.
Task instructions, edits and checks unchanged; alternative and frozen manifest verified.
```

Re-run the check with `NB_LIVE=0 python build/check_amendment3.py compare`; never replace
the before-edit snapshot. The offline command uses all nine documents and five models,
`NB_STOP_BEFORE_CALLS=1` and `NB_LIVE=0`, with temporary files and matplotlib configuration
under `build/.amendment3/`. The existing
`audit guard` blocks model processes, network access,
every data write and writes outside this notebook folder during validation. Full output is
saved in `amendment3_test_output.txt`. Any spend printed there
belongs to the separate live collection's existing caches.

The final `NB_STOP_BEFORE_CALLS=1 python build/nb38.py` run completed with exit 0:

```text
Oracle: 36 tasks + 1 accepted alternatives x 20 methods; 740 exact reproductions (20 from alternatives).
Instrument unit checks: 756 passed.
Cache and wrapper local-fake checks: 24 passed; zero model/network calls.
Pipeline/scoring/analysis local-fake checks: 147 passed; 9 figures tested in a temporary folder;
no experimental data/results or production figures written.
Offline audit: {'model_processes': 0, 'network_attempts': 0, 'data_writes': 0, 'outside_writes': 0}
```

No model was called, `NB_LIVE=1` was never used, and neither collection cache files nor
`data/results/` were written. The input migration wrote only the alternative, task metadata
and frozen manifest; the other data change is the requested protocol entry.

## Final figures and worked cases (2026-10-30)

Implemented `SPEC_FIGURES.md` in `nb38.py`. The first analysis
cell defines the seven exact finding titles once, and each production figure call passes
its corresponding title. Figure layout reserves space for finding titles and wraps long
case labels. The token axis uses only the specified in-range fixed ticks, with comma
separators and no minor tick labels. The line-offset plot uses the specified integer ticks
up to the observed maximum, the requested axis title, and a separate right-hand text
column for each model's exact share and hunk count.

Eight worked-case cells follow the example helpers, each with its own narrative placeholder
in the requested order. Retry cases display the original reply, first application failures,
the actual corrective request after its original-prompt prefix, the retry reply and final
status. Extra displays compare generation character/token counts, find rename occurrences
outside all SEARCH spans, count quotation changes throughout the expected and returned
documents, locate every literal occurrence of the repeated sketch anchor, compare both
patch methods, display the missed-year lines, and expose inserted line breaks as escaped
quoted strings.

`examples_silent_errors.png` is built from cases 4,
5 and 7. Its instructions, reply excerpts and first unequal expected/merged lines are
computed from `case()`. The measured examples contain 104 straightened double quotation
marks, two original rename lines omitted from SEARCH blocks, and a sketch segment whose
opening `(ii) [Reserved]` occurs at original lines 183 and 189. The last case keeps 1995
where the correct replacement calls for 2000. Each case retains its stable task ID.

The synthetic checks now cover retry display order and provenance, occurrence coverage,
character-change categories, mismatch excerpts, repeated anchors, fixed tick formatting
and the separate annotation column. All seven production figure designs were rendered
and visually inspected at 900 px width; their text does not overlap. The ordered 34 TODO
lines are also saved in `figures_narrative_placeholders.txt`.

Before editing, source and read-only data hashes were frozen under `build/.figures/`.
AST comparison confirms that all original top-level assignments, collection cells and
request builders are unchanged, including Claude concurrency 12, the native-diff final
newline and the $0.50 Haiku cost reservation. The replay audit guard permits writes to
`data/results/` and figures while rejecting model processes, network access, writes to
other data files (including every `data/cache_*.jsonl`) and writes outside this folder.
The owner concurrently appended the collection record to `data/PROTOCOL.md`; that edit
was preserved. Both response-cache hashes remain identical to the before-edit snapshot.
