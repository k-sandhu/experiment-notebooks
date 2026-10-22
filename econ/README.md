# Economics experiments

A cheaper automated decision can become expensive if somebody has to check it or correct a missed error.
A government spending announcement can make a budget look larger even though no money has been paid.
These are economic measurement problems: the number that is easiest to collect is not always the number
needed for a decision.

The verification experiment uses fresh synthetic invoices with answers calculated in Python. The fiscal
experiment now uses nine recent public reports or releases and one updated publication-history record, with
answers checked against the sources. Its original synthetic pilot remains archived. Each notebook has its
own inputs, cached model responses, results, figures and explanation. Neither imports code from the other.

| Notebook | Question | What the experiment measures |
|---|---|---|
| [21. Verification costs](21-verification-costs/) | When do checking costs and missed mistakes erase the savings from a cheaper model? | Correct procurement decisions, errors that survive checking, escalation or review, and total cost under explicit price and loss assumptions. |
| [22. Fiscal measurement](22-fiscal-implementation/) | Does an evidence ledger improve answers about real reported amounts, accounting boundaries and missing payment disclosures? | Correct amounts/status on 22 held-out questions from 8 packets, paired method differences, literal evidence checks, latency and known list-equivalent cost. |

## Results from this run

On 72 held-out invoices, Qwen returned 14 exact answers and GPT returned 72. Repeating Qwen or checking it
with Claude before escalating to GPT also produced 72 exact answers. Both routes avoided GPT only on the 14
zero-payment holds. At an assumed GPT price of USD 0.05 per invocation, the repeat route costs USD 0.04050 per
invoice; the Claude route costs USD 0.06618 using Claude's list-price equivalent. Claude checking therefore
erases the savings at that assumed price. The model calls had no calculator, Qwen's reasoning was disabled,
and a deterministic rule engine solved all 72 cases. These conditions limit the result to the tested workflows.

On 22 held-out fiscal questions from eight packets, GPT-6.1 Sol: Direct 22/22, Ledger 22/22; Claude Opus 5.5: Direct 22/22, Ledger 22/22; Muse Wonder Full: Direct 21/22, Ledger 21/22. All 130 protocol-valid held-out answers were correct. Muse had one Direct timeout and one correct Ledger answer excluded after an internal CLI retry; no financial-answer advantage was demonstrated.
The test used Codex, Claude Code and Muse with the same evidence in both methods. It retained all failures,
including timeouts and extra model attempts, in the primary score. The source text includes gross/net figures, revisions,
cash-versus-accrual distinctions and six missing-disclosure questions. The small selected sample and supplied
excerpts limit conclusions about other documents or open-web retrieval. The earlier synthetic pilot also
found no financial-value advantage for the ledger once formatting was separated.

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

Across both experiments and the archived fiscal pilot, 730 CLI or OpenRouter invocations were recorded, including
development, wording authoring and earlier retries. The new real-document fiscal study contributes 150
CLI invocations and no runner-initiated retry or answer repair. Muse also retried internally on two held-out
invocations; one ended in a timeout and the other was excluded by the fixed run checks despite a correct final
answer. These invocation totals are not a count of all internal provider attempts. OpenRouter metered charges
remain USD 0.018873976. Claude's reported list-price
equivalent across the experiments totals USD 9.48575240, of which
USD 4.28489600 belongs to the new fiscal study. Actual Claude, Codex and Muse subscription
charges attributable to these requests are unknown, so these figures are not a complete cash bill. Both
current notebooks execute from their committed caches without new model calls.
