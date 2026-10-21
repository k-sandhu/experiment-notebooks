# Experiment notebooks

A data scientist builds intuition by running experiments. You take a new tool, or one you already use, and go deep
on it: set up conditions that show where it works and where it fails, how long it takes to build, how hard it is to
get right, what it costs, and how much accuracy a given amount of effort buys. Before you train or post-train a
model, you try several candidates on your own task and keep the one that holds up.

AI coding agents make this much cheaper. You describe an experiment, an agent builds and runs it, and you read the
results and decide what to try next. Experiments that each took days by hand can now run side by side, so you can
test more hypotheses, and test each one more carefully.

This repo collects such experiments. Each notebook asks one question and answers it with measurements, failures
included.

- Some build intuition about a new tool. OpenAI's Decisions API returns a probability for every option instead of
  writing text; seven notebooks measure how accurate it is, on which kinds of decision, at what cost and speed, and
  whether its probabilities can decide which answers to accept without review.
- Some open up something usually hidden. Notebook 07 builds a subagent harness from scratch to show the handoffs,
  messages and waits that agent frameworks keep out of sight, and what each pattern costs in time and calls.
- Some check whether general-purpose models hold up on work that matters in practice: reading regulatory filings
  and lab forms, writing safe SQL, staying inside permissions, grading other models, preparing tax workpapers.
  Planned notebooks extend this to many more kinds of decision and to general-purpose time-series forecasting
  models.

Each test is small on purpose, tens to hundreds of items with known right answers: enough to show where a method
breaks and what to test at scale, not enough to rank models in general. Test data is new, either written for the
experiment or published after the models were trained, so a model cannot score well by remembering it (notebooks
01-04 and 06 predate this rule; see [Data and licences](#data-and-licences)). Every notebook states its question
first, runs end to end and is committed with its outputs. Every model response is cached in the notebook's `data/`
folder, so you can read the results on GitHub or replay a notebook offline without an API key.

## Reading documents

A document pipeline starts with three steps: work out what arrived, cut it into pieces a search can find, and
pull out the fields that matter. A mistake at any step carries into everything after it. A misfiled permit is
never searched, a chunk that splits a section returns half an answer, and a missed checkbox on a lab form is a
test that never runs.

Five of these notebooks (01-04, 06) test OpenAI's **Decisions API** (`openai/gpt-6-luna-decisions`, served by
OpenRouter). It is not a chat model. You send it evidence (text or an image) and multiple-choice or yes/no
questions, and it returns a probability for every option instead of writing an answer. That makes it cheap and
fast for classification, and the probabilities can decide which answers to accept automatically and which to
send to a person.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 01 | [Decisions API, 500-label classification](notebooks/01-decisions-api-500-label-classification/) | Real label sets (product catalogues, ticket queues, research areas) often have hundreds of labels, but one Decisions API question accepts at most 255 options. Sorting 200 article abstracts into 508 research topics: which way of splitting the task gives the best accuracy for the cost, and are the probabilities good enough to auto-accept confident answers? | Embedding shortlist of 25 labels, then one Decisions call: 89.5% top-1, $0.29 per 1,000 documents. Auto-accepting at confidence ≥ 0.9 covers 86.5% of documents at 93.6% accuracy |
| 02 | [Decisions API chunking](notebooks/02-decisions-api-chunking/) | Retrieval-augmented generation (RAG) systems cut long documents into chunks and search the chunks to answer questions. A chunk that splits a section or joins two sections is harder to find and to quote. On six public documents, can the Decisions API's probability that "a new section starts here" place chunk boundaries better than fixed-size windows, recursive splitting, heading rules or embedding similarity? | Best at finding real section starts (average precision 0.60 vs 0.43 for a heading heuristic); 8% of its chunks mix two sections vs 46% for fixed windows. Retrieval recall@5 is the same for every chunker (0.76-0.79) |
| 03 | [Document-type classification](notebooks/03-document-type-classification/) | Document pipelines often start by working out what kind of document arrived: a permit, a settlement, an inspection form, a recall notice. Notebook 01 used clean abstracts; this uses about 300 messy public PDFs from US and UK regulators. Can the Decisions API sort them into 101 document types, and how much of each document does it need to read? | One question over all 101 types: 90.9% top-1, $0.48 per 1,000 documents. The embedding shortlist that won in 01 drops to 88% here; reading 8,000 characters instead of 2,000 adds 4 points |
| 04 | [Industry document chunking](notebooks/04-industry-document-chunking/) | Notebook 02's chunking test used six well-structured documents. Regulatory filings are harder: long permits, a 387-page utility rate case and inspection forms full of tables. On 12 such PDFs with 276 evidence quotes, does the Decisions API still place better chunk boundaries, and does that help retrieval? | Still the best boundary detector (average precision 0.35 vs 0.21 for headings); retrieval recall@5 unchanged (0.50-0.55 for all). Its boundaries split 22% of short evidence quotes vs 6-8% for other methods, so add chunk overlap |
| 06 | [Car make and model from one photo](notebooks/06-car-make-model-from-image/) | Labelling photos against a fixed list (products, parts, vehicles) is a task where a probability per label is cheaper than generated text and gives a confidence score. Can the Decisions API name a car's make and model from one photo over 109 labels, and how does it compare with frontier vision models (Claude, GPT, Muse) on accuracy, cost and speed? | Decisions API: 94.5% top-1 over 109 labels at $0.20 per 1,000 images and 0.9 s per call; GPT-6.1 and Muse Wonder 100%, Claude Opus 5.5 99.3% at 4-12 s per call |
| 08 | [Ontario lab requisition extraction](notebooks/08-lab-requisition-extraction/) | Labs receive paper test requisitions as scans, faxes and phone photos, and a missed checkbox is a test that never runs. The Ontario form has about 70 tests in a tight grid of small boxes, plus typed and handwritten patient details. On 24 synthetic forms with exact ground truth, can vision LLMs read which tests were ordered and the patient and clinician fields? | Claude Opus 5.5 read every marked test on 24 forms (F1 1.00); GPT-6.1 0.995, Muse Wonder 0.986; best open model 0.94, open models weak on phone photos and written-in tests |

## Making bounded decisions

Routing, approvals and checks need one allowed answer rather than generated prose. A high score on easy matches can hide arithmetic or sequence failures, so these experiments compare the same models across controlled difficulty, probability calibration and serving speed.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 18 | [Four decision models as tasks get harder](notebooks/18-decisions-api-comparison/) | A one-cent payment error or obsolete record can trigger the wrong action. How do OpenAI Decisions, Jev 1.14, Mercury Decide and Clef Flash compare on 768 fresh cases, and do clearer prompts or staged calculations fix ledger failures? A follow-up adds 288 ledger claims and 144 pilot plus 768 held-out join, policy and counting cases, with shortcut audits and all difficulty levels reported. | Clarified ledger prompts: 49.7–53.8%; model block sums: 51.0–56.9%; row labels plus Python: 99.7–100% (assisted). Pilot-selected replication: OpenAI 55.2%, Jev 70.1%, Mercury 72.1%; Clef 59.2% among valid replies, 44.3% including failures. Direct record equality explains the original shared 100% ceiling. Original serial medians: Jev/Clef about 0.21 s, Mercury 0.31 s |

## Forecasting observations

Demand, weather and traffic histories are easy to collect, but fitting and maintaining one forecast model per series takes work. These experiments test whether pretrained models can use recent observations directly, and whether their error ranges match what happens next.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 16 | [Zero-shot time-series forecasting](notebooks/16-time-series-zero-shot/) | A bad demand or traffic forecast can leave too little capacity. On six fresh public series and 112 rolling origins, do seven pretrained forecasting families, given 512 or 2,048 past observations without weight updates, beat five seasonal or fitted baselines? | At 512 inputs, Chronos-2: 0.860 error relative to repeating the seasonal cycle (14.0% less); best baseline AutoETS: 0.961. Nominal 80% interval coverage averaged 67.4%; six selected series |

## Letting models act

Once a model can run a query or edit a file, a wrong answer becomes a wrong action. These notebooks test the
layers between what a model writes and what it changes: whether it respects written permissions (05, 09), what
should enforce them when it does not (10), how agents hand work to each other (07), whether one model can grade
another (11), and whether review loops make a model more reliable at regulated work (12).

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 05 | [Text-to-SQL safety](notebooks/05-text-to-sql-safety/) | A text-to-SQL assistant turns an analyst's plain-English question into SQL that runs on a live database, so one bad query can change data or leak personal details. Given a written read-only policy, how often do 8 open-weight models write a query that breaks it on 29 policy-breaking requests, compared with Claude, GPT and Muse, and do they still answer 23 legitimate questions? | Claude, GPT, Muse Wonder and 6 of 8 open models: 0 violations on 29 policy-breaking requests. Mistral Small 4: 7 (one an `UPDATE` hidden in a "refused" reply); Gemma 4 31B: 3 |
| 07 | [Subagent handoff harness](notebooks/07-subagent-handoff-harness/) | Agent frameworks hide how a main agent hands work to subagents, receives their messages and decides when to wait for them. This builds that harness in plain Python one pattern at a time (synchronous handoff, async spawn, messages both ways, a subagent asking a question, racing, nesting) and runs each pattern with real Claude agents on the same trip-planning task. What does each pattern cost and gain in time and LLM calls? | All 7 levels correct. Async spawn: 57 s vs 82 s single agent; sync handoff slower (120 s). A late reply to a finished subagent is silently lost |
| 09 | [Proposed unsafe agent actions](notebooks/09-agent-action-safety/) | An assistant with a terminal can delete files, read secrets or push code, and its written permissions are often the only guard. On 12 forbidden requests, each paired with a similar permitted one, how often do two open-weight models (DeepSeek, Gemma) and two closed ones (Claude, GPT) propose an action outside their permissions, how many permitted requests do they complete, and does a checklist in the prompt help? Proposed commands are judged as text by other models and never run. | On 96 forbidden requests the judges flagged one reply, and that flag is disputed. The clearest problem was on a permitted request: a search that follows a symlink out of the project. GPT-6.1 completed 12/12 permitted requests, Gemma 4 31B 5/12; the checklist did not reduce flags |
| 10 | [Code execution guardrails](notebooks/10-code-execution-guardrails/) | When a model proposes a forbidden action, the code that decides whether to run it is the last guard, and a string check on the path is easy to get past. On 22 requests with known right answers (8 permitted, 14 forbidden), what do five enforcement designs let through, and how much legitimate work does each block? | A path-prefix check let through 5/14 forbidden actions. Typed operations on resolved paths let through 0/14 and kept all 8 permitted ones. Read-only also allowed 0/14 but blocked 4/8 permitted actions |
| 11 | [LLM judges across four tasks](notebooks/11-llm-judges/) | Many evaluations, including notebook 09, use one model to grade another, and judges can favour the first or the longer answer. On 12 pairs where one answer is objectively right (arithmetic, extraction, grounded summaries, policy decisions), do Claude and GPT judges pick it, with and without an evidence rubric, and with the order swapped? | Both judges were right in 96/96 ratings and never changed their pick when the order was swapped. The pairs were too easy to tell the judges apart: a perfect score on 12 pairs still allows a true accuracy as low as 76% |
| 12 | [Tax workpaper harnesses](notebooks/12-tax-research-harnesses/) | An S-Corporation tax workpaper is mechanical but unforgiving: one misclassified ledger line flows into every shareholder's numbers, and some cases need an accountant's judgment. On 12 fictional 2025 US S-Corps, do detailed instructions, a self-review pass, feedback from a custom validator or the smolagents agent framework give more fully correct workpapers than one direct call, at the same model and call budget? | No. Qwen3.8 Flash's direct call got 12/12, and review steps only matched or lowered that (generic self-review with detailed instructions: 9/12). Gemma 4 31B got 0/12 in every setup. All 24 Qwen framework runs failed because the provider rejects the framework's default tool setting |

## Recognising model outputs

If a model is sold under the wrong name, a plausible answer gives no proof of its source. These experiments
ask whether patterns in generated text can identify an endpoint, and whether that evidence survives a change
of topic, formatting or wording.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 13 | [Attributing older model outputs](notebooks/13-older-model-attribution/) | Checking a claimed text source can expose a substituted model, but topic or formatting can give the answer away. On 100 fresh texts from four older endpoints in two families, can five newer models name the source on ten held-out prompts (40 texts), compared with trained character and embedding classifiers? | GPT-6.1 / few-shot: 27/40 (67.5%); character classifier 16/40 (40.0%, 12 training texts), embedding baseline 14/40 (35.0%); chance 25%. The identical-order GPT zero-shot repeat changes 13/40 guesses. Shared calls connect all ten prompts; no population confidence interval or general ranking. Serving-provider confounds remain |

## Predicting from tables

When only a few labeled rows exist, an analyst still needs to predict the next category or number. A pretrained
tabular model can use those examples as context without updating its weights. The useful comparison is with
ordinary fitted models on the same rows, including inputs outside the examples' range. Balanced accuracy gives
each class equal weight; numeric mean absolute error (MAE) is the average size of a prediction error.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 14 | [Zero-shot prediction from small tables](notebooks/14-tabular-zero-shot/) | A new process may have only a few labeled outcomes, so a prediction must work before there is much data to tune it. On 24 fresh synthetic numeric tables (four mechanisms, classification and regression, three seeds), how does pretrained TabPFN compare with four fitted baselines using 32 or 128 labeled examples and 128 held-out rows? | At 128 labeled rows, TabPFN balanced accuracy 82.9% vs 71.7% for Random forest; numeric MAE 0.198 times a constant predictor vs 0.479 for Gradient boosting. Four synthetic mechanisms do not establish a real-data ranking |

## Writing analyses

An analysis must help its reader make a decision. These experiments separate the content of a model's draft from the preferences of the models asked to grade it, including whether naming the author or asking for a prose audit changes the score.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 15 | [Analytical writing and judge framing](notebooks/15-analytical-writing-style/) | A draft can contain the right numbers yet bury its decision in vague or repeated prose. On two fresh numerical cases in four genres (216 requested drafts), how do 27 writers fare under 30 model judges, and do author disclosure and an explicit prose audit change ratings of the same text? | Anonymous external clarity 88.9/100; audit 0.76 quoted issues per 100 words. Audit clarity change -1.66 points; neutral author-disclosure change -0.06. Model ratings on two cases, no human comprehension claim |
| 17 | [Writing validation on longer documents](notebooks/17-writing-validation-extension/) | A prose flag can reflect reading difficulty, a factual error or taste. Reassess 108 cached drafts from 27 writers, then compare six writers on 24 fresh cases in four genres with realistic lengths (288 requested drafts), using only Codex and Claude judges. | 288/288 usable drafts; model reviewers upheld 1.6% of sampled old flags as prose concerns on average. Warning effect -0.31/100; human validation materials ready, human results pending |

## Creating presentations

A generated deck must keep its facts correct while making a decision easy to see. These experiments test the authoring tools and review steps between a model's response and the slides an audience reads.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 19 | [PowerPoint harnesses and screenshot judges](notebooks/19-powerpoint-harness/) | A presentation edit can leave stale values or unreadable charts. On two fresh briefs and 24 four-slide decks from three models, do layout helpers and screenshot feedback improve native editable PowerPoints under the same two-call workflow? Three frontier judges see only images. | 24/24 rendered; GPT-6.1 Sol had the highest model average, 94.5/100. Helpers -2.9 points; screenshots +0.2. Two related briefs, no general ranking |

## Planned experiments

Experiments that are written up but not built yet are open issues with the
[`notebook-proposal`](https://github.com/k-sandhu/experiment-notebooks/issues?q=is%3Aissue+is%3Aopen+label%3Anotebook-proposal)
label. Each one gives the question, the fresh data to use, the models, the measures and a cost estimate.

| Issue | Question |
|---|---|
| [#12](https://github.com/k-sandhu/experiment-notebooks/issues/12) | People have used the Decisions API since its October beta to route complaints, grade agent transcripts, pick an agent's next action from a screenshot and choose which LLM should answer a prompt, and their reports disagree on whether its probabilities can be trusted. On 14 tasks with fresh data, including those uses plus bird recordings, wildlife photos and restaurant inspection reports, which uses hold up, are its probabilities calibrated and stable when options are reordered or reworded, how does it compare with other decision models such as Jev where a task calls for it, and what does each cost? |

Notebooks 01-04 were first run inside another project and moved here with their data and caches.

## How models are called

| Provider | Models used | How |
|---|---|---|
| Anthropic | Claude Opus 5.5, Sonnet 5.5, Haiku 5.5 and older versions in 15 | `claude -p` (Claude Code CLI), headless, no tools |
| OpenAI | GPT-6.1, GPT-6 Astra/Sol/Luna and GPT-5.6 Sol/Terra/Luna | `codex exec` (Codex CLI), read-only sandbox |
| Meta | Muse Spark 1.2/1.3 and Muse Wonder/Wonder Full | `muse exec` (Muse CLI), empty preset |
| Decision models | OpenAI Decisions, Jev 1.14, Mercury Decide, Clef Flash | OpenRouter Decisions HTTP API; dated IDs and provider pins in 18 |
| Prior Labs | TabPFN-3.5, numeric tabular classification and regression | Prior Labs REST API, labeled context and unlabeled test features |
| Open-weight models | Llama 3.1, DeepSeek, Qwen, GLM, Kimi, Gemma, Mistral, gpt-oss, Muse Spark Open, Nemotron | OpenRouter HTTP API |
| Time-series foundation models | Chronos-2, TimesFM 2.5, Moirai 2, TiRex-2, Toto 2, TTM R3, Lag-Llama | TSFM.ai HTTP API; notebook 16 defaults to frozen caches |

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
* New collection in 09, 11, 12 and 13: set `NB_LIVE=1` explicitly. These notebooks stop on an offline cache miss. Notebook 10 replays saved container evidence; its fixed Docker probes require a separate opt-in.
* Notebook 13 verifies cached evidence before replay. For a new collection, use a separate copy and follow its README; keep the committed cache intact.
* Notebook 19 replays the complete PowerPoint study offline. New collection uses explicit --live commands and requires Windows, PowerPoint and authenticated model CLIs.
* Notebook 14 uses `PRIORLABS_API_KEY` and `NB_LIVE=1` for new collection, with a checked computation-token cap. Its default replay reads 48 saved responses without network access.
* **Smoke test**: `NB_SMOKE=1` makes notebooks 05, 06 and 08 run on a handful of items.
* Notebooks 02-04 download public PDFs on first run into `data/docs/` (git-ignored, sha256-checked where pinned).
* Notebook 16 forecasts six public series through TSFM.ai. Its own `requirements.txt` pins the fitted-baseline libraries; replay needs no key. New collection requires `TS16_LIVE=1` and `TSFMAI_API_KEY`.

Notebook 15 uses strict offline replay with an evidence manifest and a $10 OpenRouter guard. Its README gives model coverage and limits.

Notebook 18 uses 768 fresh synthetic cases, all four decision models and strict offline replay. Its README records provider pins, scoring audits, diagnostics and reported spend.

## Data and licences

Only public or synthetic data. OpenAlex metadata (CC0); public PDFs from US and UK agencies and other publishers,
referenced by URL and downloaded on demand; the Chinook sample database (MIT); Wikimedia Commons photos (licence
and author per image in `notebooks/06-car-make-model-from-image/data/images.csv`); synthetic lab requisitions generated for notebook 08,
stamped SYNTHETIC with invalid identifiers. Notebook 16 uses IESO demand, Open-Meteo weather analysis, Wikimedia CC0 page views and Bank of Canada exchange rates; its [source notices and redistribution terms](notebooks/16-time-series-zero-shot/data/ATTRIBUTION.md) are recorded separately. Code and text in this repo are MIT licensed (see `LICENSE`).

New notebooks use data the models cannot have seen: synthetic data written for the experiment, or public data
created after every tested model's training cutoff (for time series, the last one to two months), with creation
dates recorded. Notebooks 01-04 and 06 predate this rule. Their abstracts, PDFs and Wikipedia photos are older than
the models, which may have seen them, so treat those accuracy figures as upper bounds.

Notebook 14 uses 24 newly generated numeric tables with exact generation rules, seeds and input hashes.

Notebooks 09-12 use authored synthetic cases and objective fixtures. Notebook 12 records original IRS source URLs and section names alongside authored summaries for its restricted 2025 US federal S-Corporation workpaper; original US government material has separate source provenance.

Notebook 13 uses 100 fresh synthetic model outputs collected on 2026-10-19, with per-item timestamps and sourced model cutoff or release dates in its data folder. Its gold labels are the recorded generation endpoints.

Notebook 15 uses two fresh numerical packets and model drafts collected on 2026-10-19, with exact answers generated in code and model date sources in its data folder.

Notebook 17 extends the writing pilot with 24 fresh programmatic cases and copied legacy evidence. Human reader and editor results are pending; their participant materials and import workflow are included.

## For AI agents

See [AGENTS.md](AGENTS.md): layout, the pull-request workflow, claiming a notebook number with an issue,
proposing an experiment as an issue, self-containment, fresh data with no training-set leakage, workflow
diagrams and explainers, the closing future-work and further-reading section, how to call models, and the writing
style (including LLM prose habits to avoid).
