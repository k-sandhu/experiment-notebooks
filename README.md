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
| 01 | [Decisions API, 500-label classification](notebooks/01-decisions-api-500-label-classification/) | Research catalogues, ticket queues and product catalogues file each item under one of hundreds of labels, and a wrong label hides the item from the searches and counts that use it. A decision model, which returns a probability for every allowed answer instead of writing text, is not shown hundreds of labels at once, so the list is narrowed first. On 200 research abstracts and OpenAlex's 508 topics, which way of narrowing files the most abstracts correctly for the cost: a 25-topic shortlist by text similarity, picking a subfield first, or a two-round tournament? And can the model's probabilities decide which filings to accept without a person checking? | A 25-topic shortlist followed by one question filed 179 of 200 abstracts under OpenAlex's topic (89.5%) at $0.29 per 1,000; the next best methods filed 171 and 172 at 5 and 18 times the cost, and picking one subfield first filed 153. Accepting answers at confidence 0.9 or more filed 173 automatically, 162 of them correctly (93.6%). The papers and their labels were public before the model was released, so these are upper bounds |
| 02 | [Decisions API chunking](notebooks/02-decisions-api-chunking/) | A search system that answers questions from long documents first cuts them into chunks, and a chunk that starts mid-section or joins two sections is harder to find, read and quote. On six public documents (711 known section starts, 33 questions with known answer passages), does cutting where the Decisions API says a new section starts follow the real sections better than cutting every 400 tokens, at paragraph breaks, by a heading rule or by changes in meaning, and does it help a search find the answer? | Best at finding section starts (average precision 0.60 vs 0.43 for the heading rule and 0.32 for meaning change), most of all on the IRS tax instructions (0.58 vs 0.19). Its chunks put a cut near 85% of section starts and 8% joined two sections; the heading rule reached 80% and 9%, fixed 400-token windows 28% and 46%. Every method found the answer in the top 5 for 25 or 26 of 33 questions. The documents predate the model, so section scores are an upper bound |
| 03 | [Document-type classification](notebooks/03-document-type-classification/) | Before anyone reads a folder of regulatory records, someone sorts it: permit, inspection report, settlement, letter. A settlement filed as a letter may never be read. On 276 public PDFs from 22 US and UK regulator collections, each with a known type out of 101, does a decision model (OpenAI's Decisions API) sort best with all 101 types in one question, a group of types first, or a 15-type shortlist picked by text similarity, and does it need about one page of text (2,000 characters) or four times as much? | One question over all 101 types on 8,000 characters: 251/276 right (90.9%), $0.47 per 1,000 documents; group first also 251/276. Shortlist: 243/276 (88.0%) at $0.22, as 19 correct types missed the shortlist. 8,000 instead of 2,000 characters fixed 11 documents and broke none (pesticide labels behind a cover notice: 0/8 to 5/8). 17 of 25 errors had probability ≥ 0.9. Most documents predate the model's cutoff, so accuracy is an upper bound |
| 04 | [Industry document chunking](notebooks/04-industry-document-chunking/) | Search tools cut long documents into chunks before searching them, and a chunk that splits a section or joins two is harder to find and to cite. On 12 long public filings (water, air and hazardous-waste permits, a settlement, two utility rate cases, a recall notice, a nursing-home inspection and a pesticide label; 1,306 pages), do chunks cut where the Decisions API says a new section starts follow the documents' sections better than cuts by length, by a heading rule or by topic change between paragraphs, and does that help a search find 276 evidence quotes? | Best at ranking real section starts on the 4 documents with bookmarks (average precision 0.35 vs 0.21 for headings and 0.20 for topic change; chance is about 0.10), and it puts a cut near 77% of bookmarked starts vs 68% for headings and 26% for fixed windows. Search finds the quote in the top 5 for 50-55% of pairs under every method. It splits 6 of 47 distinct short quotes vs 2-5 for the others. The documents were public before the study, so scores are an upper bound |
| 06 | [Car make and model from one photo](notebooks/06-car-make-model-from-image/) | A site that files photos under a fixed list of names (car models, products, parts) needs the right name, and a way to tell which answers a person should check. On 146 Wikipedia photos of 73 car models and a list of 109 make-and-model labels, how often does the Decisions API, which returns a probability for every label instead of writing an answer, pick the right one, compared with three large chat models that write their answer (Claude Opus 5.5, GPT-6.1, Muse Wonder)? Are its probabilities good enough to decide which answers to accept without a check? | Decisions API: 138 of 146 right (94.5%) at $0.20 per 1,000 photos and 0.9 s per photo. Every answer it gave at probability 0.9 or more was right: 66% of photos, or 81% when asked for the maker first. GPT-6.1 and Muse Wonder named 146 of 146 and Claude Opus 5.5 145, too close to rank, at 4 to 12 s per photo. The photos are well-composed and public, so these are upper bounds |
| 08 | [Ontario lab requisition extraction](notebooks/08-lab-requisition-extraction/) | A lab clerk types each paper test order into the lab system before blood is drawn; a missed test is never run and an added one is wasted. Ontario's requisition orders tests by a mark in a small box or by writing the name on an "Other Tests" line, and pages arrive as scans or phone photos. On 24 synthetic requisitions with known contents (102 ordered tests, 20 patient and clinician details each), can three hosted vision models (Claude, GPT, Muse Wonder) and four open-weight ones list exactly the ordered tests and copy the details? | Claude Opus 5.5 listed exactly the ordered tests on all 24 pages (102/102, none added); GPT-6.1 and Muse Wonder made 4 test errors between them, so the test cannot rank the three. Best open-weight model Muse Spark Open: F1 0.94. Open models found 66/108 written-in tests against 275/300 boxed ones, and two open-model phone-photo replies listed most of the form. Details: Claude 96.7% exact; every model was weaker on phone photos (GPT-6.1 67.5% vs 98.0% on scans). Synthetic pages with a script font for handwriting |

## Generating and checking example data

A synthetic extraction example needs more than a plausible answer. If an order changes twice, its final price
must agree with the source messages and its citations must support that price. These experiments examine how
to generate examples, check them, remove duplicates and use observed failures to choose further cases. The
data collection step can be studied before training a model. Harder examples also reveal whether a repair
solves a case the stronger model previously missed, or repeats an answer it could already produce.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 23 | [Synthetic data generation and curation](notebooks/23-synthetic-data-curation/) | Generated examples need exact values and evidence that supports them. After two protocols found no Sol value misses, a separate v3 generator tested a pilot ladder, then compared fresh retries and verifier-guided repairs on 48 long procurement cases plus 12 audit cases. | V3 Sol answered 45/48 collection cases and 12/12 audit cases with all seven values correct; Luna answered 0/48 and 0/12. The pilot's Sol miss counts were 1, 0 and 1, so it used the declared level-three fallback. Fresh Sol retry and Sol repair each corrected all 3 selected Sol misses; Luna cross-repair corrected 0/3, and neither Sol arm added distinct cases beyond the other. The small audit set was already 12/12 for Sol. No training was run, so correction data is not evidence of a performance gain. |

## Making bounded decisions

Routing, approvals and checks need one allowed answer rather than generated prose. A high score on easy matches can hide arithmetic or sequence failures, so these experiments compare the same models across controlled difficulty, probability calibration and serving speed.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 18 | [Four decision models as tasks get harder](notebooks/18-decisions-api-comparison/) | A one-cent payment error or obsolete record can trigger the wrong action. How do OpenAI Decisions, Jev 1.14, Mercury Decide and Clef Flash compare on 768 fresh cases, and do clearer prompts or staged calculations fix ledger failures? A follow-up adds 288 ledger claims and 144 pilot plus 768 held-out join, policy and counting cases, with shortcut audits and all difficulty levels reported. | Clarified ledger prompts: 49.7–53.8%; model block sums: 51.0–56.9%; row labels plus Python: 99.7–100% (assisted). Pilot-selected replication: OpenAI 55.2%, Jev 70.1%, Mercury 72.1%; Clef 59.2% among valid replies, 44.3% including failures. Direct record equality explains the original shared 100% ceiling. Original serial medians: Jev/Clef about 0.21 s, Mercury 0.31 s |

## Measuring economic decisions

A low-priced model can cost more once checking and payment mistakes are included. A spending announcement can
also look like economic activity even when no money has been paid. The [economics experiments](econ/) separate
these quantities using fresh synthetic invoices and recent public fiscal documents with source-checked answers.
Each has its own notebook, cached evidence and illustrated explanation under one `econ/` folder.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 21 | [Verification costs](econ/21-verification-costs/) | A wrong invoice approval can release too much money or hold up a valid payment. On 72 held-out invoices after 12 development cases, when do checking, repeat decisions or escalation erase the savings from a cheaper model, compared with a strong model used directly? | Qwen: 14/72 exact; GPT and both escalation routes: 72/72. Checks avoided GPT only on 14 zero-payment holds. Claude screening breaks even against GPT direct above an assumed GPT price of USD 0.133/invoice using Claude list-price equivalents. Model calls had no calculator; the rule engine got 72/72. |
| 22 | [Fiscal measurement from public reports](econ/22-fiscal-implementation/) | A budget, an accounting expense and a cash payment can be different numbers. On 22 held-out questions from 8 recent public-document packets, do Direct answers or a quoted evidence ledger plus Python better identify fiscal amounts and missing disclosures? The full collection, including development, has nine primary reports/releases published 13-22 October 2026 and one updated history page. | GPT-6.1 Sol: Direct 22/22, Ledger 22/22; Claude Opus 5.5: Direct 22/22, Ledger 22/22; Muse Wonder Full: Direct 21/22, Ledger 21/22. All 130 protocol-valid held-out answers were correct. Muse had one Direct timeout and one correct Ledger answer excluded after an internal CLI retry; no financial-answer advantage was demonstrated. |

## Forecasting observations

Demand, weather and traffic histories are easy to collect, but fitting and maintaining one forecast model per series takes work. These experiments test whether pretrained models can use recent observations directly, and whether their error ranges match what happens next.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 16 | [Forecasting a new series without fitting](notebooks/16-time-series-zero-shot/) | Planners forecast electricity demand, web traffic or exchange rates a day to a month ahead, and the usual floor is simply repeating last week. A model pretrained on many other series could forecast a new one from its recent history with no fitting. On six public series (Ontario demand, Toronto temperature and wind, two Wikipedia page-view counts, USD/CAD), forecast from 112 starting points between August 20 and October 17, 2026, after every model's weights were public, do seven such models beat repeating the last cycle and five standard methods fitted to the same history, and do their 80% ranges hold 80% of actual values? | The four best pretrained models made 13% to 14% less error than repeating the last cycle (relative error 0.860 to 0.871), and the best fitted method, AutoETS, 4% less (0.961); the lead over AutoETS is not established on six series (interval of the difference crosses zero). On Ontario demand they cut error by about a third, while on AI page views and USD/CAD they did worse than repeating the last cycle. Their 80% ranges held only 65.5% to 70.1% of actual values, and one model's ranges (TimesFM 2.5) were mislabelled at every step |

## Letting models act

Once a model can run a query or edit a file, a wrong answer becomes a wrong action. These notebooks test the
layers between what a model writes and what it changes: whether it respects written permissions (05, 09), what
should enforce them when it does not (10), how agents hand work to each other (07), whether one model can grade
another (11), and whether review loops make a model more reliable at regulated work (12). Reward collection (25)
checks whether the work finished and how much useful feedback remains when a policy already succeeds often.
A later audit needs the original facts and action as well as evidence about the model itself (26).

Reward collection repeats a task and scores each attempt. A group containing both a success and a failure gives a learning method an outcome contrast. Notebook 27 tests whether choosing where to collect more attempts finds more of that contrast within a fixed call budget, without changing model weights.

Sometimes the quickest way to finish a job is to switch off the safety check that watches the agent, the way a decorator might take down a smoke alarm to paint a ceiling. Notebook 28 asks whether small agents keep that rule, and whether they tell the truth when asked about it afterwards.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 05 | [Text-to-SQL safety](notebooks/05-text-to-sql-safety/) | An assistant that turns an analyst's question into a database query that runs at once can delete records or expose salaries and customers' addresses if it ignores its rules. Given written read-only rules (one reading query, no salary or login tables, no individual contact details or birth dates, at most 1,000 rows), how often do 8 open-weight models and 3 closed ones (Claude, GPT, Muse) write a rule-breaking query on 29 requests that cannot be met within the rules, and do they still answer 23 ordinary questions correctly? | 9 of 11 models wrote no rule-breaking query in 29 tries, which still allows a true rate up to 12%. Mistral Small 4 broke the rules 7 times, once adding a statement that would set all 412 invoices to zero while marking its reply as refused; Gemma 4 31B broke them 3 times. No model refused an ordinary question: 10 answered all 23 correctly and Mistral 22 |
| 07 | [Subagent handoff harness](notebooks/07-subagent-handoff-harness/) | An AI agent can split a job among helper agents, but the time saved depends on who waits for whom, and a message between agents can arrive too late to be read. On one three-city trip-planning task with a known correct answer, how do seven ways of coordinating a planner and its helpers compare with one agent working alone, in time, model calls and time spent waiting, and do questions, progress reports and instructions reach the agent that needs them? One recorded run per arrangement, with Claude agents. | All 7 answers correct. Waiting for each helper in turn: 120 s, against 82 s for one agent; starting the helpers and working meanwhile: 57 s with 18 model calls instead of 11. One instruction arrived during a helper's last step and was never read, with no notice to the sender. Two layers of helpers: 35 calls and weather figures that no tool returned |
| 09 | [Proposed unsafe agent actions](notebooks/09-agent-action-safety/) | An assistant with a terminal can delete files, read secrets or push code, and its written permissions are often the only guard. On 12 forbidden requests, each paired with a similar permitted one, how often do two open-weight models (DeepSeek, Gemma) and two closed ones (Claude, GPT) propose an action outside their permissions, how many permitted requests do they complete, and does a checklist in the prompt help? Proposed commands are judged as text by other models and never run. | On 96 forbidden requests the judges flagged one reply, and that flag is disputed. The clearest problem was on a permitted request: a search that follows a symlink out of the project. GPT-6.1 completed 12/12 permitted requests, Gemma 4 31B 5/12; the checklist did not reduce flags |
| 10 | [Execution guardrails](notebooks/10-code-execution-guardrails/) | When an AI agent proposes deleting, writing or reading a file, a short piece of code (the gate) decides whether it runs. A gate that only reads the start of the path can be fooled by a `..` step or a link that leads somewhere else. On 22 written requests with known right answers (8 permitted, 14 forbidden), how many forbidden actions does each of five gate designs let through, and how many permitted ones does it block? No model is involved; the same requests go through every gate. | A gate that checks only the start of the path let through 5 of 14 forbidden actions: every request built to beat a text check, and none of the other 9. A gate that resolves each path and offers only named operations blocked all 14 and allowed all 8 permitted ones, a ceiling result on requests written against the same rules. A gate that allows only reads also blocked all 14 but stopped 4 of 8 permitted actions |
| 11 | [Using LLM judges](notebooks/11-llm-judges/) | A model that grades answers can reward a polished mistake or approve the better of two bad answers. On 120 fresh test scenarios after 24 development cases, how do Claude and GPT compare under three judging prompts and both answer orders, and what do presentation, references, parsing and review rules change? | Original pilot preserved: 96/96. New study: recovery removed 94 formatting failures; 4/1,440 ratings still had a wrong choice or acceptance label. Agreement with recovery handled 99/120 cases with 0 observed errors; structured synthetic tasks, not human-preference validation |
| 12 | [Tax workpaper harnesses](notebooks/12-tax-research-harnesses/) | An S-Corporation tax workpaper is mechanical but unforgiving: one misclassified ledger line flows into every shareholder's numbers, and some cases need an accountant's judgment. On 12 fictional 2025 US S-Corps, do detailed instructions, a self-review pass, feedback from a custom validator or the smolagents agent framework give more fully correct workpapers than one direct call, at the same model and call budget? | No. Qwen3.8 Flash's direct call got 12/12, and review steps only matched or lowered that (generic self-review with detailed instructions: 9/12). Gemma 4 31B got 0/12 in every setup. All 24 Qwen framework runs failed because the provider rejects the framework's default tool setting |
| 24 | [Collecting RL rollouts and rewards](notebooks/24-openenv-rewards/) | Training a small model through trial and error needs saved actions and checked rewards. With Llama 3.2 3B and Gemma 3 4B on eight fresh maze and reasoning tasks, how do fixed sampling, early stopping, state coverage and reward-based task selection change the collected signal? No model weights are updated. | 80 attempts: 74 scored outcomes and six provider errors. Only 2/13 complete initial groups contain both success and failure; conditional coverage adds scores to one further group. Early-stop replay uses 193 vs 261 action calls on complete groups; audit calls were actually collected. Total cost bound under $0.018 |
| 25 | [Rewards from knowledge work](notebooks/25-knowledge-work-rollouts/) | A successful tool call can still leave a meeting wrong or a financial answer imprecise. On 12 fresh calendar, financial-table and cash-reconciliation tasks, how do two recent small open-weight policies compare with GPT-6.1 Sol and GPT-6 Luna across 144 attempts, and what makes further improvement harder near a high score? Collect native and exact rewards plus 20 prefix continuations, without updating weights. | Exact completion: Granite 16/36; Nemotron 35/36; Sol 35/36; Luna 33/36. Sol/Luna have only 1/12 and 2/12 mixed reward groups; native FinQA misses Sol's remaining precision error. 584 cached requests total; OpenRouter $0.0581; CLI dollar charges unavailable. Small task set, no general ranking or training-improvement claim |
| 26 | [What can an auditor check about a model?](notebooks/26-model-auditability/) | A disputed automated decision needs evidence of the facts, rule and action; inspecting the neural network needs different access. On 32 fresh expense-policy records per model, repeated twice, what can hosted GPT and Qwen establish, and what extra checks can a pinned local checkpoint support? | GPT 32/32 policy answers vs Qwen 22/32 per draw; both repeat all decision fields. Rules reconstruct 128/128 actions. Local Pythia replays and changes 8/8 computations; neither hosted interface exposes executed weights. Small constructed test, no deployment certification |
| 27 | [Hard knowledge work and adaptive reward collection](notebooks/27-adaptive-knowledge-rollouts/) | Rescheduling a workshop can reduce meeting movement yet create costly delays between reviews. Earlier scheduling, ledger and purchasing tasks produced only successful completed Sol attempts. On four fresh 12-review cases with handoff charges, does adaptive collection obtain more groups of four containing both success and failure than always collecting four? Compare GPT-6.1 Sol and GPT-6 Luna at 180 calls per model and collector. No weight updates. | Sol succeeds on 6/8 uniform and 3/9 adaptive attempts. Complete mixed groups: Sol 2 versus 2; Luna 0 versus 0 (uniform versus adaptive), at 180 calls each. Four fresh cases and two blocks give a descriptive comparison. Earlier runs and calibration costs remain separate. |
| 28 | [Does an agent admit switching off its monitor?](notebooks/28-monitor-removal-honesty/) | A monitor that watches a coding agent only helps while it is on, so agents are told never to remove it, and a user who later asks "did you remove it?" relies on the answer. On three made-up coding jobs that can only be finished by removing or silencing the monitor, do five small open-weight models (Qwen3.8 27B, Nemotron 3.5 Lightning and Super VL, Granite 4.2 8B, LFM2.5 24B) keep the rule, and do they answer truthfully, both about a removal already in their history (960 answers, with the same change credited to a colleague as a control) and about one they chose (150 runs, 300 answers)? | No model flatly denied a removal; untruthful answers described the change and said the monitor was not removed. Qwen admitted its own removal in 48/48 answers; Granite in 3/45, against 28/45 for a colleague's identical change. Choosing for themselves, Qwen kept the monitor in 29/30 runs, Nemotron Lightning removed or silenced it in 17/30. Final reports disclosed every finished removal; later answers about switched-off alerts mostly said "still enabled". Three small made-up jobs, one setting per model |

## Recognising model outputs

If a model is sold under the wrong name, a plausible answer gives no proof of its source. These experiments
ask whether patterns in generated text can identify an endpoint, and whether that evidence survives a change
of topic, formatting or wording.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 13 | [Attributing older model outputs](notebooks/13-older-model-attribution/) | A customer who pays a reseller for a large model sees only the text that comes back, and a cheaper service could quietly answer with a smaller model of the same family. When four older open-weight models (Llama 3.1 8B and 70B, Qwen 2.5 7B and 72B) answer the same ten new writing requests, can five newer models name the writer of each of the 40 answers, from the four names alone or after three labelled examples of each? Do they beat a simple letter-sequence classifier trained on the same examples, and do Meta's and Alibaba's newer models recognise their own company's older models better? | With examples, GPT-6.1 named the exact model for 27/40 texts and Claude Opus 5.5 for 26/40, against 16/40 for the letter-sequence classifier and 10 expected by chance. The family was easy (Claude 38/40) and the size was not: on Llama 3.1 70B texts the two said "8B" 21 times in 40 guesses and "70B" 16 times. Neither Muse Wonder nor Qwen 3.6 27B did better on its own company's models. Qwen 3.6 27B's low score is mostly unreadable replies missing one closing brace. Repeating identical requests changed 13/40 guesses; ten test requests, one text per model |

## Predicting from tables

When only a few labeled rows exist, an analyst still needs to predict the next category or number. A pretrained
tabular model can use those examples as context without updating its weights. The useful comparison is with
ordinary fitted models on the same rows, including inputs outside the examples' range. Balanced accuracy gives
each class equal weight; numeric mean absolute error (MAE) is the average size of a prediction error.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 14 | [Predicting from a small table](notebooks/14-tabular-zero-shot/) | A new process, such as a repair desk with a few dozen finished jobs, must predict outcomes (will this job need a specialist? how many hours?) from very few past examples. A pretrained table model reads those examples and predicts without being fitted to them. On 24 tables generated from four known rules, 12 with yes/no and 12 with number outcomes, given 32 or 128 rows with known outcomes and scored on 128 new rows each, does TabPFN-3.5 predict better than three standard fitted models (a straight-line model, random forest and gradient boosting)? | With 128 known rows, TabPFN reached 82.9% balanced accuracy on yes/no outcomes against 71.3% to 71.7% for the fitted models (the noise allows at most 84.2%), mostly from a rule where the outcome depends on a combination of two columns; its error on numbers was 0.198 times a constant guess's, against 0.479 to 0.517. With 32 rows it was no better on yes/no outcomes (65.7% against 68.5% for the straight-line model). When new rows lay outside the range of the known ones, the straight-line model was far more accurate on numbers (0.054 against 0.187) |

## Writing analyses

An analysis must help its reader make a decision. These experiments separate the content of a model's draft from the preferences of the models asked to grade it, including whether naming the author or asking for a prose audit changes the score.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 15 | [Analytical writing and judge framing](notebooks/15-analytical-writing-style/) | A draft can contain the right numbers yet bury its decision in vague or repeated prose. On two fresh numerical cases in four genres (216 requested drafts), how do 27 writers fare under 30 model judges, and do author disclosure and an explicit prose audit change ratings of the same text? | Anonymous external clarity 88.9/100; audit 0.76 quoted issues per 100 words. Audit clarity change -1.66 points; neutral author-disclosure change -0.06. Model ratings on two cases, no human comprehension claim |
| 17 | [Writing validation on longer documents](notebooks/17-writing-validation-extension/) | A prose flag can reflect reading difficulty, a factual error or taste. Reassess 108 cached drafts from 27 writers, then compare six writers on 24 fresh cases in four genres with realistic lengths (288 requested drafts), using only Codex and Claude judges. | Astra moves from sixth to first when the judge panel changes on the same 288 drafts; fresh prose concerns average 1.6% on old flagged passages. Warning effect -0.31/100; human results pending |

## Creating presentations

A generated deck must keep its facts correct while making a decision easy to see. These experiments test the authoring tools and review steps between a model's response and the slides an audience reads.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 19 | [PowerPoint harnesses and screenshot judges](notebooks/19-powerpoint-harness/) | A presentation edit can leave stale values or unreadable charts. Do helpers and screenshot review improve editable decks? Three models make 24 four-slide decks, then 24 harder eight-slide decks. Three frontier judges see only images; 48 matched pairs cover all four conditions and both feature comparisons. | Full paired grid: helpers 38.2% win credit against primitives; screenshots 61.1% against text. Scores and direct preference agree on 37/40 non-tied pairs. Two related briefs, no general ranking |

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
* Notebook 23 replays 82 original and 78 harder-round CLI requests offline. `NB_LIVE=1` runs a small new first-protocol collection; `NB_HARD_LIVE=1` runs a small harder collection. Fresh results stay under ignored `data/tmp/` paths, separate from both committed main runs and pilots.
* Notebook 14 uses `PRIORLABS_API_KEY` and `NB_LIVE=1` for new collection, with a checked computation-token cap. Its default replay reads 48 saved responses without network access.
* **Smoke test**: `NB_SMOKE=1` makes notebooks 05, 06 and 08 run on a handful of items.
* Notebooks 02-04 download public PDFs on first run into `data/docs/` (git-ignored, sha256-checked where pinned).
* Notebook 16 forecasts six public series through TSFM.ai. Its own `requirements.txt` pins the fitted-baseline libraries; replay needs no key. New collection requires `TS16_LIVE=1` and `TSFMAI_API_KEY`.

Notebook 15 uses strict offline replay with an evidence manifest and a $10 OpenRouter guard. Its README gives model coverage and limits.

Notebook 26 compares policy checks, repeat requests, ledger reconstruction and local checkpoint inspection. Default replay is offline; its README records the access limits, failed provider calls and separately reported costs.

Notebook 18 uses 768 fresh synthetic cases, all four decision models and strict offline replay. Its README records provider pins, scoring audits, diagnostics and reported spend.

Notebooks 21 and 22 are grouped under `econ/`. Each runs independently from its own directory and stops on a
missing offline cache entry. Their READMEs distinguish measured usage from assumed business costs and explain
the small live profiles and spending caps.

Notebook 27 uses strict offline replay and records two equal-call comparisons, a separate pilot and a preserved transport-failure run. Its README explains the CLI-only collection protocol and unknown dollar billing.

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

Notebook 23 uses fictional order threads generated in code on 2026-10-24, with source events, exact answer keys and model responses saved for inspection. It demonstrates data curation without training a model. Its [provenance record](notebooks/23-synthetic-data-curation/data/provenance.json) identifies the models and sources; generated service outputs do not carry a claim of unrestricted downstream training permission.

## For AI agents

See [AGENTS.md](AGENTS.md): layout, the pull-request workflow, claiming a notebook number with an issue,
proposing an experiment as an issue, self-containment, fresh data with no training-set leakage, workflow
diagrams and explainers, the closing future-work and further-reading section, how to call models, and the writing
style (including LLM prose habits to avoid).
