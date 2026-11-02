"""Amendment-006 analysis binding, layered on the unchanged 003 calculator.

Definitions only. This file opens no study files and authorizes no calls. The
new plan binds the additional controller loss before continuation; the older
eight-outcome plan and its source bytes remain historical evidence.
"""

SCALE_MISSING_006_VERSION = "23-scale-v5-missing-outcomes-006-v1"


def scale_missing_validate_plan_006(plan, unavailable, previous_unavailable):
    """Check metadata alone, without looking at answers or verification flags."""
    expected = {"scheduled_pairs": 600, "observed_pair_target": 595,
                "unknown_outcomes": 9, "unknown_whole_pairs": 4,
                "unknown_partial_pairs": 1, "hypothetical_completions": 512,
                "bootstrap_seed": 246600, "bootstrap_samples": 20000}
    if any(type(plan.get(k)) is not int or plan[k] != v for k, v in expected.items()):
        raise ValueError("Amendment 006 analysis counts/settings differ from the fixed plan")
    def identities(items):
        values = [(r["case_id"], r["arm"], r["request_key"]) for r in items]
        if len(values) != len(set(values)) or len({v[2] for v in values}) != len(values):
            raise ValueError("Duplicate amendment-006 unavailable identity")
        if any(v[1] not in SCALE_MISSING_ARMS for v in values):
            raise ValueError("Unknown amendment-006 arm")
        return set(values)
    current, previous = identities(unavailable), identities(previous_unavailable)
    if len(previous) != 8 or len(current) != 9 or not previous.issubset(current):
        raise ValueError("Amendment 006 must preserve the exact eight earlier unknown cells")
    cells = {}
    for cid, arm, key in current:
        cells.setdefault(cid, set()).add(arm)
    whole = {cid for cid, arms in cells.items() if len(arms) == 2}
    partial = {cid for cid, arms in cells.items() if len(arms) == 1}
    prior_cases = {v[0] for v in previous}
    if len(whole) != 4 or len(partial) != 1 or whole != prior_cases:
        raise ValueError("Amendment 006 requires four prior whole pairs and one new partial pair")
    if (sorted(v[2] for v in current) != sorted(plan.get("unknown_request_keys", [])) or
            sorted(cells) != sorted(plan.get("unknown_case_ids", []))):
        raise ValueError("Amendment 006 unknown identities differ from the bound plan")
    partners = plan.get("known_partners", [])
    if len(partners) != 1:
        raise ValueError("Amendment 006 requires one preserved observed partner")
    partner = partners[0]
    cid = next(iter(partial))
    if (plan.get("partial_pair_case_id") != cid or
            plan.get("known_partner_request_key") != partner.get("request_key") or
            partner.get("case_id") != cid or partner.get("arm") not in SCALE_MISSING_ARMS or
            partner["arm"] in cells[cid] or partner.get("request_key") in {v[2] for v in current} or
            not isinstance(partner.get("request_key"), str) or not partner["request_key"] or
            not isinstance(partner.get("cache_sha256"), str) or len(partner["cache_sha256"]) != 64):
        raise ValueError("Amendment 006 known partner identity is invalid")
    return {"unknown_cells": current, "known_partner": partner,
            "partial_case_id": cid, "whole_case_ids": sorted(whole)}


def scale_missing_outcome_analysis_006(manifest, selection, interventions, unavailable,
                                      cfg, plan, previous_unavailable,
                                      paired_statistics=None, bootstrap_envelope=True):
    """595 complete pairs; all 512 assignments retain the actual known partner."""
    if not manifest or manifest.get("phase") != "interventions_complete":
        raise ValueError("Missing-outcome analysis requires interventions_complete")
    binding = scale_missing_validate_plan_006(plan, unavailable, previous_unavailable)
    if (len(selection["selected_case_ids"]) != plan["scheduled_pairs"] or
            cfg["bootstrap_seed"] != plan["bootstrap_seed"] or
            cfg["bootstrap_draws"] != plan["bootstrap_samples"]):
        raise ValueError("Amendment 006 changed the scheduled cohort or bootstrap settings")
    partner = binding["known_partner"]
    partner_rows = [r for r in interventions if r["request_key"] == partner["request_key"]]
    if (len(partner_rows) != 1 or any(partner_rows[0][k] != partner[k] for k in ("case_id", "arm")) or
            partner_rows[0].get("outcome_unavailable")):
        raise ValueError("Amendment 006 observed partner was lost or changed")
    result = scale_missing_outcome_analysis(manifest, selection, interventions, unavailable,
                                           cfg, paired_statistics, bootstrap_envelope)
    if (result["n_observed_pairs"] != 595 or result["n_unavailable_outcomes"] != 9 or
            result["n_wholly_unavailable_pairs"] != 4 or result["n_completions"] != 512):
        raise ValueError("Amendment 006 analysis shape differs from the fixed plan")
    result.update(version=SCALE_MISSING_006_VERSION,
                  n_partially_unavailable_pairs=1,
                  known_partner_request_keys=[partner["request_key"]],
                  known_partner_policy="Observed partner fixed in every scheduled-cohort completion; partial pair excluded only from complete-pair inference")
    return result
