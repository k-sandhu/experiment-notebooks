"""Exact paired-McNemar power grid for the high-v4 repair study scale-up.

This is planning code only. It reads no study files, makes no model calls, and
writes only scale_power_plan.json and scale_power_plan.md beside this script.
Requires SciPy for stable binomial probabilities and exact binomial tails.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.special import bdtr, bdtrc
from scipy.stats import binom


HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / "scale_power_plan.json"
OUT_MD = HERE / "scale_power_plan.md"
ALPHA = 0.05
N_GRID = (200, 300, 400, 500, 600)
DELTA_GRID = (0.05, 0.08, 0.10, 0.1333)
DISCORDANCE_GRID = (0.25, 0.35, 0.50)


def exact_mcnemar_critical_lowers(max_n: int, alpha: float = ALPHA) -> np.ndarray:
    """Largest x <= k/2 with two-sided exact null p <= alpha, for each k."""
    critical = np.full(max_n + 1, -1, dtype=int)
    for k in range(1, max_n + 1):
        for x in range(k // 2 + 1):
            if 2.0 * float(bdtr(x, k, 0.5)) <= alpha + 1e-14:
                critical[k] = x
            else:
                break
    return critical


def exact_paired_power(
    n_pairs: int,
    discordance: float,
    recovery_difference: float,
    critical_lowers: np.ndarray | None = None,
    alpha: float = ALPHA,
) -> float:
    """Power of two-sided exact McNemar under specified paired probabilities.

    ``discordance`` is P(only one arm succeeds). ``recovery_difference`` is
    P(repair-only success) - P(fresh-only success). Thus the conditional chance
    that a discordant pair favors repair is (discordance + difference) /
    (2 * discordance). The discordant count is Binomial(n_pairs, discordance).
    """
    d = float(discordance)
    delta = float(recovery_difference)
    if not (0.0 < d <= 1.0):
        raise ValueError("discordance must be in (0, 1]")
    if abs(delta) > d:
        raise ValueError("absolute recovery difference cannot exceed discordance")
    if n_pairs < 1:
        raise ValueError("n_pairs must be positive")
    if critical_lowers is None or len(critical_lowers) <= n_pairs:
        critical_lowers = exact_mcnemar_critical_lowers(n_pairs, alpha)

    k = np.arange(n_pairs + 1)
    lo = critical_lowers[: n_pairs + 1]
    valid = (k > 0) & (lo >= 0)
    k = k[valid]
    lo = lo[valid]
    p_favors_repair = (d + delta) / (2.0 * d)

    # Conditional rejection probability sums the two symmetric exact tails.
    conditional_reject = bdtr(lo, k, p_favors_repair) + bdtrc(
        k - lo - 1, k, p_favors_repair
    )
    return float(np.dot(binom.pmf(k, n_pairs, d), conditional_reject))


def exact_positive_direction_power(
    n_pairs: int,
    discordance: float,
    recovery_difference: float,
    critical_lowers: np.ndarray | None = None,
    alpha: float = ALPHA,
) -> float:
    """Power for positive effect plus two-sided exact McNemar rejection."""
    d = float(discordance)
    delta = float(recovery_difference)
    if not (0.0 < d <= 1.0):
        raise ValueError("discordance must be in (0, 1]")
    if not (0.0 <= delta <= d):
        raise ValueError("positive-direction recovery difference must be in [0, discordance]")
    if n_pairs < 1:
        raise ValueError("n_pairs must be positive")
    if critical_lowers is None or len(critical_lowers) <= n_pairs:
        critical_lowers = exact_mcnemar_critical_lowers(n_pairs, alpha)
    k = np.arange(n_pairs + 1)
    lo = critical_lowers[: n_pairs + 1]
    valid = (k > 0) & (lo >= 0)
    k, lo = k[valid], lo[valid]
    p_favors_repair = (d + delta) / (2.0 * d)
    # X >= k-lo is the repair-favoring rejection tail of the two-sided test.
    conditional_reject = bdtrc(k - lo - 1, k, p_favors_repair)
    return float(np.dot(binom.pmf(k, n_pairs, d), conditional_reject))


def build_plan() -> dict:
    critical = exact_mcnemar_critical_lowers(max(N_GRID))
    rows = []
    for delta in DELTA_GRID:
        for discordance in DISCORDANCE_GRID:
            rows.append(
                {
                    "true_recovery_difference": delta,
                    "discordance_probability": discordance,
                    "primary_positive_direction_power_by_n_pairs": {
                        str(n): exact_positive_direction_power(
                            n, discordance, delta, critical_lowers=critical
                        )
                        for n in N_GRID
                    },
                    "two_sided_any_direction_power_by_n_pairs": {
                        str(n): exact_paired_power(
                            n, discordance, delta, critical_lowers=critical
                        )
                        for n in N_GRID
                    },
                }
            )

    observed_v4 = {
        "repair_only": 10,
        "fresh_only": 4,
        "discordant_pairs": 14,
        "pairs": 45,
        "difference": 6 / 45,
        "discordance": 14 / 45,
        "note": "Planning reference only; these estimates are noisy and conditional on v4's selected failure cohort.",
    }
    # The recommended n is the first requested grid point with >=90% power at
    # delta=.10 for every requested discordance value.
    recommendation = next(
        n
        for n in N_GRID
        if min(
            exact_paired_power(n, d, 0.10, critical_lowers=critical)
            for d in DISCORDANCE_GRID
        )
        >= 0.90
    )
    v4_failure_rate = 45 / 240
    sizing_scenario_cap = 3600
    probability_reach_target_at_v4_rate = float(
        binom.sf(recommendation - 1, sizing_scenario_cap, v4_failure_rate)
    )
    return {
        "purpose": "Prospective planning for a paired repair-package versus fresh-retry comparison; no model calls or study data changes.",
        "test": {
            "name": "two-sided exact conditional McNemar test",
            "alpha": ALPHA,
            "paired_unit": "one distinct eligible original-failure source case, sent to both arms",
            "primary_outcome": "all seven values correct with valid schema; citation acceptance is secondary",
            "alternative": "repair-only success probability minus fresh-only success probability equals the listed true difference",
            "discordance": "probability that exactly one of the paired arms succeeds",
        },
        "assumptions": {
            "case_pairs_independent": True,
            "generator_scope": "Power is nominal conditional on independent case pairs from this fixed generator. The current six scenario variants share one generator program; they are not six independent template programs.",
            "fixed_true_discordance_per_scenario": True,
            "fixed_true_difference_per_scenario": True,
            "no_interim_peeking": True,
            "no_adjustment_for_clustering": "Power is exact only for independent case pairs from the fixed generator. The six current scenario variants share one generator program and do not provide six independent program clusters. Family-stratified descriptive results can be reported, but broader-template validation is future work, not implemented here.",
            "failure_cohort": "Condition on valid-schema original value failures, defined before any intervention outcomes are inspected. The target count may drive original-case accrual only; it may not be changed based on the repair-versus-retry difference.",
            "estimand": "Recovery conditional on the specified original-failure cohort, not ordinary-stream accuracy or a training gain.",
        },
        "planning_reference_v4": observed_v4,
        "grid": {
            "n_pairs": list(N_GRID),
            "true_differences": list(DELTA_GRID),
            "discordance_probabilities": list(DISCORDANCE_GRID),
            "rows": rows,
        },
        "recommendation": {
            "fixed_eligible_failure_pairs": recommendation,
            "worthwhile_difference": 0.10,
            "minimum_primary_positive_direction_power_over_requested_discordances": min(
                exact_positive_direction_power(recommendation, d, 0.10, critical_lowers=critical)
                for d in DISCORDANCE_GRID
            ),
            "minimum_two_sided_any_direction_power_over_requested_discordances": min(
                exact_paired_power(recommendation, d, 0.10, critical_lowers=critical)
                for d in DISCORDANCE_GRID
            ),
            "reason": "600 is the first requested cohort size with at least 90% power for the preregistered positive-difference plus two-sided exact-test criterion at all three requested discordance rates. A smaller realized difference can still be inconclusive.",
            "accrual_rule": "Adopted protocol: accrue original cases in an initial 512-case tranche, then fixed 256-case tranches up to a hard cap of 2,048 originals. Stop accrual only when 600 eligible original failures are frozen or the cap is reached. Eligibility is a schema-valid original answer with at least one wrong value. If the cap yields fewer than 600 failures, run the paired comparison on the attained cohort and report it as underpowered/inconclusive; never extend based on intervention outcomes. The 3,600-case value is retained only as a sizing scenario, not the adopted cap.",
            "planning_failure_rate_reference": v4_failure_rate,
            "adopted_original_case_cap": 2048,
            "original_case_tranches": [512, 256],
            "expected_eligible_failures_at_adopted_cap_if_v4_rate_persisted": 2048 * v4_failure_rate,
            "sizing_scenario_original_case_cap": sizing_scenario_cap,
            "sizing_scenario_probability_reach_600_at_v4_rate": probability_reach_target_at_v4_rate,
            "adopted_pilot_max_requests": 32,
            "adopted_audit_cases": 96,
            "maximum_planned_cli_requests": 3376,
            "v4_excluded_from_inference": True,
            "new_case_id_requirement": "All selected scale-up case IDs must be new and non-overlapping with v1, hard-v2, v3, and v4 source/pilot corpora; compare semantic hashes where representations support a compatible comparison.",
            "arms": "Each selected original failure receives one fresh retry and one repair-package attempt; the latter receives the exact old answer plus generic verified failed-field flags. This estimates the package versus another attempt, not the isolated effect of feedback.",
            "cost_note": "The planned cohort implies 1,200 intervention item attempts, plus original-case accrual and audit calls. Actual CLI calls, tokens, and elapsed time depend on batching and must be reported; USD cost is unknown unless the CLI supplies a defensible charge.",
        },
        "main_preregistration": {
            "status": "fixed before scale-up model calls",
            "cohort_target": 600,
            "original_case_cap": 2048,
            "original_case_tranches": [512, 256],
            "eligibility": "schema-valid original answer with at least one incorrect typed value; citation-only, schema, transport, and unusable responses are excluded from the eligible failure cohort",
            "selection": "After each original tranche, identify only eligible cases by the frozen value-failure rule. At the stop, freeze exactly 600 eligible case IDs if at least 600 are available; if fewer, freeze all available. If a tranche produces more eligible cases than needed, choose with the recorded predeclared seeded ranking, independent of error magnitude and intervention outcomes. All IDs and semantic source records must be new and non-overlapping with v1, hard-v2, v3, and v4 corpora, using compatible semantic comparisons where possible.",
            "paired_arms": "one fresh retry and one feedback-repair request per selected case; same original source and verifier; repair package contains the original output plus generic verified failed-field labels, but no gold value or calculation trace",
            "primary_outcome": "valid schema and all seven exact typed values",
            "primary_effect": "paired recovery difference = repair success proportion minus fresh-retry success proportion among selected original failures",
            "primary_success_criterion": "positive paired recovery difference AND two-sided exact conditional McNemar p < 0.05",
            "confidence_interval": "report paired case-level percentile bootstrap 95% interval for the recovery difference; resample whole paired cases, 20,000 replicates, fixed seed 246600; report interval regardless of primary test result",
            "secondary_outcome": "full acceptance including evidence citations; report separately and do not replace primary outcome",
            "stopping_and_peeking": "no interim intervention-outcome inspection or efficacy stopping; original accrual may stop only when 600 eligible failures are frozen or 2,048 originals are exhausted; the 96-case audit and up-to-32 pilot are separate and excluded from paired efficacy inference",
            "prior_data": "All v1, hard-v2, v3, and v4 results are excluded from scale-up inferential analysis; v4 is used only as a planning reference.",
            "cluster_sensitivity": "The six scenario variants share one generator program. Report family-stratified results descriptively; they do not estimate between-program variation. Broader-template validation is future work, not implemented. The exact McNemar power grid is nominal conditional on independent case pairs from this fixed generator.",
            "maximum_planned_cli_requests": 3376,
            "request_count_arithmetic": "2,048 original + 96 audit + 32 pilot + 2*600 intervention requests; this counts planned CLI requests, not internal subprocess retries",
            "seed_policy": "Record source-generation, case-ranking, and bootstrap seeds in the frozen protocol before any scale-up model call; bootstrap seed is fixed here as 246600."
        },
        "randomness": {
            "power_calculation": "Deterministic exact enumeration; no simulation is used and no random seed applies to power values.",
            "future_cohort_seed": "Predeclare and record separate seeds for source generation and the failure-case ranking before calls; do not select by intervention outcomes or error magnitude.",
        },
        "software": {
            "python": "3.13-compatible",
            "scipy": "1.17.0 used for this saved calculation",
            "calculation": "For K discordant pairs, X repair-only wins is Binomial(K, (D+delta)/(2D)); K is Binomial(N,D). The primary probability sums only the repair-favoring tail that also passes the two-sided exact McNemar boundary; the optional any-direction probability sums both tails.",
        },
    }


def write_reports(plan: dict) -> None:
    OUT_JSON.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    rec = plan["recommendation"]["fixed_eligible_failure_pairs"]
    grid = plan["grid"]
    lines = [
        "# Paired recovery scale-up: power and design",
        "",
        "## Recommendation",
        "",
        f"Target **{rec} eligible original-failure cases**, with one fresh retry and one feedback-repair attempt on each case. At a 10 percentage-point recovery difference, this gives at least {plan['recommendation']['minimum_primary_positive_direction_power_over_requested_discordances']:.1%} power for the preregistered criterion across discordance scenarios 0.25, 0.35 and 0.50: a positive repair-minus-fresh difference and a two-sided exact McNemar p-value below 0.05. Five hundred pairs reach only 87.7% for this criterion at discordance 0.50, so 600 is the first requested grid size that clears 90% throughout the range.",
        "",
        "This is nominal power conditional on independent paired cases from the fixed generator. The current six scenario variants share one generator program; they are not six independent template programs. Family-stratified results can be shown descriptively, but broader-template validation is not implemented. Validation across independently authored programs remains future work, and shared generator structure can lower effective power.",
        "",
        "The adopted protocol caps original accrual at 2,048 cases: start with 512, then add fixed 256-case tranches. Stop only when 600 eligible original failures are frozen or the cap is reached. At v4's observed 18.75% eligible-failure rate, 2,048 originals would yield 384 failures on average, so this cap may leave the study short of its power target. That rate is only a planning reference; the harder source distribution may differ. If the cap yields fewer than 600 failures, report the attained paired sample and treat the test as underpowered or inconclusive. Never extend because interim repair results look favorable.",
        "",
        "The earlier 3,600-case figure remains a sizing scenario, not the adopted cap. Under a simple independent binomial calculation that assumes the v4 18.75% failure rate repeats, 3,600 originals would have a 99.95% chance of yielding at least 600 failures. This is not a forecast. The adopted run also has up to 96 separate audit cases and 32 pilot requests; neither contributes to the intervention inference.",
        "",
        "The adopted cap implies at most 3,376 planned CLI requests: 2,048 originals, 96 audit cases, 32 pilot requests, and 1,200 paired intervention requests. It compares a repair package (old answer plus field feedback) with a fresh attempt, not feedback isolated from seeing the old answer. This request count excludes internal CLI subprocess retries. Collect token and time totals because equal call counts do not imply equal compute; USD cost is unknown unless reported by the CLI.",
        "",
        "## Deterministic main preregistration",
        "",
        "The primary analysis uses only new scale-up cases. All selected case IDs and semantic source records must be new and non-overlapping with v1, hard-v2, v3, and v4, comparing compatible semantic hashes where available. Earlier results are excluded from this inference; v4 is a planning reference only. Pilot and audit requests are also excluded from the paired intervention test.",
        "",
        "The target is 600 distinct eligible original-failure cases. Eligibility means a valid-schema original answer with at least one incorrect typed value. Citation-only failures, schema failures, transport errors, and unusable responses do not enter this cohort. Cases accrue in an initial 512-original tranche followed by fixed 256-original tranches, stopping at 600 eligible failures or 2,048 originals, whichever comes first. The separate audit has 96 cases; the pilot is capped at 32 requests and checks service health and source solvability only.",
        "",
        "Before intervention calls, freeze the selected IDs with a recorded seed/ranking independent of intervention outcomes and error magnitude. If a tranche yields more eligible failures than needed, select exactly 600 with that ranking; if fewer than 600 accrue by the cap, freeze all eligible cases. All selected IDs and semantic records must be new and non-overlapping with prior corpora. Each selected source gets one fresh retry and one feedback-repair attempt. Repair receives the exact original answer and generic verified failed-field labels, but no gold values or calculation traces. No intervention outcomes are inspected until the fixed cohort or cap is complete.",
        "",
        "The primary outcome is a valid-schema response with all seven typed values correct. For each case, define the paired difference as repair success minus fresh-retry success. The primary success criterion is a positive observed paired difference and a two-sided exact conditional McNemar p-value below 0.05. Report the paired case-level percentile-bootstrap 95% interval regardless of the test result, resampling whole paired cases with 20,000 replicates and seed 246600. Full acceptance including evidence citations is a separate secondary outcome; it does not replace the all-value primary outcome.",
        "",
        "The exact power grid assumes independent case pairs from this fixed generator. Its six current scenario variants share one generator program, so family-stratified results are descriptive and do not estimate between-program variation. Broader-template validation remains future work. If fewer than 600 eligible failures accrue by the cap, use the attained cohort and label the result underpowered or inconclusive; do not raise the cap because the paired difference appears promising. The 10-point effect is the planning alternative, not a promised gain or a minimum effect that will be observed.",
        "",
        "",
        "## Exact power grid",
        "",
        "Each primary cell is the exact probability of satisfying both parts of the preregistered criterion: repair has a positive paired difference and the two-sided conditional McNemar test rejects at 5%. The optional any-direction two-sided power grid follows separately. Both assume independent case pairs, fixed discordance D, and paired difference δ = P(repair-only success) − P(fresh-only success). The v4 planning reference was 10 repair-only and 4 fresh-only outcomes in 45 selected cases (14/45 discordant, observed difference 6/45); that small selected cohort is not a precise estimate of future D or δ.",
        "",
        "### Primary criterion: positive difference plus two-sided p < 0.05",
        "",
        "| True difference | Discordance | " + " | ".join(str(n) for n in grid["n_pairs"]) + " |",
        "|---:|---:|" + "---:|" * len(grid["n_pairs"]),
    ]
    for row in grid["rows"]:
        vals = " | ".join(f"{row['primary_positive_direction_power_by_n_pairs'][str(n)]:.1%}" for n in grid["n_pairs"])
        lines.append(f"| {row['true_recovery_difference']:.2%} | {row['discordance_probability']:.0%} | {vals} |")
    lines += [
        "",
        "### Optional two-sided power: either effect direction",
        "",
        "This secondary calculation counts rejection in either direction and does not require a positive repair-minus-fresh difference. The primary recommendation uses the table above.",
        "",
        "| True difference | Discordance | " + " | ".join(str(n) for n in grid["n_pairs"]) + " |",
        "|---:|---:|" + "---:|" * len(grid["n_pairs"]),
    ]
    for row in grid["rows"]:
        vals = " | ".join(f"{row['two_sided_any_direction_power_by_n_pairs'][str(n)]:.1%}" for n in grid["n_pairs"])
        lines.append(f"| {row['true_recovery_difference']:.2%} | {row['discordance_probability']:.0%} | {vals} |")
    lines += [
        "",
        "A 10-point difference is the planning effect, not a claim that a 10-point gain is guaranteed or the smallest effect worth detecting. At 600 pairs and discordance 0.50, power is 38.8% for a 5-point difference and 77.8% for an 8-point difference. A nonsignificant result at 600 therefore remains compatible with smaller gains.",
        "",
        "## Method and design safeguards",
        "",
        "The calculation exactly sums over the number of discordant pairs K ~ Binomial(N, D). Conditional on K, repair-only wins follow Binomial(K, (D + δ)/(2D)). For each K, the two-sided exact binomial test sets the critical boundary under equal arm success probability. Primary power sums only the repair-favoring rejection tail; optional power sums both rejection tails. The calculation is deterministic; no Monte Carlo seed is used. SciPy 1.17.0 supplies stable binomial probabilities and tails. Full inputs and both grids are in [scale_power_plan.json](scale_power_plan.json).",
        "",
        "Treat each distinct source case as the paired unit. Do not count duplicate renderings or repeated draws as separate pairs. Define the primary outcome as valid schema plus all seven exact values; report citation acceptance secondarily. Fix the prompt, model alias, reasoning effort, tools, retry behavior, and verifier before the main run. Use the same case and verifier for both arms, and retain the complete request, output, token usage, elapsed time, and failure status.",
        "",
        "Pilot only for service health and source solvability, not for estimating the intervention advantage. Main-case accrual may be conditioned on original value failures because those are the target population; never inspect paired outcomes until the fixed cohort or cap is complete. If the adopted 2,048-case cap or a service-health rule prevents reaching 600 pairs, state that plainly and do not silently replace it with an easier source set.",
        "",
        "The v4 observed difference was 13.33 points, but the sample contained only 14 discordant pairs and was selected after a difficulty pilot. This calculation does not convert that observed difference into a forecast. The next experiment should create harder, answerable cases from more independent templates and estimate recovery on a predeclared cohort.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    plan = build_plan()
    write_reports(plan)
    print(json.dumps({
        "recommendation_n": plan["recommendation"]["fixed_eligible_failure_pairs"],
        "minimum_primary_positive_direction_power_at_10pp": plan["recommendation"]["minimum_primary_positive_direction_power_over_requested_discordances"],
        "minimum_two_sided_any_direction_power_at_10pp": plan["recommendation"]["minimum_two_sided_any_direction_power_over_requested_discordances"],
        "json": str(OUT_JSON),
        "markdown": str(OUT_MD),
    }, indent=2))
