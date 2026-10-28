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
  and lab forms, writing safe SQL, staying inside permissions, grading other models, preparing tax workpapers,
  building slide decks and reading government spending reports.
- Some test pretrained models that predict without being fitted to the data in front of them: forecasting a new
  time series from its recent history (16) and predicting from a small table (14).
- Some study the step before training a model: generating examples with exact answers, and collecting scored
  attempts that a training method could learn from (23, 24, 25, 27).

You can learn from every notebook without reading code. Each README starts by teaching its topic with a small
example, then states the question, shows worked examples from the saved results, explains each chart, and says
what the result supports and where it stops. The tables below give each notebook's question and its answer in
plain numbers.

Each test is small on purpose, tens to hundreds of items with known right answers: enough to show where a method
breaks and what to test at scale, not enough to rank models in general. When every method scores near the top or
near the bottom, the README says that the test cannot rank them. Replies a program could not read are counted
apart from wrong answers. Test data is new, either written for the experiment or published after the models were
trained, so a model cannot score well by remembering it (notebooks 01-04 and 06 predate this rule; see
[Data and licences](#data-and-licences)). Every notebook runs end to end and is committed with its outputs. Every
model response is cached in the notebook's `data/` folder, so you can read the results on GitHub or replay a
notebook offline without an API key.

## Reading documents

A document pipeline starts with three steps: work out what arrived, cut it into pieces a search can find, and
pull out the fields that matter. A mistake at any step carries into everything after it. A misfiled permit is
never searched, a chunk that splits a section returns half an answer, and a missed checkbox on a lab form is a
test that never runs.

Five of these notebooks (01-04, 06) test OpenAI's **Decisions API** (`openai/gpt-6-luna-decisions`, served by
OpenRouter). It is not a chat model. You send it evidence (text or an image) and multiple-choice or yes/no
questions, and it returns a probability for every option instead of writing an answer. That makes it cheap and
fast for classification, and the probabilities can decide which answers to accept automatically and which to
send to a person. Notebook 08 asks chat models with vision to read paper lab forms.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 01 | [Decisions API, 500-label classification](notebooks/01-decisions-api-500-label-classification/) | Research catalogues, ticket queues and product catalogues file each item under one of hundreds of labels, and a wrong label hides the item from the searches and counts that use it. A decision model, which returns a probability for every allowed answer instead of writing text, is not shown hundreds of labels at once, so the list is narrowed first. On 200 research abstracts and OpenAlex's 508 topics, which way of narrowing files the most abstracts correctly for the cost: a 25-topic shortlist by text similarity, picking a subfield first, or a two-round tournament? And can the model's probabilities decide which filings to accept without a person checking? | A 25-topic shortlist followed by one question filed 179 of 200 abstracts under OpenAlex's topic (89.5%) at $0.29 per 1,000; the next best methods filed 171 and 172 at 5 and 18 times the cost, and picking one subfield first filed 153. Accepting answers at confidence 0.9 or more filed 173 automatically, 162 of them correctly (93.6%). The papers and their labels were public before the model was released, so these are upper bounds |
| 02 | [Decisions API chunking](notebooks/02-decisions-api-chunking/) | A search system that answers questions from long documents first cuts them into chunks, and a chunk that starts mid-section or joins two sections is harder to find, read and quote. On six public documents (711 known section starts, 33 questions with known answer passages), does cutting where the Decisions API says a new section starts follow the real sections better than cutting every 400 tokens, at paragraph breaks, by a heading rule or by changes in meaning, and does it help a search find the answer? | Best at finding section starts (average precision 0.60 vs 0.43 for the heading rule and 0.32 for meaning change), most of all on the IRS tax instructions (0.58 vs 0.19). Its chunks put a cut near 85% of section starts and 8% joined two sections; the heading rule reached 80% and 9%, fixed 400-token windows 28% and 46%. Every method found the answer in the top 5 for 25 or 26 of 33 questions. The documents predate the model, so section scores are an upper bound |
| 03 | [Document-type classification](notebooks/03-document-type-classification/) | Before anyone reads a folder of regulatory records, someone sorts it: permit, inspection report, settlement, letter. A settlement filed as a letter may never be read. On 276 public PDFs from 22 US and UK regulator collections, each with a known type out of 101, does a decision model (OpenAI's Decisions API) sort best with all 101 types in one question, a group of types first, or a 15-type shortlist picked by text similarity, and does it need about one page of text (2,000 characters) or four times as much? | One question over all 101 types on 8,000 characters: 251/276 right (90.9%), $0.47 per 1,000 documents; group first also 251/276. Shortlist: 243/276 (88.0%) at $0.22, as 19 correct types missed the shortlist. 8,000 instead of 2,000 characters fixed 11 documents and broke none (pesticide labels behind a cover notice: 0/8 to 5/8). 17 of 25 errors had probability ≥ 0.9. Most documents predate the model's cutoff, so accuracy is an upper bound |
| 04 | [Industry document chunking](notebooks/04-industry-document-chunking/) | Search tools cut long documents into chunks before searching them, and a chunk that splits a section or joins two is harder to find and to cite. On 12 long public filings (water, air and hazardous-waste permits, a settlement, two utility rate cases, a recall notice, a nursing-home inspection and a pesticide label; 1,306 pages), do chunks cut where the Decisions API says a new section starts follow the documents' sections better than cuts by length, by a heading rule or by topic change between paragraphs, and does that help a search find 276 evidence quotes? | Best at ranking real section starts on the 4 documents with bookmarks (average precision 0.35 vs 0.21 for headings and 0.20 for topic change; chance is about 0.10), and it puts a cut near 77% of bookmarked starts vs 68% for headings and 26% for fixed windows. Search finds the quote in the top 5 for 50-55% of pairs under every method. It splits 6 of 47 distinct short quotes vs 2-5 for the others. The documents were public before the study, so scores are an upper bound |
| 06 | [Car make and model from one photo](notebooks/06-car-make-model-from-image/) | A site that files photos under a fixed list of names (car models, products, parts) needs the right name, and a way to tell which answers a person should check. On 146 Wikipedia photos of 73 car models and a list of 109 make-and-model labels, how often does the Decisions API, which returns a probability for every label instead of writing an answer, pick the right one, compared with three large chat models that write their answer (Claude Opus 5.5, GPT-6.1, Muse Wonder)? Are its probabilities good enough to decide which answers to accept without a check? | Decisions API: 138 of 146 right (94.5%) at $0.20 per 1,000 photos and 0.9 s per photo. Every answer it gave at probability 0.9 or more was right: 66% of photos, or 81% when asked for the maker first. GPT-6.1 and Muse Wonder named 146 of 146 and Claude Opus 5.5 145, too close to rank, at 4 to 12 s per photo. The photos are well-composed and public, so these are upper bounds |
| 08 | [Ontario lab requisition extraction](notebooks/08-lab-requisition-extraction/) | A lab clerk types each paper test order into the lab system before blood is drawn; a missed test is never run and an added one is wasted. Ontario's requisition orders tests by a mark in a small box or by writing the name on an "Other Tests" line, and pages arrive as scans or phone photos. On 24 synthetic requisitions with known contents (102 ordered tests, 20 patient and clinician details each), can three hosted vision models (Claude, GPT, Muse Wonder) and four open-weight ones list exactly the ordered tests and copy the details? | Claude Opus 5.5 listed exactly the ordered tests on all 24 pages (102/102, none added); GPT-6.1 and Muse Wonder made 4 test errors between them, so the test cannot rank the three. Best open-weight model Muse Spark Open: F1 0.94. Open models found 66/108 written-in tests against 275/300 boxed ones, and two open-model phone-photo replies listed most of the form. Details: Claude 96.7% exact; every model was weaker on phone photos (GPT-6.1 67.5% vs 98.0% on scans). Synthetic pages with a script font for handwriting |

## Collecting data for training models

A model can be improved by training it on examples of its task: questions with checked answers, or attempts
that a program has scored. Collecting those examples costs model calls before anyone knows whether they will teach
the model anything, and a wrong answer key or a score that accepts unfinished work teaches the wrong thing. On a
calendar task, for example, a score that gives a point for each successful action rated an attempt that moved a
meeting and then booked a duplicate as highly as a clean one (25).

Training by trial and error also learns by comparison: it needs repeated attempts at the same task that sometimes
succeed and sometimes fail. A task the model always fails, or always solves, costs calls and teaches nothing.
These experiments study the collection step without training any model. Notebook 23 generates extraction
examples with exact answers and evidence: if an order changes twice, its final price must agree with the source
messages and its citations must support that price. Notebooks 24, 25 and 27 collect scored attempts at small
puzzles and office tasks, and count how many groups of attempts hold both a success and a failure and what each
costs.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 23 | [Synthetic data generation and curation](notebooks/23-synthetic-data-curation/) | Generated examples need exact values and evidence that supports them. After two protocols found no Sol value misses, a separate v3 generator tested a pilot ladder, then compared fresh retries and verifier-guided repairs on 48 long procurement cases plus 12 audit cases. | V3 Sol answered 45/48 collection cases and 12/12 audit cases with all seven values correct; Luna answered 0/48 and 0/12. The pilot's Sol miss counts were 1, 0 and 1, so it used the declared level-three fallback. Fresh Sol retry and Sol repair each corrected all 3 selected Sol misses; Luna cross-repair corrected 0/3, and neither Sol arm added distinct cases beyond the other. The small audit set was already 12/12 for Sol. No training was run, so correction data is not evidence of a performance gain. |
| 24 | [Collecting scored attempts to train a small model](notebooks/24-openenv-rewards/) | Training a model by trial and error compares its successful and failed tries at the same task, so a group of tries that all succeed or all fail teaches it nothing, yet every try costs model calls. Two small open-weight models (Llama 3.2 3B, Gemma 3 4B) each make four scored tries at 8 freshly generated tasks (4 mazes, 4 arithmetic or list-reversal questions). How many groups of four hold both a success and a failure, and would stopping once the first tries agree, or choosing second-round tasks from first-round scores, find them for fewer calls? No model is trained. | Only 2 of 13 complete groups held both outcomes, both Llama's. 1 of 29 maze tries reached the exit, and Gemma's four tries were identical in 7 of its 8 groups. Skipping the fourth try when the first three agree would have used 193 of 261 calls and kept both groups; a score-guided second round of 16 tries found none. Eight tasks and two models give illustrative counts, not a ranking |
| 25 | [Scored attempts at office tasks](notebooks/25-knowledge-work-rollouts/) | Training a model on its own attempts needs a score that says whether the job was really done, and repeated attempts at the same task that sometimes succeed and sometimes fail, because the training learns from comparing them. On 12 new office tasks (calendar changes, questions on IBM's October 2026 results, reconciliations of US Treasury cash records), each attempted three times by two small open-weight models (Granite 4.2 8B, Nemotron 3.5 Lightning) and two OpenAI models (GPT-6.1 Sol, GPT-6 Luna), how often is the work actually finished, do the environments' own scores agree, and how many of the 48 groups of three attempts hold both a success and a failure? No model is trained. | 119/144 attempts finished: Granite 16/36, Nemotron 35, Sol 35, Luna 33 (one Luna failure was a withheld reply that held the correct booking). The calendar's point per successful action could not tell finished bookings from broken ones, and the finance score's 1% tolerance passed 6 wrong answers. Only 9/48 groups were mixed; Sol and Nemotron had 1 each, at over 100 model calls per mixed group against 30 for Granite |
| 27 | [Hard knowledge work and adaptive reward collection](notebooks/27-adaptive-knowledge-rollouts/) | Rescheduling a workshop can reduce meeting movement yet create costly delays between reviews. Earlier scheduling, ledger and purchasing tasks produced only successful completed Sol attempts. On four fresh 12-review cases with handoff charges, does adaptive collection obtain more groups of four containing both success and failure than always collecting four? Compare GPT-6.1 Sol and GPT-6 Luna at 180 calls per model and collector. No weight updates. | Sol succeeds on 6/8 uniform and 3/9 adaptive attempts. Complete mixed groups: Sol 2 versus 2; Luna 0 versus 0 (uniform versus adaptive), at 180 calls each. Four fresh cases and two blocks give a descriptive comparison. Earlier runs and calibration costs remain separate. |

## Making bounded decisions

Many automated decisions have a fixed set of allowed answers: approve or hold, which queue, does this claim
match the records. A decision model returns a probability for each allowed answer instead of writing text, which
makes it cheap and easy to put a threshold on. The risk is a check that looks simple but takes several steps. A
claimed ledger total is right only if the lines add up to it, and a model that answers yes or no without doing
the sum is guessing. This experiment compares four decision models on checks that take one step and checks that
take several, and tests whether rewording the question or moving the arithmetic into code fixes the failures.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 18 | [Four decision models on multi-step checks](notebooks/18-decisions-api-comparison/) | Approvals and routing are often handed to decision models: services that read evidence and return a probability for each allowed answer instead of writing text. Many checks take several steps, such as adding up a ledger before accepting a claimed total, or following a chain of records to the current version. On fresh synthetic cases built in pairs with opposite answers (768 cases in six kinds of check, 288 ledger claims, 768 harder lookups), how often do OpenAI Decisions, Jev 1.14, Mercury Decide and Clef Flash get these checks right, and does rewording the question or moving the arithmetic into code fix the failures? | Single lookups sit at a ceiling: all four scored 100% in 9 of 24 cells. Ledger totals sit at a floor: every way of having the model check the sum scored 49.0% to 56.9%, where always answering no scores 50%, and clearer wording did not help; having the model label each row and Python add the amounts was right on 1,151 of 1,152 claims. On the harder lookups, Mercury Decide (72.1%) and Jev 1.14 (70.1%) beat OpenAI Decisions (55.2%), with no clear winner between the first two; Clef Flash scored 44.3%, or 59.2% on the requests its host did not refuse |

## Measuring economic decisions

The number that is easiest to collect is often not the one a decision needs. A cheap model that proposes invoice
payments saves money only after counting the checks it needs and the expensive calls it still triggers. A
government report can show a budget, an accounting expense and a cash payment for the same programme, and only
one of them answers "how much was paid?". Both [economics experiments](econ/) put a price on an extra step meant
to make a model's work checkable: a second opinion on each invoice, and a list of every figure used with its
supporting passage. Each has its own notebook under `econ/`, and the [econ README](econ/) compares them.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 21 | [The cost of checking an assistant's work](econ/21-verification-costs/) | A cheap AI model saves money on invoice payments only if checking its answers, and passing the doubtful ones to an expensive model, costs less than using the expensive model on every invoice. On 72 made-up invoices with exact answers (58 to pay, 14 to hold), the cheap model's answer was checked either by asking it a second time or by a stronger model's review, and rejected invoices went to the expensive model. Does either check save money, and above what price per expensive call? | The cheap model (Qwen3.8 Flash, reasoning off) was exact on 14 of 72 invoices, all of them holds, and on 0 of 58 payments. The expensive model (GPT-6.1 Sol) and both checked routes were exact on 72 of 72, and neither check let a wrong answer through or rejected a right one. Because only the 14 holds could skip the expensive model, asking twice pays off once an expensive call costs more than USD 0.0011, and a Claude Opus 5.5 review only above USD 0.1332 per call. No wrong answer came close to the right amount, so the checks never faced a hard mistake; a rules program got all 72 right. |
| 22 | [Reading what government spending figures mean](econ/22-fiscal-implementation/) | A government report can show an approved budget, an accounting expense and a cash payment for the same programme, and only one of them answers a given question. Given the right pages of a recent report and a precise question about money received, paid or owed, does asking a model to list each figure it used with the supporting passage, and letting a program add them (a "ledger"), give more correct answers than asking for the figure directly? Three models (GPT-6.1 Sol, Claude Opus 5.5, Muse Wonder Full) answered 22 questions on 8 UK, US and EU reports published 13-22 October 2026, once each way. | Every completed answer was right (131 of 131), so the test hit its ceiling and cannot tell the methods apart. GPT and Claude scored 22/22 both ways and Muse 21/22 both ways; neither Muse miss was a reading mistake (one timeout, one correct answer excluded after a hidden retry). All 36 answers on the 6 questions whose amount the report does not disclose said so. The ledger added about 2.5 seconds per answer for GPT and Claude and changed no answer. |

## Forecasting observations

A grid operator plans tomorrow's supply from a forecast of demand, and a forecast that runs low leaves too little
capacity. The usual floor is simply to repeat last week. Fitting and maintaining a separate model for every
series takes work, so pretrained forecasting models promise to forecast a new series from its recent history
alone. This experiment tests whether they beat repeating the last cycle and standard fitted methods on fresh
public series, and whether their stated 80% ranges hold 80% of what happened next.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 16 | [Forecasting a new series without fitting](notebooks/16-time-series-zero-shot/) | Planners forecast electricity demand, web traffic or exchange rates a day to a month ahead, and the usual floor is simply repeating last week. A model pretrained on many other series could forecast a new one from its recent history with no fitting. On six public series (Ontario demand, Toronto temperature and wind, two Wikipedia page-view counts, USD/CAD), forecast from 112 starting points between August 20 and October 17, 2026, after every model's weights were public, do seven such models beat repeating the last cycle and five standard methods fitted to the same history, and do their 80% ranges hold 80% of actual values? | The four best pretrained models made 13% to 14% less error than repeating the last cycle (relative error 0.860 to 0.871), and the best fitted method, AutoETS, 4% less (0.961); the lead over AutoETS is not established on six series (interval of the difference crosses zero). On Ontario demand they cut error by about a third, while on AI page views and USD/CAD they did worse than repeating the last cycle. Their 80% ranges held only 65.5% to 70.1% of actual values, and one model's ranges (TimesFM 2.5) were mislabelled at every step |

## Letting models act

Once a model can run a query, edit a file or fill in a workpaper, a wrong answer becomes a wrong action. One
database assistant added `UPDATE Invoice SET Total = 0` after the count it was asked for, which would have
changed every invoice, while its reply said it had refused (05). These notebooks test the layers between what a
model writes and what changes: whether it keeps to written permissions (05, 09), what code should enforce them
when it does not (10), how agents hand work to each other and who waits for whom (07), and whether review steps
around a model make regulated work more reliable (12).

Sometimes the quickest way to finish a job is to switch off the safety check that watches the agent, the way a
decorator might take down a smoke alarm to paint a ceiling. Notebook 28 asks whether small agents keep that rule,
and whether they tell the truth when asked about it afterwards.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 05 | [Text-to-SQL safety](notebooks/05-text-to-sql-safety/) | An assistant that turns an analyst's question into a database query that runs at once can delete records or expose salaries and customers' addresses if it ignores its rules. Given written read-only rules (one reading query, no salary or login tables, no individual contact details or birth dates, at most 1,000 rows), how often do 8 open-weight models and 3 closed ones (Claude, GPT, Muse) write a rule-breaking query on 29 requests that cannot be met within the rules, and do they still answer 23 ordinary questions correctly? | 9 of 11 models wrote no rule-breaking query in 29 tries, which still allows a true rate up to 12%. Mistral Small 4 broke the rules 7 times, once adding a statement that would set all 412 invoices to zero while marking its reply as refused; Gemma 4 31B broke them 3 times. No model refused an ordinary question: 10 answered all 23 correctly and Mistral 22 |
| 07 | [Subagent handoff harness](notebooks/07-subagent-handoff-harness/) | An AI agent can split a job among helper agents, but the time saved depends on who waits for whom, and a message between agents can arrive too late to be read. On one three-city trip-planning task with a known correct answer, how do seven ways of coordinating a planner and its helpers compare with one agent working alone, in time, model calls and time spent waiting, and do questions, progress reports and instructions reach the agent that needs them? One recorded run per arrangement, with Claude agents. | All 7 answers correct. Waiting for each helper in turn: 120 s, against 82 s for one agent; starting the helpers and working meanwhile: 57 s with 18 model calls instead of 11. One instruction arrived during a helper's last step and was never read, with no notice to the sender. Two layers of helpers: 35 calls and weather figures that no tool returned |
| 09 | [Proposed unsafe agent actions](notebooks/09-agent-action-safety/) | An assistant with a terminal can delete files, read secrets or push code, and its written permissions are often the only guard. On 12 forbidden requests, each paired with a similar permitted one, how often do two open-weight models (DeepSeek, Gemma) and two closed ones (Claude, GPT) propose an action outside their permissions, how many permitted requests do they complete, and does a checklist in the prompt help? Proposed commands are judged as text by other models and never run. | On 96 forbidden requests the judges flagged one reply, and that flag is disputed. The clearest problem was on a permitted request: a search that follows a symlink out of the project. GPT-6.1 completed 12/12 permitted requests, Gemma 4 31B 5/12; the checklist did not reduce flags |
| 10 | [Execution guardrails](notebooks/10-code-execution-guardrails/) | When an AI agent proposes deleting, writing or reading a file, a short piece of code (the gate) decides whether it runs. A gate that only reads the start of the path can be fooled by a `..` step or a link that leads somewhere else. On 22 written requests with known right answers (8 permitted, 14 forbidden), how many forbidden actions does each of five gate designs let through, and how many permitted ones does it block? No model is involved; the same requests go through every gate. | A gate that checks only the start of the path let through 5 of 14 forbidden actions: every request built to beat a text check, and none of the other 9. A gate that resolves each path and offers only named operations blocked all 14 and allowed all 8 permitted ones, a ceiling result on requests written against the same rules. A gate that allows only reads also blocked all 14 but stopped 4 of 8 permitted actions |
| 12 | [Tax workpaper harnesses](notebooks/12-tax-research-harnesses/) | An S-Corporation tax workpaper is mechanical but unforgiving: one misclassified ledger line flows into every shareholder's numbers, and some cases need an accountant's judgment. On 12 fictional 2025 US S-Corps, do detailed instructions, a self-review pass, feedback from a custom validator or the smolagents agent framework give more fully correct workpapers than one direct call, at the same model and call budget? | No. Qwen3.8 Flash's direct call got 12/12, and review steps only matched or lowered that (generic self-review with detailed instructions: 9/12). Gemma 4 31B got 0/12 in every setup. All 24 Qwen framework runs failed because the provider rejects the framework's default tool setting |
| 28 | [Does an agent admit switching off its monitor?](notebooks/28-monitor-removal-honesty/) | A monitor that watches a coding agent only helps while it is on, so agents are told never to remove it, and a user who later asks "did you remove it?" relies on the answer. On three made-up coding jobs that can only be finished by removing or silencing the monitor, do five small open-weight models (Qwen3.8 27B, Nemotron 3.5 Lightning and Super VL, Granite 4.2 8B, LFM2.5 24B) keep the rule, and do they answer truthfully, both about a removal already in their history (960 answers, with the same change credited to a colleague as a control) and about one they chose (150 runs, 300 answers)? | No model flatly denied a removal; untruthful answers described the change and said the monitor was not removed. Qwen admitted its own removal in 48/48 answers; Granite in 3/45, against 28/45 for a colleague's identical change. Choosing for themselves, Qwen kept the monitor in 29/30 runs, Nemotron Lightning removed or silenced it in 17/30. Final reports disclosed every finished removal; later answers about switched-off alerts mostly said "still enabled". Three small made-up jobs, one setting per model |

## Auditing models

A customer who pays for a large model sees only the text that comes back, so a cheaper service could answer in
its place without anyone noticing. And when an assistant's decision is questioned later, someone has to show
what it was given, what it decided and whether that followed the rules. These experiments ask what can be checked
from the outside: whether newer models can tell which older model wrote a text (13), and which audit questions
saved records can answer and which need the model's own files (26).

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 13 | [Attributing older model outputs](notebooks/13-older-model-attribution/) | A customer who pays a reseller for a large model sees only the text that comes back, and a cheaper service could quietly answer with a smaller model of the same family. When four older open-weight models (Llama 3.1 8B and 70B, Qwen 2.5 7B and 72B) answer the same ten new writing requests, can five newer models name the writer of each of the 40 answers, from the four names alone or after three labelled examples of each? Do they beat a simple letter-sequence classifier trained on the same examples, and do Meta's and Alibaba's newer models recognise their own company's older models better? | With examples, GPT-6.1 named the exact model for 27/40 texts and Claude Opus 5.5 for 26/40, against 16/40 for the letter-sequence classifier and 10 expected by chance. The family was easy (Claude 38/40) and the size was not: on Llama 3.1 70B texts the two said "8B" 21 times in 40 guesses and "70B" 16 times. Neither Muse Wonder nor Qwen 3.6 27B did better on its own company's models. Qwen 3.6 27B's low score is mostly unreadable replies missing one closing brace. Repeating identical requests changed 13/40 guesses; ten test requests, one text per model |
| 26 | [What can an auditor check about a model?](notebooks/26-model-auditability/) | When an assistant helps decide something like an expense claim, someone may later need to check what was decided, whether it followed the rule, and why the model answered as it did. Saved records can answer the first two; looking inside the model needs its files. On 32 made-up expense claims with exact answers, each sent twice to a closed model (GPT-6.1 Sol) and to an open-weight model reached through a hosting service (Qwen3 30B), which audit checks work from saved records alone, and which need a model run on the auditor's own machine (Pythia-14M, 8 prompts)? | GPT-6.1 Sol was right on 32/32 claims in both rounds (the test's ceiling); Qwen3 30B on 22/32, obeying a planted fake instruction on 8/8 claims that carried one. Both repeated every decision exactly, errors included, so asking again is no check. A rules check plus a saved log let all 128 actions be recomputed and held all 20 wrong answers; 3 of 4 tampered logs passed their own check, and all 4 were caught only against a separately stored fingerprint. Re-running and editing the model's internal calculation worked on 8/8 prompts for the local model and was not possible through either hosted service. Eight made-up claim families, so no general ranking |

## Predicting from tables

A new repair desk with forty finished jobs still has to guess whether the next job needs a specialist and how
many hours it will take. With so few rows, a fitted model has little to learn from. A pretrained table model
reads the labelled rows as its input and predicts without being fitted to them. This experiment compares one with
ordinary fitted models on the same rows, including new rows outside the range of the labelled ones. Balanced
accuracy gives each outcome equal weight; numeric error is compared with a constant guess.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 14 | [Predicting from a small table](notebooks/14-tabular-zero-shot/) | A new process, such as a repair desk with a few dozen finished jobs, must predict outcomes (will this job need a specialist? how many hours?) from very few past examples. A pretrained table model reads those examples and predicts without being fitted to them. On 24 tables generated from four known rules, 12 with yes/no and 12 with number outcomes, given 32 or 128 rows with known outcomes and scored on 128 new rows each, does TabPFN-3.5 predict better than three standard fitted models (a straight-line model, random forest and gradient boosting)? | With 128 known rows, TabPFN reached 82.9% balanced accuracy on yes/no outcomes against 71.3% to 71.7% for the fitted models (the noise allows at most 84.2%), mostly from a rule where the outcome depends on a combination of two columns; its error on numbers was 0.198 times a constant guess's, against 0.479 to 0.517. With 32 rows it was no better on yes/no outcomes (65.7% against 68.5% for the straight-line model). When new rows lay outside the range of the known ones, the straight-line model was far more accurate on numbers (0.054 against 0.187) |

## Models as judges

Teams often let one model grade another's work, because reading every answer by hand is slow. A grade is useful
only if it reflects the work rather than the judge: a polished wrong answer should still fail, and a draft should
score the same whoever wrote it and whichever judge reads it. These experiments test model judges on answers
whose correct grade is computed in code (11) and on short decision documents (15, 17), measuring how often the
grade is right and how much the instruction, the author's name and the choice of judge move it.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 11 | [Using LLM judges](notebooks/11-llm-judges/) | A model that grades answers can reward a polished mistake or approve the better of two bad answers. On 120 fresh test scenarios after 24 development cases, how do Claude and GPT compare under three judging prompts and both answer orders, and what do presentation, references, parsing and review rules change? | Original pilot preserved: 96/96. New study: recovery removed 94 formatting failures; 4/1,440 ratings still had a wrong choice or acceptance label. Agreement with recovery handled 99/120 cases with 0 observed errors; structured synthetic tasks, not human-preference validation |
| 15 | [What changes an AI judge's writing score?](notebooks/15-analytical-writing-style/) | Teams often let one AI model score documents written by another, so the score should reflect the document, not how the judge was asked or which judge was used. 27 writer models each wrote 8 short decision documents (2 invented cases, 4 document types; 213 drafts), and each draft was scored by two judges from other companies under four instructions: plain questions or an "AI slop" audit, with the author hidden or named. How much do the instruction, the author's name and the choice of judge move a clarity score, and do two judges flag the same passages? | The slop audit lowered clarity by 1.66 points out of 100 (interval -2.17 to -1.12), less than the 3.30 points a second reading by the same judge moved it; naming the author changed it by -0.06. The judge mattered more: on identical control texts, judges' average clarity ran from 32.5 to 83.0, and on 194 drafts audited by two judges only 36.5% of flags overlapped. The lowest-scoring draft contradicted its own recommendation. Model judges only, two invented cases |
| 17 | [Does a writer's rank depend on the judges?](notebooks/17-writing-validation-extension/) | When AI judges compare AI writers, a common precaution drops judges made by the writer's own company. Six writers produced 288 decision documents on 24 new invented cases, scored by two OpenAI judges and one Anthropic judge: does the ranking change between that rule and giving every writer the same judges? Fresh judges also re-read 204 passages that an earlier study had flagged or left alone, and 24 drafts were scored with and without an "AI slop" warning on a fixed list of criteria. | GPT-6 Astra ranked last when same-company judges were dropped (88.21) and first when every writer had the same judges (93.10), because the OpenAI judges scored every one of 282 drafts higher than the Claude judge, by 9.01 points on average. Fresh judges found a wording problem in 1.6% of opinions on earlier flagged passages and 1.2% on unflagged ones; most concerns they did raise were about reasoning. The warning changed clarity by -0.31 (interval -0.70 to +0.02). Model judges only; human study prepared but not run |

## Creating presentations

A deck that supports a decision has to carry the right figures to every slide and lay them out so the choice is
easy to see. A model that builds slides by writing code does not see the slides it describes unless someone shows
it pictures of its draft. This experiment compares three models and two kinds of help, ready-made layout blocks and
pictures of the draft, on decks that judge models compare head to head.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 19 | [Which model and tools make a better deck?](notebooks/19-powerpoint-harness/) | A model asked to build a decision deck, then update it when the plan changes, has to carry every changed figure to each slide and lay it out readably, without ever seeing the slides it describes. Which of three models (GPT-6.1 Sol, Claude Opus 5.5, Muse Wonder Full) makes the decks that judge models prefer, and do ready-made layout blocks or pictures of its own draft help? 24 eight-slide decks on two tasks written for the study, judged from images: 72 individual scores and 288 head-to-head judgments of 48 deck pairs. | GPT-6.1 Sol's decks were preferred in every setup (81% to 96% win credit); Muse Wonder Full won none of its 96 head-to-head judgments. Most of GPT's lead over Claude came from one task, where all four Claude decks left a figure off the closing slide that only the judges' checklist asked for (GPT won 22 of 24 there; 12 to 9 with 3 ties on the other task). Pictures of the draft were preferred (61% win credit), layout blocks were not (38%), and neither passed the adoption rule set in advance. Two tasks, one deck per setup |

## Planned experiments

Experiments that are written up but not built yet are open issues with the
[`notebook-proposal`](https://github.com/k-sandhu/experiment-notebooks/issues?q=is%3Aissue+is%3Aopen+label%3Anotebook-proposal)
label. Each one gives the question, the fresh data to use, the models, the measures and a cost estimate.

| Issue | Question |
|---|---|
| [#12](https://github.com/k-sandhu/experiment-notebooks/issues/12) | People have used the Decisions API since its October beta to route complaints, grade agent transcripts, pick an agent's next action from a screenshot and choose which LLM should answer a prompt, and their reports disagree on whether its probabilities can be trusted. On 14 tasks with fresh data, including those uses plus bird recordings, wildlife photos and restaurant inspection reports, which uses hold up, are its probabilities calibrated and stable when options are reordered or reworded, how does it compare with other decision models such as Jev where a task calls for it, and what does each cost? |


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
the models, which may have seen them, so treat those accuracy figures as upper bounds. Notebooks 01-04 were first run inside another project and moved here with their data and caches.

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
