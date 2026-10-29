# Protocol and run history: notebook 02

This file records the settings and history behind the results in `README.md` and `02_decisions_api_chunking.ipynb`. It is for readers who want to check or repeat the work. Entries are in date order.

## Settings of the committed run

These are the values in the notebook's setup and method cells.

- Decisions model: `openai/gpt-6-luna-decisions`, called with HTTP POST at `https://openrouter.ai/api/alpha/decisions`. The undated name was requested; the cache stores only `answers`, `usage` and `latency_s`, so no dated version or permaslug was recorded.
- Embedding model: `nvidia/llama-nemotron-embed-vl-1b-v2:free` at `https://openrouter.ai/api/v1/embeddings`, 512 dimensions, float encoding; the notebook scales every vector to unit length. No revision or serving host was recorded. Empty strings are sent as `(blank)` because the free endpoint rejects them.
- Tokenizer for all size limits and counts: `tiktoken` `o200k_base`.
- Candidate passages ("units"): extraction blocks merged forward until at least 40 tokens (`MIN_UNIT`); passages over 200 tokens (`MAX_UNIT`) split at sentence ends, then packed up to 200 tokens.
- Size limits shared by every cutter: at most 400 tokens per piece (`MAX_CHUNK`); the segmenter subtracts a penalty of 3.0 for pieces under 100 tokens (`MIN_CHUNK`, `small_penalty`). Probabilities are clipped to 0.001 to 0.999 before taking logarithms.
- Fixed tokens: 400-token windows with a 50-token overlap. Recursive: separators blank line, `". "`, space, then token windows; pieces packed greedily up to 400 tokens.
- Headings scorer: 0.9 if either of the first two blocks of a passage has 1 to 12 words, does not end with `.`, `,`, `;` or `:`, and matches a numbered or "Chapter/Section/Part/Appendix" pattern, is Title Case, or is upper case and longer than 3 characters; otherwise 0.1.
- Semantic scorer: cosine distance between the mean embedding of the 2 passages before and the 2 passages after each candidate, passed through a logistic function centred on the 90th percentile of distances with scale 0.25 standard deviations; the first passage gets 1.0.
- Decisions scorer: windows of 40 passages (`WIN`) with 4 passages of context on each side (`CTX`); one yes/no (`noul`) question for each of the middle 32 passages; a new window every 32 passages; 8 calls in parallel (`WORKERS`). A refused window would fall back to 0.1 for its passages; none was refused.
- Reference section starts ("gold"): for PDFs, each outline entry (`doc.get_toc()`) is matched to the first block on its target page or the next page whose normalised text, with leading section numbers removed, starts with the first 40 normalised characters of the entry title (entries under 3 characters are skipped). For the RFC text, a block is a start if it is one line under 90 characters matching `^\d+(\.\d+)*\.\s+[A-Za-z]`; this pattern excludes status-code headings such as `15.5.6. 405 Method Not Allowed`. Documents with fewer than 10 starts (Berkshire 0, IPCC 5) are left out of the section tests.
- Passage labels for average precision and ROC-AUC: a passage is a start if a reference start lies within its first 120 characters. The first passage of each document is excluded.
- Section-structure measures: tolerance of 200 characters for both section-start recall and mixed-section pieces; per-document rates averaged over the four outlined documents.
- Retrieval: one pooled index per cutter over all six documents, cosine similarity between question and piece embeddings, a hit when a piece of the right document covers at least 50% of the evidence quote's characters. Bootstrap for recall@5: `numpy.random.default_rng(0)`, 2,000 resamples of the 33 questions.
- Evidence quotes: located by matching lower-case letters and digits only, falling back to the first 60 normalised characters; 33 of 33 found.

## Data sources

- Documents, downloaded on first run into `data/docs/` (not committed):
  - `https://arxiv.org/pdf/1706.03762v7`
  - `https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63b.pdf`
  - `https://www.rfc-editor.org/rfc/rfc9110.txt`
  - `https://www.berkshirehathaway.com/letters/2023ltr.pdf`
  - `https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_SPM.pdf`
  - `https://www.irs.gov/pub/irs-prior/i1040gi--2024.pdf`
- Dates printed on the documents: NIPS 2017; June 2017 with updates as of 2 March 2020; June 2022; 24 February 2024; 2021; 16 December 2024.
- Questions: `data/questions.csv`, from `https://raw.githubusercontent.com/k-sandhu/lumen-copilot/main/backend/tests/eval/benchmark/questions.csv`. 101 questions, 87 answerable; 33 have an evidence quote in one of the six documents. The file records no author, creation date or licence.
- No licence is recorded for any document or for the questions file. The date the documents were downloaded is not recorded.

## History

### 2026-10-17: first commit with outputs

- Commit `2901f83d` added the notebook with its outputs and caches: 144 Decisions calls, 4,528 yes/no answers, 1,435,206 input tokens, 0 output tokens, $0.1435 at $0.10 per million input tokens, 0 refused windows, latency 1.16 s mean and 167 s summed. The embedding cache holds 9,326 vectors (every passage, piece and question text), all used by the notebook. The notebook does not record the date or wall-clock time of the live run.
- The original takeaways said that the recall@1 and MRR leader "flips between runs": Semantic + DP led with the free embedding model, and Decisions + DP "led with the paid ones". No data from a run with a paid embedding model is in this repository, and the model is not named, so that statement cannot be checked. It was removed from the reader text in the 2026-10-28 rewrite.
- Later the same day, commits `1cf89c87` (contents and workflow diagrams), `bec1be78` (escaped dollar signs) and `5630274b` (future work and further reading, links checked on 17 October 2026) changed markdown only.

### 2026-10-28: text rewrite and replay check

- The README and the notebook's markdown cells were rewritten for new readers. No code cell, output, figure or cache was changed, and no model was called.
- Before rewriting, the notebook's code cells were replayed offline from the committed caches, with network calls disabled, to recount per-item values the notebook computes but does not print. The replay reproduced every committed table exactly: units per document, the cost table, chunk sizes, average precision and ROC-AUC per document, section-structure means and the retrieval table. Environment: Python 3.13.5, PyMuPDF 1.28.0, tiktoken 0.13.0, scikit-learn 1.9.0, pandas 2.3.1, numpy 2.2.6.
- SHA-256 of the document copies used in that replay:

  | File | SHA-256 |
  |---|---|
  | `arxiv-attention.pdf` | `bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697` |
  | `nist-sp-800-63b.pdf` | `ccfce7510a1267933f912d023306c6e7d485f21be63d271108b61aad6139127e` |
  | `rfc9110-http-semantics.txt` | `21c1cdce6ab0e5509b04d84a28000836c7a087cf786efe6f04877ebfff47232a` |
  | `berkshire-2023-letter.pdf` | `829169be21f4ce05202720fe5645cc1b9a5b1ae20bf5e6ebaff987349766eafd` |
  | `ipcc-ar6-wg1-spm.pdf` | `37c9fa760757524c8d69630a89cecab9ebcacb66786970a3439da0619875e446` |
  | `irs-1040-instructions-2024.pdf` | `0ae53ed5020d69e6571d40cd7955b7735f44a28df483626d128628d2810e93d4` |

- Values added to the reader text from that replay: the search rank of every question for every cutter (`_hits`); pooled counts of section starts hit and mixed pieces; the per-passage scores and labels quoted in the examples; the raw request and reply for the NIST window covering passages 125 to 164 (cache key `30eadf99552cbd955e38ffe3978932cc07c78e33d9f636e18b0b73f4898c80e9`); counts of heading-rule false alarms by first word; the 34 RFC passages that open with a status-code heading; and the RFC average precision when those passages are counted as starts (Decisions 0.616, Headings 0.694, Semantic 0.510, against 0.543, 0.583 and 0.502). The re-scored values are a sensitivity check and do not replace the notebook's results.
- The analysis was not preregistered. The questions, metrics and tolerances were chosen when the notebook was written, and the error analysis was added after the results were known.
