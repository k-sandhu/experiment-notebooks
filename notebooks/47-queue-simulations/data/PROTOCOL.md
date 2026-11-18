# Protocol for six queue simulations

## 2026-11-18. Design before executing the full simulation

Question: how does adding one worker or analyzer at a named stage change waiting,
unfinished work at close and, for callers, abandonment when both policies receive
the same arrivals and service requirements?

These are terminating discrete-event simulations with synthetic inputs. Each
scenario starts empty. Five scenarios accept arrivals for eight staffed hours
and the software queue accepts arrivals for 40 staffed hours. All arrivals are
followed until completion or abandonment. Resources continue to work at the same
capacity after the cutoff solely to measure what remains and how long it would
take to clear it. This is not a model of paid overtime or calendar time.

Inputs and rules are fixed in the setup cell. For each time window draw a
Poisson arrival count and place arrivals uniformly within the window. The
passport has a deterministic additional appointment stream. Individual service
times come from gamma distributions. Analyzer runs take 22 minutes whether full
or partial. Use nonpreemptive priority for urgent tickets and passport
appointments, exponential patience for bank callers, and an independent
secondary referral draw in customs. The lab analyzer runs up to eight samples at
once, starting a full batch immediately or a partial batch after the oldest has
waited 15 minutes if an analyzer is free. All other queues use first-come,
first-served within a priority group. Service starts before a tied abandonment
deadline is applied. Waiting jobs and jobs in service at the exact cutoff count
as unfinished unless they exit by that instant.

Plan: 240 independent input periods per setting, with NumPy SeedSequence
[471118, scenario index, one-based period]. Replay each list once under each policy
with identical job attributes. Compute mean within-period p90 (90th percentile)
total queue wait among all eventually served jobs, zeros included. Secondary
measures are mean wait among the served, pooled abandonment rate among all
entrants, average unfinished jobs at close, median minutes to clear after close,
and stage utilization during the staffed period. Report the added-minus-baseline
difference in mean p90 and a 95% percentile interval from 4,000 bootstrap
resamples of the paired period differences. The settings and workloads are
illustrative, so intervals describe Monte Carlo sampling uncertainty only.
Compute pooled p90 by relevant job group for priority and referral settings.
Retain period 1 in each setting for time-series figures and job-level audit.
Use hand-computed path checks and conservation checks before interpreting output.

External model calls, Langfuse traces, input purchases and API spend: none (USD 0).
Claim: [#124](https://github.com/k-sandhu/experiment-notebooks/issues/124).


## 2026-11-18. Execution and descriptive case analysis

The full design yielded 1,440 input periods and 2,880 policy runs, incorporating
200,517 distinct generated arrivals. Every comparison had 240 usable paired
periods. No algorithm, sample or primary outcome was changed after execution.

After the full run, individual job changes were tabulated for the case analysis.
These are descriptive matched counts, reported in job_changes.csv. The first
bank period with a call that switched from answered to abandoned (period 3)
was archived alongside the six period 1 examples to make that exception
auditable. No case selection changed an aggregate result.

Environment: Python 3.13.5, NumPy 2.2.6, pandas 2.3.1, matplotlib 3.11.2,
nbformat 5.11.1, nbconvert 7.17.2 and ipykernel 7.4.0.
