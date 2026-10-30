# Notebook 38, amendment 1: a second wording for the OpenAI patch format

## Why

Partial results (630 generation replies) show the `apply_patch` format failing under the `reference` applier far
more than the others: 18 of 87 exact. In 160 of 258 chunks that have an `@@` anchor line, the anchor is also one of
the chunk's own context or removed lines, usually not the first one. OpenAI's reference rules look for the old lines
only after the anchor line, so those chunks cannot be placed, although 474 of 526 chunks' old sides occur exactly in
the document. Our prompt said `@@ a line just before the change, copied from the document`, which invites a nearby
line. OpenAI's own instructions (GPT-4.1 prompting guide, "Appendix: Generating and Applying File Diffs") show 3 lines
of context immediately above and below each change and use `@@` only when that context is not unique, to name the
class or function (here: the section heading) the snippet belongs to.

## What to add (do not change anything that already exists in a cache key)

1. A new format `apply_patch_openai`, appended at the end of `FORMATS`, with the same user prompt as every other
   format and these FORMAT_INSTRUCTIONS, verbatim:

```
Reply with a patch in this format, and nothing else:

*** Begin Patch
*** Update File: document.md
@@ the heading of the section the change belongs to
[3 unchanged lines immediately above the change]
-removed line
+added line
[3 unchanged lines immediately below the change]
*** End Patch

Rules: do not use line numbers; the unchanged lines are enough to identify each change. Each line of a change starts with one character: a space for an unchanged context line, - for a removed line and + for an added line, and context and removed lines must match the document exactly. By default, show 3 unchanged lines immediately above and 3 immediately below each change. If a change is within 3 lines of a previous change, do not repeat the first change's lines below in the second change's lines above. If 3 lines of context are not enough to identify the place uniquely, add an @@ line naming the heading of the section the change belongs to; you can stack several @@ lines to narrow it down. A line that changes is removed in full and added in full.
```

   (The `[3 unchanged lines ...]` placeholders are literal in the instructions, as in OpenAI's guide.) It uses the
   same parser and appliers as `apply_patch`, the same strict method (`reference`) for retries, no LLM merge, and
   `MAIN_PIPELINES['apply_patch_openai'] = ('reference', 'fuzzy + retry')`. Labels:
   `FORMAT_LABELS['apply_patch'] = 'OpenAI patch, short wording'` and
   `FORMAT_LABELS['apply_patch_openai'] = "OpenAI patch, OpenAI's wording"`. The parser must accept several stacked
   `@@` lines before one chunk (each a further anchor, sought in order from the cursor, as the reference does).
   If the existing parser already treats consecutive `@@` lines as empty chunks, make stacked anchors work without
   changing how a single-anchor patch parses.

2. A new deterministic method for both patch formats, `reference, @@ in context`: identical to `reference`,
   except that when a chunk's old lines are not found after its anchor and the anchor line itself occurs among the
   chunk's old lines (context or removed), the search for the old lines starts at the anchor's position minus the
   number of old lines that precede the anchor's first occurrence in the chunk (never before the cursor). It
   writes the chunk the same way `reference` does. Add it to the method order after `reference`, before `fuzzy`. It
   is a merge method added after partial results were seen: say so in NOTES.md.

3. Extend the oracle self-test, perturbation tests and synthetic analysis tests to the new format and method, add
   a perturbation `anchor repeated in context` that `reference` rejects and `reference, @@ in context` recovers,
   and regenerate `build/example_prompts.md` with the eighth prompt. All existing results must stay identical:
   check that every existing generation, retry and merge request built by the script hashes to the same key as
   before your change (compute the keys for all 36 x 7 x 5 generation requests before and after and compare; the
   cache file `data/cache_cli.jsonl` may be read for this but never written).

4. Append an entry to `data/PROTOCOL.md`, dated 2026-10-30, titled "Amendment 1 (after 630 of 1,260 replies were
   seen)", stating the observation above with its counts, the added format and method, and that the original
   `apply_patch` prompt and `reference` results stay in the study unchanged.

The same constraints as before: write only in this folder; never write the caches or `data/results/`; never call a
model; do not run with `NB_LIVE=1`. Finish by running `NB_STOP_BEFORE_CALLS=1 python build/nb38.py` and report.
