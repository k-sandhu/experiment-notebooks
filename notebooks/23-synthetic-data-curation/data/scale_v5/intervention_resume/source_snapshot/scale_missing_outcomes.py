"""Pure amendment-002 analysis. No file access, model calls or missing answers.

Execute after frozen experiment definitions, or supply paired_statistics explicitly.
All inputs must describe the final interventions_complete bundle. Sensitivity
assignments are hypothetical binary outcomes, never reconstructed model responses.
"""
from collections import Counter as _SMCounter
from itertools import product as _sm_product
import math as _sm_math
import random as _sm_random

SCALE_MISSING_VERSION = "23-scale-v5-missing-outcomes-v1"
SCALE_MISSING_ARMS = ("fresh_retry", "feedback_repair")


def scale_missing_good(row):
    return bool(not row["transport_error"] and row["response"] is not None and
                row["verification"]["valid_schema"] and row["verification"]["exact_fields"])


def scale_missing_counts(pairs):
    counts = _SMCounter(pairs)
    repair, fresh = counts[False, True], counts[True, False]
    d = repair + fresh
    p = min(1., 2 * sum(_sm_math.comb(d, i) for i in range(min(repair, fresh) + 1)) / 2**d) if d else 1.
    n = len(pairs)
    return {"n_pairs": n, "both_success": counts[True, True], "repair_only": repair,
            "fresh_only": fresh, "neither_success": counts[False, False], "discordant_pairs": d,
            "repair_minus_fresh_difference": (repair - fresh) / n if n else None,
            "difference_percentage_points": ((repair - fresh) / n) * 100 if n else None,
            "exact_mcnemar_two_sided_p": p if n else None,
            "primary_criterion_met": bool(n and repair > fresh and p < .05)}


def scale_missing_quantile(values, probability):
    position = (len(values) - 1) * probability
    left, right = _sm_math.floor(position), _sm_math.ceil(position)
    return values[left] + (position - left) * (values[right] - values[left])


def scale_missing_outcome_analysis(manifest, selection, interventions, unavailable,
                                   cfg, paired_statistics=None, bootstrap_envelope=True):
    """Analyze observed whole pairs and all binary assignments to unknown outcomes.

    ``unavailable`` is a list of metadata records with case_id, arm, request_key.
    The manifest gate is checked before iterating any efficacy-bearing input.
    ``paired_statistics`` is the frozen scale_paired_statistics implementation.
    """
    if not manifest or manifest.get("phase") != "interventions_complete":
        raise ValueError("Missing-outcome analysis requires interventions_complete")
    ids = list(selection["selected_case_ids"])
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Scheduled case IDs must be nonempty and unique")
    if paired_statistics is None:
        paired_statistics = globals().get("scale_paired_statistics")
    if not callable(paired_statistics):
        raise ValueError("Frozen paired statistics helper is required")
    seed, draws = cfg["bootstrap_seed"], cfg["bootstrap_draws"]
    if type(seed) is not int or type(draws) is not int or draws < 1:
        raise ValueError("Invalid frozen bootstrap configuration")
    grouped = {arm: {} for arm in SCALE_MISSING_ARMS}
    keys = set()
    for row in interventions:
        arm, cid, key = row["arm"], row["case_id"], row["request_key"]
        if arm not in grouped or cid not in ids or cid in grouped[arm] or key in keys:
            raise ValueError("Duplicate or unexpected scheduled intervention")
        grouped[arm][cid] = row
        keys.add(key)
    if any(set(rows) != set(ids) for rows in grouped.values()):
        raise ValueError("Operational rows must retain all scheduled pairs")
    unknown_keys, unknown_cells = set(), set()
    for item in unavailable:
        arm, cid, key = item["arm"], item["case_id"], item["request_key"]
        if arm not in grouped or cid not in grouped[arm] or key != grouped[arm][cid]["request_key"]:
            raise ValueError("Unavailable identity differs from scheduled intervention")
        if key in unknown_keys or (cid, arm) in unknown_cells:
            raise ValueError("Duplicate unavailable identity")
        row = grouped[arm][cid]
        if row.get("outcome_unavailable") is not True or row["response"] is not None or not row["transport_error"]:
            raise ValueError("Unavailable operational row must have no observed response")
        unknown_keys.add(key)
        unknown_cells.add((cid, arm))
    if unknown_keys != {row["request_key"] for rows in grouped.values() for row in rows.values()
                        if row.get("outcome_unavailable")}:
        raise ValueError("Unavailable allowlist differs from all marked operational rows")
    missing_ids = [cid for cid in ids if any((cid, arm) in unknown_cells for arm in SCALE_MISSING_ARMS)]
    if any(not all((cid, arm) in unknown_cells for arm in SCALE_MISSING_ARMS) for cid in missing_ids):
        raise ValueError("Amendment 002 supports unavailable whole pairs only")
    if len(missing_ids) > 2:
        raise ValueError("Amendment 002 allowlist may not exceed two whole pairs")
    observed_ids = [cid for cid in ids if cid not in set(missing_ids)]
    observed_pairs = [(scale_missing_good(grouped["fresh_retry"][cid]),
                       scale_missing_good(grouped["feedback_repair"][cid])) for cid in observed_ids]
    paired = paired_statistics(observed_pairs, seed, draws)
    n, m = len(ids), len(missing_ids)
    observed_sum = sum(int(repair) - int(fresh) for fresh, repair in observed_pairs)
    # Reuse the exact frozen RNG draw sequence for every hypothetical completion.
    # This is algebraically the same whole-pair bootstrap, avoiding sixteen
    # repetitions of its 12 million index draws. Selection order stays frozen.
    bootstrap_parts = []
    if bootstrap_envelope and m:
        position = {cid: i for i, cid in enumerate(missing_ids)}
        deltas = [None if cid in position else int(scale_missing_good(grouped["feedback_repair"][cid])) -
                  int(scale_missing_good(grouped["fresh_retry"][cid])) for cid in ids]
        rng = _sm_random.Random(seed)
        for _ in range(draws):
            subtotal, missing_counts = 0, [0] * m
            for _ in range(n):
                index = rng.randrange(n)
                if deltas[index] is None:
                    missing_counts[position[ids[index]]] += 1
                else:
                    subtotal += deltas[index]
            bootstrap_parts.append((subtotal, missing_counts))
    completions = []
    for bits in _sm_product((False, True), repeat=2*m):
        hypothetical = list(zip(bits[::2], bits[1::2]))
        stats = scale_missing_counts(observed_pairs + hypothetical)
        row = {"completion_id": "".join(str(int(bit)) for bit in bits) or "observed",
               "hypothetical_only": True,
               "assignments": [{"case_id": cid, "fresh_success": fresh, "repair_success": repair}
                               for cid, (fresh, repair) in zip(missing_ids, hypothetical)], **stats}
        if bootstrap_parts:
            hd = [int(repair) - int(fresh) for fresh, repair in hypothetical]
            boot = sorted((base + sum(count * delta for count, delta in zip(counts, hd))) / n
                          for base, counts in bootstrap_parts)
            interval = [scale_missing_quantile(boot, .025), scale_missing_quantile(boot, .975)]
            row["paired_bootstrap_95_interval"] = interval
            row["paired_bootstrap_95_interval_percentage_points"] = [100*v for v in interval]
        elif not m:
            row["paired_bootstrap_95_interval"] = paired["paired_bootstrap_95_interval"]
            row["paired_bootstrap_95_interval_percentage_points"] = paired["paired_bootstrap_95_interval_percentage_points"]
        completions.append(row)
    all_met = all(row["primary_criterion_met"] for row in completions)
    intervals = [row["paired_bootstrap_95_interval"] for row in completions
                 if "paired_bootstrap_95_interval" in row]
    return {"version": SCALE_MISSING_VERSION, "n_scheduled_pairs": n,
            "n_observed_pairs": len(observed_ids), "n_pairs": len(observed_ids),
            "n_unavailable_pairs": m, "n_unavailable_outcomes": len(unknown_keys),
            "observed_case_ids": observed_ids, "unavailable_case_ids": missing_ids,
            "unavailable_request_keys": sorted(unknown_keys), "paired_value_recovery": paired,
            "fresh_recovered": sum(fresh for fresh, _ in observed_pairs),
            "repair_recovered": sum(repair for _, repair in observed_pairs),
            "scheduled_difference_bounds": [(observed_sum-m)/n, (observed_sum+m)/n],
            "scheduled_difference_bounds_percentage_points": [100*(observed_sum-m)/n, 100*(observed_sum+m)/n],
            "completion_sensitivity": completions,
            "completion_bootstrap_endpoint_ranges": {
                "lower_endpoint": [min(v[0] for v in intervals), max(v[0] for v in intervals)],
                "upper_endpoint": [min(v[1] for v in intervals), max(v[1] for v in intervals)]} if intervals else None,
            "bootstrap_seed": seed, "bootstrap_draws": draws,
            "amended_primary_decision": {
                "rule": "Positive repair-minus-fresh difference AND exact two-sided McNemar p<0.05 in every binary completion",
                "criterion_met": all_met, "decision": "repair_advantage" if all_met else "inconclusive",
                "n_completions": len(completions),
                "completions_meeting_criterion": sum(row["primary_criterion_met"] for row in completions)},
            "caveat": "Complete-pair inference is available-case and conditional on selected failures. Controller-interrupted outcomes are unknown, not model errors. Hypothetical completions are sensitivity calculations, not observed answers."}
