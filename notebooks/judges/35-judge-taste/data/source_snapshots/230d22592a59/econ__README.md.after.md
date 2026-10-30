# Economics experiments

Economic decisions rest on numbers, and the number that is easiest to collect is often not the one the decision
needs. An invoice states an amount, but what an organisation owes depends on what was delivered, returned or
disputed. A government report can show an approved budget, a cost recorded in the accounts and a cash payment
for the same programme, and only one of them answers "how much was paid?". The two experiments in this folder
test language models on that kind of measurement, and both put a price on an extra step meant to make the work
checkable.

Each experiment is self-contained: its own notebook, inputs, cached model responses, results, figures and a
README that explains the topic from the beginning. Start with either README; neither depends on the other or on
this page.

## The cost of checking an assistant's work (21)

A finance team could let a cheap model propose each invoice payment and send only the doubtful ones to an
expensive model. That saves money only if checking the cheap answers costs less than the expensive calls it
avoids. The experiment generated 72 invoices with exact answers (58 to pay, 14 to hold) and compared using the
expensive model (GPT-6.1 Sol) on every invoice with two checked routes: asking the cheap model (Qwen3.8 Flash)
a second time, or having a stronger model (Claude Opus 5.5) review its answer, with every rejected invoice
passed to GPT.

The cheap model chose pay or hold correctly on all 72 invoices but gave the exact amount on none of the 58
payments. GPT and both checked routes were exact on 72 of 72, and neither check let a wrong payment through.
Because only the 14 holds could skip GPT, asking twice pays for itself once a GPT call costs more than
USD 0.0011, and the Claude review only above USD 0.1332 per call. Every wrong answer was far from the right
amount, so the checks never met a hard mistake, and a rules program got all 72 right.

## Reading what government spending figures mean (22)

A journalist or researcher who asks how much a government has paid needs the cash figure, not the budget or the
accounting expense printed beside it. The experiment gave three models (GPT-6.1 Sol, Claude Opus 5.5 and Muse
Wonder Full) the right pages of 8 recent UK, US and EU reports and 22 precise questions about money received,
paid or owed, six of them about amounts the report does not disclose. Each question was asked two ways: for the
figure directly, or as a ledger, a list of each figure used with its supporting passage, which a program then
added up.

Every completed answer was right, 131 of 131, with both methods. All 36 answers to the undisclosed questions
said the amount was not disclosed. The ledger added about 2.5 seconds per answer for GPT and Claude and changed
no answer, and 74 of its 76 quoted passages appear word for word in the source.

## What the two results have in common

Both experiments priced a step that shows the work: a second opinion in 21, a list of figures and quotations
in 22. In neither did the step buy measurable accuracy, for opposite reasons. In 21 the cheap model was so far
off that any check caught its mistakes, so nothing separated a cheap check from an expensive one. That is a
floor for the cheap model and a ceiling for the checks. In 22 the models were already right on every completed
answer, so there were no mistakes for the ledger to prevent. Both tests were too easy in one direction to answer
their own question, and each README says which harder test would.

| Notebook | The problem | The question | The answer in plain words |
|---|---|---|---|
| [21. The cost of checking an assistant's work](21-verification-costs/) | A cheap model saves money on invoice payments only if checking it costs less than the expensive calls it avoids | On 72 made-up invoices, does asking the cheap model twice, or having a stronger model review it, cost less than using the expensive model on every invoice, and above what price per expensive call? | The cheap model got no payment amount right, so checks saved a call only on the 14 holds. Asking twice pays off above USD 0.0011 per expensive call, a Claude review above USD 0.1332. The checks never met a hard mistake |
| [22. Reading what government spending figures mean](22-fiscal-implementation/) | A report shows budgets, expenses and cash payments side by side, and only one answers a given question | On 22 questions about 8 recent government reports, does listing each figure with its source passage give more correct answers than asking for the figure directly? | Both methods were right on every completed answer (131 of 131), a ceiling, so the test cannot tell them apart. The ledger cost a few seconds per answer |

## Limits that apply to both

An exact answer on these records is evidence about the tested conditions, not about all invoices or all public
budgets. In 21, the loss assigned to a wrong payment is a stated assumption, not an observed business loss. In
22, working out which figure is a cash payment does not estimate the effect of government spending on the
economy, and the models were given the right pages rather than asked to find them.

## Reproducing the results

Install the repository's [requirements](../requirements.txt), change into an experiment's folder and run
`python -m jupyter nbconvert --to notebook --execute --inplace <notebook-name>.ipynb`. By default each notebook
replays its saved responses and makes no model calls. Spend, call counts and the settings for collecting new
responses are in each experiment's README and its `data/PROTOCOL.md`.
