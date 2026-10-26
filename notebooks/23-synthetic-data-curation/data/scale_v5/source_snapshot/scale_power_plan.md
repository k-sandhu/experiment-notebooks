# Paired recovery scale-up: power and design

## Recommendation

Target **600 eligible original-failure cases**, with one fresh retry and one feedback-repair attempt on each case. At a 10 percentage-point recovery difference, this gives at least 92.9% power for the preregistered criterion across discordance scenarios 0.25, 0.35 and 0.50: a positive repair-minus-fresh difference and a two-sided exact McNemar p-value below 0.05. Five hundred pairs reach only 87.7% for this criterion at discordance 0.50, so 600 is the first requested grid size that clears 90% throughout the range.

This is nominal power conditional on independent paired cases from the fixed generator. The current six scenario variants share one generator program; they are not six independent template programs. Family-stratified results can be shown descriptively, but broader-template validation is not implemented. Validation across independently authored programs remains future work, and shared generator structure can lower effective power.

The adopted protocol caps original accrual at 2,048 cases: start with 512, then add fixed 256-case tranches. Stop only when 600 eligible original failures are frozen or the cap is reached. At v4's observed 18.75% eligible-failure rate, 2,048 originals would yield 384 failures on average, so this cap may leave the study short of its power target. That rate is only a planning reference; the harder source distribution may differ. If the cap yields fewer than 600 failures, report the attained paired sample and treat the test as underpowered or inconclusive. Never extend because interim repair results look favorable.

The earlier 3,600-case figure remains a sizing scenario, not the adopted cap. Under a simple independent binomial calculation that assumes the v4 18.75% failure rate repeats, 3,600 originals would have a 99.95% chance of yielding at least 600 failures. This is not a forecast. The adopted run also has up to 96 separate audit cases and 32 pilot requests; neither contributes to the intervention inference.

The adopted cap implies at most 3,376 planned CLI requests: 2,048 originals, 96 audit cases, 32 pilot requests, and 1,200 paired intervention requests. It compares a repair package (old answer plus field feedback) with a fresh attempt, not feedback isolated from seeing the old answer. This request count excludes internal CLI subprocess retries. Collect token and time totals because equal call counts do not imply equal compute; USD cost is unknown unless reported by the CLI.

## Deterministic main preregistration

The primary analysis uses only new scale-up cases. All selected case IDs and semantic source records must be new and non-overlapping with v1, hard-v2, v3, and v4, comparing compatible semantic hashes where available. Earlier results are excluded from this inference; v4 is a planning reference only. Pilot and audit requests are also excluded from the paired intervention test.

The target is 600 distinct eligible original-failure cases. Eligibility means a valid-schema original answer with at least one incorrect typed value. Citation-only failures, schema failures, transport errors, and unusable responses do not enter this cohort. Cases accrue in an initial 512-original tranche followed by fixed 256-original tranches, stopping at 600 eligible failures or 2,048 originals, whichever comes first. The separate audit has 96 cases; the pilot is capped at 32 requests and checks service health and source solvability only.

Before intervention calls, freeze the selected IDs with a recorded seed/ranking independent of intervention outcomes and error magnitude. If a tranche yields more eligible failures than needed, select exactly 600 with that ranking; if fewer than 600 accrue by the cap, freeze all eligible cases. All selected IDs and semantic records must be new and non-overlapping with prior corpora. Each selected source gets one fresh retry and one feedback-repair attempt. Repair receives the exact original answer and generic verified failed-field labels, but no gold values or calculation traces. No intervention outcomes are inspected until the fixed cohort or cap is complete.

The primary outcome is a valid-schema response with all seven typed values correct. For each case, define the paired difference as repair success minus fresh-retry success. The primary success criterion is a positive observed paired difference and a two-sided exact conditional McNemar p-value below 0.05. Report the paired case-level percentile-bootstrap 95% interval regardless of the test result, resampling whole paired cases with 20,000 replicates and seed 246600. Full acceptance including evidence citations is a separate secondary outcome; it does not replace the all-value primary outcome.

The exact power grid assumes independent case pairs from this fixed generator. Its six current scenario variants share one generator program, so family-stratified results are descriptive and do not estimate between-program variation. Broader-template validation remains future work. If fewer than 600 eligible failures accrue by the cap, use the attained cohort and label the result underpowered or inconclusive; do not raise the cap because the paired difference appears promising. The 10-point effect is the planning alternative, not a promised gain or a minimum effect that will be observed.


## Exact power grid

Each primary cell is the exact probability of satisfying both parts of the preregistered criterion: repair has a positive paired difference and the two-sided conditional McNemar test rejects at 5%. The optional any-direction two-sided power grid follows separately. Both assume independent case pairs, fixed discordance D, and paired difference δ = P(repair-only success) − P(fresh-only success). The v4 planning reference was 10 repair-only and 4 fresh-only outcomes in 45 selected cases (14/45 discordant, observed difference 6/45); that small selected cohort is not a precise estimate of future D or δ.

### Primary criterion: positive difference plus two-sided p < 0.05

| True difference | Discordance | 200 | 300 | 400 | 500 | 600 |
|---:|---:|---:|---:|---:|---:|---:|
| 5.00% | 25% | 25.0% | 36.7% | 47.9% | 57.7% | 66.3% |
| 5.00% | 35% | 18.9% | 27.6% | 36.3% | 44.3% | 51.8% |
| 5.00% | 50% | 14.4% | 20.7% | 26.9% | 33.0% | 38.8% |
| 8.00% | 25% | 57.8% | 76.7% | 88.2% | 94.3% | 97.4% |
| 8.00% | 35% | 43.8% | 61.7% | 75.2% | 84.4% | 90.4% |
| 8.00% | 50% | 32.4% | 46.9% | 59.5% | 69.7% | 77.8% |
| 10.00% | 25% | 78.7% | 92.9% | 97.9% | 99.4% | 99.9% |
| 10.00% | 35% | 63.2% | 81.6% | 91.6% | 96.3% | 98.5% |
| 10.00% | 50% | 47.9% | 66.3% | 79.2% | 87.7% | 92.9% |
| 13.33% | 25% | 96.8% | 99.7% | 100.0% | 100.0% | 100.0% |
| 13.33% | 35% | 88.1% | 97.3% | 99.5% | 99.9% | 100.0% |
| 13.33% | 50% | 73.6% | 89.6% | 96.3% | 98.8% | 99.6% |

### Optional two-sided power: either effect direction

This secondary calculation counts rejection in either direction and does not require a positive repair-minus-fresh difference. The primary recommendation uses the table above.

| True difference | Discordance | 200 | 300 | 400 | 500 | 600 |
|---:|---:|---:|---:|---:|---:|---:|
| 5.00% | 25% | 25.0% | 36.7% | 47.9% | 57.7% | 66.3% |
| 5.00% | 35% | 19.0% | 27.7% | 36.3% | 44.3% | 51.8% |
| 5.00% | 50% | 14.6% | 20.8% | 26.9% | 33.0% | 38.8% |
| 8.00% | 25% | 57.8% | 76.7% | 88.2% | 94.3% | 97.4% |
| 8.00% | 35% | 43.8% | 61.7% | 75.2% | 84.4% | 90.4% |
| 8.00% | 50% | 32.4% | 46.9% | 59.5% | 69.7% | 77.8% |
| 10.00% | 25% | 78.7% | 92.9% | 97.9% | 99.4% | 99.9% |
| 10.00% | 35% | 63.2% | 81.6% | 91.6% | 96.3% | 98.5% |
| 10.00% | 50% | 47.9% | 66.3% | 79.2% | 87.7% | 92.9% |
| 13.33% | 25% | 96.8% | 99.7% | 100.0% | 100.0% | 100.0% |
| 13.33% | 35% | 88.1% | 97.3% | 99.5% | 99.9% | 100.0% |
| 13.33% | 50% | 73.6% | 89.6% | 96.3% | 98.8% | 99.6% |

A 10-point difference is the planning effect, not a claim that a 10-point gain is guaranteed or the smallest effect worth detecting. At 600 pairs and discordance 0.50, power is 38.8% for a 5-point difference and 77.8% for an 8-point difference. A nonsignificant result at 600 therefore remains compatible with smaller gains.

## Method and design safeguards

The calculation exactly sums over the number of discordant pairs K ~ Binomial(N, D). Conditional on K, repair-only wins follow Binomial(K, (D + δ)/(2D)). For each K, the two-sided exact binomial test sets the critical boundary under equal arm success probability. Primary power sums only the repair-favoring rejection tail; optional power sums both rejection tails. The calculation is deterministic; no Monte Carlo seed is used. SciPy 1.17.0 supplies stable binomial probabilities and tails. Full inputs and both grids are in [scale_power_plan.json](scale_power_plan.json).

Treat each distinct source case as the paired unit. Do not count duplicate renderings or repeated draws as separate pairs. Define the primary outcome as valid schema plus all seven exact values; report citation acceptance secondarily. Fix the prompt, model alias, reasoning effort, tools, retry behavior, and verifier before the main run. Use the same case and verifier for both arms, and retain the complete request, output, token usage, elapsed time, and failure status.

Pilot only for service health and source solvability, not for estimating the intervention advantage. Main-case accrual may be conditioned on original value failures because those are the target population; never inspect paired outcomes until the fixed cohort or cap is complete. If the adopted 2,048-case cap or a service-health rule prevents reaching 600 pairs, state that plainly and do not silently replace it with an easier source set.

The v4 observed difference was 13.33 points, but the sample contained only 14 discordant pairs and was selected after a difficulty pilot. This calculation does not convert that observed difference into a forecast. The next experiment should create harder, answerable cases from more independent templates and estimate recovery on a predeclared cohort.
