# Protocol and run history: notebook 01

This file keeps the run record that the README and notebook leave out of the reader's text. Entries are in date
order. No preregistration or analysis plan was written before the results were seen.

## Before 17 October 2026: data collection and model calls

The exact collection dates were not recorded. The Decisions responses carry the model version
`openai/gpt-6-luna-decisions-20261006`, so every call was made on or after 6 October 2026.

- Topics: every OpenAlex topic in fields 17 (Computer Science), 14 (Business, Management and Accounting) and 18
  (Decision Sciences), fetched from `https://api.openalex.org/topics` in three pages of 200 and saved to
  `openalex_topics.json` (508 topics, 24 subfields). Each topic text sent to the model is the name, the description
  and the first six keywords.
- Works: `https://api.openalex.org/works` with filter
  `primary_topic.field.id:17|14|18,has_abstract:true,type:article,language:en,publication_year:2020-2024`,
  `sample=600`, `seed=42`, three pages of 200, saved to `openalex_works.jsonl` (600 works). Filters applied in the
  notebook: topic in the 508, de-duplication by ID and title (none removed), `primary_topic.score >= 0.9`, abstract
  of at least 80 words (332 left), then a pandas sample of 200 with `random_state=42`. The model sees title and
  abstract cut at 3,000 characters.
- The download date of the works file is not recorded. OpenAlex's topic help page, checked on 28 October 2026,
  says the topic classifier was replaced in October 2026 (the old one used title, abstract, citations and journal;
  the new one title, abstract and source name). Which classifier assigned the saved primary topics is not known.
- Licence: OpenAlex data is CC0.
- Decisions endpoint: `POST https://openrouter.ai/api/alpha/decisions`, requested model
  `openai/gpt-6-luna-decisions` (undated). Each request holds only `model`, `state` (title and abstract) and
  `questions`. Responses are cached in `decisions_cache.jsonl` under the SHA-256 of the JSON request with sorted keys.
- Embeddings: `POST https://openrouter.ai/api/v1/embeddings`, model `nvidia/llama-nemotron-embed-vl-1b-v2:free`,
  512 dimensions, float encoding, batches of 256, normalised to length 1. Cached in `embeddings_cache.npz` under the
  SHA-1 of model name and text (708 vectors). The free endpoint allowed 1,000 requests per day per key and may log
  inputs.
- Settings: `N_DOCS = 200`, `SEED = 42`, `WORKERS = 8` (abstracts in parallel), shortlist `K = 25`, tournament
  finalists 8 per half from a fixed random split of the 508 topics (seed 42), subfield-first beams 1 and 3.
- Retries: HTTP 429 and 5xx responses were retried up to 8 times with exponential backoff. An HTTP 502 whose body
  contained "refused" was not retried; it was cached as a refusal and scored as an abstention (no label,
  confidence 0).

### The option-limit probe

The notebook's text reports that one `choice` question with all 508 topics as options was rejected, that a question
accepts at most 255 options, and that a call accepts at most 200 questions. The rejection was not cached, because
the cache stores only answers and refusals, so the committed output of that cell reads "Not in the cache and
OPENROUTER_API_KEY is not set". No question in the run has more than 254 options and no call more than 2 questions.
On 28 October 2026 OpenAI's Decisions guide said a request may include 1 to 400 questions and stated no limit on
options; OpenRouter's API reference stated neither limit.

### Refusals

Four cached responses are refusals, each an HTTP 502 with the message "OpenAI refused to answer question" naming the
question: W4281612646 and W3098278328 (tournament with descriptions, round 1), W3098314892 (subfield question shared
by both subfield-first versions) and W4226081738 (shortlist then choose). They count as 5 refused runs because the
two subfield-first versions share their first call.

### An earlier shortlist run with a different embedding model

`decisions_cache.jsonl` holds 1,795 responses, of which the current notebook uses 1,595. The other 200 are single
25-option topic questions. Matching request hashes shows they are shortlist then choose on the same 200 abstracts
with a different shortlist: the right topic was on the shortlist for 197 of 200, and the first choice matched
OpenAlex for 182 (91.0%). Their recorded cost is $0.0576. The notebook's earlier takeaways attributed a 91% run with
a 98.5% shortlist to OpenAI's paid `text-embedding-3-small`. Those embeddings are not in `embeddings_cache.npz`, so
this run cannot be replayed. The free Nemotron model replaced it, and only the Nemotron run is reported.

### Spend

$1.76 recorded in the cache over 1,795 responses: $1.70 over the 1,595 the notebook uses (4 of them refusals with no
cost) and $0.058 over the 200 earlier shortlist calls. Input tokens were billed at $0.10 per million; output tokens
were 0 in every response. Embeddings cost $0.

## 17 October 2026: notebook added to this repository

Commit 2901f83d moved the notebook and its caches from an earlier repository (lumen-copilot). The same day,
markdown-only commits added the contents and diagrams (1cf89c87), escaped dollar signs (bec1be78) and added future
work and further reading with links checked on 17 October (5630274b). No code cell or output changed and the
notebook was not re-run.

## 28 October 2026: reader text rewritten

The README and the notebook's markdown cells were rewritten to the repository's current writing rules. Code cells,
outputs and figures are unchanged and nothing was re-run. New counts in the text (readable-reply accuracy, the
confidence bands, the split of misses into shortlist and choice errors, paired comparisons and the earlier shortlist
run) were recounted from `decisions_cache.jsonl`, `embeddings_cache.npz` and the OpenAlex files by a read-only replay
of the notebook's code that made no API calls. Further reading links were re-opened on 28 October 2026.
