"""Read-only v4 reporting. No collection, cache replay, resumption or model calls."""
from pathlib import Path
import copy
import hashlib
import gzip
import json
from collections import Counter


HIGH_REPORT_VERSION = "23-high-offline-report-v1"
HIGH_REPORT_STATUS_ORDER = ["usable_answer", "http_429", "other_terminal_failure", "pending"]
HIGH_REPORT_STATUS_LABELS = {
    "usable_answer": "Usable model answer", "http_429": "Terminal HTTP 429",
    "other_terminal_failure": "Other terminal failure", "pending": "Interrupted / pending",
}


def high_report_read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def high_report_read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line]


def high_report_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def high_report_source_map(root):
    data = Path(root) / "data"
    sources = {}
    for directory in sorted(data.glob("high_v4*")):
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*cases.jsonl")):
            for case in high_report_read_jsonl(path):
                cid = case["case_id"]
                if cid in sources and sources[cid]["content_hash"] != case["content_hash"]:
                    raise ValueError("Same source ID has different documents: " + cid)
                sources[cid] = case
    return sources


def high_read_preflight(root):
    """Stream hash-checked potential cohorts; retain only representative sources."""
    directory = Path(root) / "data" / "high_v4" / "preflight"
    if not (directory / "manifest.json").exists():
        return None
    manifest = high_report_read_json(directory / "manifest.json")
    identities, semantic_ids, examples = set(), set(), []
    for block in manifest["levels"]:
        path = directory / block["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != block["compressed_sha256"]:
            raise ValueError("Compressed preflight source hash differs: " + path.name)
        digest, count, kept = hashlib.sha256(), 0, set()
        with gzip.open(path, "rb") as stream:
            for raw in stream:
                digest.update(raw)
                case = json.loads(raw)
                if case["case_id"] in identities or case["semantic_hash"] in semantic_ids:
                    raise ValueError("Repeated potential preflight source")
                identities.add(case["case_id"])
                semantic_ids.add(case["semantic_hash"])
                count += 1
                if case["family"] not in kept:
                    examples.append(case)
                    kept.add(case["family"])
        if count != block["n_cases"] or digest.hexdigest() != block["uncompressed_sha256"]:
            raise ValueError("Preflight row count or uncompressed source hash differs")
    checks = {}
    for filename in ["independent_sql_audit.json", "independent_fraction_audit.json"]:
        if (directory / filename).exists():
            result = high_report_read_json(directory / filename)
            checks[filename] = {k: v for k, v in result.items()
                                if k in {"n_cases", "n_cases_total", "all_passed", "all_level_cohorts_pass", "n_answer_or_evidence_mismatches_total"}}
    return {"manifest": manifest, "n_unique_main_sources": len(identities), "case_ids": identities,
            "examples": examples, "independent_checks": checks}


def high_inspect_raw_attempts(root, source_map=None, validator=None):
    """Read incomplete records directly; never invoke high_call_model."""
    root = Path(root)
    source_map = source_map if source_map is not None else high_report_source_map(root)
    validator = validator or globals().get("high_validate_answer")
    attempts, unknown_records = [], []
    for directory in sorted((root / "data").glob("high_v4*")):
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("cache/*.json")):
            row = high_report_read_json(path)
            request = row.get("request", {})
            canonical = json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            key = hashlib.sha256(canonical.encode()).hexdigest()
            if row.get("key") != key or path.stem != key:
                raise ValueError("Raw request cache identity mismatch: " + str(path))
            recorded = row.get("attempts") or []
            if not recorded:
                unknown_records.append(str(path.relative_to(root)).replace("\\", "/"))
            for index, attempt in enumerate(recorded):
                pending = bool(attempt.get("pending"))
                error = attempt.get("error")
                final = attempt.get("final_assistant_response") or ""
                parsed = attempt.get("parsed")
                if parsed is None and final:
                    try:
                        parsed = json.loads(final)
                    except ValueError:
                        pass
                answer = None
                if (type(parsed) is dict and set(parsed) == {"results"}
                        and type(parsed["results"]) is list and len(parsed["results"]) == 1
                        and type(parsed["results"][0]) is dict):
                    candidate = parsed["results"][0]
                    expected_ids = request.get("expected_case_ids", [])
                    if len(expected_ids) == 1 and candidate.get("case_id") == expected_ids[0]:
                        answer = candidate
                if pending:
                    status = "pending"
                elif error and "429" in str(error):
                    status = "http_429"
                elif error or answer is None:
                    status = "other_terminal_failure"
                else:
                    status = "usable_answer"
                cid = (request.get("expected_case_ids") or [None])[0]
                source = source_map.get(cid)
                verification = None
                if status == "usable_answer" and source is not None and validator is not None:
                    verification = validator(source, answer)
                attempts.append({
                    "request_key": key, "attempt_index": index, "case_id": cid,
                    "protocol": request.get("protocol"), "directory": directory.name,
                    "source_path": str(path.relative_to(root)).replace("\\", "/"),
                    "status": status, "pending": pending, "error": error,
                    "started_at": attempt.get("started_at"), "finished_at": attempt.get("finished_at"),
                    "reasoning_effort": request.get("reasoning_effort"), "model": request.get("model"),
                    "stage": request.get("stage"), "usage": attempt.get("token_usage") or {},
                    "request": request, "response": answer, "raw_response": final,
                    "verification": verification,
                })
    identities = [(row["request_key"], row["attempt_index"]) for row in attempts]
    if len(set(identities)) != len(identities):
        raise ValueError("A raw physical attempt appears in multiple report directories")
    return attempts, unknown_records


def high_load_report(root=Path("."), validator=None):
    """Support both completed scientific bundles and service-blocked artifacts."""
    root = Path(root)
    sources = high_report_source_map(root)
    preflight = high_read_preflight(root)
    if preflight:
        sources.update({case["case_id"]: case for case in preflight["examples"]})
    attempts, unknown = high_inspect_raw_attempts(root, sources, validator)
    main = root / "data" / "high_v4" / "main"
    complete = (main / "manifest.json").exists() and (main / "metrics.json").exists()
    bundle = None
    if complete:
        manifest = high_report_read_json(main / "manifest.json")
        complete = manifest.get("phase") == "interventions_complete"
        if complete:
            bundle = {"manifest": manifest, "metrics": high_report_read_json(main / "metrics.json"),
                      "protocol": high_report_read_json(main / "protocol.json"),
                      "selection": high_report_read_json(main / "selection.json"),
                      "cases": high_report_read_jsonl(main / "cases.jsonl"),
                      "candidates": high_report_read_jsonl(main / "candidates.jsonl"),
                      "interventions": high_report_read_jsonl(main / "interventions.jsonl")}
    protocol_path = root / "data" / "high_v4" / "pilot" / "protocol.json"
    pilot_protocol = high_report_read_json(protocol_path) if protocol_path.exists() else None
    ladder_path = protocol_path.parent / "ladder.json"
    ladder = high_report_read_json(ladder_path) if ladder_path.exists() else None
    counts = Counter(row["status"] for row in attempts)
    tokens = Counter()
    for row in attempts:
        tokens.update({k: v for k, v in row["usage"].items() if type(v) in (int, float)})
    audits = []
    for directory in sorted((root / "data").glob("high_v4*")):
        if directory.is_dir():
            for path in sorted(directory.rglob("material_audit.json")):
                data = high_report_read_json(path)
                audits.append({"path": str(path.relative_to(root)).replace("\\", "/"),
                               "passed": data.get("passed"), "n_cases": data.get("n_cases"),
                               "method": data.get("method")})
    active = [row for row in attempts if row["directory"] == "high_v4"]
    stopped = bool(list((root / "data" / "high_v4").rglob("infrastructure_stop.json")))
    state = ("complete" if complete else "service_blocked" if stopped else
             "pilot_complete_main_incomplete" if ladder else "in_progress" if active else
             "service_blocked" if attempts else "prepared_only")
    return {"report_version": HIGH_REPORT_VERSION, "root": str(root),
            "state": state,
            "bundle": bundle, "sources": sources, "attempts": attempts,
            "status_counts": {key: counts[key] for key in HIGH_REPORT_STATUS_ORDER},
            "n_started_requests": len(attempts), "unknown_cache_records": unknown,
            "recorded_usage": dict(tokens),
            "n_requests_with_usage": sum(bool(row["usage"]) for row in attempts),
            "n_requests_missing_usage": sum(not bool(row["usage"]) for row in attempts),
            "usage_incomplete": bool(counts["pending"] or unknown or any(not row["usage"] for row in attempts)),
            "pilot_protocol": pilot_protocol, "pilot_ladder": ladder,
            "preflight": preflight,
            "material_audits": audits,
            "usable_answers": [row for row in attempts if row["status"] == "usable_answer"],
            "accuracy_warning": "Service failures and pending attempts have no model answer. They are not wrong extraction values. Archived interrupted-pilot answers do not select difficulty or estimate population accuracy."}


def high_report_table(headers, rows):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "| " + " | ".join(["---"] * len(headers)) + " |"] +
                     ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows])


def high_plot_report(report, root=Path("."), write=False):
    """Return figures; save only on explicit write=True, without any model calls."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    root = Path(root)
    output = root / "figures" / "high_v4"
    figures = []
    cfg = (report.get("pilot_protocol") or {}).get("config", {})
    levels = cfg.get("levels", [1, 2, 3, 4])
    sizes = {1: 32, 2: 64, 3: 128, 4: 192}
    fig, ax = plt.subplots(figsize=(10, 4.5))
    bars = ax.bar([str(level) for level in levels], [sizes[level] for level in levels],
                  color="#376d91", edgecolor="white")
    ax.bar_label(bars, labels=[f"{sizes[level]} shipments\n{cfg.get('n_cases', 8)} planned cases" for level in levels], padding=5)
    ax.set_ylim(0, max(sizes.values()) * 1.26)
    ax.set_xlabel("Predeclared difficulty level")
    ax.set_ylabel("Logical SH-* shipment IDs per source packet")
    ax.set_title("The planned ladder increases source histories from 32 to 192 shipments", pad=16)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    figures.append({"filename": "planned_ladder.png", "figure": fig,
                    "alt": "Planned shipment counts of 32, 64, 128 and 192 across the four source difficulty levels.",
                    "interpretation": "These bars describe generated source size, not model difficulty or observed error rates. Correction copies, returns, reversals and distractor shipments are additional rows."})
    counts = report["status_counts"]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    labels = [HIGH_REPORT_STATUS_LABELS[k] for k in HIGH_REPORT_STATUS_ORDER]
    values = [counts[k] for k in HIGH_REPORT_STATUS_ORDER]
    bars = ax.barh(labels[::-1], values[::-1], color=["#76838d", "#a46d3c", "#a7473f", "#46825c"])
    ax.bar_label(bars, padding=4)
    ax.set_xlim(0, max(values + [1]) * 1.25)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Recorded CLI subprocess attempts across preserved protocols")
    ax.set_title(f"Service status: {counts['usable_answer']} usable answers from {report['n_started_requests']} recorded attempts", pad=16)
    figures.append({"filename": "service_status.png", "figure": fig,
                    "alt": f"Raw attempt status: {counts['usable_answer']} usable answers, {counts['http_429']} terminal HTTP 429 failures, {counts['other_terminal_failure']} other terminal failures and {counts['pending']} interrupted pending records.",
                    "interpretation": "An HTTP 429 is a service rejection, and a pending record has no terminal answer. This is an availability chart. It is not an extraction-accuracy chart, and a missing answer is not a wrong quantity or price."})
    if report["state"] == "complete" and report["bundle"]["metrics"]["n_selected"]:
        metrics = report["bundle"]["metrics"]
        rows = metrics["interventions"]
        fig, ax = plt.subplots(figsize=(10, 4.8))
        names = [row["arm"].replace("_", " ") for row in rows]
        n = metrics["n_selected"]
        bars = ax.bar(names, [row["value_correct_valid_schema"] for row in rows], color=["#376d91", "#46825c"])
        ax.bar_label(bars, labels=[f"{row['value_correct_valid_schema']}/{n}" for row in rows], padding=5)
        ax.set_ylim(0, max(1, n) * 1.25)
        ax.set_ylabel("Paired selected cases recovered with valid schema and all values correct")
        ax.set_title("Fresh retry and feedback repair are compared on the same original value failures", pad=16)
        figures.append({"filename": "paired_recovery.png", "figure": fig,
                        "alt": "Recovered source cases for fresh retry and feedback repair, using the same selected original failures.",
                        "interpretation": "The numerator counts usable, schema-valid replies with all seven values correct. Every selected case remains in each denominator. Citation correctness is reported separately; equal request counts do not imply equal prompt-token or compute cost."})
    if write:
        output.mkdir(parents=True, exist_ok=True)
        for item in figures:
            path = output / item["filename"]
            item["figure"].savefig(path, bbox_inches="tight", dpi=160)
            item["path"] = str(path.relative_to(root)).replace("\\", "/")
            plt.close(item["figure"])
    return figures


def high_source_worked_example(case, trace=None, heading="Preflight source audit"):
    """Traceable arithmetic from visible source. Never invent a model response."""
    trace_fn = globals().get("high_calculation_trace")
    if trace is None:
        if trace_fn is None:
            raise RuntimeError("Load embedded fixture helpers before source-audit reporting")
        trace = trace_fn(case)
    record = case["source_record"]
    q, p = trace["ordered_units"], trace["price"]
    positive = sum(row["net_dispatched_units"] for row in trace["events"] if row["net_dispatched_units"] > 0)
    returned = -sum(row["net_dispatched_units"] for row in trace["events"] if row["net_dispatched_units"] < 0)
    changed = [row for row in trace["events"] if row["reason"] not in {"shipment", "accepted_return", "other_line_allocation"}]
    returned_rows = [row for row in trace["events"] if row["reason"] == "accepted_return" and row["net_dispatched_units"]]
    interesting = returned_rows[:1] + changed[:2]
    rows = []
    for row in interesting:
        rows.append([row["event_id"], row["selected_revision"], row["reason"].replace("_", " "),
                     row["net_dispatched_units"], row.get("units_per_uom", ""), row.get("target_share_percent", "")])
    winners = trace["term_winners"]
    text = (f"#### {heading}: {case['case_id']}\n\n"
        f"This is source validation, not a model result. Target {record['target_order_id']} / {record['target_line_id']} "
        f"uses SKU {record['target_sku']}. The current demand winner is {winners['ordered_units']['approval']} "
        f"in {winners['ordered_units']['source']}: {q:,} ordered individual units. "
        f"The selected physical histories allocate {positive:,} dispatched units and {returned:,} accepted returned units "
        f"to this line. Open demand is {q:,} - ({positive:,} - {returned:,}) = **{trace['open_units']:,} units**.\n\n")
    if rows:
        text += high_report_table(["Event", "Selected revision", "Outcome", "Signed target units", "Units/UOM", "Target share %"], rows) + "\n\n"
    if returned_rows:
        row = returned_rows[0]
        text += (f"Return {row['event_id']} refers to {row['reference']}. Its selected amount is {row['selected_quantity']} original handling units; "
                 f"the shipment-date factor is {row['units_per_uom']} and target allocation is {row['target_share_percent']}%. "
                 f"The lookup dates are {row['uom_effective_from']} for UOM and {row['allocation_effective_from']} for allocation. "
                 "The return's own later date does not select a new factor or share.\n\n")
    text += (f"Price plan {p['plan']} uses the {p['tier_minimum']:,}-unit tier, tested against {p['tier_ordered_units']:,} "
             f"ordered units. Its {p['gross_pack_cents']:,}-cent pack contains {p['pack_units']} units. "
             f"Divide first, apply {p['rebate_a_bps']}/10,000 then {p['rebate_b_bps']}/10,000 sequential rebates, "
             f"add the {p['fee_unit_cents']}-cent unit fee and {p['pack_fee_unit_cents']}-cent converted pack fee, "
             f"subtract the {p['credit_unit_cents']}-cent unit credit. The exact unrounded unit cents are "
             f"{p['unrounded_unit_cents']}; final half-up rounding gives **{p['rounded_unit_cents']} cents**. "
             "These expected values check source solvability; they are not predictions or evidence that a model failed.\n")
    return text


def high_choose_source_examples(report, n=5):
    preferred = (report.get("preflight") or {}).get("examples") or list(report["sources"].values())
    potential = sorted(preferred, key=lambda c: (c["level"], c["family"], c["case_id"]))
    chosen, seen = [], set()
    # Cover different semantic variants and lengths where the frozen sources permit it.
    for level in [1, 2, 3, 4]:
        candidates = [c for c in potential if c["level"] == level]
        fresh = next((c for c in candidates if c["family"] not in seen), None)
        if fresh:
            chosen.append(fresh)
            seen.add(fresh["family"])
    for case in potential:
        if len(chosen) >= n:
            break
        if case["family"] not in seen:
            chosen.append(case)
            seen.add(case["family"])
    return chosen[:n]

