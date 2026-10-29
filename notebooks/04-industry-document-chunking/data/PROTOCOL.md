# Notebook 04 protocol and run history

This file keeps the run settings and history that matter to someone checking the work. The reader-facing account is in `../README.md` and the notebook.

No analysis plan was registered before the results were seen. This notebook predates the repository's rule that test data must be newer than the models.

## Settings of the committed run

- Decisions model: `openai/gpt-6-luna-decisions`, requested through OpenRouter's Decisions endpoint (`https://openrouter.ai/api/alpha/decisions`). The cached replies hold `answers`, `usage` and `latency_s` only; no model version, permaslug or date was returned or saved.
- Embedding model: `nvidia/llama-nemotron-embed-vl-1b-v2:free`, OpenRouter free endpoint (`https://openrouter.ai/api/v1/embeddings`), 512 dimensions, `encoding_format: float`, vectors normalised after loading. Empty strings are sent as `(blank)` because the free endpoint rejects empty input. No dated version recorded.
- Tokenizer for all token counts: `tiktoken` `o200k_base`.
- Chunk budget: at most 400 tokens (`MAX_CHUNK`); chunks under 100 tokens (`MIN_CHUNK`) cost a penalty of 3.0 in the cut-placing step. Fixed windows overlap by 50 tokens.
- Candidate paragraphs ("units"): text blocks merged forward to at least 40 tokens (`MIN_UNIT`), split at sentence ends above 200 tokens (`MAX_UNIT`).
- Decisions windows: 40 units (`WIN`) with 4 units of context on each side (`CTX`), so 32 `noul` questions per call; 8 calls in parallel (`WORKERS`). A refused window would fall back to probability 0.1 for its units; none was refused.
- Heading scorer: 0.9 if one of a unit's first two blocks matches the heading test, else 0.1. Topic-change scorer: cosine distance between the mean embeddings of the 2 units before and after each candidate, passed through a logistic centred on the 90th percentile with scale 0.25 standard deviations.
- Bookmarked section starts: PDF outline entries matched to a block on the target page or the next one; documents with at least 10 matched starts are used for the section tests. A unit counts as a start when a bookmarked start lies within its first 120 characters; boundary tolerance for the chunk measures is 200 characters.
- Evidence: question files in `catalog/` whose name does not contain `generated`; answerable questions with evidence in at most two files; quotes of at least 40 characters from the 12 PDFs. Quotes are matched on letters and digits; when the full quote is not found the first 60 normalised characters are tried. Retrieval hit: a top-k chunk from the right document covering at least min(half the quote, 300 characters). Evidence intact: quotes of at most 600 characters lying inside one chunk. Bootstrap: 2,000 resamples of the pairs, seed 0.
- PDFs: downloaded on first run into `docs/` (git-ignored) and checked against the sha256 in each `catalog/<dataset>/files.jsonl` row.

## History

- Before 2026-10-17: the Decisions calls in `decisions_cache_chunking.jsonl` were collected (278 calls; the cache stores no timestamps). The notebook text recorded that an earlier configuration used OpenAI's `text-embedding-3-small` for the topic-change scorer and the search index, and that its recall@5 on these documents was 0.36 to 0.42. Neither that run's cache nor its outputs are in `data/`; `embeddings_cache.npz` holds only the 16,763 vectors the committed run uses. The README and notebook no longer report the earlier figure.
- 2026-10-17: the notebook was executed top to bottom (cell execution metadata, 06:02 UTC) and committed with its outputs and caches (commit `2901f83d`). Same day: contents, workflow diagrams and explainers were added (`1cf89c87`), and the future work and further reading section was added with links checked on 17 October 2026 (`5630274b`).
- 2026-10-28: the README and the notebook's markdown were rewritten. No model calls, no re-run, no code or figure changes. Counts the notebook does not print (per-pair search ranks, splits per distinct quote, per-document positives, page counts) were recounted by a script outside the repository that replays the notebook's code on the sha256-verified PDFs and the committed caches; it reproduced every printed table exactly. Two statements in the earlier text were corrected: the other methods' split rates are 7.0% to 8.5% of short quotes (the earlier text said 6% to 8%), and the questions' authorship is not recorded in `catalog/` (the earlier text called them human-authored).

## Spend

- Decisions API: 278 calls, 2,701,384 input tokens, $0.270 recorded in the cache (`usage.cost`), summed call time 531 s.
- Embeddings: free endpoint, $0.
- The 2026-10-28 rewrite: $0.
