# Economics experiments

A cheaper automated decision can become expensive if somebody has to check it or correct a missed error.
A government spending announcement can make a budget look larger even though no money has been paid.
These are economic measurement problems: the number that is easiest to collect is not always the number
needed for a decision.

The two experiments in this folder use fresh fictional records with answers calculated independently in
Python. The records let us distinguish model errors from uncertainty about the real world. Each notebook
has its own inputs, cached model responses, results, figures and explanation. Neither notebook imports code
from the other.

| Notebook | Question | What the experiment measures |
|---|---|---|
| [21. Verification costs](21-verification-costs/) | When do checking costs and missed mistakes erase the savings from a cheaper model? | Correct procurement decisions, errors that survive checking, escalation or review, and total cost under explicit price and loss assumptions. |
| [22. Fiscal implementation](22-fiscal-implementation/) | Can a model distinguish spending announcements, authorizations, corrections and cash payments across dated documents? | Errors in cumulative paid amounts, duplicate reporting and event timing, comparing direct answers with an extracted event ledger and deterministic reconciliation. |

## Results from this run

On 72 held-out invoices, Qwen returned 14 exact answers and GPT returned 72. Repeating Qwen or checking it
with Claude before escalating to GPT also produced 72 exact answers. Both routes avoided GPT only on the 14
zero-payment holds. At an assumed GPT price of USD 0.05 per invocation, the repeat route costs USD 0.04050 per
invoice; the Claude route costs USD 0.06618 using Claude's list-price equivalent. Claude checking therefore
erases the savings at that assumed price. The model calls had no calculator, Qwen's reasoning was disabled,
and a deterministic rule engine solved all 72 cases. These conditions limit the result to the tested workflows.

On 48 held-out fiscal histories, GPT direct and ledger methods each returned 48 exact cash histories. Claude
returned 47 with direct answers and 48 with a ledger. All 191 valid answers had the correct amounts, authority
and status. One Claude direct answer put prose before otherwise correct JSON and failed the strict format
rule. The ledger took longer and did not demonstrate better fiscal measurement on these explicit records.
All quarterly totals were reconstructed using the same September information set, including retrospective
corrections.

## Reading the experiments

Start with either linked README. It explains the topic, follows actual examples through the method and
interprets the charts without requiring Python. The executed notebook gives the same explanation alongside
the code and saved outputs.

An exact answer on these records is evidence about the tested conditions. It does not establish performance
on all invoices or public budgets. A price assigned to a missed payment error is an explicit scenario, not
an observed business loss. Reconstructing cash payments does not estimate the causal effect of government
spending on the economy.

## Reproducing the results

Install the repository's [requirements](../requirements.txt), change into the experiment's directory, and run
the notebook with `python -m jupyter nbconvert --to notebook --execute --inplace <notebook-name>.ipynb`.
Default execution replays the saved responses. Each experiment's README explains its small live profile,
call and spending caps, model access, and cache checks.

All model requests and results belong to the individual experiment folders. Closed models are called through
their command-line tools. Observed OpenRouter charges and Claude's reported list-price equivalent are kept
separate from subscription dollar charges that the command-line tools do not expose.

Across both experiments, 580 model requests were recorded, including development, wording authoring and
three retries. OpenRouter metered charges total USD 0.018873976. Claude's reported list-price equivalent totals
USD 5.2008564. Actual Claude and Codex subscription charges attributable to these requests are unknown, so
these amounts are not a complete cash bill. Both notebooks execute from their committed caches without
new model calls.
