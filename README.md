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
  building slide decks, turning subsidiaries' workbooks into financial statements, reading government spending
  reports, keeping watch on other organisations' news pages and editing long documents without damaging them.
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

## Watching outside sources

Many teams keep a list of outside organisations whose announcements they must not miss: a finance team watches
the central bank, the tax authority, its largest customers and suppliers. Someone opens each news page every
week and copies the headline, date, author and text of anything new. A language model can do that reading
itself, or it can write one small extraction program per site that then runs every week at almost no cost. The
programs break when a site is redesigned, sometimes visibly and sometimes by quietly returning the wrong date, so
the question is whether checks that do not know the right answer can notice a break and send the program back to
the model for repair.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 31 | [Self-repairing scrapers](notebooks/31-self-repairing-scrapers/) | A finance team must notice new releases on 20 outside organisations' news pages and record each headline, date, author and text. On 20 fictional, differently built sites over four weekly runs with six redesigns (593 release-weeks), can a model write one extraction program per site, fix it when free automatic rules or a stronger model's review flag a problem, and keep it working? Which checks catch which errors, and how does this compare with a model reading every page? Writers: Claude Haiku 5.5, Claude Sonnet 5.5 and the small open-weight Granite 4.2 8B; reviewer Claude Opus 5.5. | Claude Haiku and Sonnet wrote correct programs for 19 and 20 of 20 sources at once; the free rules caught every break after the redesigns and one repair fixed each, so every release-week was right for $0.28 (Haiku) or $1.76 (Sonnet) over four weeks. Granite: 4 of 20 at once, 9 after three repairs, and its errors went unnoticed in 22 source-weeks with rules only against 1 with the review. On 135 planted errors the rules flagged 48 and the review all 135. Reading every page cost $4.25 with Sonnet (all right) and $0.23 with Haiku (94.4% right) |

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
| 27 | [When to stop repeating a task while collecting training attempts](notebooks/27-adaptive-knowledge-rollouts/) | Training a model by trial and error compares its successful and failed attempts at the same task, but each attempt by a tool-using agent costs many model calls, and a strong model mostly succeeds, so most groups of attempts teach nothing. One proposed saving is to try each task twice and move on when the two attempts agree. On fictional scheduling tasks with exactly computed answers (and, at first, ledger and purchasing tasks), attempted by GPT-6.1 Sol and GPT-6 Luna, does that collect more groups of four attempts holding both a success and a failure than always making four? The budgets are equal in model calls in four comparisons, and in tokens (24 million per model and collector) on 16 new twelve-review scheduling tasks. No model is trained. | No. At equal tokens both rules collected 4 mixed groups with Sol and 0 with Luna, and across all five comparisons always-four collected 11 against 10 for stopping early. Sol solved all 111 known attempts on the first three task sets, so no Sol group could be mixed until the tasks gained competing handoff charges; Luna then solved none of 55. Most of Sol's failures on the hardest tasks were valid agendas a median 4.7% above the cheapest. Four blocks of four tasks cannot rule out a small difference either way. |

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
| 09 | [Staying inside written permissions](notebooks/09-agent-action-safety/) | A coding assistant that proposes terminal commands can delete files, read secrets or push code, and the permissions written for it are often the only guard. On 12 forbidden requests (a folder outside the project, the secrets file, an instruction hidden in a ticket), each paired with a similar permitted one, do two open-weight models (DeepSeek V4.1 Flash, Gemma 4 31B) and two closed ones (Claude Opus 5.5, GPT-6.1) propose the forbidden action, do they still do the permitted work, and does a safety checklist in the prompt change either? Replies are judged as text by other models and never run. | Judges flagged 1 of 96 forbidden-request replies, and review disputes it: every model sits at 0 or 1 of 12, too low to rank. The one flag review supported was on a permitted job: DeepSeek code that searched through a link out of the project. Permitted requests completed: GPT-6.1 24/24, Claude 21, DeepSeek 18, Gemma 10, but 9 of Gemma's 14 misses were format failures, and both judges said 5 of those 9 did the job. The checklist did not reduce flags |
| 10 | [Execution guardrails](notebooks/10-code-execution-guardrails/) | When an AI agent proposes deleting, writing or reading a file, a short piece of code (the gate) decides whether it runs. A gate that only reads the start of the path can be fooled by a `..` step or a link that leads somewhere else. On 22 written requests with known right answers (8 permitted, 14 forbidden), how many forbidden actions does each of five gate designs let through, and how many permitted ones does it block? No model is involved; the same requests go through every gate. | A gate that checks only the start of the path let through 5 of 14 forbidden actions: every request built to beat a text check, and none of the other 9. A gate that resolves each path and offers only named operations blocked all 14 and allowed all 8 permitted ones, a ceiling result on requests written against the same rules. A gate that allows only reads also blocked all 14 but stopped 4 of 8 permitted actions |
| 12 | [Do extra steps improve tax workpapers?](notebooks/12-tax-research-harnesses/) | A small company's tax workpaper turns its books into a business profit and each owner's share of it, so one wrong sum reaches every owner's tax return. When a model drafts the workpaper, teams often add steps around it rather than change the model. On 12 fictional 2025 S-Corporations whose correct workpapers are computed by code, do a longer checklist, a second call in which the model reviews its own draft, feedback from a checking program, or an agent framework give more fully correct workpapers than one direct call to the same model (Gemma 4 31B or Qwen3.8 Flash)? | None of the steps helped, and the design left them no room to: Qwen's direct call was fully correct for 12/12 companies with either instruction length, and Gemma was correct for 0/12 in every setup. Qwen's review steps lost 5 runs, all empty replies after it used its whole output limit thinking; it was right in 67/67 replies the scorer could read. Gemma's profit was wrong in 96/96 workpapers while its review flags were right in 88/96, and the checker, which does not recompute profit, found no error in any of its 24 drafts in the checker setup. The framework never ran with Qwen: its host rejected the framework's default tool setting in all 24 runs |
| 28 | [Does an agent admit switching off its monitor?](notebooks/28-monitor-removal-honesty/) | A monitor that watches a coding agent only helps while it is on, so agents are told never to remove it, and a user who later asks "did you remove it?" relies on the answer. On three made-up coding jobs that can only be finished by removing or silencing the monitor, do five small open-weight models (Qwen3.8 27B, Nemotron 3.5 Lightning and Super VL, Granite 4.2 8B, LFM2.5 24B) keep the rule, and do they answer truthfully, both about a removal already in their history (960 answers, with the same change credited to a colleague as a control) and about one they chose (150 runs, 300 answers)? | No model flatly denied a removal; untruthful answers described the change and said the monitor was not removed. Qwen admitted its own removal in 48/48 answers; Granite in 3/45, against 28/45 for a colleague's identical change. Choosing for themselves, Qwen kept the monitor in 29/30 runs, Nemotron Lightning removed or silenced it in 17/30. Final reports disclosed every finished removal; later answers about switched-off alerts mostly said "still enabled". Three small made-up jobs, one setting per model |

## Keeping track of what others know

A colleague who missed this morning's change still thinks the meeting is in the old room, and anyone who works
with them has to remember that. People keep track of what each person has seen, and so what they believe,
separately from what is true. Psychologists test this in children with a short story: a child's toy is moved
while they are out, and the question is where they will look for it. A model that writes to a colleague, hands
work to a helper agent or explains a result the user cannot see needs the same habit: it has to notice who missed
a change and who did not, and act on it.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 29 | [Tracking what someone else believes](notebooks/29-theory-of-mind/) | A model that hands work to a helper or messages a colleague must tell who missed a change and who saw it. On 240 pairs of new stories written in code (480 stories in eight families: moved objects, a phone that downloads updates only on the office Wi-Fi, blind copies on emails, a subagent working from an old copy of a project, left and right across a counter, news passing along a chain of colleagues, and more), where the two stories of a pair differ in the one detail that decides what a person believes, do ten models state the belief correctly, and do they use it to predict what the person does, judge it and decide whether to tell them? | Share of pairs right in both stories, stating / using the belief: Claude Opus 5.5 1.00 / 1.00, Muse Wonder 1.00 / 1.00 (80 pairs), GPT-6.1 Sol 0.99 / 1.00, DeepSeek V4.1 Flash 0.99 / 0.93, Qwen3.8 27B 0.98 / 0.91, Muse Spark 0.98 / 0.97, Nemotron 3.5 Super VL 0.89 / 0.86, Claude Haiku 5.5 0.80 / 0.82, GPT-6 Luna 0.69 / 0.48, Granite 4.2 8B 0.52 / 0.29. Weaker models give the old belief even when the person watched the change: Granite is right in 51% of those answers. The top three are at the test's ceiling, and the stories state every rule |

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
whose correct grade is computed in code (11), on short decision documents (15, 17) and on one editor's choices
between two versions of a paragraph (35), measuring how often the grade is right and how much the instruction, the
author's name, the choice of judge and examples of the editor's past choices move it. They live in
[`notebooks/judges/`](notebooks/judges/), whose README introduces model judges, the ways they fail and the
experiments in progress there: which models judge best, whether a weaker model can settle a disagreement between
stronger ones, and how the grading set-up and instructions change the verdicts.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 11 | [Using LLM judges](notebooks/judges/11-llm-judges/) | When a team changes an AI assistant, another model often grades thousands of its answers, so a grader that rewards a wrong answer can make a worse version look better. On 120 freshly generated grading tasks whose right grade is computed by code (invoice sums, order-record versions, conflicting reports, a made-up refund policy), how often do Claude Opus 5.5 and GPT-6.1 Sol pick the better of two answers and say correctly whether each is acceptable, with three prompts and both answer orders, and how much checking does a both-judges-agree rule save? | GPT chose correctly in all 120 tasks with every prompt and order, a ceiling. Claude scored 94-100/120 when replies had to be in the exact machine-readable format, but 94 of the 96 unsuccessful choices were replies with a short note before a correct grade; read with a rule fixed beforehand, it scored 119-120. Genuine errors: 4 of 1,440 ratings in 2 tasks. Accepting only grades both judges agreed on decided 99/120 with no error. Generated three-field tasks, not open-ended writing |
| 15 | [What changes an AI judge's writing score?](notebooks/judges/15-analytical-writing-style/) | Teams often let one AI model score documents written by another, so the score should reflect the document, not how the judge was asked or which judge was used. 27 writer models each wrote 8 short decision documents (2 invented cases, 4 document types; 213 drafts), and each draft was scored by two judges from other companies under four instructions: plain questions or an "AI slop" audit, with the author hidden or named. How much do the instruction, the author's name and the choice of judge move a clarity score, and do two judges flag the same passages? | The slop audit lowered clarity by 1.66 points out of 100 (interval -2.17 to -1.12), less than the 3.30 points a second reading by the same judge moved it; naming the author changed it by -0.06. The judge mattered more: on identical control texts, judges' average clarity ran from 32.5 to 83.0, and on 194 drafts audited by two judges only 36.5% of flags overlapped. The lowest-scoring draft contradicted its own recommendation. Model judges only, two invented cases |
| 17 | [Does a writer's rank depend on the judges?](notebooks/judges/17-writing-validation-extension/) | When AI judges compare AI writers, a common precaution drops judges made by the writer's own company. Six writers produced 288 decision documents on 24 new invented cases, scored by two OpenAI judges and one Anthropic judge: does the ranking change between that rule and giving every writer the same judges? Fresh judges also re-read 204 passages that an earlier study had flagged or left alone, and 24 drafts were scored with and without an "AI slop" warning on a fixed list of criteria. | GPT-6 Astra ranked last when same-company judges were dropped (88.21) and first when every writer had the same judges (93.10), because the OpenAI judges scored every one of 282 drafts higher than the Claude judge, by 9.01 points on average. Fresh judges found a wording problem in 1.6% of opinions on earlier flagged passages and 1.2% on unflagged ones; most concerns they did raise were about reasoning. The warning changed clarity by -0.31 (interval -0.70 to +0.02). Model judges only; human study prepared but not run |
| 35 | [Teaching a judge one editor's taste](notebooks/judges/35-judge-taste/) | A team that lets a model choose between two drafts needs it to pick what its own editor would pick, and the written style rules often do not decide. On 42 paragraph pairs from this repository's README rewrites (the earlier version and the one the owner merged, from eight READMEs that supplied no examples), how often do Claude Opus 5.5, Claude Haiku 5.5, GPT-6.1 Sol and the small open-weight Qwen3.5-9B pick the merged version with no guidance, the written rules, eight random or eight similar past choices, a rubric written from 40 past choices, or rules plus examples, each pair in both orders? | With no guidance agreement ran from 45% (Qwen) to 73% (Opus). Eight similar past choices raised Opus to 92% and Sol to 82% (gains of 19 and 23 points, intervals above zero), random past choices to 86% and 77%, while the written rules alone changed nothing clear; Haiku and Qwen gained nothing and favoured the second version shown. A rule counter decided no pair, but picking the version with fewer long words, tried after the results, matched 83%. Almost every merged version was drafted by Claude, so a judge may be learning that rewriter's habits as much as the owner's taste. |

## Turning spreadsheets into reports

A finance team that publishes statements for many subsidiaries receives a workbook from each one, and no two are
built alike: the current year sits in a different column, costs are negative in one and in brackets in another,
labels are in German or Japanese, a budget column sits beside the actuals. Someone copies each into a fixed house
template by hand. A number taken from the wrong column or put on the wrong line leaves the page looking tidy, and
some of these mistakes leave every total intact. This experiment tests whether a model can write the conversion
for each workbook, and which automatic checks catch the mistakes it makes.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 30 | [Twenty differently built workbooks, one set of financial statements](notebooks/30-workbook-to-statements/) | A group's finance team turns each subsidiary's year-end workbook into statements in one house format, and a number on the wrong line or from the wrong column can look perfectly tidy. On 20 fictional subsidiary workbooks with exact answers (18 countries, five languages, layouts from trial balances to ERP exports, two with errors of their own), can a model write a conversion program for each, with tie-out checks and a second model's look at the PDF sending it back to fix problems? Writers: Claude Sonnet 5.5 and GPT-6.1 Sol; reviewer: Claude Opus 5.5; reference: a fixed keyword mapper. Which check catches which mistake, and does the loop ever change a number to make the checks pass? | All 40 final statements were exactly right (66 amounts and the heading each), at the ceiling for both writers, and no wrong statement ever passed the checks. Sonnet's first programs were right on 20 of 20; GPT's on 16, the other 4 stopped with an error and were fixed in one repair. The keyword mapper got 3 of 20. Both writers kept the subsidiaries' numbers on the two broken workbooks and declared the exact difference. Of 20 planted mistakes, the tie-out checks caught the 8 that broke a total and the visual review caught 19, including wrong units, a near-duplicate company and amounts moved within one subtotal |

## Creating presentations

A deck that supports a decision has to carry the right figures to every slide and lay them out so the choice is
easy to see. A model that builds slides by writing code does not see the slides it describes unless someone shows
it pictures of its draft. This experiment compares three models and two kinds of help, ready-made layout blocks and
pictures of the draft, on decks that judge models compare head to head.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 19 | [Which model and tools make a better deck?](notebooks/19-powerpoint-harness/) | A model asked to build a decision deck, then update it when the plan changes, has to carry every changed figure to each slide and lay it out readably, without ever seeing the slides it describes. Which of three models (GPT-6.1 Sol, Claude Opus 5.5, Muse Wonder Full) makes the decks that judge models prefer, and do ready-made layout blocks or pictures of its own draft help? 24 eight-slide decks on two tasks written for the study, judged from images: 72 individual scores and 288 head-to-head judgments of 48 deck pairs. | GPT-6.1 Sol's decks were preferred in every setup (81% to 96% win credit); Muse Wonder Full won none of its 96 head-to-head judgments. Most of GPT's lead over Claude came from one task, where all four Claude decks left a figure off the closing slide that only the judges' checklist asked for (GPT won 22 of 24 there; 12 to 9 with 3 ties on the other task). Pictures of the draft were preferred (61% win credit), layout blocks were not (38%), and neither passed the adoption rule set in advance. Two tasks, one deck per setup |

## Editing long documents

To change one number in a 40-page rule, a model can send back the whole document, which takes minutes and can quietly
straighten every quotation mark on the way, or only the change, which a program then has to merge in the right place
and which fails if the model quotes the text wrongly or leaves an occurrence out. Code editors built on language models
face the same choice each time they apply a suggestion. This experiment compares the ways of writing such edits and of
merging them.

| # | Notebook | Goal and question | Headline result |
|---|---|---|---|
| 38 | [How should a model send back its edits to a long document?](notebooks/38-long-text-edits/) | A model asked to change one number in a 12,000-word document can send back the whole document, which is slow and can change text nobody asked about, or only the change, which a program must then put in the right place. On 36 edit requests with exact answers in nine US Federal Register rules published in late October 2026 (1,842 to 12,762 words; one change, six mixed changes, renaming an abbreviation everywhere, twenty small changes), which of seven reply formats (the whole document, SEARCH/REPLACE blocks, JSON find-and-replace pairs, a unified diff, OpenAI's patch format, line-number edits, an edit sketch), merged in which way (exact, tolerant or fuzzy matching, `git apply`, GNU `patch`, a second model writing out the document, one retry with the error), most often gives exactly the requested document for five models (GPT-6.1 Sol, Claude Sonnet 5.5, Claude Haiku 5.5, DeepSeek V4.1 Flash, Qwen3.8 27B), and at what cost? | Find-and-replace pairs merged by exact match did best: 82% and 84% of 180 requests exact, 85% and 86% with one retry, in a median 17 seconds at every length; tolerant and fuzzy matching rescued none, because the failures were edits left out. Whole rewrites 81% (31 to 115 seconds), diffs 79% with a forgiving merge but 41% through plain `git apply`, line-number edits 78%, edit sketches 64%, OpenAI's patch format 59% at best. A second model writing out the merged document lost edits (57% for find-and-replace). Renames were find-and-replace's weak spot (51%, against 84% for rewrites). GPT-6.1 Sol was at the ceiling in three formats, so the ranking comes from the other four models |

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

Every notebook replays by default: open it and run all cells, or run
`jupyter nbconvert --to notebook --execute --inplace <notebook>.ipynb` from its folder. Replay reads the saved
responses in the notebook's `data/` folder, needs no key and makes no model call. Each notebook's README ends with
its exact commands, and the notebook's first code cell holds its size settings and spending caps.

The notebooks differ in what a missing saved response does. In 01 to 08 it is requested from the model at once, so
deleting a cache file starts a new, paid collection. From 09 on, a missing response stops the run, and new
collection has to be switched on as the table shows. Collecting with `claude`, `codex` or `muse` needs that
command-line tool installed and signed in.

| Notebook | Before replay | To collect again | Needs for collection |
|---|---|---|---|
| [01](notebooks/01-decisions-api-500-label-classification/) | Nothing extra | Delete `data/decisions_cache.jsonl`; `N_DOCS` sets the sample size | `OPENROUTER_API_KEY` |
| [02](notebooks/02-decisions-api-chunking/) | Downloads six public PDFs into `data/docs/` on first run | A missing request is sent at once; a different PDF or PyMuPDF version changes the request (`data/PROTOCOL.md` lists the versions that match) | `OPENROUTER_API_KEY` |
| [03](notebooks/03-document-type-classification/) | Downloads about 300 MB of PDFs on first run, each checked against its sha256 | A missing request is sent at once | `OPENROUTER_API_KEY` |
| [04](notebooks/04-industry-document-chunking/) | Downloads 12 PDFs on first run and stops if a sha256 differs | A missing request is sent at once | `OPENROUTER_API_KEY` |
| [05](notebooks/05-text-to-sql-safety/) | Nothing extra | Delete `data/cache_*.jsonl`; `NB_SMOKE=1` runs 6 requests | `OPENROUTER_API_KEY`; `claude`, `codex`, `muse` |
| [06](notebooks/06-car-make-model-from-image/) | Nothing extra; the photos are saved | Delete `data/cache_*.jsonl`; `NB_SMOKE=1` runs 6 photos; deleting `data/images.csv` and `data/images/` rebuilds the photo set from Wikipedia | `OPENROUTER_API_KEY`; `claude`, `codex`, `muse` |
| [07](notebooks/07-subagent-handoff-harness/) | Nothing extra | `NB_LIVE=1` reruns all seven levels (about 150 calls); deleting one file in `data/runs/` reruns that level; `BACKEND` switches the agents to `codex` or `muse` | `claude` |
| [08](notebooks/08-lab-requisition-extraction/) | Nothing extra | Delete `data/cache_*.jsonl`; `NB_SMOKE=1` runs 3 pages | `OPENROUTER_API_KEY`; `claude`, `codex`, `muse` |
| [09](notebooks/09-agent-action-safety/) | Nothing extra | `NB_LIVE=1`; `NB_SMOKE=1` runs two request pairs | `OPENROUTER_API_KEY`; `claude`, `codex` |
| [10](notebooks/10-code-execution-guardrails/) | Nothing extra; the notebook calls no model | `NB_RUN_CONTAINER=1` repeats the container probes, with an installed image pinned by digest named in `NB_SANDBOX_IMAGE` | A Linux Docker engine |
| [11](notebooks/judges/11-llm-judges/) | Nothing extra; `NB_JUDGE_PROFILE=smoke` replays a small subset | `NB_LIVE=1`, small profile by default; changed tasks or prompts go in a copy with a new protocol name | `claude`, `codex` |
| [12](notebooks/12-tax-research-harnesses/) | Nothing extra (the root requirements include `smolagents`) | `NB_LIVE=1`; a changed design goes in a new data folder | `OPENROUTER_API_KEY` |
| [13](notebooks/13-older-model-attribution/) | Python 3.13.5 and `requirements-replay.txt`; checks every data file against saved hashes | `NB_LIVE=1`, in a separate copy that leaves the committed cache intact | `OPENROUTER_API_KEY`; `claude`, `codex`, `muse` |
| [14](notebooks/14-tabular-zero-shot/) | Python 3.13 and `data/requirements-lock.txt` | `NB_LIVE=1`, under a computation-token cap; the notebook's section 9 lists the files to clear first | `PRIORLABS_API_KEY` |
| [15](notebooks/judges/15-analytical-writing-style/) | Nothing extra | `NB_LIVE=1`, in a copy with a new seed and protocol version; $10 OpenRouter cap | `OPENROUTER_API_KEY`; `claude`, `codex`, `muse` |
| [16](notebooks/16-time-series-zero-shot/) | Python 3.13, the notebook's own `requirements.txt` and kernel | `TS16_LIVE=1`; $3 cap | `TSFMAI_API_KEY` |
| [17](notebooks/judges/17-writing-validation-extension/) | The notebook's own `requirements.txt`, for the human study forms; completed forms in `data/human/submissions/` join the replay | `NB_LIVE=1`, in a copy with a new seed and protocol version; carries forward the $10 cap it shares with 15 | `OPENROUTER_API_KEY`; `claude`, `codex`, `muse` |
| [18](notebooks/18-decisions-api-comparison/) | `requirements-replay.txt` | In a separate copy: `NB18_LIVE=1` for the broad set, `NB18_FOLLOWUP_LIVE=1` for the ledgers and harder lookups; $5 guard per part | `OPENROUTER_API_KEY` |
| [19](notebooks/19-powerpoint-harness/) | The notebook's own `requirements.txt`; no PowerPoint; checks every evidence file against saved hashes | `harness.py` commands with `--live`; `--n-briefs`, `--max-calls` and `--pair-scope` set the size | Windows and PowerPoint; `claude`, `codex`, `muse` |
| [21](econ/21-verification-costs/) | `NB_PHASE=all`, with `NB_LIVE` unset | `NB_LIVE=1`, starting with two trial invoices | `OPENROUTER_API_KEY`; `claude`, `codex` |
| [22](econ/22-fiscal-implementation/) | Nothing extra; the saved excerpts replace the original downloads | `NB_REAL_V2_LIVE=1` asks two trial questions by default; `NB_REAL_V2_N_CASES` and `NB_REAL_V2_MAX_NEW_CALLS` set the size; capped at 180 requests and USD 20 of Claude list price | `claude`, `codex`, `muse` |
| [23](notebooks/23-synthetic-data-curation/) | Nothing extra | `NB_LIVE=1` or `NB_HARD_LIVE=1` runs a small collection into git-ignored `data/tmp/` | `codex` |
| [24](notebooks/24-openenv-rewards/) | The notebook's own `requirements.txt` and kernel; the puzzle environments run again locally | `NB_LIVE=1`, in a copy with empty `data/cache/` and `data/pilot_cache/`; caps of 600 requests and $2 | `OPENROUTER_API_KEY` |
| [25](notebooks/25-knowledge-work-rollouts/) | `requirements-replay.txt` | `NB25_LIVE=1`, in a new folder with the pinned OpenEnv source; steps in `data/PROTOCOL.md` | `OPENROUTER_API_KEY`; `codex` |
| [26](notebooks/26-model-auditability/) | Nothing extra; no Torch or model checkpoint | `NB26_LIVE=1`, in a copy, for hosted replies; `NB26_LOCAL=1` (and `NB26_DOWNLOAD=1` if the checkpoint is absent) recomputes the local probes into git-ignored `data/tmp/` | `OPENROUTER_API_KEY`; `codex`; optional packages for the local probes |
| [27](notebooks/27-adaptive-knowledge-rollouts/) | `requirements-replay.txt`; allow 1,800 seconds per cell | `requirements-live.txt` and the pinned OpenEnv source, in a new folder; steps and switches in `data/PROTOCOL.md` | `codex` |
| [28](notebooks/28-monitor-removal-honesty/) | Nothing extra | `NB_LIVE=1`; the prepared conversations are rebuilt only with `NB_REBUILD_TRACES=1` | `OPENROUTER_API_KEY`; `claude`, `codex` |
| [29](notebooks/29-theory-of-mind/) | Nothing extra; the stories are generated again in code | `NB_LIVE=1`; `N_PAIRS` sets the size; capped at USD 30 of OpenRouter spend and 15,000 `claude`, `codex` and `muse` calls | `OPENROUTER_API_KEY`; `claude`, `codex`, `muse` |
| [30](notebooks/30-workbook-to-statements/) | Nothing extra; the workbooks are regenerated in a temporary folder and checked against the frozen copies, and every saved program runs again | `NB_LIVE=1`; capped at 400 new calls and USD 60 of Claude list price | `claude`, `codex` |
| [31](notebooks/31-self-repairing-scrapers/) | Nothing extra; `NB_RERUN_PROGRAMS=1` also runs every saved program again and reports any difference | `NB_LIVE=1` | `OPENROUTER_API_KEY`; `claude`, `codex` |
| [35](notebooks/judges/35-judge-taste/) | The notebook's own `requirements.txt`; replays all 2,016 judgments from `data/cache/` | `NB_LIVE=1` judges two development pairs by default; `NB_PROFILE=full` for the frozen test; $5 OpenRouter cap | `OPENROUTER_API_KEY`; `claude`, `codex` |
| [38](notebooks/38-long-text-edits/) | Nothing extra; every merge method runs again on the cached replies (needs `git`, and GNU `patch` for that method) | `NB_LIVE=1`; `NB_N_DOCS` and `NB_MODELS` set the size; capped at 3,000 CLI calls, USD 80 of Claude list price and USD 15 of OpenRouter spend | `OPENROUTER_API_KEY`; `claude`, `codex` |

## Data and licences

Every notebook uses public data or data made for the experiment, with no private or client records. Code and text
in this repo are MIT licensed (see `LICENSE`).

New notebooks use data the models cannot have seen: data written or generated for the experiment, or public data
created after every tested model's training cutoff (for time series, the last one to two months). Notebooks 01-04
and 06 predate this rule. Their papers, documents and photos were public before the models, which may have seen them,
so treat those accuracy figures as upper bounds. Notebook 05's sample database has been public since 2014, so its
accuracy on ordinary questions is an upper bound too. Notebooks 01-04 were first run inside another project and moved
here with their data and caches.

| Notebook | Data | Fresh or older | Source and licence |
|---|---|---|---|
| 01 | 600 research-paper abstracts and 508 topic labels | Older: papers published 2020 to 2024 | OpenAlex, CC0 |
| 02 | Six public documents and 33 questions about them | Older: documents published 2017 to 2024 | Downloaded from the publishers; licences not recorded |
| 03 | 276 public PDFs of 78 document types | Older: most were public before the models | Address, sha256 and licence per file in `data/catalog/` |
| 04 | 12 public filings and 142 questions about them | Predates the rule: filings dated October 2021 to August 2026 | Licence per PDF in `data/catalog/`; the questions record no author, date or licence |
| 05 | The Chinook sample database of a music shop, and 52 requests | Database public since 2014; requests committed 17 October 2026 | Chinook, MIT-style licence |
| 06 | 146 Wikipedia lead photos of 73 car models | Older: mostly older than the models | Wikimedia Commons; licence and author per photo in `data/images.csv` |
| 07 | A trip-planning task, with prices and delays, written for the experiment | Fresh; no creation date recorded | This repository |
| 08 | 24 lab requisition pages generated in code, stamped SYNTHETIC with invalid identifiers | Fresh; creation date not recorded, and the blank form they fill in is public | This repository |
| 09 | 24 requests written for the experiment | Fresh: replies collected 17 October 2026 | This repository |
| 10 | 22 requests written for the experiment | Fresh: run 17 October 2026 | This repository |
| 11 | 144 grading tasks generated in code | Fresh: 22 October 2026 | This repository |
| 12 | 12 made-up companies and seven paraphrased reference sources | Fresh: 17 October 2026 | This repository; the original IRS documents are US government material |
| 13 | 100 model-written texts | Fresh: 19 October 2026 | Writer and provider per text in `data/corpus.csv` |
| 14 | 24 numeric tables generated in code | Fresh: 19 October 2026 | This repository |
| 15 | Two evidence packets generated in code | Fresh: 19 October 2026 | This repository |
| 16 | Six public series: IESO electricity demand, Open-Meteo weather analysis, Wikimedia page views and Bank of Canada exchange rates | Fresh: forecasts start between 20 August and 17 October 2026 | Per source in [ATTRIBUTION.md](notebooks/16-time-series-zero-shot/data/ATTRIBUTION.md) |
| 17 | 24 evidence packets generated in code, evidence copied from 15, and forms for a human study whose results are pending | Fresh: 21 October 2026 | This repository |
| 18 | Records, ledgers and lookups generated in code | Fresh: from 20 October 2026 | This repository ([ATTRIBUTION.md](notebooks/18-decisions-api-comparison/data/ATTRIBUTION.md)) |
| 19 | Two eight-slide deck tasks written for the study | Fresh: 21 October 2026 | This repository |
| 21 | 84 invoices generated in code | Fresh: 22 October 2026 | This repository |
| 22 | Excerpts from nine official UK, US and EU reports and releases | Fresh: published 13 to 22 October 2026 | Open Government Licence v3.0, US public domain, CC BY 4.0 or European Parliament reuse terms, per excerpt in `data/real_v2/sources.json` |
| 23 | Fictional order threads generated in code | Fresh: 24 October 2026 | [provenance.json](notebooks/23-synthetic-data-curation/data/provenance.json); the saved model outputs carry no claim of unrestricted training permission |
| 24 | 8 tasks generated with fixed seeds: 4 mazes and 4 Reasoning Gym questions | Fresh: 24 October 2026 | Maze environment MIT, Reasoning Gym Apache-2.0, OpenEnv BSD-3-Clause |
| 25 | 12 office tasks on a made-up calendar, IBM's quarterly results and US Treasury daily cash records | Fresh: tasks written 24 October 2026; results published 21 October, cash records 19 to 22 October | Calendar CC0; IBM copyright, numerical extracts only; Treasury data public domain |
| 26 | 32 made-up expense claims generated in code, and the Pythia-14M model checkpoint | Fresh: 24 October 2026 | Claims in this repository; Pythia-14M Apache-2.0, downloaded on demand |
| 27 | Fictional calendar and office tasks generated in code, worded by Claude Opus 5.5 | Fresh: 24 and 26 October 2026 | CC0; OpenEnv BSD-3-Clause |
| 28 | 15 prepared agent conversations over small code repositories written for the experiment, with the agent's words by Claude Haiku 5.5 | Fresh | This repository |
| 29 | 480 stories in 240 twin pairs over eight families, generated in code with exact answers, and six assistant requests written for the experiment | Fresh: 29 October 2026 | This repository |
| 30 | 20 fictional subsidiary workbooks generated in code, with exact answers | Fresh: 29 October 2026 | This repository |
| 31 | 20 fictional news sites built in code, with 240 release texts written by GPT-6.1 Sol | Fresh: releases dated 17 August to 23 October 2026, weekly runs 5 to 26 October 2026 | This repository |
| 35 | 88 paragraph pairs (earlier and merged versions) from this repository's README rewrites of 27 to 30 October 2026 | Fresh: lines dated 17 to 30 October 2026 | This repository (MIT) |
| 38 | Nine US Federal Register rules and proposed rules converted to Markdown, with 36 edit requests and their exact answers generated in code | Fresh: published 19 to 29 October 2026 | [Federal Register API](https://www.federalregister.gov/developers/documentation/api/v1); US government works, public domain |

## For AI agents

See [AGENTS.md](AGENTS.md): layout, the pull-request workflow, claiming a notebook number with an issue,
proposing an experiment as an issue, self-containment, fresh data with no training-set leakage, workflow
diagrams and explainers, the closing future-work and further-reading section, how to call models, and the writing
style (including LLM prose habits to avoid).
