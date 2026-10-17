# Experiment notebooks

Small, self-contained experiments with language models on document work and agent systems. Each notebook
states its question first, runs end to end, and is committed with its outputs. Every model response is cached
in the notebook's `data/` folder, so you can read the results on GitHub or re-run a notebook offline without any
API key.

## Notebooks

Five notebooks (01-04, 06) test OpenAI's **Decisions API** (`openai/gpt-6-luna-decisions`, served by OpenRouter).
It is not a chat model. You send it evidence (text or an image) and multiple-choice or yes/no questions, and it
returns a probability for every option instead of writing an answer. That makes it cheap and fast for
classification, and the probabilities can decide which answers to accept automatically and which to send to a
person.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 01 | [Decisions API, 500-label classification](notebooks/01-decisions-api-500-label-classification/) | Real label sets (product catalogues, ticket queues, research areas) often have hundreds of labels, but one Decisions API question accepts at most 255 options. Sorting 200 article abstracts into 508 research topics: which way of splitting the task gives the best accuracy for the cost, and are the probabilities good enough to auto-accept confident answers? | Embedding shortlist of 25 labels, then one Decisions call: 89.5% top-1, $0.29 per 1,000 documents. Auto-accepting at confidence ≥ 0.9 covers 86.5% of documents at 93.6% accuracy |
| 02 | [Decisions API chunking](notebooks/02-decisions-api-chunking/) | Retrieval-augmented generation (RAG) systems cut long documents into chunks and search the chunks to answer questions. A chunk that splits a section or joins two sections is harder to find and to quote. On six public documents, can the Decisions API's probability that "a new section starts here" place chunk boundaries better than fixed-size windows, recursive splitting, heading rules or embedding similarity? | Best at finding real section starts (average precision 0.60 vs 0.43 for a heading heuristic); 8% of its chunks mix two sections vs 46% for fixed windows. Retrieval recall@5 is the same for every chunker (0.76-0.79) |
| 03 | [Document-type classification](notebooks/03-document-type-classification/) | Document pipelines often start by working out what kind of document arrived: a permit, a settlement, an inspection form, a recall notice. Notebook 01 used clean abstracts; this uses about 300 messy public PDFs from US and UK regulators. Can the Decisions API sort them into 101 document types, and how much of each document does it need to read? | One question over all 101 types: 90.9% top-1, $0.48 per 1,000 documents. The embedding shortlist that won in 01 drops to 88% here; reading 8,000 characters instead of 2,000 adds 4 points |
| 04 | [Industry document chunking](notebooks/04-industry-document-chunking/) | Notebook 02's chunking test used six well-structured documents. Regulatory filings are harder: long permits, a 387-page utility rate case and inspection forms full of tables. On 12 such PDFs with 276 evidence quotes, does the Decisions API still place better chunk boundaries, and does that help retrieval? | Still the best boundary detector (average precision 0.35 vs 0.21 for headings); retrieval recall@5 unchanged (0.50-0.55 for all). Its boundaries split 22% of short evidence quotes vs 6-8% for other methods, so add chunk overlap |
| 05 | [Text-to-SQL safety](notebooks/05-text-to-sql-safety/) | A text-to-SQL assistant turns an analyst's plain-English question into SQL that runs on a live database, so one bad query can change data or leak personal details. Given a written read-only policy, how often do 8 open-weight models write a query that breaks it on 29 policy-breaking requests, compared with Claude, GPT and Muse, and do they still answer 23 legitimate questions? | Claude, GPT, Muse Wonder and 6 of 8 open models: 0 violations on 29 policy-breaking requests. Mistral Small 4: 7 (one an `UPDATE` hidden in a "refused" reply); Gemma 4 31B: 3 |
| 06 | [Car make and model from one photo](notebooks/06-car-make-model-from-image/) | Labelling photos against a fixed list (products, parts, vehicles) is a task where a probability per label is cheaper than generated text and gives a confidence score. Can the Decisions API name a car's make and model from one photo over 109 labels, and how does it compare with frontier vision models (Claude, GPT, Muse) on accuracy, cost and speed? | Decisions API: 94.5% top-1 over 109 labels at $0.20 per 1,000 images and 0.9 s per call; GPT-6.1 and Muse Wonder 100%, Claude Opus 5.5 99.3% at 4-12 s per call |
| 07 | [Subagent handoff harness](notebooks/07-subagent-handoff-harness/) | Agent frameworks hide how a main agent hands work to subagents, receives their messages and decides when to wait for them. This builds that harness in plain Python one pattern at a time (synchronous handoff, async spawn, messages both ways, a subagent asking a question, racing, nesting) and runs each pattern with real Claude agents on the same trip-planning task. What does each pattern cost and gain in time and LLM calls? | All 7 levels correct. Async spawn: 57 s vs 82 s single agent; sync handoff slower (120 s). A late reply to a finished subagent is silently lost |
| 08 | [Ontario lab requisition extraction](notebooks/08-lab-requisition-extraction/) | Labs receive paper test requisitions as scans, faxes and phone photos, and a missed checkbox is a test that never runs. The Ontario form has about 70 tests in a tight grid of small boxes, plus typed and handwritten patient details. On 24 synthetic forms with exact ground truth, can vision LLMs read which tests were ordered and the patient and clinician fields? | Claude Opus 5.5 read every marked test on 24 forms (F1 1.00); GPT-6.1 0.995, Muse Wonder 0.986; best open model 0.94, open models weak on phone photos and written-in tests |

Notebooks 01-04 were first run inside another project and moved here with their data and caches.

## How models are called

| Provider | Models used | How |
|---|---|---|
| Anthropic | Claude Opus 5.5, Sonnet 5.5, Haiku 5.5 | `claude -p` (Claude Code CLI), headless, no tools |
| OpenAI | GPT-6.1 | `codex exec` (Codex CLI), read-only sandbox |
| Meta | Muse Wonder | `muse exec` (Muse CLI), empty preset |
| OpenAI Decisions API | `openai/gpt-6-luna-decisions` | OpenRouter HTTP API (there is no CLI for it) |
| Open-weight models | DeepSeek, Qwen, GLM, Kimi, Gemma, Mistral, gpt-oss, Muse Spark Open, Nemotron | OpenRouter HTTP API |

Paid OpenRouter calls are small by default and every notebook has a size knob at the top (`N_DOCS`,
`OPEN_MODELS`, `IMAGES_PER_MODEL`, ...). Each notebook prints what it spent.

## Running

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # or .venv/bin/pip on macOS/Linux
.venv/Scripts/jupyter lab
```

* **Replay** (default): open a notebook and run all cells. Cached responses are used; no keys are needed.
* **Re-query the models**: delete the notebook's `data/cache_*.jsonl` (or `data/runs/` in 07). This needs
  `OPENROUTER_API_KEY` and logged-in `claude`, `codex` and `muse` CLIs.
* **Smoke test**: `NB_SMOKE=1` makes notebooks 05, 06 and 08 run on a handful of items.
* Notebooks 02-04 download public PDFs on first run into `data/docs/` (git-ignored, sha256-checked where pinned).

## Data and licences

Only public or synthetic data. OpenAlex metadata (CC0); public PDFs from US and UK agencies and other publishers,
referenced by URL and downloaded on demand; the Chinook sample database (MIT); Wikimedia Commons photos (licence
and author per image in `notebooks/06-car-make-model-from-image/data/images.csv`); synthetic lab requisitions generated for notebook 08,
stamped SYNTHETIC with invalid identifiers. Code and text in this repo are MIT licensed (see `LICENSE`).

## For AI agents

See [AGENTS.md](AGENTS.md): layout, the pull-request workflow, self-containment, workflow diagrams and
explainers, how to call models, and the writing style.
