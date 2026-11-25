"""High-effort v4 with separately controlled prepare/original/intervention phases.

Load high_transport, high_fixtures, and independent high_material_audit first.
All helpers are notebook-local; no earlier round is imported or overwritten.
"""
import copy
import hashlib
import json
import math
import random
import statistics
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


HIGH_PROTOCOL = "23-high-v4b"
HIGH_MODEL = "gpt-6.1-sol"
HIGH_ARMS = ["fresh_retry", "feedback_repair"]
HIGH_PILOT_CONFIG = {"levels": [1, 2, 3, 4], "seeds": [244101, 244202, 244303, 244404],
    "n_cases": 8, "min_value_failures": 3, "max_workers": 1, "timeout_s": 900,
    "max_physical_cli_requests": 456, "protocol": HIGH_PROTOCOL}
HIGH_MAIN_CONFIG = {"n_initial": 160, "n_expansion": 80, "expand_below_value_failures": 40,
    "n_audit": 24, "max_selected": 80, "seed_initial": 244160, "seed_expansion": 244080,
    "seed_audit": 244024, "ranking_seed": 244777, "dispatch_seed": 244888,
    "bootstrap_seed": 244999, "bootstrap_draws": 20000, "max_workers": 1,
    "timeout_s": 900, "max_physical_cli_requests": 456, "protocol": HIGH_PROTOCOL}
HIGH_FULL_CONFIG = HIGH_MAIN_CONFIG


def high_canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def high_hash(value):
    return hashlib.sha256(high_canonical(value).encode("utf-8")).hexdigest()


def high_write_json(path, value):
    high_transport_atomic_json(Path(path), value)


def high_write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("".join(high_canonical(row) + "\n" for row in rows), encoding="utf-8", newline="\n")
    temporary.replace(path)


def high_read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def high_freeze_json(path, value):
    path = Path(path)
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != value:
        raise ValueError(f"Frozen v4 protocol/input changed: {path.name}")
    high_write_json(path, value)


def high_freeze_jsonl(path, rows):
    path = Path(path)
    if path.exists() and high_read_jsonl(path) != rows:
        raise ValueError(f"Frozen v4 cases changed: {path.name}")
    high_write_jsonl(path, rows)


def high_config(config=None, pilot=False):
    cfg = {**(HIGH_PILOT_CONFIG if pilot else HIGH_MAIN_CONFIG), **copy.deepcopy(config or {})}
    if cfg["protocol"] != HIGH_PROTOCOL or cfg["timeout_s"] != 900 or cfg["max_workers"] != 1:
        raise ValueError("Use the frozen v4b profile, 900-second timeout, and one worker")
    if type(cfg["max_physical_cli_requests"]) is not int or not 1 <= cfg["max_physical_cli_requests"] <= 456:
        raise ValueError("Physical CLI request cap must be within 1..456")
    if pilot:
        if cfg["levels"] != [1, 2, 3, 4] or len(cfg["seeds"]) != 4 or len(set(cfg["seeds"])) != 4:
            raise ValueError("The ladder has four declared levels and distinct seeds")
        if not 1 <= cfg["n_cases"] <= 8 or not 1 <= cfg["min_value_failures"] <= cfg["n_cases"]:
            raise ValueError("Pilot size/threshold outside bounds")
    else:
        for field, maximum in (("n_initial", 160), ("n_expansion", 80), ("n_audit", 24), ("max_selected", 80)):
            if type(cfg[field]) is not int or not 0 <= cfg[field] <= maximum:
                raise ValueError(f"{field} outside declared bounds")
        if not cfg["n_initial"] or not 0 <= cfg["expand_below_value_failures"] <= 40:
            raise ValueError("Initial cohort must be nonempty; expansion threshold is bounded at 40")
        if len({cfg["seed_initial"], cfg["seed_expansion"], cfg["seed_audit"]}) != 3 or cfg["bootstrap_draws"] < 100:
            raise ValueError("Use distinct cohort seeds and at least 100 bootstrap draws")
    return cfg


def high_profile_protocol(config, phase, **extra):
    return {"protocol": HIGH_PROTOCOL, "phase": phase, "config": config, "model": HIGH_MODEL,
        "reasoning_effort": "high", "case_count_per_cli_request": 1, "timeout_s": 900,
        "max_workers": config["max_workers"], "transport_version": HIGH_TRANSPORT_VERSION,
        "cli_options": list(HIGH_CLI_OPTIONS), "fixture_version": HIGH_VERSION,
        "task_instructions": HIGH_TASK_INSTRUCTIONS, "instructions_hash": high_hash(HIGH_TASK_INSTRUCTIONS),
        "retry_boundary": "One CLI subprocess per full request; no orchestration retries. Internal CLI network retries are not independently disabled or verified; raw error/reconnect events are retained.",
        "infrastructure_stop_policy": "One worker. Stop the incomplete phase after the first transport failure, before dispatching any next request; retain the complete failed cache and require explicit service review. Cached failures never requery.",
        "eligibility": "Successful usable single-case reply, valid schema, and at least one incorrect typed field value. Citation-only, schema, parse, missing-response, and transport failures are never primary value-failure cases.",
        "model_weights_updated": False, "errors_guaranteed": False, **extra}


def high_preflight(cases):
    fixture = high_audit_fixtures(cases)
    material = high_material_audit(cases)
    if not material.get("passed") or material.get("n_cases") != len(cases):
        raise AssertionError("Independent rendered-source audit did not pass every potential case")
    if len({c["case_id"] for c in cases}) != len(cases) or len({c["semantic_hash"] for c in cases}) != len(cases):
        raise AssertionError("Potential cases must have unique IDs and independent semantic records")
    return fixture, material


def high_model_input(case):
    return {"case_id": case["case_id"], "task_instructions": HIGH_TASK_INSTRUCTIONS, "documents": case["document"]}


def high_case_prompt(case):
    return {"task_instructions": HIGH_TASK_INSTRUCTIONS, "documents": case["document"]}


def high_value_failure(row):
    return (not row["transport_error"] and row["response"] is not None and
            row["verification"]["valid_schema"] and not row["verification"]["exact_fields"])


def high_value_success(row):
    return (not row["transport_error"] and row["response"] is not None and
            row["verification"]["valid_schema"] and row["verification"]["exact_fields"])


def high_error_kind(verification, transport_error, response):
    if transport_error:
        return "transport_failure"
    if response is None:
        return "unusable_response"
    if not verification["valid_schema"]:
        return "schema_failure"
    if not verification["exact_fields"]:
        return "value_failure"
    return "accepted" if verification["accepted"] else "evidence_only_failure"


def high_generic_feedback(original):
    verification = original["verification"]
    return {"wrong_fields": [f for f in HIGH_FIELDS if not verification["field_correct"][f]],
        "schema_failed": not verification["valid_schema"],
        "evidence_failed_fields": [f for f in HIGH_FIELDS if not verification["evidence_correct"][f]]}


def high_extract_single(response, case_id):
    parsed = response.get("parsed")
    if parsed is None:
        try:
            parsed = json.loads(response.get("final_assistant_response", ""))
        except (TypeError, ValueError):
            return None, "unparseable_json"
    if (type(parsed) is not dict or set(parsed) != {"results"} or type(parsed["results"]) is not list
            or len(parsed["results"]) != 1 or type(parsed["results"][0]) is not dict
            or parsed["results"][0].get("case_id") != case_id):
        return None, "single_case_integrity_error"
    return parsed["results"][0], None


def high_make_job(case, arm="original", original=None):
    job = {"case": case, "arm": arm, "stage": "repair" if arm == "feedback_repair" else "generate",
           "sample": 1 if arm == "fresh_retry" else 0}
    if original is not None:
        job["original"] = original
    return job


def high_job_request(job):
    feedback = None
    if job["arm"] == "feedback_repair":
        old = job["original"]
        feedback = {job["case"]["case_id"]: {"original_output": old["response"],
                                                "validator_feedback": high_generic_feedback(old)}}
    return high_make_request(HIGH_MODEL, job["stage"], [high_model_input(job["case"])],
        sample=job["sample"], feedback=feedback, protocol=HIGH_PROTOCOL)


def high_numeric_errors(case, answer):
    values = answer.get("answer", {}) if type(answer) is dict else {}
    output = {}
    for field in ("quantity_units", "unit_price_cents"):
        gold, value = case["gold"][field], values.get(field)
        output[field] = abs(value - gold) if type(value) is int and type(gold) is int else None
    return output


def high_run_jobs(jobs, directory, config, live=False, progress=None):
    if len(jobs) > config["max_physical_cli_requests"]:
        raise RuntimeError("Declared physical CLI request cap would be exceeded")

    def invoke(job):
        case = job["case"]
        request = high_job_request(job)
        response = high_call_model(request, Path(directory) / "cache", live=live, timeout_s=900)
        key = response["request_key"]
        answer, parse_error = high_extract_single(response, case["case_id"])
        verification = high_validate_answer(case, answer if not response.get("error") else None)
        reconnect = response.get("observed_reconnect_events", []) or []
        row = {field: case[field] for field in ("case_id", "family", "level", "split", "content_hash", "semantic_hash")}
        row.update({"candidate_id": f"{case['case_id']}:{job['arm']}:{job['sample']}", "model": HIGH_MODEL,
            "reasoning_effort": "high", "arm": job["arm"], "stage": job["stage"], "sample": job["sample"],
            "request_key": key, "response": answer, "verification": verification,
            "transport_error": response.get("error"), "parse_error": response.get("parse_error") or parse_error,
            "error_kind": high_error_kind(verification, response.get("error"), answer), "batch_position": 0,
            "batch_case_ids": [case["case_id"]], "observed_reconnect": bool(reconnect),
            "numeric_absolute_errors": high_numeric_errors(case, answer),
            "raw_failure": response.get("final_assistant_response", "") if answer is None else None})
        if job.get("original"):
            old = job["original"]
            old_ok, new_ok = old["verification"]["field_correct"], verification["field_correct"]
            original_magnitudes = high_numeric_errors(case, old["response"])
            row.update({"original_candidate_id": old["candidate_id"], "original_request_key": old["request_key"],
                "original_wrong_fields": [f for f in HIGH_FIELDS if not old_ok[f]],
                "original_wrong_fields_fixed": [f for f in HIGH_FIELDS if not old_ok[f] and new_ok[f]],
                "new_wrong_fields": [f for f in HIGH_FIELDS if old_ok[f] and not new_ok[f]],
                "original_numeric_absolute_errors": original_magnitudes,
                "worsened_numeric_fields": [f for f in original_magnitudes if original_magnitudes[f] is not None
                    and row["numeric_absolute_errors"][f] is not None and row["numeric_absolute_errors"][f] > original_magnitudes[f]],
                "answer_unchanged": type(answer) is dict and answer.get("answer") == old["response"].get("answer"),
                "feedback_supplied": job["arm"] == "feedback_repair"})
        entry = {"request_key": key, "candidate_id": row["candidate_id"], "case_id": case["case_id"],
            "source_hash": case["content_hash"], "arm": job["arm"], "stage": job["stage"], "sample": job["sample"],
            "split": case["split"], "model": HIGH_MODEL, "reasoning_effort": "high", "timeout_s": 900,
            "usage": response.get("usage", {}) or {}, "transport_error": response.get("error"), "parse_error": row["parse_error"],
            "cli_error_events": response.get("cli_error_events", []) or [], "observed_reconnect_events": reconnect,
            "started_at": response.get("started_at"), "finished_at": response.get("finished_at"),
            "subprocess_elapsed_s": response.get("elapsed_s"), "return_code": response.get("return_code"),
            "resolved_model": response.get("resolved_model"), "cached_this_run": bool(response.get("cached")),
            "cache_file": f"cache/{key}.json"}
        if progress:
            progress({"arm": job["arm"], "case_id": case["case_id"], "cached": entry["cached_this_run"], "error_kind": row["error_kind"]})
        return row, entry

    # Sequential dispatch is intentional in v4b: queued pool work must not keep
    # spending requests after an infrastructure failure has been observed.
    if config["max_workers"] != 1:
        raise ValueError("The v4b infrastructure gate requires exactly one worker")
    completed = []
    for job in jobs:
        row, entry = invoke(job)
        completed.append((row, entry))
        if row["transport_error"]:
            high_write_json(Path(directory) / "infrastructure_stop.json", {
                "protocol": HIGH_PROTOCOL, "phase_complete": False,
                "request_key": row["request_key"], "case_id": row["case_id"], "arm": row["arm"],
                "transport_error": row["transport_error"], "candidate": row, "request_ledger_entry": entry,
                "completed_requests_this_dispatch": len(completed),
                "remaining_requests_not_dispatched": len(jobs) - len(completed),
                "resolution": "Review service availability explicitly. Replaying the same failed cache will stop again; no orchestration retry occurs."})
            raise RuntimeError(f"V4b infrastructure stop after {len(completed)} request(s): {row['transport_error']}")
    return [row for row, _ in completed], [entry for _, entry in completed]


def high_canonical_ledger(ledger):
    validation = {"new_cli_subprocesses_this_run": sum(not e["cached_this_run"] for e in ledger),
                  "replayed_requests_this_run": sum(e["cached_this_run"] for e in ledger)}
    for entry in ledger:
        entry.pop("cached_this_run")
    return validation


def high_row_metrics(rows):
    counts = Counter(r["error_kind"] for r in rows)
    return {"n_attempted_cases": len(rows), "usable_replies": sum(r["response"] is not None and not r["transport_error"] for r in rows),
        "valid_schema": sum(r["verification"]["valid_schema"] for r in rows),
        "raw_exact_fields": sum(r["verification"]["exact_fields"] for r in rows),
        "value_correct_valid_schema": sum(high_value_success(r) for r in rows),
        "accepted": sum(r["verification"]["accepted"] for r in rows),
        "value_failure_cases": sum(high_value_failure(r) for r in rows),
        "error_categories": {kind: counts[kind] for kind in ("accepted", "value_failure", "evidence_only_failure", "schema_failure", "unusable_response", "transport_failure")},
        "wrong_field_counts": {field: sum(not r["verification"]["field_correct"][field] for r in rows if r["response"] is not None and not r["transport_error"]) for field in HIGH_FIELDS}}


def high_usage(ledger):
    output, total = {}, Counter()
    groups = defaultdict(list)
    for entry in ledger:
        groups["audit" if entry["split"] == "audit" else entry["arm"]].append(entry)
    for arm, entries in sorted(groups.items()):
        usage = Counter()
        for entry in entries:
            usage.update({k: v for k, v in entry["usage"].items() if type(v) in (int, float)})
        total.update(usage)
        seconds = [e["subprocess_elapsed_s"] for e in entries if e["subprocess_elapsed_s"] is not None]
        output[arm] = {"physical_cli_requests": len(entries), "tokens": dict(usage),
            "summed_subprocess_seconds": sum(seconds), "median_request_seconds": statistics.median(seconds) if seconds else None,
            "requests_with_observed_reconnects": sum(bool(e["observed_reconnect_events"]) for e in entries),
            "requests_with_cli_error_events": sum(bool(e["cli_error_events"]) for e in entries)}
    return {"overall": dict(total), "by_arm": output,
        "note": "One physical CLI subprocess per request, no orchestration retries; internal inference/network retries are not independently guaranteed. Equal intervention request budgets do not imply equal prompt-token budgets. Cached/reasoning token components must not be added twice."}


def high_prepare_pilot(config=None, root=Path(".")):
    cfg = high_config(config, pilot=True)
    directory = Path(root) / "data" / "high_v4" / "pilot"
    cases, levels = [], []
    for level, seed in zip(cfg["levels"], cfg["seeds"]):
        block = high_make_cases(cfg["n_cases"], seed, level=level, split="pilot", start_index=0)
        levels.append({"level": level, "seed": seed, "case_ids": [c["case_id"] for c in block], "cases_hash": high_hash(block)})
        cases.extend(block)
    fixture, material = high_preflight(cases)
    protocol = high_profile_protocol(cfg, "pilot_ladder", potential_cases_hash=high_hash(cases), levels=levels,
        stopping_policy="First level with at least min_value_failures genuine valid-schema value-failure cases; otherwise highest level with threshold_met=false",
        max_pilot_requests=cfg["n_cases"] * len(cfg["levels"]), material_audit_hash=high_hash(material))
    high_freeze_json(directory / "protocol.json", protocol)
    high_freeze_jsonl(directory / "potential_cases.jsonl", cases)
    high_freeze_json(directory / "fixture_audit.json", fixture)
    high_freeze_json(directory / "material_audit.json", material)
    return {"config": cfg, "protocol": protocol, "cases": cases, "directory": directory}


def high_run_pilot(config=None, root=Path("."), live=False, progress=None):
    prepared = high_prepare_pilot(config, root)
    cfg, directory, potential = prepared["config"], prepared["directory"], prepared["cases"]
    outcomes, bundles = [], []
    selected, met = cfg["levels"][-1], False
    for level in cfg["levels"]:
        start = time.perf_counter()
        cases = [case for case in potential if case["level"] == level]
        output = directory / f"level_{level}"
        protocol = {"pilot_protocol_hash": high_hash(prepared["protocol"]), "level": level, "cases_hash": high_hash(cases)}
        high_freeze_json(output / "protocol.json", protocol)
        candidates, ledger = high_run_jobs([high_make_job(case) for case in cases], output, cfg, live, progress)
        failures = sum(high_value_failure(row) for row in candidates)
        metrics = {**high_row_metrics(candidates), "usage": high_usage(ledger), "spend_usd": None}
        validation = {**high_canonical_ledger(ledger), "offline": not live, "wall_seconds_this_run": time.perf_counter() - start}
        manifest = {"protocol_hash": high_hash(protocol), "cases_hash": high_hash(cases),
            "request_keys": [e["request_key"] for e in ledger], "level": level, "n_cases": len(cases)}
        high_freeze_json(output / "manifest.json", manifest)
        high_freeze_jsonl(output / "cases.jsonl", cases)
        high_freeze_jsonl(output / "candidates.jsonl", candidates)
        high_freeze_jsonl(output / "request_ledger.jsonl", ledger)
        high_freeze_json(output / "metrics.json", metrics)
        high_write_json(output / "run_validation.json", validation)
        outcomes.append({"level": level, "n_cases": len(cases), "value_failure_cases": failures,
            "threshold_met": failures >= cfg["min_value_failures"], "cases_hash": high_hash(cases), "request_keys": manifest["request_keys"]})
        bundles.append({"cases": cases, "candidates": candidates, "request_ledger": ledger, "metrics": metrics, "manifest": manifest})
        if failures >= cfg["min_value_failures"]:
            selected, met = level, True
            break
    called = {r["case_id"] for bundle in bundles for r in bundle["candidates"]}
    ladder = {"protocol_hash": high_hash(prepared["protocol"]), "config": cfg, "levels": outcomes,
        "selected_level": selected, "threshold_met": met,
        "selection_reason": "First declared value-failure threshold crossing" if met else "Highest declared level; value-failure threshold not met",
        "physical_cli_requests": sum(len(item["request_keys"]) for item in outcomes),
        "uncalled_potential_case_ids": [c["case_id"] for c in potential if c["case_id"] not in called]}
    high_freeze_json(directory / "ladder.json", ladder)
    return {"selected_level": selected, "threshold_met": met, "ladder": ladder, "levels": bundles}


def high_prepare_main(config=None, root=Path("."), pilot=None):
    cfg = high_config(config)
    directory = Path(root) / "data" / "high_v4" / "main"
    ladder_path = Path(root) / "data" / "high_v4" / "pilot" / "ladder.json"
    if not ladder_path.exists():
        raise ValueError("Complete/replay the bounded high-effort pilot before preparing main")
    ladder = json.loads(ladder_path.read_text(encoding="utf-8"))
    if pilot is not None and pilot.get("ladder", pilot) != ladder:
        raise ValueError("Supplied pilot differs from frozen ladder")
    level = ladder["selected_level"]
    initial = high_make_cases(cfg["n_initial"], cfg["seed_initial"], level=level, split="collection", start_index=0)
    expansion = high_make_cases(cfg["n_expansion"], cfg["seed_expansion"], level=level, split="collection", start_index=cfg["n_initial"]) if cfg["n_expansion"] else []
    audit = high_make_cases(cfg["n_audit"], cfg["seed_audit"], level=level, split="audit", start_index=cfg["n_initial"] + cfg["n_expansion"]) if cfg["n_audit"] else []
    cases = initial + expansion + audit
    fixture, material = high_preflight(cases)
    pilot_cases = high_read_jsonl(ladder_path.parent / "potential_cases.jsonl")
    if {c["semantic_hash"] for c in cases} & {c["semantic_hash"] for c in pilot_cases}:
        raise AssertionError("Potential main and pilot semantics overlap")
    ranking = [c["case_id"] for c in initial + expansion]
    random.Random(cfg["ranking_seed"]).shuffle(ranking)
    allocation = {"initial_case_ids": [c["case_id"] for c in initial], "expansion_case_ids": [c["case_id"] for c in expansion],
        "audit_case_ids": [c["case_id"] for c in audit], "failure_selection_ranking": ranking}
    upper = cfg["n_initial"] + cfg["n_expansion"] + cfg["n_audit"] + 2 * min(cfg["max_selected"], cfg["n_initial"] + cfg["n_expansion"])
    if ladder["physical_cli_requests"] + upper > cfg["max_physical_cli_requests"]:
        raise ValueError("Declared total physical CLI request cap would be exceeded")
    protocol = high_profile_protocol(cfg, "prepared_main", selected_level=level, pilot_ladder_hash=high_hash(ladder),
        pilot_threshold_met=ladder["threshold_met"], potential_cases_hash=high_hash(cases), allocation_hash=high_hash(allocation),
        material_audit_hash=high_hash(material), main_request_upper_bound=upper,
        total_request_upper_bound=ladder["physical_cli_requests"] + upper,
        expansion_policy="Collect initial cohort, then the fixed pre-generated expansion iff initial valid-schema value-failure cases are fewer than the declared threshold; never inspect intervention outcomes to expand",
        selection_policy="At most max_selected eligible value-failure cases in the fixed seeded random ranking; all eligible when within cap",
        intervention_policy="Separate explicit phase after original/source review. Fresh retry and feedback repair use the same source, high effort, one-case requests; job dispatch is deterministically shuffled",
        contrast="Repair package (prior answer plus generic failed-field flags) versus a fresh attempt; not isolated feedback versus prior-answer exposure",
        primary_recovery="Successful single-case response with valid schema and all seven typed field values correct; citation content correctness is a separate secondary outcome",
        statistics={"difference": "Feedback repair minus fresh retry success on paired selected cases",
            "bootstrap": "Case-paired resampling with replacement, percentile 95% interval", "draws": cfg["bootstrap_draws"],
            "seed": cfg["bootstrap_seed"], "mcnemar": "Exact conditional two-sided binomial test on discordant pairs",
            "caveat": "Descriptive after adaptive pilot and failure selection; template dependence and small samples limit inference",
            "reconnect_sensitivity": "Exclude a pair if original or either intervention has an observed CLI reconnect event; do not blanket-exclude warnings"},
        audit_boundary="Potential audit packets are validated up front but audit answers are called only after failure selection is frozen and never affect expansion, selection, or repairs")
    high_freeze_json(directory / "protocol.json", protocol)
    high_freeze_jsonl(directory / "potential_cases.jsonl", cases)
    high_freeze_json(directory / "allocation.json", allocation)
    high_freeze_json(directory / "fixture_audit.json", fixture)
    high_freeze_json(directory / "material_audit.json", material)
    return {"config": cfg, "protocol": protocol, "cases": cases, "allocation": allocation,
        "directory": directory, "pilot_ladder": ladder}


def high_load_prepared(root):
    directory = Path(root) / "data" / "high_v4" / "main"
    protocol = json.loads((directory / "protocol.json").read_text(encoding="utf-8"))
    cases = high_read_jsonl(directory / "potential_cases.jsonl")
    allocation = json.loads((directory / "allocation.json").read_text(encoding="utf-8"))
    if high_hash(cases) != protocol["potential_cases_hash"] or high_hash(allocation) != protocol["allocation_hash"]:
        raise ValueError("Frozen potential source/allocation integrity failed")
    if protocol["instructions_hash"] != high_hash(HIGH_TASK_INSTRUCTIONS):
        raise ValueError("Task instructions changed after preparation")
    return directory, protocol, cases, allocation


def high_collect_originals(root=Path("."), live=False, progress=None):
    directory, protocol, potential, allocation = high_load_prepared(root)
    cfg = protocol["config"]
    by_case = {c["case_id"]: c for c in potential}
    initial = [by_case[cid] for cid in allocation["initial_case_ids"]]
    candidates, ledger = high_run_jobs([high_make_job(c) for c in initial], directory, cfg, live, progress)
    initial_failures = sum(high_value_failure(r) for r in candidates)
    expand = initial_failures < cfg["expand_below_value_failures"]
    if expand:
        block = [by_case[cid] for cid in allocation["expansion_case_ids"]]
        rows, entries = high_run_jobs([high_make_job(c) for c in block], directory, cfg, live, progress)
        candidates.extend(rows)
        ledger.extend(entries)
    called_collection = {r["case_id"] for r in candidates}
    eligible = {r["case_id"]: r for r in candidates if high_value_failure(r)}
    selected_ids = [cid for cid in allocation["failure_selection_ranking"] if cid in eligible][:cfg["max_selected"]]
    selection = {"protocol_hash": high_hash(protocol), "initial_value_failure_cases": initial_failures,
        "expanded": expand, "called_collection_case_ids": [c["case_id"] for c in potential if c["case_id"] in called_collection],
        "unused_expansion_case_ids": [cid for cid in allocation["expansion_case_ids"] if cid not in called_collection],
        "eligible_candidate_ids": [eligible[cid]["candidate_id"] for cid in allocation["failure_selection_ranking"] if cid in eligible],
        "selected_case_ids": selected_ids, "selected_candidate_ids": [eligible[cid]["candidate_id"] for cid in selected_ids],
        "selection_ranking_hash": high_hash(allocation["failure_selection_ranking"]),
        "source_hashes": {cid: by_case[cid]["content_hash"] for cid in selected_ids}}
    high_freeze_json(directory / "selection.json", selection)
    # Sealed audit responses follow the frozen selection and cannot change it.
    audit_cases = [by_case[cid] for cid in allocation["audit_case_ids"]]
    rows, entries = high_run_jobs([high_make_job(c) for c in audit_cases], directory, cfg, live, progress)
    candidates.extend(rows)
    ledger.extend(entries)
    validation = {**high_canonical_ledger(ledger), "offline": not live, "phase": "originals"}
    called_ids = {r["case_id"] for r in candidates}
    called_cases = [c for c in potential if c["case_id"] in called_ids]
    metrics = {"collection": high_row_metrics([r for r in candidates if r["split"] == "collection"]),
        "audit": high_row_metrics([r for r in candidates if r["split"] == "audit"]),
        "by_family": [{"family": f, **high_row_metrics([r for r in candidates if r["split"] == "collection" and r["family"] == f])} for f in HIGH_FAMILIES],
        "n_potential_collection": cfg["n_initial"] + cfg["n_expansion"], "n_unused_collection": len(selection["unused_expansion_case_ids"]),
        "n_selected": len(selected_ids), "usage": high_usage(ledger), "physical_cli_requests": len(ledger), "spend_usd": None}
    manifest = {"phase": "originals_complete", "protocol_hash": high_hash(protocol), "cases_hash": high_hash(called_cases),
        "selection_hash": high_hash(selection), "request_keys": [e["request_key"] for e in ledger],
        "n_called_collection": len(called_collection), "n_audit": len(audit_cases), "n_selected": len(selected_ids)}
    high_freeze_jsonl(directory / "cases.jsonl", called_cases)
    high_freeze_jsonl(directory / "candidates.jsonl", candidates)
    high_freeze_jsonl(directory / "original_request_ledger.jsonl", ledger)
    high_freeze_json(directory / "original_metrics.json", metrics)
    high_freeze_json(directory / "original_manifest.json", manifest)
    high_write_json(directory / "original_run_validation.json", validation)
    return {"config": cfg, "protocol": protocol, "cases": called_cases, "candidates": candidates,
        "selection": selection, "request_ledger": ledger, "metrics": metrics, "manifest": manifest}


def high_quantile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    left = math.floor(position)
    right = math.ceil(position)
    return sorted_values[left] + (position - left) * (sorted_values[right] - sorted_values[left])


def high_paired_statistics(pairs, seed, draws, outcome="value"):
    # Pair entries are (fresh_success, repair_success), one per selected case.
    counts = Counter((bool(fresh), bool(repair)) for fresh, repair in pairs)
    n = len(pairs)
    repair_only, fresh_only = counts[False, True], counts[True, False]
    discordant = repair_only + fresh_only
    p = min(1., 2 * sum(math.comb(discordant, i) for i in range(min(repair_only, fresh_only) + 1)) / 2**discordant) if discordant else 1.
    difference = (repair_only - fresh_only) / n if n else None
    interval = [None, None]
    if n:
        deltas = [int(repair) - int(fresh) for fresh, repair in pairs]
        rng = random.Random(seed)
        boot = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws))
        interval = [high_quantile(boot, .025), high_quantile(boot, .975)]
    return {"outcome": outcome, "n_pairs": n, "both_success": counts[True, True], "repair_only": repair_only,
        "fresh_only": fresh_only, "neither_success": counts[False, False],
        "repair_minus_fresh_difference": difference, "paired_bootstrap_95_interval": interval,
        "difference_percentage_points": difference * 100 if n else None,
        "paired_bootstrap_95_interval_percentage_points": [x * 100 if x is not None else None for x in interval],
        "exact_mcnemar_two_sided_p": p if n else None, "discordant_pairs": discordant,
        "bootstrap_draws": draws, "bootstrap_seed": seed,
        "caveat": "Case-paired descriptive inference conditional on pilot and failure selection; shared templates can violate independent-case assumptions. A small or degenerate interval is not proof of equivalence."}


def high_build_exports(cases, originals, interventions):
    by_case = {c["case_id"]: c for c in cases}
    by_original = {r["candidate_id"]: r for r in originals}
    exports = {}
    for arm in ["original", *HIGH_ARMS]:
        rows = [r for r in originals + interventions if r["split"] == "collection" and r["arm"] == arm]
        accepted, rejected, pairs, seen = [], [], [], set()
        for row in rows:
            case = by_case[row["case_id"]]
            if row["verification"]["accepted"] and row["semantic_hash"] not in seen:
                if not high_validate_answer(case, row["response"])["accepted"]:
                    raise AssertionError("Accepted high-effort export failed verification")
                accepted.append({"case_id": row["case_id"], "prompt": high_case_prompt(case), "response": row["response"],
                    "candidate_id": row["candidate_id"], "request_key": row["request_key"], "arm": arm,
                    "reasoning_effort": "high", "semantic_hash": row["semantic_hash"], "verification": row["verification"]})
                seen.add(row["semantic_hash"])
            elif not row["verification"]["accepted"]:
                rejected.append(row)
            if arm != "original" and row["verification"]["accepted"]:
                old = by_original[row["original_candidate_id"]]
                if not high_value_failure(old):
                    raise AssertionError("Preference rejection must be a genuine original value failure")
                pairs.append({"case_id": row["case_id"], "prompt": high_case_prompt(case), "chosen": row["response"],
                    "rejected": old["response"], "chosen_candidate_id": row["candidate_id"], "rejected_candidate_id": old["candidate_id"],
                    "request_keys": [row["request_key"], old["request_key"]], "arm": arm, "semantic_hash": row["semantic_hash"],
                    "provenance": "Verified intervention answer versus an actual original high-effort Sol value failure; no injected model failure"})
        exports[arm] = {"accepted_examples": accepted, "rejected_examples": rejected, "value_preference_pairs": pairs}
    return exports


def high_main_metrics(cases, originals, interventions, selection, ledger, cfg, exports):
    original_by_id = {r["candidate_id"]: r for r in originals}
    grouped = {arm: {r["case_id"]: r for r in interventions if r["arm"] == arm} for arm in HIGH_ARMS}
    ids = selection["selected_case_ids"]
    original_good = {r["semantic_hash"] for r in originals if r["split"] == "collection" and high_value_success(r)}
    original_accepted = {r["semantic_hash"] for r in originals if r["split"] == "collection" and r["verification"]["accepted"]}
    arm_metrics = []
    for arm in HIGH_ARMS:
        rows = list(grouped[arm].values())
        magnitudes = {}
        for field in ("quantity_units", "unit_price_cents"):
            values = [r["numeric_absolute_errors"][field] for r in rows if r["numeric_absolute_errors"][field] is not None]
            magnitudes[field] = {"n_numeric": len(values), "n_non_numeric": len(rows) - len(values),
                "mean_absolute_error": statistics.mean(values) if values else None,
                "median_absolute_error": statistics.median(values) if values else None}
        arm_metrics.append({"arm": arm, **high_row_metrics(rows),
            "original_wrong_fields_fixed": sum(len(r["original_wrong_fields_fixed"]) for r in rows),
            "cases_with_new_wrong_fields": sum(bool(r["new_wrong_fields"]) for r in rows),
            "cases_with_worsened_numeric_error": sum(bool(r["worsened_numeric_fields"]) for r in rows),
            "unchanged_answer_objects": sum(r["answer_unchanged"] for r in rows), "numeric_error_magnitudes": magnitudes,
            "new_value_correct_cases_vs_original": len({r["semantic_hash"] for r in rows if high_value_success(r)} - original_good),
            "new_accepted_cases_vs_original": len({r["semantic_hash"] for r in rows if r["verification"]["accepted"]} - original_accepted)})
    pairs = [(high_value_success(grouped["fresh_retry"][cid]), high_value_success(grouped["feedback_repair"][cid])) for cid in ids]
    accepted_pairs = [(grouped["fresh_retry"][cid]["verification"]["accepted"], grouped["feedback_repair"][cid]["verification"]["accepted"]) for cid in ids]
    clean_ids = [cid for cid in ids if not any(row["observed_reconnect"] for row in
        (grouped["fresh_retry"][cid], grouped["feedback_repair"][cid], original_by_id[grouped["fresh_retry"][cid]["original_candidate_id"]]))]
    clean_pairs = [(high_value_success(grouped["fresh_retry"][cid]), high_value_success(grouped["feedback_repair"][cid])) for cid in clean_ids]
    return {"original_collection": high_row_metrics([r for r in originals if r["split"] == "collection"]),
        "audit": high_row_metrics([r for r in originals if r["split"] == "audit"]), "n_selected": len(ids),
        "interventions": arm_metrics,
        "paired_value_recovery": high_paired_statistics(pairs, cfg["bootstrap_seed"], cfg["bootstrap_draws"]),
        "paired_accepted_recovery": high_paired_statistics(accepted_pairs, cfg["bootstrap_seed"] + 1, cfg["bootstrap_draws"], "strict_acceptance"),
        "reconnect_sensitivity": {"excluded_case_ids": [cid for cid in ids if cid not in clean_ids],
            "paired_value_recovery": high_paired_statistics(clean_pairs, cfg["bootstrap_seed"] + 2, cfg["bootstrap_draws"])},
        "usage": high_usage(ledger), "physical_cli_requests": len(ledger), "spend_usd": None,
        "exports": {arm: {name: len(rows) for name, rows in files.items()} for arm, files in exports.items()},
        "interpretation": {"contrast": "Repair package including previous answer and failed-field flags versus fresh high-effort retry, not feedback alone",
            "primary": "Valid schema and all seven typed values correct; citation-content correctness is secondary",
            "selection": "Conditional on genuine original Sol value failures chosen by pre-outcome random ranking",
            "no_training": "Weights remain frozen; collection recovery is not model learning",
            "money": "CLI tokens and timings recorded; dollar spend is unknown, not zero"}}


def high_load_originals(root):
    directory, protocol, potential, allocation = high_load_prepared(root)
    manifest = json.loads((directory / "original_manifest.json").read_text(encoding="utf-8"))
    cases = high_read_jsonl(directory / "cases.jsonl")
    originals = high_read_jsonl(directory / "candidates.jsonl")
    selection = json.loads((directory / "selection.json").read_text(encoding="utf-8"))
    ledger = high_read_jsonl(directory / "original_request_ledger.jsonl")
    if (manifest["protocol_hash"] != high_hash(protocol) or manifest["cases_hash"] != high_hash(cases)
            or manifest["selection_hash"] != high_hash(selection) or manifest["request_keys"] != [r["request_key"] for r in ledger]):
        raise ValueError("Completed original phase integrity failed")
    return directory, protocol, cases, originals, selection, ledger


def high_run_interventions(root=Path("."), live=False, progress=None):
    directory, protocol, cases, originals, selection, original_ledger = high_load_originals(root)
    cfg = protocol["config"]
    by_case = {c["case_id"]: c for c in cases}
    by_original = {r["candidate_id"]: r for r in originals}
    selected = [by_original[cid] for cid in selection["selected_candidate_ids"]]
    if any(not high_value_failure(row) or row["split"] != "collection" for row in selected):
        raise AssertionError("Selected intervention source is not a genuine collection value failure")
    jobs = [high_make_job(by_case[row["case_id"]], arm, row) for row in selected for arm in HIGH_ARMS]
    random.Random(cfg["dispatch_seed"]).shuffle(jobs)
    dispatch = {"protocol_hash": high_hash(protocol), "selection_hash": high_hash(selection), "seed": cfg["dispatch_seed"],
        "jobs": [{"case_id": job["case"]["case_id"], "arm": job["arm"], "request_key": high_request_key(high_job_request(job))} for job in jobs]}
    high_freeze_json(directory / "dispatch.json", dispatch)
    interventions, new_ledger = high_run_jobs(jobs, directory, cfg, live, progress)
    validation = {**high_canonical_ledger(new_ledger), "offline": not live, "phase": "interventions"}
    ledger = original_ledger + new_ledger
    for arm in HIGH_ARMS:
        if {r["case_id"] for r in interventions if r["arm"] == arm} != set(selection["selected_case_ids"]):
            raise AssertionError("Paired intervention coverage differs")
    if len({e["request_key"] for e in ledger}) != len(ledger):
        raise AssertionError("A physical request hash was counted twice")
    exports = high_build_exports(cases, originals, interventions)
    metrics = high_main_metrics(cases, originals, interventions, selection, ledger, cfg, exports)
    manifest = {"phase": "interventions_complete", "protocol_hash": high_hash(protocol), "selection_hash": high_hash(selection),
        "dispatch_hash": high_hash(dispatch), "cases_hash": high_hash(cases), "request_keys": [e["request_key"] for e in ledger],
        "n_selected": len(selected), "n_intervention_items": len(interventions), "physical_cli_requests": len(ledger),
        "usage": metrics["usage"], "spend_usd": None}
    high_freeze_jsonl(directory / "interventions.jsonl", interventions)
    high_freeze_jsonl(directory / "repairs.jsonl", [r for r in interventions if r["arm"] == "feedback_repair"])
    high_freeze_jsonl(directory / "retries.jsonl", [r for r in interventions if r["arm"] == "fresh_retry"])
    high_freeze_jsonl(directory / "request_ledger.jsonl", ledger)
    high_freeze_json(directory / "metrics.json", metrics)
    high_freeze_json(directory / "manifest.json", manifest)
    high_write_json(directory / "intervention_run_validation.json", validation)
    for arm, files in exports.items():
        for name, rows in files.items():
            high_freeze_jsonl(directory / "exports" / arm / (name + ".jsonl"), rows)
    return {"config": cfg, "protocol": protocol, "cases": cases, "candidates": originals, "interventions": interventions,
        "selection": selection, "request_ledger": ledger, "metrics": metrics, "manifest": manifest, "exports": exports}


def high_build_summary(bundle):
    return {"selected_level": bundle["protocol"]["selected_level"], "metrics": bundle["metrics"],
            "n_called_cases": len(bundle["cases"]), "n_selected": len(bundle["selection"]["selected_case_ids"])}
