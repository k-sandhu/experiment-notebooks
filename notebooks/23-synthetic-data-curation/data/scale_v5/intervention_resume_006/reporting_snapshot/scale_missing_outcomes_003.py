"""Pure amendment-003 analysis; no files, calls, answers or imputed records.

The caller must bind the exact unavailable identities in amendment 003 before
continuation. This generic calculator accepts whole or partial missing pairs;
it never authorizes expansion of that bound allowlist after another loss.
"""
from collections import Counter as _SMCounter
from itertools import product as _sm_product
import math as _sm_math
import random as _sm_random

SCALE_MISSING_VERSION = "23-scale-v5-missing-outcomes-003-v1"
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
    """Conditional complete-pair statistics and every unknown-cell completion.

    Phase gating precedes iteration of any efficacy-bearing input. Known cells
    in an incomplete pair remain fixed. Each completion bootstraps the entire
    scheduled cohort in its frozen selection order, using the frozen RNG draws.
    Reusing index multiplicities and equal delta vectors changes no bootstrap
    draw or endpoint. Binary assignments remain hypothetical sensitivity data.
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
    keys, scheduled_ids = set(), set(ids)
    for row in interventions:
        arm, cid, key = row["arm"], row["case_id"], row["request_key"]
        if arm not in grouped or cid not in scheduled_ids or cid in grouped[arm] or key in keys:
            raise ValueError("Duplicate or unexpected scheduled intervention")
        grouped[arm][cid] = row
        keys.add(key)
    if any(set(rows) != scheduled_ids for rows in grouped.values()):
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
    missing_set = set(missing_ids)
    observed_ids = [cid for cid in ids if cid not in missing_set]
    cells = [(cid, arm) for cid in ids for arm in SCALE_MISSING_ARMS if (cid, arm) in unknown_cells]
    known = {(cid, arm): scale_missing_good(grouped[arm][cid])
             for cid in ids for arm in SCALE_MISSING_ARMS if (cid, arm) not in unknown_cells}
    observed_pairs = [tuple(known[cid, arm] for arm in SCALE_MISSING_ARMS) for cid in observed_ids]
    paired = paired_statistics(observed_pairs, seed, draws)
    n, m, u = len(ids), len(missing_ids), len(cells)
    known_sum = sum((1 if arm == "feedback_repair" else -1) * int(value)
                    for (cid, arm), value in known.items())
    lower = known_sum - sum(arm == "fresh_retry" for cid, arm in cells)
    upper = known_sum + sum(arm == "feedback_repair" for cid, arm in cells)
    bootstrap_parts = []
    if bootstrap_envelope and m:
        position = {cid: i for i, cid in enumerate(missing_ids)}
        missing_positions = [position.get(cid) for cid in ids]
        deltas = [0 if cid in missing_set else int(known[cid, "feedback_repair"]) -
                  int(known[cid, "fresh_retry"]) for cid in ids]
        rng = _sm_random.Random(seed)
        for _ in range(draws):
            subtotal, missing_counts = 0, [0] * m
            for _ in range(n):
                index = rng.randrange(n)
                pos = missing_positions[index]
                if pos is None:
                    subtotal += deltas[index]
                else:
                    missing_counts[pos] += 1
            bootstrap_parts.append((subtotal, missing_counts))
    completions, intervals_by_delta = [], {}
    for bits in _sm_product((False, True), repeat=u):
        assigned = dict(zip(cells, bits))
        filled = {**known, **assigned}
        full_pairs = [tuple(filled[cid, arm] for arm in SCALE_MISSING_ARMS) for cid in ids]
        stats = scale_missing_counts(full_pairs)
        row = {"completion_id": "".join(str(int(bit)) for bit in bits) or "observed",
               "hypothetical_only": True,
               "assignments": [{"case_id": cid, "fresh_success": filled[cid, "fresh_retry"],
                                "repair_success": filled[cid, "feedback_repair"],
                                "unavailable_arms": [arm for arm in SCALE_MISSING_ARMS if (cid, arm) in unknown_cells]}
                               for cid in missing_ids],
               "hypothetical_cell_assignments": [{"case_id": cid, "arm": arm,
                   "success": assigned[cid, arm], "hypothetical_only": True} for cid, arm in cells], **stats}
        if bootstrap_parts:
            hd = tuple(int(filled[cid, "feedback_repair"]) - int(filled[cid, "fresh_retry"]) for cid in missing_ids)
            if hd not in intervals_by_delta:
                boot = sorted((base + sum(count * delta for count, delta in zip(counts, hd))) / n
                              for base, counts in bootstrap_parts)
                intervals_by_delta[hd] = (scale_missing_quantile(boot, .025), scale_missing_quantile(boot, .975))
            interval = list(intervals_by_delta[hd])
            row["paired_bootstrap_95_interval"] = interval
            row["paired_bootstrap_95_interval_percentage_points"] = [100*v for v in interval]
        elif not m:
            row["paired_bootstrap_95_interval"] = list(paired["paired_bootstrap_95_interval"])
            row["paired_bootstrap_95_interval_percentage_points"] = list(paired["paired_bootstrap_95_interval_percentage_points"])
        completions.append(row)
    all_met = all(row["primary_criterion_met"] for row in completions)
    intervals = [row["paired_bootstrap_95_interval"] for row in completions
                 if "paired_bootstrap_95_interval" in row]
    return {"version": SCALE_MISSING_VERSION, "n_scheduled_pairs": n,
            "n_observed_pairs": len(observed_ids), "n_pairs": len(observed_ids),
            "n_unavailable_pairs": m, "n_incomplete_pairs": m, "n_unavailable_outcomes": u,
            "n_wholly_unavailable_pairs": sum(all((cid, arm) in unknown_cells for arm in SCALE_MISSING_ARMS) for cid in missing_ids),
            "n_completions": len(completions),
            "observed_case_ids": observed_ids, "unavailable_case_ids": missing_ids,
            "unavailable_cells": [{"case_id": cid, "arm": arm, "request_key": grouped[arm][cid]["request_key"]} for cid, arm in cells],
            "unavailable_request_keys": sorted(unknown_keys), "paired_value_recovery": paired,
            "fresh_recovered": sum(fresh for fresh, _ in observed_pairs),
            "repair_recovered": sum(repair for _, repair in observed_pairs),
            "scheduled_difference_bounds": [lower/n, upper/n],
            "scheduled_difference_bounds_percentage_points": [100*lower/n, 100*upper/n],
            "completion_sensitivity": completions,
            "completion_bootstrap_endpoint_ranges": {
                "lower_endpoint": [min(v[0] for v in intervals), max(v[0] for v in intervals)],
                "upper_endpoint": [min(v[1] for v in intervals), max(v[1] for v in intervals)]} if intervals else None,
            "bootstrap_seed": seed, "bootstrap_draws": draws,
            "bootstrap_method": "Frozen whole-pair common-RNG resampling in selected-case order; equal delta vectors share identical intervals",
            "amended_primary_decision": {
                "rule": "Positive repair-minus-fresh difference AND exact two-sided McNemar p<0.05 in every binary completion",
                "criterion_met": all_met, "decision": "repair_advantage" if all_met else "inconclusive",
                "n_completions": len(completions),
                "completions_meeting_criterion": sum(row["primary_criterion_met"] for row in completions)},
            "caveat": "Complete-pair inference is available-case and conditional on selected failures. Controller-interrupted outcomes are unknown, not model errors. Hypothetical completions are sensitivity calculations, not observed answers."}
