# Experiment notebooks

Small, self-contained experiments with language models on document work and agent systems. Each notebook
states its question first, runs end to end, and is committed with its outputs. Every model response is cached
in the notebook's `data/` folder, so you can read the results on GitHub or re-run a notebook offline without any
API key.

## Notebooks

| # | Notebook | Question | Headline result |
|---|---|---|---|
| 01 | [Decisions API, 500-label classification](notebooks/01-decisions-api-500-label-classification/) | How do you classify into ~500 labels with an API that takes at most 255 options per question? | Embedding shortlist + one Decisions call: 89.5% top-1 over 508 labels, $0.29 per 1,000 documents |
| 02 | [Decisions API chunking](notebooks/02-decisions-api-chunking/) | Can calibrated "a new section starts here" probabilities make better chunks than classic splitters? | Best boundary detector (AP 0.60 vs 0.43 headings); 8% of chunks mix sections vs 46% for fixed windows; retrieval recall unchanged |
| 03 | [Document-type classification](notebooks/03-document-type-classification/) | Does it hold on messy regulatory and industry PDFs with 101 document types? | One flat question: 90.9% top-1, $0.48 per 1,000 documents; shortlists hurt here |
| 04 | [Industry document chunking](notebooks/04-industry-document-chunking/) | The chunking test again, on long table-heavy permits and filings | Still the best boundary detector; 22% of short evidence quotes get split, so add overlap |
| 05 | [Text-to-SQL safety](notebooks/05-text-to-sql-safety/) | Do open-weight models write SQL that breaks a read-only policy, compared with Claude, GPT and Muse? | Claude, GPT, Muse Wonder and 6 of 8 open models: 0 violations on 29 policy-breaking requests. Mistral Small 4: 7 (one an `UPDATE` hidden in a "refused" reply); Gemma 4 31B: 3 |
| 06 | [Car make and model from one photo](notebooks/06-car-make-model-from-image/) | Can the OpenAI Decisions API identify a car from an image, against frontier vision models? | Decisions API: 94.5% top-1 over 109 labels at $0.20 per 1,000 images and 0.9 s per call; GPT-6.1 and Muse Wonder 100%, Claude Opus 5.5 99.3% at 4-12 s per call |
| 07 | [Subagent handoff harness](notebooks/07-subagent-handoff-harness/) | How do handoffs, messages and blocking work in a multi-agent harness, built from scratch? | All 7 levels correct. Async spawn: 57 s vs 82 s single agent; sync handoff slower (120 s). A late reply to a finished subagent is silently lost |
| 08 | [Ontario lab requisition extraction](notebooks/08-lab-requisition-extraction/) | Can vision LLMs read marked tests and handwriting on a dense government form? | Claude Opus 5.5 read every marked test on 24 forms (F1 1.00); GPT-6.1 0.995, Muse Wonder 0.986; best open model 0.94, open models weak on phone photos and written-in tests |

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

See [AGENTS.md](AGENTS.md): layout, self-containment, how to call models, and the writing style.
