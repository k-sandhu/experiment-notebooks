# Notebook 03 protocol and run history

This file records what is known about how the results in this folder were produced. Nothing here was written before the run: the comparison was not preregistered, and the analysis was not fixed before the results were seen.

## Before 17 October 2026: the run

The notebook, its catalog and both caches were built in an earlier project and moved into this repository with their caches. The date of the model calls is not recorded in `data/`. The catalog includes documents with estimated publication dates up to late September 2026 (`published` in `catalog/nydps-liberty-water-26-w-0358/files.jsonl`).

Settings, from the notebook's code:

| Setting | Value |
|---|---|
| Decision model | `openai/gpt-6-luna-decisions` through OpenRouter's Decisions endpoint (`https://openrouter.ai/api/alpha/decisions`); undated name, no dated version recorded in the cache |
| Embedding model | `nvidia/llama-nemotron-embed-vl-1b-v2:free` through OpenRouter's embeddings endpoint, 512 dimensions; free endpoint, no dated version recorded |
| Instruction for type questions | "What type of document is this? Choose the single best-matching document type. Judge by the document's form and purpose, not just its topic." |
| Instruction for the group question | "Which family of documents does this document belong to?" |
| Excerpt lengths | First 2,000 and first 8,000 characters of the extracted text |
| Text extraction | PyMuPDF, first 6 pages, whitespace collapsed; documents with under 300 characters dropped |
| File size limit | 3,000,000 bytes |
| Sampling | Seed 7; documents per type per collection set in `RULES` (1 to 8); facility records taken from the hand-reviewed list `REVIEWED` |
| Shortlist size | 15 types |
| Group-first beam | Top 2 groups |
| Parallel workers | 8 documents at a time |
| Retries | Up to 8 attempts on HTTP 429 and 5xx; an HTTP 502 containing "refused" is a refusal and is not retried |

Selection: 289 documents selected, 13 dropped for too little text (10 with no text layer, 3 with 131 to 261 characters), 276 scored. All 13 dropped files downloaded and matched their sha256.

Correct types: rules over publisher metadata for 21 collections (194 documents); a first-page review for 82 facility records, about four files per file-name pattern. The reviewer is not recorded and there was no second reviewer.

## Contents of the caches

`decisions_cache_classification.jsonl` holds 1,634 replies with a total recorded cost of $0.4746. Matching the cache against a replay of the final code (see below) gives:

| Part | Replies | Cost | Notes |
|---|---|---|---|
| Used by the final run | 1,357 | $0.4142 | 1,379 calls: 276 + 276 for one question at 2,000 and 8,000 characters, 552 for group first, 275 answered shortlist calls. 22 documents with 2,000 characters of text or fewer send the same request at both lengths. |
| Final run's refusal | 1 | $0 | Line 1514; shortlist request for `wild-mooring-anglian-waterways`, HTTP 502 "OpenAI refused to answer question "doc_type"" |
| Earlier shortlist requests | 275 | $0.0604 | Lines 1083 to 1358; each a 15-type choice question whose option set matches none of the final run's shortlists. Probably an earlier embedding ranking; the cache does not record which. Not used by any result. |
| Earlier refusal | 1 | $0 | Line 1146, among the earlier shortlist requests |

`embeddings_cache.npz` holds 377 vectors: the 101 type descriptions and the 276 documents of the final run. No vectors from the earlier shortlist remain.

## 17 October 2026: added to this repository

- Commit `2901f83d` added the notebook, catalog and caches.
- Commit `1cf89c87` added the contents list, the workflow diagram, the call graph and explainers.
- Commit `5630274b` added the future work and further reading section; its links were checked on 17 October 2026.

## 28 October 2026: text rewrite

The README and the notebook's markdown cells were rewritten. No model was called and the notebook was not re-run; code cells, outputs and figures are unchanged.

New per-document counts in the text (counts of correct documents, errors by probability, shortlist misses, refusals, the date split, the drop reasons and the cache split above) were computed by a read-only replay. The replay ran the notebook's own selection and extraction code on the previously downloaded PDFs, with network access disabled, and looked up each request's key in the cache. All 1,380 decision requests (1,379 answered calls and the refused one) and all 377 embedding inputs were found in the caches, and the replay reproduced the notebook's printed counts, results table and confusion pairs.

The decision model's knowledge cutoff, 18 May 2026, was taken from OpenAI's GPT-6 Luna model page (https://developers.openai.com/api/docs/models/gpt-6-luna), checked on 28 October 2026. Against the catalog's `published` dates, 236 documents are dated before the cutoff, 35 after and 5 span it.

Statements in the earlier README that the data does not support were corrected:

- "About 300 public PDFs": 276 documents were scored (289 selected).
- "$0.48 per 1,000 documents" for one question on 8,000 characters: the notebook's results table gives $0.47 ($0.4748).
- "One flat question is the best design": it ties with group first at 251 of 276.
- "Embeddings capture topic, not document form", stated as a finding: the measured part is that the shortlist held the correct type for 93.1% of documents; the explanation is now given as a possible reading.
- Comparisons with other notebooks were removed so that this notebook stands alone.
