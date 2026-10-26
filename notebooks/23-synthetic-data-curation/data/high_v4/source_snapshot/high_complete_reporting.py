"""Post-collection v4d/v4e presentation only. Load frozen helpers and high_reporting first."""
from pathlib import Path
from collections import Counter
import hashlib
import html
import json


HIGH_COMPLETE_REPORT_VERSION = "23-high-complete-presentation-v1"
HIGH_COMPLETE_ARMS = ["fresh_retry", "feedback_repair"]
HIGH_COMPLETE_CATEGORIES = ["original_success", "both_recover", "retry_only", "repair_only", "neither_recovers"]
HIGH_COMPLETE_LABELS = {
    "original_success": "Ordinary original success", "both_recover": "Both recover",
    "retry_only": "Fresh retry only", "repair_only": "Feedback repair only", "neither_recovers": "Neither recovers",
}


def high_complete_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def high_complete_jsonl(path):
    return [json.loads(s) for s in Path(path).read_text(encoding="utf-8-sig").splitlines() if s]


def high_complete_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def high_complete_success(row):
    return bool(row and not row.get("transport_error") and row.get("response") is not None
                and row["verification"]["valid_schema"] and row["verification"]["exact_fields"])


def high_complete_table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"] +
                     ["| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in row) + " |" for row in rows])


def high_complete_median(values):
    values = sorted(values)
    if not values:
        return None
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def high_complete_numeric_summary(report):
    if report["state"] != "complete":
        return {}
    selected = set(report["selection"]["selected_case_ids"])
    stages = [("Selected original", [r for r in report["originals"] if r["case_id"] in selected])] + [
        (arm.replace("_", " "), [r for r in report["interventions"] if r["arm"] == arm]) for arm in HIGH_COMPLETE_ARMS]
    summary = {}
    for field in ["quantity_units", "unit_price_cents"]:
        summary[field] = []
        for label, rows in stages:
            values = []
            for row in rows:
                obj = row.get("response")
                value = obj.get("answer", {}).get(field) if type(obj) is dict and type(obj.get("answer")) is dict else None
                gold = report["sources"][row["case_id"]]["gold"][field]
                if type(value) is int and not row["transport_error"]:
                    values.append(abs(value - gold))
            summary[field].append({"stage": label, "n_numeric": len(values), "n_total": len(rows),
                                   "median": high_complete_median(values), "maximum": max(values, default=None)})
    return summary


def high_complete_family_summary(report):
    rows = [r for r in report["originals"] if r["split"] == "collection"]
    result = []
    for family in sorted({r["family"] for r in rows}):
        group = [r for r in rows if r["family"] == family]
        failures = sum(r["response"] is not None and not r["transport_error"] and r["verification"]["valid_schema"]
                       and not r["verification"]["exact_fields"] for r in group)
        result.append({"family": family, "n": len(group), "failures": failures})
    return result


def high_complete_error_analysis(report):
    if report["state"] != "complete":
        return ("Main error analysis remains provisional. No final field-error mix, signed-difference frequency or relative error distribution is inferred from a partial cache.")
    rows = [r for r in report["originals"] if r["split"] == "collection" and r["response"] is not None
            and not r["transport_error"] and r["verification"]["valid_schema"]]
    failures = [r for r in rows if not r["verification"]["exact_fields"]]
    counts = {field: sum(not r["verification"]["field_correct"][field] for r in rows) for field in HIGH_FIELDS}
    mix = "; ".join(f"{field}: {n}" for field, n in counts.items())
    text = (f"Among {len(rows)} usable, schema-valid original collection replies, {len(failures)} had at least one wrong typed value. "
            f"They contain {sum(counts.values())} wrong field values: {mix}. A case may contribute several wrong fields. "
            "One wrong field rejects all-value success; six correct fields do not authorize the remaining wrong commercial value.")
    if counts['quantity_units'] and not any(counts[field] for field in HIGH_FIELDS if field != 'quantity_units'):
        text += (f" All six non-quantity fields are correct across these {len(rows)} replies. "
                 "The observed weakness is in the final quantity reconciliation; the output does not locate its cause within that calculation.")
    differences, relative = Counter(), []
    null_quantity = 0
    for row in failures:
        value = row["response"]["answer"].get("quantity_units")
        gold = report["sources"][row["case_id"]]["gold"]["quantity_units"]
        if not row["verification"]["field_correct"]["quantity_units"]:
            if type(value) is int:
                differences[value - gold] += 1
                if gold:
                    relative.append(abs(value - gold) / gold * 100)
            else:
                null_quantity += 1
    if differences:
        text += " Observed quantity differences (answer minus truth) are " + "; ".join(f"{delta:+,} units on {n} cases" for delta, n in sorted(differences.items())) + "."
    if relative:
        text += (f" Their median absolute relative quantity error is {high_complete_median(relative):.3f}% and maximum is {max(relative):.3f}%. "
                 "A small relative error still fails exact reconciliation and can change how many individual units are ordered or released.")
    if null_quantity:
        text += f" Another {null_quantity} wrong quantities are null rather than numeric, so they have no numeric error magnitude."
    evidence_only = sum(r["verification"]["exact_fields"] and not r["verification"]["accepted"] for r in rows)
    text += (f" Separately, {evidence_only} value-correct replies fail full citation acceptance. These are not original value-failure cases. "
             "The observed difference patterns describe outputs; they do not identify which internal calculation or source-reading step produced them.")
    return text


def high_complete_less_common_errors_markdown(report):
    """Read a saved posthoc source audit; never infer a model's arithmetic path."""
    review = report.get("less_common_quantity_review")
    heading = "### Less-common original quantity offsets\n\n"
    if review is None:
        return heading + "The separate saved counterfactual source review is not available yet; no explanation or intervention outcome is inferred for these offsets."
    originals = {r["case_id"]: r for r in report["originals"]}
    interventions = {(r["case_id"], r["arm"]): r for r in report["interventions"]}
    cases = review["cases"]
    rows = []
    def outcome(cid, arm):
        if report["state"] != "complete":
            return "Pending"
        row = interventions.get((cid, arm))
        if row is None:
            return "Not selected"
        obj = row.get("response")
        answer = obj.get("answer") if type(obj) is dict else None
        quantity = answer.get("quantity_units") if type(answer) is dict else "Unavailable"
        shown = f"{quantity:,}" if type(quantity) is int else str(quantity)
        verification = row["verification"]
        right = sum(verification["field_correct"].values())
        return f"{shown}; {right}/7 values; " + ("accepted" if verification["accepted"] else "rejected")
    for item in cases:
        cid = item["case_id"]
        case = report["sources"][cid]
        original = originals[cid]
        if (case["content_hash"] != item["content_hash"]
                or case["gold"]["quantity_units"] != item["expected_quantity_units"]
                or original["response"]["answer"]["quantity_units"] != item["observed_quantity_units"]):
            raise ValueError("Saved less-common-offset review does not match the current frozen source/response: " + cid)
        rows.append([cid,
                     f"{item['ordered_units']:,} - {item['net_target_dispatch_units']:,} = {item['expected_quantity_units']:,}",
                     f"{item['observed_quantity_units']:,} ({item['observed_minus_expected']:+,})",
                     outcome(cid, "fresh_retry"), outcome(cid, "feedback_repair")])
    distribution = Counter(item["observed_minus_expected"] for item in cases)
    distribution_text = ", ".join(f"{count} at {delta:+,}" for delta, count in sorted(distribution.items()))
    blocks = [heading +
              f"A separate [saved source review](data/high_v4/posthoc/less_common_quantity_errors.md), with [machine-readable traces](data/high_v4/posthoc/less_common_quantity_errors.json), "
              f"checks {len(cases)} original collection errors outside the repeated -100/-200-unit offsets: {distribution_text} units. "
              "Delta means observed minus expected open units. The expected balance is approved demand minus net allocated dispatch, which already includes accepted returns. "
              "This is posthoc error description and does not change scores, selection or feedback.\n\n" +
              high_complete_table(["Case", "Ordered - net dispatch = expected open", "Original (delta units)", "Fresh retry", "Feedback repair"], rows)]
    if report["state"] == "complete":
        denominators = {arm: [interventions[(item["case_id"], arm)] for item in cases if (item["case_id"], arm) in interventions]
                        for arm in HIGH_COMPLETE_ARMS}
        blocks.append("For these same audited sources, " + "; ".join(
            f"{arm.replace('_', ' ')} recovers {sum(high_complete_success(row) for row in values)}/{len(values)} by all seven values"
            for arm, values in denominators.items()) +
            ". The table also reports full acceptance, which adds citations. These seven were selected after inspecting unusual deltas, so their recovery rates do not replace the complete paired comparison.")
        harms = []
        for arm, values in denominators.items():
            changed = [f"{row['case_id']}: {row['new_wrong_fields']}" for row in values if row.get("new_wrong_fields")]
            harms.append(f"{arm.replace('_', ' ')} newly wrong fields: " + ("; ".join(changed) if changed else "none"))
        blocks.append("For this seven-case subset, " + "; ".join(harms) + ".")
    else:
        blocks.append("All seven original discrepancies are observed, but the main paired comparison remains incomplete. Fresh and repair cells stay pending rather than treating missing replies as failures.")
    blocks.append("Each of the four -72 outputs has at least one accepted 72-unit return whose hypothetical omission produces the same delta. "
                  "The saved review lists RT-02 for account-56fd10ed56500a83af17 and RT-01/RT-02/RT-03 alternatives for account-6096dbb0d4b1dff23766, account-81ae28dafc747351824c and account-ff063de4c5006a400e7d. "
                  "Several operations can match one number: some valid shipment amounts also equal 72 or 144, so counting one twice can reproduce a negative delta. Numerical agreement alone cannot identify which operation, if any, the model performed.")
    for cid, shipment_id, reversal_id, arithmetic in [
            ("account-ff063de4c5006a400e7d", "SH-03", "RV-01", "12 BOX × 12 units per BOX × 1/2 target-line share = 72 units"),
            ("account-f3fc844a1c0b64528f2d", "SH-13", "RX-13", "8 CASE × 24 units per CASE × 3/4 target-line share = 144 units")]:
        case = report["sources"][cid]
        literal = list(dict.fromkeys(line for line in case["document"].splitlines()
                                   if line.split("|", 1)[0].strip() in {shipment_id, reversal_id}))
        if len(literal) < 2:
            raise ValueError("Missing literal P06 shipment/reversal rows for " + cid)
        blocks.append(f"For {cid}, these are the actual P06 shipment and reversal rows (event, revision, kind, order, SKU, quantity, UOM, allocation, reference, occurrence, recording, state):\n\n"
                      "\x60\x60\x60text\n" + "\n".join(literal) + "\n\x60\x60\x60\n\n" +
                      f"The dated conversion and allocation give {arithmetic} before reversal. The POSTED {reversal_id} removes {shipment_id}, so its correct contribution is zero. "
                      "Including the reversed shipment is another exact arithmetic possibility for this negative delta, not an observed model reasoning step.")
    blocks.append("No tested single accepted return, counted shipment, active-reversed shipment or earlier shipment revision matches the +100 or -544 deltas. "
                  "For account-fec037740b6811d6ce5e, ignoring all returns gives -444 units, still 100 units short of -544. "
                  "Those discrepancies remain unexplained by these tests; combinations and other arithmetic paths were not exhaustively searched. "
                  "The same output error can have several numerical explanations, and the cached final answers do not reveal an internal cause.")
    return "\n\n".join(blocks)


def high_complete_load(root=Path(".")):
    """Read cached observations; do not call any generation, replay or model function."""
    root = Path(root)
    loader = globals().get("high_load_report")
    if loader is None:
        raise RuntimeError("Load the embedded high_reporting helper before the complete-results helper")
    base = loader(root)
    pilot_dir = root / "data" / "high_v4" / "pilot"
    ladder = high_complete_json(pilot_dir / "ladder.json") if (pilot_dir / "ladder.json").exists() else None
    pilot = []
    if ladder:
        for block in ladder["levels"]:
            level_dir = pilot_dir / f"level_{block['level']}"
            rows = high_complete_jsonl(level_dir / "candidates.jsonl")
            cases = high_complete_jsonl(level_dir / "cases.jsonl")
            pilot.append({"level": block["level"], "block": block, "rows": rows,
                          "cases": cases, "metrics": high_complete_json(level_dir / "metrics.json")})
    current = [row for row in base["attempts"] if row["directory"] == "high_v4"]
    raw = {row["request_key"]: row for row in current}
    main_dir = root / "data" / "high_v4" / "main"
    protocol = high_complete_json(main_dir / "protocol.json") if (main_dir / "protocol.json").exists() else None
    selection = high_complete_json(main_dir / "selection.json") if (main_dir / "selection.json").exists() else None
    originals_path = main_dir / "candidates.jsonl"
    interventions_path = main_dir / "interventions.jsonl"
    originals = high_complete_jsonl(originals_path) if originals_path.exists() else []
    interventions = high_complete_jsonl(interventions_path) if interventions_path.exists() else []
    original_phase_complete = (main_dir / "original_manifest.json").exists()
    if not originals:
        for cached in current:
            if not cached["source_path"].startswith("data/high_v4/main/cache/") or cached["stage"] != "generate" or cached["request"].get("sample") != 0:
                continue
            case = base["sources"].get(cached["case_id"])
            if case is None:
                continue
            verification = cached["verification"] or high_validate_answer(case, None)
            kind = ("pending" if cached["pending"] else "transport_failure" if cached["error"] else
                    "unusable_response" if cached["response"] is None else
                    "schema_failure" if not verification["valid_schema"] else
                    "value_failure" if not verification["exact_fields"] else
                    "accepted" if verification["accepted"] else "evidence_only_failure")
            originals.append({"case_id": case["case_id"], "candidate_id": case["case_id"] + ":original:0",
                              "family": case["family"], "split": case["split"], "semantic_hash": case["semantic_hash"],
                              "request_key": cached["request_key"], "response": cached["response"], "verification": verification,
                              "transport_error": cached["error"], "error_kind": kind, "provisional": True})
    report = {"version": HIGH_COMPLETE_REPORT_VERSION, "root": str(root), "base": base,
              "state": "complete" if base["state"] == "complete" else "main_incomplete",
              "pilot_ladder": ladder, "pilot": pilot, "protocol": protocol, "selection": selection,
              "originals": originals, "interventions": interventions, "raw_current": raw,
              "sources": base["sources"], "original_phase_complete": original_phase_complete,
              "bundle": base.get("bundle"), "metrics": base["bundle"]["metrics"] if base.get("bundle") else None}
    posthoc_path = root / "data" / "high_v4" / "posthoc" / "less_common_quantity_errors.json"
    report["less_common_quantity_review"] = high_complete_json(posthoc_path) if posthoc_path.exists() else None
    report["categories"] = high_complete_categories(report)
    report["examples"] = high_complete_examples(report)
    if report["state"] == "complete":
        high_complete_validate(report)
    return report


def high_complete_categories(report):
    groups = {key: [] for key in HIGH_COMPLETE_CATEGORIES}
    originals = {r["case_id"]: r for r in report["originals"] if r["split"] == "collection"}
    groups["original_success"] = sorted(cid for cid, row in originals.items() if row["verification"]["accepted"])
    if report["state"] == "complete":
        arms = {arm: {r["case_id"]: r for r in report["interventions"] if r["arm"] == arm} for arm in HIGH_COMPLETE_ARMS}
        for cid in report["selection"]["selected_case_ids"]:
            fresh, repair = high_complete_success(arms["fresh_retry"][cid]), high_complete_success(arms["feedback_repair"][cid])
            key = "both_recover" if fresh and repair else "retry_only" if fresh else "repair_only" if repair else "neither_recovers"
            groups[key].append(cid)
        for key in groups:
            groups[key].sort()
    return groups


def high_complete_examples(report, n=5):
    examples, seen = [], set()
    for category in HIGH_COMPLETE_CATEGORIES:
        members = report["categories"][category]
        if members:
            examples.append({"case_id": members[0], "category": category, "scope": "main"})
            seen.add(members[0])
    rows = sorted((r for r in report["originals"] if r["split"] == "collection"),
                  key=lambda r: (r["error_kind"] != "value_failure", r["case_id"]))
    for row in rows:
        if len(examples) >= n:
            break
        if row["response"] is not None and not row["transport_error"] and row["case_id"] not in seen:
            examples.append({"case_id": row["case_id"], "category": "additional_original", "scope": "main"})
            seen.add(row["case_id"])
    for block in report["pilot"]:
        for row in sorted(block["rows"], key=lambda r: (r["error_kind"] != "value_failure", r["case_id"])):
            if len(examples) >= n:
                break
            if row["case_id"] not in seen:
                examples.append({"case_id": row["case_id"], "category": "pilot_observation", "scope": "pilot"})
                seen.add(row["case_id"])
    examples = examples[:n]
    # Add diversity after category-first selection, without using intervention outcomes.
    def signed_delta(cid):
        row = next((r for r in rows if r["case_id"] == cid), None)
        answer = row["response"].get("answer") if row and type(row.get("response")) is dict else None
        quantity = answer.get("quantity_units") if type(answer) is dict else None
        expected = report["sources"][cid]["gold"]["quantity_units"]
        return quantity - expected if type(quantity) is int and type(expected) is int else None
    shown_deltas = {signed_delta(e["case_id"]) for e in examples if e["scope"] == "main"}
    for row in sorted(rows, key=lambda r: r["case_id"]):
        delta = signed_delta(row["case_id"])
        if (len(examples) >= 9 or delta is None or delta in {-100, -200, 0} or delta in shown_deltas
                or row["case_id"] in seen or row["transport_error"] or not row["verification"]["valid_schema"]):
            continue
        examples.append({"case_id": row["case_id"], "category": "additional_signed_delta", "scope": "main"})
        seen.add(row["case_id"])
        shown_deltas.add(delta)
    return examples


def high_complete_validate(report):
    """Recheck completed reported counts, sources, pairings and feedback against saved rows."""
    bundle, metrics = report["bundle"], report["metrics"]
    cases = {c["case_id"]: c for c in bundle["cases"]}
    manifest = bundle["manifest"]
    for label, data in [("protocol", bundle["protocol"]), ("selection", bundle["selection"]), ("cases", bundle["cases"])]:
        expected = manifest.get(label + "_hash")
        if expected is not None and high_complete_hash(data) != expected:
            raise ValueError("Completed presentation input hash mismatch: " + label)
    originals = {r["candidate_id"]: r for r in report["originals"]}
    for row in report["originals"] + report["interventions"]:
        case = cases[row["case_id"]]
        checked = high_validate_answer(case, None if row["transport_error"] else row["response"])
        if checked != row["verification"]:
            raise ValueError("Saved verification differs from frozen checker: " + row["candidate_id"])
        raw = report["raw_current"].get(row["request_key"])
        if raw is None:
            raise ValueError("A reported row lacks a current raw cache")
        request = raw["request"]
        if request.get("protocol") != report["protocol"]["protocol"]:
            raise ValueError("Reported main row belongs to a different protocol")
        if (request["model"] != "gpt-6.1-sol" or request["reasoning_effort"] != "high"
                or len(request["case_inputs"]) != 1 or 'model_reasoning_effort="high"' not in request["cli_options"]):
            raise ValueError("Reported request has the wrong model/effort/case profile")
        visible = request["case_inputs"][0]
        if set(visible) != {"case_id", "task_instructions", "documents"} or visible["documents"] != case["document"]:
            raise ValueError("Reported source mismatch or evaluator-label leakage")
        if row.get("arm") == "feedback_repair":
            old = originals[row["original_candidate_id"]]
            feedback = request["feedback"]
            if set(feedback) != {case["case_id"]} or feedback[case["case_id"]]["original_output"] != old["response"]:
                raise ValueError("Repair does not reference the actual original output")
            flags = feedback[case["case_id"]]["validator_feedback"]
            if set(flags) != {"wrong_fields", "schema_failed", "evidence_failed_fields"}:
                raise ValueError("Unexpected feedback beyond generic field flags")
            for key in ["wrong_fields", "evidence_failed_fields"]:
                if any(value not in HIGH_FIELDS for value in flags[key]):
                    raise ValueError("Feedback contains something other than field names")
        elif request["feedback"] is not None:
            raise ValueError("Original or fresh retry received repair feedback")
    selected = report["selection"]["selected_case_ids"]
    arm_maps = {arm: {r["case_id"]: r for r in report["interventions"] if r["arm"] == arm} for arm in HIGH_COMPLETE_ARMS}
    if any(set(rows) != set(selected) for rows in arm_maps.values()):
        raise ValueError("Completed treatment arms do not cover the same selected source IDs")
    actual = Counter((high_complete_success(arm_maps["fresh_retry"][cid]), high_complete_success(arm_maps["feedback_repair"][cid])) for cid in selected)
    pair = metrics["paired_value_recovery"]
    for field, key in [("both_success", (True, True)), ("fresh_only", (True, False)), ("repair_only", (False, True)), ("neither_success", (False, False))]:
        if pair[field] != actual[key]:
            raise ValueError("Saved paired metric disagrees with actual case outcomes")
    if pair["n_pairs"] != len(selected):
        raise ValueError("Paired denominator differs from selected sources")
    return {"passed": True, "n_rows": len(report["originals"]) + len(report["interventions"]), "n_pairs": len(selected)}


def high_complete_case(report, cid):
    return report["sources"][cid]


def high_complete_example_rows(report, example):
    cid = example["case_id"]
    original = next((r for r in report["originals"] if r["case_id"] == cid), None)
    if example["scope"] == "pilot":
        original = next(r for block in report["pilot"] for r in block["rows"] if r["case_id"] == cid)
    arms = {arm: next((r for r in report["interventions"] if r["case_id"] == cid and r["arm"] == arm), None) for arm in HIGH_COMPLETE_ARMS}
    return original, arms


def high_complete_excerpt(case, trace):
    """Select literal source rows, not paraphrases of hidden source_record."""
    lines = case["document"].splitlines()
    returned = next((r for r in trace["events"] if r["reason"] == "accepted_return" and r["net_dispatched_units"]), None)
    keys = {"P01": [case["source_record"]["target_line_id"]],
            "P02": [trace["term_winners"]["ordered_units"]["approval"], trace["term_winners"]["price_plan"]["approval"]],
            "P03": [case["source_record"]["target_sku"]], "P04": [], "P05": [trace["price"]["plan"]], "P06": []}
    if returned:
        keys["P06"] = [returned["event_id"], returned["reference"]]
        # The excerpt must use the same selected physical revision as the trace,
        # even if an older ingestion row appears first in the shuffled export.
        available = [r for r in case["source_record"]["ledger"]
                     if r["event_id"] == returned["reference"]
                     and r["recorded_at"] <= case["source_record"]["cutoff"]]
        shipment = max(available, key=lambda r: r["row_revision"])
        keys["P04"] = [shipment["allocation"]]
    chosen = []
    for doc, ids in keys.items():
        a, b = lines.index("BEGIN TABLE " + doc), lines.index("END TABLE " + doc)
        rows = [s for s in lines[a + 2:b] if s.split(" | ", 1)[0] in ids]
        if doc == "P05":
            rows = [s for s in rows if int(s.split(" | ")[2]) == trace["price"]["tier_minimum"]]
        if rows:
            chosen.extend(["[" + doc + "] literal source rows", lines[a + 1], *rows])
    return "\n".join(chosen)


def high_complete_trace_text(case):
    trace = high_calculation_trace(case)
    positive = sum(r["net_dispatched_units"] for r in trace["events"] if r["net_dispatched_units"] > 0)
    returned = -sum(r["net_dispatched_units"] for r in trace["events"] if r["net_dispatched_units"] < 0)
    p = trace["price"]
    text = (f"Current approved demand is {trace['ordered_units']:,} units, selected from "
            f"{trace['term_winners']['ordered_units']['approval']}. Selected shipments allocate {positive:,} units "
            f"and accepted returns reopen {returned:,}, so open units are {trace['ordered_units']:,} - "
            f"({positive:,} - {returned:,}) = **{trace['open_units']:,}**. "
            f"The plan {p['plan']} qualifies at tier {p['tier_minimum']:,} using ordered demand, not the open balance. "
            f"Its {p['gross_pack_cents']:,}-cent price pack contains {p['pack_units']} units. Apply the "
            f"{p['rebate_a_bps']}/10,000 and {p['rebate_b_bps']}/10,000 rebates in sequence, then add "
            f"{p['fee_unit_cents']} cents/unit and {p['pack_fee_unit_cents']} cents/unit converted pack fee, "
            f"subtract {p['credit_unit_cents']} cents/unit credit. The exact result is "
            f"{p['unrounded_unit_cents']} cents (a slash means exact division), rounded once half-up to "
            f"**{p['rounded_unit_cents']} cents**.")
    ret = next((r for r in trace["events"] if r["reason"] == "accepted_return" and r["net_dispatched_units"]), None)
    if ret:
        text += (f" Return {ret['event_id']} inherits shipment {ret['reference']}'s {ret['units_per_uom']}-unit UOM "
                 f"and {ret['target_share_percent']}% allocation. Their effective lookup dates are "
                 f"{ret['uom_effective_from']} and {ret['allocation_effective_from']}; the return date does not replace them.")
    return text


def high_complete_examples_markdown(report):
    groups = report["categories"]
    summary = high_complete_table(["Observed category", "Available main cases", "Shown if available"],
        [[HIGH_COMPLETE_LABELS[key], len(groups[key]) if report["state"] == "complete" or key == "original_success" else "Pending",
          "Yes" if groups[key] else "Absent" if report["state"] == "complete" else "Not established"] for key in HIGH_COMPLETE_CATEGORIES])
    blocks = ["### Worked cases selected from observed categories\n\n"
              "Examples use the first stable case ID in each available category, then additional real original failures/successes to reach five. "
              "After that, the first stable collection case for each unshown nonzero signed quantity delta outside -100/-200 is appended, up to nine examples. This adds error variety without selecting on intervention outcomes. "
              "Category counts describe how common each pattern is; an absent category is stated rather than filled with an invented response. "
              "Until main is complete, saved original/pilot cases are provisional illustrations and unsaved intervention values are marked unavailable.\n\n" + summary]
    if report["state"] == "complete":
        blocks.append(f"The original-success group contains {len(groups['original_success'])} fully accepted unselected originals. "
                      f"Among {len(report['selection']['selected_case_ids'])} paired selected failures, "
                      f"{len(groups['both_recover'])} are recovered by both arms, {len(groups['retry_only'])} by fresh retry only, "
                      f"{len(groups['repair_only'])} by repair only and {len(groups['neither_recovers'])} by neither. "
                      "These are counts of sources, not independent extra solved cases. The first ID in a category is an illustration, not a representative estimate by itself.")
    else:
        blocks.append(f"Current saved main records include {len(groups['original_success'])} fully accepted originals. "
                      "Paired categories are not yet established; a pending category is not evidence that its count is zero.")
    for i, example in enumerate(report["examples"], 1):
        case = high_complete_case(report, example["case_id"])
        original, arms = high_complete_example_rows(report, example)
        trace = high_calculation_trace(case)
        label = HIGH_COMPLETE_LABELS.get(example["category"], example["category"].replace("_", " "))
        blocks += [f"#### Case {i}: {label}, {case['case_id']}\n\n"
                   f"Scope: {example['scope']}, split: {case['split']}; {'complete measured main result' if report['state'] == 'complete' and example['scope'] == 'main' else 'saved observation, not a completed paired result'}. "
                   "The excerpt shows literal input rows. The complete ledger, including excluded histories, is used for the arithmetic.\n\n"
                   "\x60\x60\x60text\n" + high_complete_excerpt(case, trace) + "\n\x60\x60\x60\n\n" + high_complete_trace_text(case)]
        def value(row, field):
            obj = row.get("response") if row else None
            return obj["answer"].get(field) if type(obj) is dict and type(obj.get("answer")) is dict else "Unavailable"
        blocks.append(high_complete_table(["Field", "Expected", "Original", "Fresh retry", "Feedback repair"],
            [[field, case["gold"][field], value(original, field), value(arms["fresh_retry"], field), value(arms["feedback_repair"], field)] for field in HIGH_FIELDS]))
        for name, row in [("Original", original), ("Fresh retry", arms["fresh_retry"]), ("Feedback repair", arms["feedback_repair"])]:
            if row is None:
                reason = ("This original already passed, so it was ineligible for the failure-only intervention comparison."
                          if original and original['verification']['accepted'] else
                          "Pilot and audit cases do not enter the paired collection-failure comparison."
                          if case['split'] != 'collection' else
                          "No intervention outcome is saved for this example.")
                status = ("no intervention was called here. " if report['state'] == 'complete' else
                          "no completed intervention outcome is available. ")
                blocks.append(name + ": " + status + reason)
                continue
            wrong = [f for f in HIGH_FIELDS if not row["verification"]["field_correct"][f]]
            cites = [f for f in HIGH_FIELDS if not row["verification"]["evidence_correct"][f]]
            right = sum(row["verification"]["field_correct"].values())
            detail = (f"{name}: {right}/7 field values correct; outcome {row['error_kind']}; wrong value fields {wrong}; insufficient citation fields {cites}.")
            quantity = row["response"].get("answer", {}).get("quantity_units") if row["response"] and type(row["response"].get("answer")) is dict else None
            gold_quantity = case["gold"]["quantity_units"]
            if type(quantity) is int and quantity != gold_quantity:
                detail += f" Its open quantity differs by {quantity-gold_quantity:+,} individual units"
                if gold_quantity:
                    detail += f" ({abs(quantity-gold_quantity)/gold_quantity*100:.3f}% of the true open balance)"
                detail += "; exact reconciliation still rejects it. The output alone does not identify the calculation step responsible."
            if row.get("new_wrong_fields") is not None:
                detail += (f" Original wrong fields now fixed {row.get('original_wrong_fields_fixed', [])}; newly wrong fields {row['new_wrong_fields']}; previously wrong numeric fields with greater absolute error "
                           f"{row.get('worsened_numeric_fields', [])}. These are different forms of harm.")
            blocks.append(detail)
        repair = arms["feedback_repair"]
        if repair:
            flags = report["raw_current"][repair["request_key"]]["request"]["feedback"][case["case_id"]]["validator_feedback"]
            blocks.append("Actual feedback supplied with the exact saved original output:\n\n\x60\x60\x60json\n" +
                          json.dumps(flags, indent=2) + "\n\x60\x60\x60")
            blocks.append(f"The supplied wrong-value feedback names {flags['wrong_fields']}; it provides no expected numeric value. "
                          "This is privileged external checking, while the original and fresh-retry calls receive no such flags.")
        else:
            blocks.append("Actual feedback: none was supplied to the original call; no saved repair feedback exists for this example.")
        path = report["raw_current"].get(original["request_key"], {}).get("source_path")
        if path:
            blocks.append(f"Exact original request and raw response: [{original['request_key']}]({path}).")
    return "\n\n".join(blocks)


def high_complete_prompt_markdown(report):
    examples = report["examples"]
    if not examples:
        return "### Exact current request\n\nNo current usable request/response pair is available."
    example = next((e for e in examples if e["scope"] == "main"), examples[0])
    if report["state"] == "complete":
        example = next((e for e in examples
                        if all(high_complete_example_rows(report, e)[1][arm] is not None
                               for arm in HIGH_COMPLETE_ARMS)), example)
    original, arms = high_complete_example_rows(report, example)
    example_number = examples.index(example) + 1
    paired = all(arms[arm] is not None for arm in HIGH_COMPLETE_ARMS)
    blocks = ["### Exact supplied CLI inputs and raw responses for one worked case\n\n"
              f"These saved requests belong to Case {example_number}, {example['case_id']}. "
              "Its seven-field parsed comparison table above shows the expected and observed values. "
              + ("The original, fresh retry and feedback repair below use that same source case. "
                 "Open the repair input to inspect the exact old-answer-plus-flags package beside the fresh input. "
                 if paired else
                 "A completed paired example is not available here; only the saved requests for this same case are shown. ")
              + "These are current healthy-run requests, not responses reused from archived service attempts. "
              "Each collapsed block preserves the complete CLI stdin we supplied and the raw assistant response. "
              "JSON escape sequences are retained as sent; the worked source excerpt above is easier to read. "
              "This captures the experiment-controlled input, not Codex's additional internal system context or the provider's internal HTTP payload."]
    for label, row in [("Original", original), ("Fresh retry", arms["fresh_retry"]),
                       ("Feedback repair", arms["feedback_repair"])]:
        if row is None:
            continue
        raw = report["raw_current"][row["request_key"]]
        request = raw["request"]
        prompt = "\n\n".join(message["content"] for message in request["messages"])
        blocks.append(f"{label} profile: {request['model']} via codex exec, reasoning effort {request['reasoning_effort']}, "
                      f"protocol {raw['protocol']}, stage {request['stage']}, sample {request['sample']}. "
                      f"Full cached request, raw response and diagnostics: [{raw['request_key']}]({raw['source_path']}).\n\n"
                      f"<details><summary>{label}: exact CLI input we supplied and raw response</summary>\n\n"
                      "Complete CLI stdin we supplied:\n<pre>" + html.escape(prompt) +
                      "</pre>\n\nRaw assistant response:\n<pre>" + html.escape(raw["raw_response"]) +
                      "</pre>\n\n</details>")
    return "\n\n".join(blocks)


def high_complete_pilot_markdown(report):
    if not report["pilot_ladder"]:
        return "### Pilot ladder\n\nThe healthy pilot is not complete. No selected main difficulty is claimed."
    rows = []
    for block in report["pilot"]:
        values = sum(high_complete_success(r) for r in block["rows"])
        accepted = sum(r["verification"]["accepted"] for r in block["rows"])
        rows.append([block["level"], {1:32,2:64,3:128,4:192}[block["level"]], len(block["rows"]),
                     values, accepted, block["block"]["value_failure_cases"], block["block"]["threshold_met"]])
    ladder = report["pilot_ladder"]
    accepted_total, n_total = sum(r[4] for r in rows), sum(r[2] for r in rows)
    return ("### A healthy pilot selected the main source size\n\n" +
            high_complete_table(["Level", "Base shipments/source", "Replies", "Seven values correct", "Fully accepted", "Genuine value failures", "Threshold met"], rows) +
            f"\n\nThe healthy pilot fully accepted {accepted_total}/{n_total} replies. The healthy serial pilot made {ladder['physical_cli_requests']} requests and first reached its declared "
            f"three-failure threshold at level {ladder['selected_level']}. Levels 3 and 4 were not called after that crossing. "
            "The level-2 pilot's three observed misses were quantity values 100 units below truth; that is an output pattern, "
            "not proof of an internal reasoning cause. Earlier interrupted service attempts are preserved separately and do not enter this ladder. "
            "Different seeds and shared source rules mean two visited levels do not establish a monotonic causal effect of source length.")


def high_complete_paired_uncertainty(p):
    """Explain saved paired statistics without turning a bootstrap artifact into a win."""
    low, high = p["paired_bootstrap_95_interval_percentage_points"]
    discordant = p["discordant_pairs"]
    if not discordant:
        return ("Neither arm has an exclusive recovery, so these pairs provide no disagreement evidence for an advantage. "
                "A zero-width bootstrap interval here repeats the observed ties; it does not establish equivalence or rule out differences on new sources.")
    interval_text = ("The bootstrap interval includes zero, so its range includes no recovery difference. "
                     if low <= 0 <= high else
                     "The bootstrap interval excludes zero, but that alone does not establish an advantage. ")
    if low == high:
        interval_text += ("Its zero width comes from resampling the observed case differences; it cannot represent outcomes absent from this sample. ")
    repair_wins, fresh_wins = p["repair_only"], p["fresh_only"]
    exact_p = p["exact_mcnemar_two_sided_p"]
    test_text = (f"The exact test uses only the {discordant} repair-versus-fresh disagreements "
                 f"({repair_wins} repair-only and {fresh_wins} fresh-only recoveries), asking whether their split is compatible with equal recovery chances. ")
    if exact_p < 0.05 and repair_wins != fresh_wins:
        favored = "feedback repair" if repair_wins > fresh_wins else "fresh retry"
        test_text += (f"At the conventional 5% threshold, that test gives evidence in favor of {favored} within this selected paired sample. ")
    else:
        test_text += ("At the conventional 5% threshold, that test does not give clear evidence of an advantage for either arm. ")
    if discordant < 10:
        test_text += f"Only {discordant} disagreements carry that comparison, so a large percentage difference can still have weak support. "
    return interval_text + test_text + "The inference remains conditional on these selected failures and shared source templates."


def high_complete_results_markdown(report):
    if report["state"] != "complete":
        rows = [r for r in report["originals"] if r["response"] is not None and not r["transport_error"]]
        failures = sum(r["verification"]["valid_schema"] and not r["verification"]["exact_fields"] for r in rows)
        return ("### Main outcomes are pending\n\n"
                f"Read-only inspection currently finds {len(rows)} usable saved main original replies, including {failures} typed-value failures. "
                "These are partial cached observations, not the final baseline. Expansion, selected-cohort size, intervention denominators and paired recovery remain unreported until the complete bundle is saved. "
                "No missing or pending output is filled with a fabricated answer or scored as an extraction error.")
    metrics = report["metrics"]
    baseline = []
    for label, key in [("Collection originals", "original_collection"), ("Separate audit originals", "audit")]:
        r = metrics[key]
        baseline.append([label, r["n_attempted_cases"], r["valid_schema"], r["value_correct_valid_schema"], r["accepted"], r["value_failure_cases"]])
    arms = [[r["arm"].replace("_", " "), r["n_attempted_cases"], r["value_correct_valid_schema"], r["accepted"],
             r["original_wrong_fields_fixed"], r["cases_with_new_wrong_fields"], r["cases_with_worsened_numeric_error"]]
            for r in metrics["interventions"]]
    p = metrics["paired_value_recovery"]
    original_stats, audit_stats = metrics["original_collection"], metrics["audit"]
    arm_stats = {r["arm"]: r for r in metrics["interventions"]}
    fresh_stats, repair_stats = arm_stats["fresh_retry"], arm_stats["feedback_repair"]
    pairtable = high_complete_table(["", "Repair fails", "Repair succeeds"],
        [["Fresh retry fails", p["neither_success"], p["repair_only"]], ["Fresh retry succeeds", p["fresh_only"], p["both_success"]]])
    selection = report["selection"]
    initial_n = report["protocol"]["config"]["n_initial"]
    extension_n = report["protocol"]["config"]["n_expansion"]
    threshold = report["protocol"]["config"]["expand_below_value_failures"]
    expansion_text = (f"The first {initial_n} originals produced {selection['initial_value_failure_cases']} genuine value failures. "
        + (f"That was below the declared {threshold}-failure threshold, so the fixed {extension_n}-case extension was run. "
           if selection['expanded'] else
           f"The declared expansion condition was not met, so the {extension_n}-case extension was left uncalled. ")
        + f"The fixed ranking selected {p['n_pairs']} failures from {len(selection['eligible_candidate_ids'])} eligible collection failures. "
        "Neither extension nor selection uses repair outcomes. ")
    text = ("### Baseline and conditional recovery answer different questions\n\n"
            "The baseline denominator is every attempted original source in its split. The intervention denominator contains only selected genuine original value failures. "
            "Their percentages describe different populations and cannot be read as an ordinary before/after accuracy gain.\n\n" +
            high_complete_table(["Original split", "Attempted", "Schema valid", "Seven values correct", "Fully accepted", "Value-failure cases"], baseline) +
            f"\n\nThe original collection has {original_stats['value_correct_valid_schema']}/{original_stats['n_attempted_cases']} all-value successes, "
            f"compared with {audit_stats['value_correct_valid_schema']}/{audit_stats['n_attempted_cases']} on the separate audit. "
            "Those counts describe original extraction on their respective source splits; the smaller audit is not a post-training evaluation. "
            + expansion_text +
            "The same selected failures then go to both interventions. Full acceptance remains secondary to the primary all-value result:\n\n" +
            high_complete_table(["Conditional arm", "Selected attempts", "Seven values correct", "Fully accepted", "Original wrong fields fixed", "Cases with newly wrong fields", "Cases with worse numeric error"], arms) +
            f"\n\nFresh retry recovers {fresh_stats['value_correct_valid_schema']}/{fresh_stats['n_attempted_cases']} selected failures by values; "
            f"feedback repair recovers {repair_stats['value_correct_valid_schema']}/{repair_stats['n_attempted_cases']}. "
            f"They fully accept {fresh_stats['accepted']} and {repair_stats['accepted']} sources, respectively. "
            "This counts usable corrected orders in a failure-enriched cohort. Comparing those arm percentages with original baseline accuracy would mix different populations. "
            "Newly wrong fields and greater error in an already wrong field remain separate harms.\n\n"
            "Paired all-value outcomes, one cell per selected source case:\n\n" + pairtable)
    if p["n_pairs"]:
        text += (f"\n\nBoth arms recover {p['both_success']} sources, repair alone {p['repair_only']}, retry alone {p['fresh_only']}, "
                 f"and neither {p['neither_success']}. Feedback repair minus fresh retry is {p['difference_percentage_points']:.2f} percentage points across "
                 f"{p['n_pairs']} selected cases. The case-paired percentile bootstrap 95% interval is "
                 f"[{p['paired_bootstrap_95_interval_percentage_points'][0]:.2f}, {p['paired_bootstrap_95_interval_percentage_points'][1]:.2f}] percentage points; the exact conditional two-sided McNemar p-value is "
                 f"{p['exact_mcnemar_two_sided_p']:.3f}, based on {p['discordant_pairs']} discordant cases. "
                 "The bootstrap resamples whole source-case pairs; the exact test conditions on disagreements. "
                 "Both calculations are descriptive after pilot difficulty selection and failure selection. "
                 "Shared templates can violate independent-case assumptions; a small or degenerate interval is not evidence of equivalence.")
        text += "\n\n" + high_complete_paired_uncertainty(p)
    else:
        text += "\n\nNo original value failures were selected, so no paired recovery estimate exists."
    clean = metrics["reconnect_sensitivity"]
    retained = clean["paired_value_recovery"]
    text += (f"\n\nThe predeclared reconnect sensitivity excludes {len(clean['excluded_case_ids'])} pairs with an observed reconnect "
             f"in the original or either intervention and retains {retained['n_pairs']}/{p['n_pairs']} pairs. ")
    if retained["n_pairs"]:
        text += (f"Repair minus retry is {retained['difference_percentage_points']:.2f} percentage points in the retained pairs, "
                 f"with paired 95% interval [{retained['paired_bootstrap_95_interval_percentage_points'][0]:.2f}, {retained['paired_bootstrap_95_interval_percentage_points'][1]:.2f}] percentage points. ")
    else:
        text += "No pairs remain, so the sensitivity difference and interval are unavailable. "
    text += "This checks whether observed service reconnects change the description; ordinary warnings are not blanket exclusion criteria."
    return text


def high_complete_coverage_markdown(report):
    if report["state"] != "complete":
        return "Unique corrected-case coverage is pending; no number of recovered new sources is claimed."
    originals = {r["semantic_hash"] for r in report["originals"] if r["split"] == "collection" and r["verification"]["accepted"]}
    arms = {a: {r["semantic_hash"] for r in report["interventions"] if r["arm"] == a and r["verification"]["accepted"]} for a in HIGH_COMPLETE_ARMS}
    fresh, repair = arms["fresh_retry"] - originals, arms["feedback_repair"] - originals
    return (f"The baseline already contains {len(originals)} uniquely accepted collection sources. Fresh retry contributes {len(fresh)} "
            f"new accepted sources, repair contributes {len(repair)}, and {len(fresh & repair)} are the same sources. "
            f"The union is {len(fresh | repair)} new unique sources, not {len(fresh) + len(repair)}. "
            "Two accepted responses to the same packet do not create two independent training examples or two separate solved tasks.")


def high_complete_usage_markdown(report):
    base = report["base"]
    text = (f"Across all preserved high-v4 protocols, raw inspection currently finds {base['n_started_requests']} subprocess attempts. "
            f"Usage is present for {base['n_requests_with_usage']} and absent for {base['n_requests_missing_usage']}; "
            "missing usage remains unknown rather than zero. Earlier interrupted service attempts stay outside scientific accuracy denominators but remain part of operational history.\n\n")
    if report["state"] == "complete":
        rows = []
        for arm, item in report["metrics"]["usage"]["by_arm"].items():
            tokens = item["tokens"]
            rows.append([arm.replace("_", " "), item["physical_cli_requests"], tokens.get("input_tokens", "Unknown"),
                         tokens.get("output_tokens", "Unknown"), tokens.get("reasoning_output_tokens", "Unknown"),
                         round(item["median_request_seconds"], 2) if item["median_request_seconds"] is not None else "Unknown",
                         round(item["summed_subprocess_seconds"], 2)])
        text += high_complete_table(["Main arm/split", "Requests", "Input tokens", "Output tokens", "Reasoning component", "Median seconds/request", "Summed subprocess seconds"], rows)
        usage = report["metrics"]["usage"]
        text += (f"\n\nThe main ledger has {report['metrics']['physical_cli_requests']} unique requests, with known totals "
                 f"{usage['overall'].get('input_tokens', 'Unknown')} input tokens and {usage['overall'].get('output_tokens', 'Unknown')} output tokens. "
                 "Reasoning and cached-input counts are components, not additional tokens to add again. Summed subprocess time is not wall-clock time when two requests run in a wave. "
                 "Equal item/request counts do not equalize the longer repair prompt or actual reasoning/output tokens; USD cost remains unavailable.")
    else:
        text += "Final per-arm usage/timing remains pending with the main bundle. No final cost or latency comparison is estimated from partial requests."
    return text


def high_complete_figure_interpretations(report):
    """Numerical interpretation shared by saved-figure metadata and narrative."""
    pilot_parts = []
    pilot_n, pilot_ok = 0, 0
    for block in report["pilot"]:
        n, fail = len(block["rows"]), block["block"]["value_failure_cases"]
        accepted = sum(r["verification"]["accepted"] for r in block["rows"])
        pilot_n += n
        pilot_ok += accepted
        pilot_parts.append(f"level {block['level']}: {fail}/{n} genuine value failures and {accepted}/{n} fully accepted")
    descriptions = {"healthy_pilot.png": ("The visited levels show " + "; ".join(pilot_parts) +
        f". That is {pilot_ok}/{pilot_n} fully accepted replies across the healthy ladder. "
        "The first three-failure threshold crossing chooses level 2; unvisited levels are not zero-error observations. "
        "This calibrates source size for the study, not a causal effect of source length.")}
    if report["state"] == "complete":
        metrics = report["metrics"]
        baseline, audit = metrics["original_collection"], metrics["audit"]
        arms = {r["arm"]: r for r in metrics["interventions"]}
        fresh, repair = arms["fresh_retry"], arms["feedback_repair"]
        descriptions["baseline_and_recovery.png"] = (
            f"Collection originals have {baseline['value_correct_valid_schema']}/{baseline['n_attempted_cases']} all-value successes "
            f"and {baseline['accepted']}/{baseline['n_attempted_cases']} fully accepted answers; the separate audit has "
            f"{audit['value_correct_valid_schema']}/{audit['n_attempted_cases']} all-value successes and {audit['accepted']}/{audit['n_attempted_cases']} fully accepted. "
            f"On the selected original failures, fresh retry recovers {fresh['value_correct_valid_schema']}/{fresh['n_attempted_cases']} "
            f"and feedback repair {repair['value_correct_valid_schema']}/{repair['n_attempted_cases']} by values, with "
            f"{fresh['accepted']} and {repair['accepted']} fully accepted, respectively. "
            "Only the right-hand arms share the selected-failure denominator. Their recovery rates cannot be subtracted from unselected baseline accuracy as an ordinary before/after gain.")
        p = metrics["paired_value_recovery"]
        delta = f"{p['difference_percentage_points']:.2f} percentage points" if p["n_pairs"] else "unavailable"
        descriptions["paired_outcomes.png"] = (
            f"Of {p['n_pairs']} paired sources, {p['both_success']} are recovered by both, {p['repair_only']} by repair only, "
            f"{p['fresh_only']} by retry only and {p['neither_success']} by neither. Repair minus retry is {delta}. "
            f"The {p['discordant_pairs']} disagreements carry the exact conditional test; shared successes overlap in corrected-source coverage. "
            "This selected, template-dependent sample cannot establish an unconditional production accuracy gain.")
        numeric = high_complete_numeric_summary(report)
        parts = []
        for field, unit in [("quantity_units", "individual units"), ("unit_price_cents", "cents/unit")]:
            parts.append(field + ": " + "; ".join(
                f"{r['stage']} median {r['median']}, maximum {r['maximum']} {unit}, numeric {r['n_numeric']}/{r['n_total']}"
                for r in numeric[field]))
        descriptions["numeric_error_distribution.png"] = (
            ". ".join(parts) + ". Each dot uses the same selected source cohort; zero is a correct numeric value. "
            "Nonnumeric, missing and transport-failed values are excluded with coverage reported, never replaced by zero. "
            "A previously wrong field can become numerically worse without adding a newly wrong field.")
        families = high_complete_family_summary(report)
        descriptions["family_groups.png"] = (
            "Original value failures by source variant are " + "; ".join(
                f"{r['family'].replace('_', ' ')} {r['failures']}/{r['n']}" for r in families) +
            ". These group counts locate observed errors and show each attempted denominator. "
            "Families share most accounting rules, so differences cannot identify which rule caused a failure.")
    else:
        rows = [r for r in report["originals"] if r["response"] is not None and not r["transport_error"]]
        fail = sum(r["verification"]["valid_schema"] and not r["verification"]["exact_fields"] for r in rows)
        descriptions["main_pending.png"] = (
            f"This inspection has {len(rows)} usable saved original replies, including {fail} typed-value failures. "
            "The run is incomplete, so no final baseline or paired recovery denominator is inferred. The notice is not a zero-percent result.")
    if report["examples"]:
        example = next((e for e in report["examples"] if e["category"] != "original_success"), report["examples"][0])
        case = high_complete_case(report, example["case_id"])
        trace = high_calculation_trace(case)
        shipped = sum(r["net_dispatched_units"] for r in trace["events"] if r["net_dispatched_units"] > 0)
        returned = -sum(r["net_dispatched_units"] for r in trace["events"] if r["net_dispatched_units"] < 0)
        original, _ = high_complete_example_rows(report, example)
        observed = original["response"].get("answer", {}).get("quantity_units") if original and original["response"] else "unavailable"
        descriptions["quantity_source_audit.png"] = (
            f"For {case['case_id']}, {trace['ordered_units']:,} ordered units minus ({shipped:,} allocated shipments minus "
            f"{returned:,} accepted returns) leaves {trace['open_units']:,} open units. The original answer's quantity is {observed}. "
            "The complete selected ledger establishes this expected balance; the small event table illustrates returns and excluded histories only. "
            "One source audit verifies the answer key, not the model's private reasoning or a population error rate.")
    return descriptions



def high_complete_plot_report(report, root=Path("."), write=False):
    """Six descriptive figure types. Pending outcomes get no fabricated bars."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    output = Path(root) / "figures" / "high_v4_complete"
    figures = []
    interpretations = high_complete_figure_interpretations(report)
    def keep(fig, name, alt, interpretation):
        item = {"filename": name, "figure": fig, "alt": alt, "interpretation": interpretations.get(name, interpretation)}
        if write:
            output.mkdir(parents=True, exist_ok=True)
            path = output / name
            fig.savefig(path, bbox_inches="tight", dpi=160)
            item["path"] = str(path.relative_to(Path(root))).replace("\\", "/")
            plt.close(fig)
        figures.append(item)

    fig, ax = plt.subplots(figsize=(10, 4.6))
    pilot = report["pilot"]
    if pilot:
        bars = ax.bar([f"Level {b['level']}\n{ {1:32,2:64,3:128,4:192}[b['level']]} shipments" for b in pilot],
                      [b["block"]["value_failure_cases"] for b in pilot], color="#376d91")
        ax.bar_label(bars, labels=[f"{b['block']['value_failure_cases']}/{len(b['rows'])}" for b in pilot], padding=5)
        ax.axhline(3, color="#a7473f", linestyle="--", label="Declared threshold: 3 genuine value failures")
        ax.set_ylim(0, max(4, max(b["block"]["value_failure_cases"] for b in pilot) + 1.4))
        ax.set_ylabel("Valid-schema typed-value failure cases")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        pilot_counts = ", ".join(f"{b['block']['value_failure_cases']}/{len(b['rows'])}" for b in pilot)
        ax.set_title(f"Pilot value failures {pilot_counts}: level 2 reaches the threshold", pad=16)
        ax.legend(loc="upper left")
    else:
        ax.text(.5, .5, "Healthy pilot not complete", ha="center", va="center", transform=ax.transAxes)
    keep(fig, "healthy_pilot.png", "Observed genuine value failures at each visited healthy pilot level.",
         "The healthy pilot has eight accepted level-1 replies and five accepted plus three quantity failures at level 2. Counts are per source case. Unvisited levels are not plotted as zero errors; this is a calibration rule, not proof that length alone causes difficulty.")

    if report["state"] == "complete":
        metrics = report["metrics"]
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        groups = [("Collection originals", metrics["original_collection"]), ("Separate audit", metrics["audit"])]
        for ax, rows, title in [(axes[0], groups, "All original sources"),
            (axes[1], [(r["arm"].replace("_", " "), r) for r in metrics["interventions"]], "Conditional on selected original value failures")]:
            for i, (label, row) in enumerate(rows):
                ax.bar(i - .17, row["value_correct_valid_schema"], width=.34, color="#376d91", label="Seven exact values" if i == 0 else None)
                ax.bar(i + .17, row["accepted"], width=.34, color="#46825c", hatch="//", label="Values + citations" if i == 0 else None)
                ax.text(i, max(row["value_correct_valid_schema"], row["accepted"]) + max(1, row["n_attempted_cases"] * .03),
                        f"{row['value_correct_valid_schema']}/{row['n_attempted_cases']} values\n{row['accepted']}/{row['n_attempted_cases']} accepted", ha="center", fontsize=9)
            ax.set_xticks(range(len(rows)), [r[0] for r in rows])
            ax.set_ylim(0, max([r["n_attempted_cases"] for _, r in rows] + [1]) * 1.28)
            ax.set_ylabel("Cases")
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.set_title(title)
            ax.legend(fontsize=9)
        by_arm = {r["arm"]: r for r in metrics["interventions"]}
        baseline = metrics["original_collection"]
        fresh, repair = by_arm["fresh_retry"], by_arm["feedback_repair"]
        fig.suptitle(f"Collection {baseline['value_correct_valid_schema']}/{baseline['n_attempted_cases']} correct; "
                     f"selected retry {fresh['value_correct_valid_schema']}/{fresh['n_attempted_cases']} vs repair {repair['value_correct_valid_schema']}/{repair['n_attempted_cases']}", y=1.03)
        keep(fig, "baseline_and_recovery.png", "Separate panels for all original source outcomes and conditional intervention recovery.",
             "The left panel uses all attempted original collection/audit sources. The right uses the same selected original failures in both arms. Bars are case counts, labelled with their own denominators. The right panel is not an unselected test-set accuracy improvement.")
        p = metrics["paired_value_recovery"]
        fig, ax = plt.subplots(figsize=(7.5, 5))
        matrix = [[p["neither_success"], p["repair_only"]], [p["fresh_only"], p["both_success"]]]
        image = ax.imshow(matrix, cmap="Blues", vmin=0)
        for i in range(2):
            for j in range(2):
                label = [["Neither", "Repair only"], ["Retry only", "Both"]][i][j]
                ax.text(j, i, f"{label}\n{matrix[i][j]}", ha="center", va="center",
                        color="white" if matrix[i][j] > max(sum(matrix, []), default=0) * .55 else "#17232d", fontsize=13)
        ax.set_xticks([0, 1], ["Repair fails", "Repair succeeds"])
        ax.set_yticks([0, 1], ["Fresh retry fails", "Fresh retry succeeds"])
        delta = f"{p['difference_percentage_points']:+.2f} pp" if p["n_pairs"] else "unavailable"
        ax.set_title(f"Both {p['both_success']}, repair only {p['repair_only']}, retry only {p['fresh_only']}, neither {p['neither_success']}\n"
                     f"{p['n_pairs']} paired sources; repair minus retry {delta}", pad=16, fontsize=12)
        fig.colorbar(image, ax=ax, label="Source cases")
        keep(fig, "paired_outcomes.png", "A two-by-two table of paired fresh-retry and feedback-repair value outcomes.",
             f"The cells sum to {p['n_pairs']} selected sources. Only the {p['fresh_only'] + p['repair_only']} discordant cases determine the exact conditional McNemar test. Both-success cases reveal overlap in corrected sources, not independent extra cases.")

        selected = set(report["selection"]["selected_case_ids"])
        selected_originals = [r for r in report["originals"] if r["case_id"] in selected]
        stage_rows = [("Selected original", selected_originals)] + [
            (arm.replace("_", " "), [r for r in report["interventions"] if r["arm"] == arm]) for arm in HIGH_COMPLETE_ARMS]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
        for ax, field, unit in [(axes[0], "quantity_units", "individual units"), (axes[1], "unit_price_cents", "cents per unit")]:
            maximum = 0
            for i, (label, rows) in enumerate(stage_rows):
                values = []
                for row in rows:
                    obj = row.get("response")
                    value = obj.get("answer", {}).get(field) if type(obj) is dict else None
                    gold = report["sources"][row["case_id"]]["gold"][field]
                    if type(value) is int and not row["transport_error"]:
                        values.append(abs(value - gold))
                median = high_complete_median(values)
                if values:
                    ax.scatter(values, [i + ((k % 5) - 2) * .045 for k in range(len(values))],
                               alpha=.65, s=23, color=["#a7473f", "#376d91", "#46825c"][i], edgecolors="none")
                    ax.plot([median], [i], marker="|", markersize=20, color="black", markeredgewidth=2)
                    maximum = max(maximum, max(values))
                ax.text(.98, (i + .83) / 3, f"numeric {len(values)}/{len(rows)}; median {median}; max {max(values, default=None)}",
                        transform=ax.transAxes, ha="right", va="center", fontsize=8,
                        bbox={"facecolor":"white", "edgecolor":"none", "alpha":.85, "pad":1})
            ax.set_yticks(range(3), [s[0] for s in stage_rows])
            ax.set_ylim(-.5, 2.5)
            if maximum > 1000:
                ax.set_xscale("symlog", linthresh=1)
                ax.set_xlabel(f"Absolute error ({unit}); symmetric-log axis above 1")
            else:
                ax.set_xlabel(f"Absolute error ({unit})")
                ax.set_xlim(-max(1, maximum * .04), max(1, maximum) * 1.15)
            stages = high_complete_numeric_summary(report)[field]
            medians = "/".join(str(s["median"]) for s in stages)
            ax.set_title(f"{field.replace('_', ' ')}: medians {medians}", fontsize=11)
        max_quantity = "/".join(str(s["maximum"]) for s in high_complete_numeric_summary(report)["quantity_units"])
        fig.suptitle(f"Selected original / retry / repair quantity-error maxima: {max_quantity} units", y=1.03)
        keep(fig, "numeric_error_distribution.png", "Absolute quantity and unit-price errors for the paired selected cohort before and after each intervention.",
             "Each dot is a numeric reply on one selected source; the black mark is its stage median. Correct values have zero error. Missing, noninteger and transport-failed values are not silently replaced by zero, and numeric coverage is labelled. A field remaining wrong can nevertheless become much more wrong; this differs from introducing a new wrong field.")

        families = sorted({r["family"] for r in report["originals"] if r["split"] == "collection"})
        fig, ax = plt.subplots(figsize=(12, 4.8))
        counts, sizes = [], []
        for family in families:
            rows = [r for r in report["originals"] if r["split"] == "collection" and r["family"] == family]
            counts.append(sum(r["verification"]["valid_schema"] and not r["verification"]["exact_fields"] and not r["transport_error"] for r in rows))
            sizes.append(len(rows))
        bars = ax.bar(range(len(families)), counts, color="#a46d3c")
        ax.bar_label(bars, labels=[f"{a}/{b}" for a, b in zip(counts, sizes)], padding=4)
        ax.set_xticks(range(len(families)), [x.replace("_", "\n") for x in families], fontsize=9)
        ax.set_ylabel("Original collection value-failure cases")
        ax.set_ylim(0, max(counts + [1]) * 1.25 + 1)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_title(f"{sum(counts)}/{sum(sizes)} originals have value errors across shared-rule source variants", pad=16)
        keep(fig, "family_groups.png", "Observed original value failures by source-family label, with attempted-case denominators.",
             "Families share most accounting operations and are scenario variants, not controlled causal ablations. Compare counts and their labelled group sizes; an apparent difference does not establish which rule caused an error.")
    else:
        fig, ax = plt.subplots(figsize=(10, 3.3))
        ax.axis("off")
        usable = [r for r in report["originals"] if r["response"] is not None and not r["transport_error"]]
        ax.text(.5, .68, "Main recovery comparison is not complete", ha="center", fontsize=16, transform=ax.transAxes)
        ax.text(.5, .40, f"{len(usable)} saved usable original replies at this inspection\nNo paired recovery bars or final accuracy estimate", ha="center", fontsize=12, transform=ax.transAxes)
        keep(fig, "main_pending.png", "Main run pending; partial saved replies do not supply a completed paired comparison.",
             "This panel is a status notice, not a zero-percent recovery result. Rebuild from the completed manifest before reporting main denominators, effect sizes or interventions.")

    if report["examples"]:
        example = next((e for e in report["examples"] if e["category"] != "original_success"), report["examples"][0])
        case = high_complete_case(report, example["case_id"])
        trace = high_calculation_trace(case)
        shipped = sum(r["net_dispatched_units"] for r in trace["events"] if r["net_dispatched_units"] > 0)
        returned = -sum(r["net_dispatched_units"] for r in trace["events"] if r["net_dispatched_units"] < 0)
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios":[1.25, 1]})
        labels = ["Ordered", "Allocated shipments", "Accepted returns", "Open units"]
        amounts = [trace["ordered_units"], shipped, returned, trace["open_units"]]
        bars = axes[0].barh(labels[::-1], amounts[::-1], color=["#46825c", "#8ba8bb", "#a46d3c", "#376d91"])
        axes[0].bar_label(bars, labels=[f"{v:,}" for v in amounts[::-1]], padding=4)
        axes[0].set_xlim(0, max(amounts) * 1.25)
        axes[0].set_xlabel("Individual units for the target purchase line")
        axes[0].set_title(f"{trace['ordered_units']:,} - ({shipped:,} - {returned:,}) = {trace['open_units']:,}", fontsize=11)
        show = []
        for reason in ["accepted_return", "reversed_shipment", "void", "future_occurrence"]:
            found = next((r for r in trace["events"] if r["reason"] == reason), None)
            if found:
                show.append(found)
        shown_ids = {r["event_id"] for r in show}
        show += [r for r in trace["events"] if r["reason"] == "accepted_return" and r["event_id"] not in shown_ids][:7-len(show)]
        axes[1].axis("off")
        short = {"accepted_return":"Return", "reversed_shipment":"Reversed", "void":"VOID", "future_occurrence":"Future"}
        table = axes[1].table(cellText=[[r["event_id"], r["selected_revision"], r["net_dispatched_units"], short[r["reason"]]] for r in show],
                             colLabels=["Event", "Rev", "Signed units", "Action"], loc="center")
        table.auto_set_font_size(False); table.set_fontsize(9); table.scale(1, 1.65)
        axes[1].set_title("Selected source-history contributions")
        original, _ = high_complete_example_rows(report, example)
        observed = original["response"].get("answer", {}).get("quantity_units") if original and original["response"] else "unavailable"
        fig.suptitle(f"Expected open {trace['open_units']:,}; original quantity {observed}\n{case['case_id']}", y=1.07)
        keep(fig, "quantity_source_audit.png", "One actual source's independently derived ordered, shipped, returned and open quantities, with selected event contributions.",
             "This is a ground-truth source audit, not a model's private reasoning. The complete ledger is reduced using selected revisions, reversals and original-date conversion/allocation. The small event table shows examples of non-additive histories; it does not replace the full saved trace.")
    return figures


def high_complete_render(report):
    complete = report["state"] == "complete"
    protocol = report["protocol"] or {}
    workers = protocol.get("max_workers", "not yet saved")
    search_yield = ""
    if complete:
        baseline = report['metrics']['original_collection']
        failures = baseline['value_failure_cases']
        if failures:
            search_yield = (f"In collection alone, {baseline['n_attempted_cases']} original requests yielded {failures} qualifying mistakes, "
                f"or {baseline['n_attempted_cases']/failures:.2f} originals per observed failure. "
                "Accepted originals remain demonstrations, while only the failures supply observed mistakes for this correction comparison. "
                "The pilot, audit and two follow-ups per selected failure add requests.\n\n")
    intro = """## 13. Larger source packs and higher reasoning

A purchasing team needs to know how many individual units remain open on one order line. Its records may arrive as repeated warehouse exports, corrections and returns. One corrected shipment must replace its old row; a return must use the packaging and line allocation that applied to the selected original shipment. A plausible-looking balance can still be wrong by one handling unit or one duplicated event.

An ordinary reconciliation process resolves approved commercial terms first, identifies current warehouse movements, converts and allocates their quantities, and prices the ordered demand under the current contract. The difficult part is keeping these rules consistent across long histories. A correct price and five other correct fields do not make a wrong open quantity safe to accept.

The earlier Sol follow-up found three misses under low reasoning; both a fresh retry and feedback repair recovered those same three. This round asks whether a repair package helps beyond another attempt when Sol receives explicit high reasoning and longer fresh source packs. This experiment does not update model weights. It tests production and checking of candidate answers; it does not train a model.
"""
    if complete:
        p = report["metrics"]["paired_value_recovery"]
        headline = (f"On {p['n_pairs']} paired selected original failures, repair alone recovered {p['repair_only']}, "
                    f"fresh retry alone recovered {p['fresh_only']}, both recovered {p['both_success']}, and neither recovered {p['neither_success']}.")
    else:
        headline = "The healthy pilot selected level 2, but the main paired comparison is not complete; no final repair advantage is claimed."
    overview = ("### Question and study summary\n\n" + headline + "\n\n"
        "All-value success means a usable reply with valid schema and seven exact typed values. Full acceptance also requires sufficient citations. "
        "A wrong quantity rejects the whole answer even when every other field is right. For example, nine correct answers out of ten sources gives 9/10 all-value success; "
        "that is different from counting 69 correct fields out of 70.\n\n"
        "The healthy pilot used eight cases per visited level. Level 2 has 64 logical base shipments per packet, plus returns, reversals, corrections and other-order/line distractors. "
        "The main plan starts with 160 originals, adds a fixed 80 only if initial genuine value failures are fewer than 40, freezes a pre-outcome random cap of 80 failures, "
        "and gives each selected source one fresh-retry CLI request and one feedback-repair CLI request. Another 24 originals form a separate audit excluded from selection. "
        "Baseline accuracy uses all original sources; recovery conditions on original failure. Equal call counts do not equalize prompt or compute cost.\n\n")
    pilot_requests = report["pilot_ladder"]["physical_cli_requests"] if report["pilot_ladder"] else "up to 32"
    collection_label = (str(report["metrics"]["original_collection"]["n_attempted_cases"]) + " collection originals"
                        if complete else "160 originals; +80 iff fewer than 40 value failures")
    selected_label = str(report["metrics"]["n_selected"]) if complete else "up to 80"
    flow = f"""\x60\x60\x60mermaid
flowchart TB
    source["Fresh generated sources<br/>all 1056 potential main + 32 pilot pre-audited"] --> pilot["Sol via codex exec, high<br/>{pilot_requests} one-case pilot CLI requests<br/>returns 7 fields + citations"]
    pilot -->|"level 2 threshold met"| main["Sol via codex exec, high<br/>{collection_label}<br/>returns 7 fields + citations"]
    main --> select["Freeze {selected_label} genuine value failures<br/>pre-outcome seeded ranking"]
    select --> audit["Sol via codex exec, high<br/>24 audit originals; selection already frozen<br/>returns 7 fields + citations"]
    audit --> gate["All collection and audit originals complete<br/>source review before intervention phase"]
    gate --> fresh["Sol fresh retry via codex exec<br/>same source, high reasoning<br/>returns 7 fields + citations"]
    gate -->|"old answer + failed field names"| repair["Sol feedback repair via codex exec<br/>same source, high reasoning<br/>returns 7 fields + citations"]
    fresh --> score["Paired values, citations, numeric harm<br/>unique source coverage, tokens and timing"]
    repair --> score
\x60\x60\x60

Each CLI-request node asks for the same seven-field answer and source-group citations. The fresh-retry task payload has the original source/task; repair also includes the exact original output and field-name flags. The runner waits for all requests in a bounded dispatch wave before starting the next wave. There is one CLI request per arm, not a guaranteed single physical model draw: internal CLI reconnect/retry behavior is not independently disabled. The comparison is the repair package versus another attempt, rather than isolated feedback versus prior-answer exposure.
"""
    rules = ("### What the sources say and how solvability was checked\n\n"
        "Resolve each commercial field separately: line scope beats order defaults, then authority, effective timestamp and revision; both recorded and effective timestamps must be available by the inclusive cutoff. "
        "In the movement table, select the highest recorded-by-cutoff revision before testing occurrence and state. Exact ingestion copies count once; selected VOID rows and active reversal references do not become additive shipments. "
        "For a return, use its referenced selected shipment's date, SKU, handling UOM and dated allocation version. Same-SKU lines remain distinct accounts.\n\n"
        "Open units are approved ordered demand minus allocated shipments plus accepted allocated returns. Price tiers use ordered demand before movements. Divide gross pack cents by pricing pack size, "
        "apply tier rebates sequentially, add unit fee and converted pack fee, subtract unit credit, then round once half-up to integer cents. Warehouse cartons and pricing packs are different units. "
        "All generated order statuses remain active; this round does not test order cancellations.\n\n"
        "Every rendered packet is reconstructed into source facts, checked for unique current terms, complete dated joins, exact allocation units, reference validity and return bounds. "
        "Constructor Decimal gold, a separate Fraction reducer, independent text/SQL/Decimal auditing and a separately authored text/Fraction audit agree. "
        "All 1,056 possible main sources across four levels and 32 potential pilot sources were pre-audited; the selected level's actual 264 possible main sources were independently checked again before a main CLI request. "
        "Instruction review checked units and precedence explicitly. Reducer agreement alone would not rule out two implementations sharing the same mistaken rule. "
        "Seventeen fixture tests include hand equations, historical returns, cutoff boundaries, exact half-up rounding, source tampering and separate citation checks.\n\n"
        "Directly exporting the generator's exact targets would be the simplest labelling method. Requesting candidate answers from Sol also supplies natural rejected answers and corrections for the paired comparison.\n\n"
        "[EvoEnv](https://arxiv.org/abs/2605.14392) (Shi et al., 2026) combines executable task generators with staged validation, semantic review, solver-relative difficulty calibration and novelty checks. "
        "Our coded procurement packs, independent source reviews and pilot ladder illustrate related data steps; our duplicate checks address record overlap, not novelty of task programs. "
        "We do not reproduce EvoEnv's reinforcement-learning training or downstream evaluation, and these corrected answers do not establish gains for frontier models.\n\n"
        f"The healthy pilot protocol is 23-high-v4d. Main is {protocol.get('protocol', 'not yet saved')} with {workers} maximum workers in bounded waves; "
        "the main-only infrastructure helper changes dispatch metadata, not model, source, prompt, eligibility, scoring or paired statistics. "
        "Earlier HTTP 429 attempts remain archived and do not enter the healthy ladder or main accuracy. The experiment-supplied task payload contains only opaque ID, task instructions and rendered documents; no gold, family, level or structured record is sent. "
        "Codex can add its own internal context, which these caches do not capture.\n\n")
    figure_names = ["healthy_pilot.png", "baseline_and_recovery.png", "paired_outcomes.png", "numeric_error_distribution.png", "family_groups.png", "quantity_source_audit.png"] if complete else ["healthy_pilot.png", "main_pending.png", "quantity_source_audit.png"]
    figure_text = ["### Reading the figures\n\nThe pilot chart counts observed value failures, not service errors. The main figures separate unselected original sources from the selected paired cohort; source audits are labelled expectations rather than model reasoning."]
    descriptions = high_complete_figure_interpretations(report)
    for name in figure_names:
        figure_text.append(f"![{descriptions[name]}](figures/high_v4_complete/{name})\n\n{descriptions[name]}")
    discussion = ("### Why reliable gains are hard to establish\n\n"
        "When original accuracy is high, only a selected failure cohort remains, and another attempt can also succeed on it. "
        "A genuine failure first needs valid source truth: an evaluator bug, missing conversion rule or unsupported citation policy can create apparent headroom without a wrong model value. "
        "This round checks visible-text solvability and keeps citation errors secondary for that reason.\n\n"
        + search_yield +
        "One wrong field rejects all-value success, which is appropriate for using an order but can hide partial improvements. Report newly wrong fields separately from worsening a field that was already wrong. "
        "Also count unique corrected sources: two successful methods on the same packet do not yield two independently solved cases. " +
        high_complete_coverage_markdown(report) +
        "\n\nThe verifier is an oracle for this fictional task because it knows exact truth. Field-name feedback is privileged even though it omits the expected values. "
        "A result on selected failures does not estimate accuracy on an ordinary production stream, and the separate audit is a baseline check rather than a post-training evaluation. "
        "No weights are updated, no held-out evaluation after training is performed, and corrected outputs are only candidate correction data. "
        "Shared templates, active-only statuses, clean tables, a model alias and the particular inference setup limit generalization. "
        "This round changes source length and reasoning relative to earlier rounds, so cross-round differences cannot isolate which change caused a pattern.\n\n")
    reporting = ("### Usage, provenance and offline reproduction\n\n"
        "All responses and failed/pending attempts remain in their original full-request caches. The healthy pilot and main results are separate from the archived service attempts. "
        "USD cost is unavailable, not zero. Token components must not be double-counted, and requests without usage remain unknown. "
        "The complete metrics report per-arm input/output components, request counts, timings and observed reconnect sensitivity. "
        "The appendix reads saved files only, rechecks completed pair counts/source identities/feedback, and generates figures without calling a model. "
        "The frozen four core helpers are retained unchanged; high_parallel.py records the main-only two-worker infrastructure fork. "
        "The posthoc helper below is presentation code, and normal execution has no automatic live branch.\n")
    text = "\n\n".join([intro, overview, flow, high_complete_pilot_markdown(report), rules,
                         high_complete_results_markdown(report), "### Wrong fields and their practical effect\n\n" + high_complete_error_analysis(report),
                         high_complete_less_common_errors_markdown(report), "\n\n".join(figure_text),
                         high_complete_examples_markdown(report), high_complete_prompt_markdown(report), discussion, reporting,
                         high_complete_usage_markdown(report)])
    return {"markdown": text, "readme_appendix": text, "headline": headline, "state": report["state"],
            "example_case_ids": [e["case_id"] for e in report["examples"]],
            "absent_categories": [HIGH_COMPLETE_LABELS[k] for k in HIGH_COMPLETE_CATEGORIES if complete and not report["categories"][k]]}

