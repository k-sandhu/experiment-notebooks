"""Scale v5: frozen source packs, failure-count accrual, then paired interventions.

Load scale_transport, scale_fixtures (with its explicit isolated frozen source
strings), and scale_parallel first. Importing this code makes no model calls.
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

def scale_canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def scale_hash(value):
    return hashlib.sha256(scale_canonical(value).encode("utf-8")).hexdigest()

def scale_write_json(path, value):
    scale_transport_atomic_json(Path(path), value)

def scale_write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("".join(scale_canonical(row) + "\n" for row in rows), encoding="utf-8", newline="\n")
    temporary.replace(path)

def scale_read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]

def scale_freeze_json(path, value):
    path = Path(path)
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != value:
        raise ValueError(f"Frozen v5 protocol/input changed: {path.name}")
    scale_write_json(path, value)

def scale_freeze_jsonl(path, rows):
    path = Path(path)
    if path.exists() and scale_read_jsonl(path) != rows:
        raise ValueError(f"Frozen v5 cases changed: {path.name}")
    scale_write_jsonl(path, rows)

def scale_case_prompt(case):
    return {"task_instructions": SCALE_TASK_INSTRUCTIONS, "documents": case["document"]}

def scale_value_failure(row):
    return (not row["transport_error"] and row["response"] is not None and
            row["verification"]["valid_schema"] and not row["verification"]["exact_fields"])

def scale_value_success(row):
    return (not row["transport_error"] and row["response"] is not None and
            row["verification"]["valid_schema"] and row["verification"]["exact_fields"])

def scale_error_kind(verification, transport_error, response):
    if transport_error:
        return "transport_failure"
    if response is None:
        return "unusable_response"
    if not verification["valid_schema"]:
        return "schema_failure"
    if not verification["exact_fields"]:
        return "value_failure"
    return "accepted" if verification["accepted"] else "evidence_only_failure"

def scale_generic_feedback(original):
    verification = original["verification"]
    return {"wrong_fields": [f for f in SCALE_FIELDS if not verification["field_correct"][f]],
        "schema_failed": not verification["valid_schema"],
        "evidence_failed_fields": [f for f in SCALE_FIELDS if not verification["evidence_correct"][f]]}

def scale_extract_single(response, case_id):
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

def scale_make_job(case, arm="original", original=None):
    job = {"case": case, "arm": arm, "stage": "repair" if arm == "feedback_repair" else "generate",
           "sample": 1 if arm == "fresh_retry" else 0}
    if original is not None:
        job["original"] = original
    return job

def scale_job_request(job):
    feedback = None
    if job["arm"] == "feedback_repair":
        old = job["original"]
        feedback = {job["case"]["case_id"]: {"original_output": old["response"],
                                                "validator_feedback": scale_generic_feedback(old)}}
    return scale_make_request(SCALE_MODEL, job["stage"], [scale_model_input(job["case"])],
        sample=job["sample"], feedback=feedback, protocol=SCALE_PROTOCOL)

def scale_numeric_errors(case, answer):
    values = answer.get("answer", {}) if type(answer) is dict else {}
    output = {}
    for field in ("quantity_units", "unit_price_cents"):
        gold, value = case["gold"][field], values.get(field)
        output[field] = abs(value - gold) if type(value) is int and type(gold) is int else None
    return output

def scale_canonical_ledger(ledger):
    validation = {"new_cli_subprocesses_this_run": sum(not e["cached_this_run"] for e in ledger),
                  "replayed_requests_this_run": sum(e["cached_this_run"] for e in ledger)}
    for entry in ledger:
        entry.pop("cached_this_run")
    return validation

def scale_row_metrics(rows):
    counts = Counter(r["error_kind"] for r in rows)
    return {"n_attempted_cases": len(rows), "usable_replies": sum(r["response"] is not None and not r["transport_error"] for r in rows),
        "valid_schema": sum(r["verification"]["valid_schema"] for r in rows),
        "raw_exact_fields": sum(r["verification"]["exact_fields"] for r in rows),
        "value_correct_valid_schema": sum(scale_value_success(r) for r in rows),
        "accepted": sum(r["verification"]["accepted"] for r in rows),
        "value_failure_cases": sum(scale_value_failure(r) for r in rows),
        "error_categories": {kind: counts[kind] for kind in ("accepted", "value_failure", "evidence_only_failure", "schema_failure", "unusable_response", "transport_failure")},
        "wrong_field_counts": {field: sum(not r["verification"]["field_correct"][field] for r in rows if r["response"] is not None and not r["transport_error"]) for field in SCALE_FIELDS}}

def scale_usage(ledger):
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
        "requests_with_usage": sum(bool(entry["usage"]) for entry in ledger),
        "requests_missing_usage": sum(not bool(entry["usage"]) for entry in ledger),
        "note": "One physical CLI subprocess per request, no orchestration retries; internal inference/network retries are not independently guaranteed. Equal intervention request budgets do not imply equal prompt-token budgets. Cached/reasoning token components must not be added twice."}

def scale_quantile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    left = math.floor(position)
    right = math.ceil(position)
    return sorted_values[left] + (position - left) * (sorted_values[right] - sorted_values[left])

def scale_paired_statistics(pairs, seed, draws, outcome="value"):
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
        interval = [scale_quantile(boot, .025), scale_quantile(boot, .975)]
    return {"outcome": outcome, "n_pairs": n, "both_success": counts[True, True], "repair_only": repair_only,
        "fresh_only": fresh_only, "neither_success": counts[False, False],
        "repair_minus_fresh_difference": difference, "paired_bootstrap_95_interval": interval,
        "difference_percentage_points": difference * 100 if n else None,
        "paired_bootstrap_95_interval_percentage_points": [x * 100 if x is not None else None for x in interval],
        "exact_mcnemar_two_sided_p": p if n else None, "discordant_pairs": discordant,
        "bootstrap_draws": draws, "bootstrap_seed": seed,
        "caveat": "Case-paired descriptive inference conditional on pilot and failure selection. Pairs come from one shared generator, not independent task programs; shared templates can violate independent-case assumptions. A small or degenerate interval is not proof of equivalence."}

def scale_build_exports(cases, originals, interventions):
    by_case = {c["case_id"]: c for c in cases}
    by_original = {r["candidate_id"]: r for r in originals}
    exports = {}
    for arm in ["original", *SCALE_ARMS]:
        rows = [r for r in originals + interventions if r["split"] == "collection" and r["arm"] == arm]
        accepted, rejected, pairs, seen = [], [], [], set()
        for row in rows:
            case = by_case[row["case_id"]]
            if row["verification"]["accepted"] and row["semantic_hash"] not in seen:
                if not scale_validate_answer(case, row["response"])["accepted"]:
                    raise AssertionError("Accepted high-effort export failed verification")
                accepted.append({"case_id": row["case_id"], "prompt": scale_case_prompt(case), "response": row["response"],
                    "candidate_id": row["candidate_id"], "request_key": row["request_key"], "arm": arm,
                    "reasoning_effort": "high", "semantic_hash": row["semantic_hash"], "verification": row["verification"]})
                seen.add(row["semantic_hash"])
            elif not row["verification"]["accepted"]:
                rejected.append(row)
            if arm != "original" and row["verification"]["accepted"]:
                old = by_original[row["original_candidate_id"]]
                if not scale_value_failure(old):
                    raise AssertionError("Preference rejection must be a genuine original value failure")
                pairs.append({"case_id": row["case_id"], "prompt": scale_case_prompt(case), "chosen": row["response"],
                    "rejected": old["response"], "chosen_candidate_id": row["candidate_id"], "rejected_candidate_id": old["candidate_id"],
                    "request_keys": [row["request_key"], old["request_key"]], "arm": arm, "semantic_hash": row["semantic_hash"],
                    "provenance": "Verified intervention answer versus an actual original high-effort Sol value failure; no injected model failure"})
        exports[arm] = {"accepted_examples": accepted, "rejected_examples": rejected, "value_preference_pairs": pairs}
    return exports

def scale_main_metrics(cases, originals, interventions, selection, ledger, cfg, exports):
    original_by_id = {r["candidate_id"]: r for r in originals}
    grouped = {arm: {r["case_id"]: r for r in interventions if r["arm"] == arm} for arm in SCALE_ARMS}
    ids = selection["selected_case_ids"]
    original_good = {r["semantic_hash"] for r in originals if r["split"] == "collection" and scale_value_success(r)}
    original_accepted = {r["semantic_hash"] for r in originals if r["split"] == "collection" and r["verification"]["accepted"]}
    arm_metrics = []
    for arm in SCALE_ARMS:
        rows = list(grouped[arm].values())
        magnitudes = {}
        for field in ("quantity_units", "unit_price_cents"):
            values = [r["numeric_absolute_errors"][field] for r in rows if r["numeric_absolute_errors"][field] is not None]
            magnitudes[field] = {"n_numeric": len(values), "n_non_numeric": len(rows) - len(values),
                "mean_absolute_error": statistics.mean(values) if values else None,
                "median_absolute_error": statistics.median(values) if values else None}
        arm_metrics.append({"arm": arm, **scale_row_metrics(rows),
            "original_wrong_fields_fixed": sum(len(r["original_wrong_fields_fixed"]) for r in rows),
            "cases_with_new_wrong_fields": sum(bool(r["new_wrong_fields"]) for r in rows),
            "cases_with_worsened_numeric_error": sum(bool(r["worsened_numeric_fields"]) for r in rows),
            "unchanged_answer_objects": sum(r["answer_unchanged"] for r in rows), "numeric_error_magnitudes": magnitudes,
            "new_value_correct_cases_vs_original": len({r["semantic_hash"] for r in rows if scale_value_success(r)} - original_good),
            "new_accepted_cases_vs_original": len({r["semantic_hash"] for r in rows if r["verification"]["accepted"]} - original_accepted)})
    pairs = [(scale_value_success(grouped["fresh_retry"][cid]), scale_value_success(grouped["feedback_repair"][cid])) for cid in ids]
    accepted_pairs = [(grouped["fresh_retry"][cid]["verification"]["accepted"], grouped["feedback_repair"][cid]["verification"]["accepted"]) for cid in ids]
    clean_ids = [cid for cid in ids if not any(row["observed_reconnect"] for row in
        (grouped["fresh_retry"][cid], grouped["feedback_repair"][cid], original_by_id[grouped["fresh_retry"][cid]["original_candidate_id"]]))]
    clean_pairs = [(scale_value_success(grouped["fresh_retry"][cid]), scale_value_success(grouped["feedback_repair"][cid])) for cid in clean_ids]
    return {"original_collection": scale_row_metrics([r for r in originals if r["split"] == "collection"]),
        "audit": scale_row_metrics([r for r in originals if r["split"] == "audit"]), "n_selected": len(ids),
        "interventions": arm_metrics,
        "paired_value_recovery": scale_paired_statistics(pairs, cfg["bootstrap_seed"], cfg["bootstrap_draws"]),
        "paired_accepted_recovery": scale_paired_statistics(accepted_pairs, cfg["bootstrap_seed"] + 1, cfg["bootstrap_draws"], "strict_acceptance"),
        "reconnect_sensitivity": {"excluded_case_ids": [cid for cid in ids if cid not in clean_ids],
            "paired_value_recovery": scale_paired_statistics(clean_pairs, cfg["bootstrap_seed"] + 2, cfg["bootstrap_draws"])},
        "usage": scale_usage(ledger), "physical_cli_requests": len(ledger), "spend_usd": None,
        "exports": {arm: {name: len(rows) for name, rows in files.items()} for arm, files in exports.items()},
        "interpretation": {"contrast": "Repair package including previous answer and failed-field flags versus fresh high-effort retry, not feedback alone",
            "primary": "Valid schema and all seven typed values correct; citation-content correctness is secondary",
            "selection": "Conditional on genuine original Sol value failures chosen by pre-outcome random ranking",
            "no_training": "Weights remain frozen; collection recovery is not model learning",
            "money": "CLI tokens and timings recorded; dollar spend is unknown, not zero"}}


import gzip
import itertools

SCALE_PROTOCOL = "23-scale-v5"
SCALE_MODEL = "gpt-6.1-sol"
SCALE_ARMS = ["fresh_retry", "feedback_repair"]
SCALE_PILOT_CONFIG = {"tiers": [128, 192], "seeds": [255128, 255192], "n_cases": 16,
    "min_value_failures": 6, "max_workers": 4, "timeout_s": 900,
    "max_physical_cli_requests": 3376, "protocol": SCALE_PROTOCOL}
SCALE_MAIN_CONFIG = {"target_failures": 600, "n_initial": 512, "chunk_size": 256,
    "collection_cap": 2048, "n_audit": 96, "seed_collection": 255600, "seed_audit": 255096,
    "ranking_seed": 255777, "dispatch_seed": 255888, "bootstrap_seed": 246600,
    "bootstrap_draws": 20000, "max_workers": 4, "timeout_s": 900,
    "max_physical_cli_requests": 3376, "protocol": SCALE_PROTOCOL}
SCALE_FULL_CONFIG = SCALE_MAIN_CONFIG


def scale_config(config=None, pilot=False):
    defaults = SCALE_PILOT_CONFIG if pilot else SCALE_MAIN_CONFIG
    unknown = set(config or {}) - set(defaults)
    if unknown:
        raise ValueError(f"Unknown scale configuration keys: {sorted(unknown)}")
    cfg = {**defaults, **copy.deepcopy(config or {})}
    if cfg["protocol"] != SCALE_PROTOCOL or cfg["timeout_s"] != 900:
        raise ValueError("Use the frozen scale protocol and 900-second timeout")
    if type(cfg["max_workers"]) is not int or not 1 <= cfg["max_workers"] <= 4:
        raise ValueError("One to four workers permitted")
    if type(cfg["max_physical_cli_requests"]) is not int or not 1 <= cfg["max_physical_cli_requests"] <= 3376:
        raise ValueError("The declared physical request cap is at most 3376")
    if pilot:
        if cfg["tiers"] != [128, 192] or len(cfg["seeds"]) != 2 or len(set(cfg["seeds"])) != 2:
            raise ValueError("Calibration requires the declared 128/192 tiers with distinct seeds")
        if any(type(cfg[k]) is not int for k in ("n_cases", "min_value_failures")) or not 1 <= cfg["min_value_failures"] <= cfg["n_cases"] <= 16:
            raise ValueError("Pilot size/threshold outside bounds")
    else:
        for key, maximum in (("target_failures",600),("n_initial",512),("chunk_size",256),("collection_cap",2048),("n_audit",96)):
            if type(cfg[key]) is not int or not 1 <= cfg[key] <= maximum:
                raise ValueError(f"{key} outside declared bounds")
        if cfg["n_initial"] > cfg["collection_cap"] or cfg["target_failures"] > cfg["collection_cap"]:
            raise ValueError("Initial size/target cannot exceed collection cap")
        if cfg["seed_collection"] == cfg["seed_audit"] or type(cfg["bootstrap_draws"]) is not int or cfg["bootstrap_draws"] < 100:
            raise ValueError("Distinct source seeds and at least 100 bootstrap draws required")
    return cfg


def scale_profile_protocol(cfg, phase, **extra):
    return {"protocol": SCALE_PROTOCOL, "phase": phase, "config": cfg, "model": SCALE_MODEL,
        "reasoning_effort": "high", "case_count_per_cli_request": 1, "timeout_s": 900,
        "max_workers": cfg["max_workers"], "transport_version": SCALE_TRANSPORT_VERSION,
        "dispatch_version": SCALE_DISPATCH_VERSION, "cli_options": list(SCALE_CLI_OPTIONS),
        "fixture_version": SCALE_VERSION, "frozen_rule_source_sha256": dict(SCALE_CORE_SHA256),
        "runtime_source_sha256": dict(globals().get("SCALE_RUNTIME_SOURCE_HASHES", {})),
        "task_instructions": SCALE_TASK_INSTRUCTIONS, "instructions_hash": scale_hash(SCALE_TASK_INSTRUCTIONS),
        "storage": "Lossless full request and raw response per hash in deterministic gzip; source cases and compact independent audits are frozen once as gzipJSONL",
        "eligibility": "Usable successful single-case response with valid schema and at least one incorrect typed value. Transport, parsing, schema-only and citation-only failures never count toward difficulty, accrual or selection.",
        "infrastructure_stop": "At most max_workers requests per bounded wave. Wait for all current-wave tasks. On any infrastructure failure/exception retain all written raw caches and stop before the next wave. No automatic resubmission.",
        "retry_boundary": "One CLI subprocess per full request, no orchestration retries. Internal CLI reconnects/network retries and exact inference draw counts are not independently disabled or guaranteed; diagnostics retained.",
        "model_alias_scope": "The requested alias is fixed for this run, not an immutable dated model snapshot. Actual CLI metadata and request timestamps are retained; alias/time drift is not ruled out.",
        "spend_usd": None, "training_performed": False, **extra}


def scale_write_records(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    raw = "".join(scale_canonical(row) + "\n" for row in rows).encode("utf-8")
    temporary.write_bytes(gzip.compress(raw, compresslevel=6, mtime=0) if path.suffix == ".gz" else raw)
    temporary.replace(path)


def scale_read_records(path):
    path = Path(path)
    raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]


def scale_freeze_records(path, rows):
    rows = list(rows)
    if Path(path).exists() and scale_read_records(path) != rows:
        raise ValueError("Frozen scale artifact changed: " + Path(path).name)
    scale_write_records(path, rows)


def scale_file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scale_prior_source_paths(root):
    """Inventory real prior source rows, excluding this study and response exports."""
    directory = Path(root) / "data"
    current = directory / "scale_v5"
    paths = []
    if not directory.exists():
        return paths
    for path in sorted(directory.rglob("*")):
        parts = [part.lower() for part in path.relative_to(directory).parts]
        if (parts and parts[0] == "tmp") or any(part in {"__pycache__", ".ipynb_checkpoints"} for part in parts):
            continue
        if not path.is_file() or current in path.parents or not (path.name.endswith(".jsonl") or path.name.endswith(".jsonl.gz")):
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8-sig") as stream:
            first = next((line for line in stream if line.strip()), None)
        if first:
            row = json.loads(first)
            if isinstance(row, dict) and {"case_id", "document", "gold", "semantic_hash"} <= set(row):
                paths.append(path)
    return paths


def scale_prior_inventory(root, paths=None):
    root = Path(root)
    prior = scale_previous_corpus_keys(scale_prior_source_paths(root) if paths is None else paths)
    serialized = {key: value for key, value in prior.items() if key not in {"case_ids", "semantic_hashes"}}
    serialized.update(case_ids=sorted(prior["case_ids"]), semantic_hashes=sorted(prior["semantic_hashes"]))
    serialized["source_files"] = [{**row, "path": Path(row["path"]).relative_to(root).as_posix()} for row in prior["source_files"]]
    return prior, serialized


def scale_prepare_source(path, specification):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = path.with_name(path.name + ".manifest.json")
    if path.exists() or manifest_path.exists():
        result = scale_verify_corpus(path, manifest_path=manifest_path, full_audit=False)
        if not result["passed"]:
            raise ValueError("Previously frozen source corpus failed integrity")
        manifest = result["manifest"]
    else:
        manifest = scale_write_corpus(path, scale_iter_cases(specification["n"], specification["seed"],
            tier=specification["tier"], split=specification["split"], start_index=specification["start_index"]))
    # JSON maps have string keys; normalize writer-returned tier-count keys so
    # first preparation and a manifest loaded from disk compare identically.
    manifest = json.loads(scale_canonical(manifest))
    expected_indices = list(range(specification["start_index"], specification["start_index"] + specification["n"]))
    index = manifest["case_index"]
    if (manifest["n_cases"] != specification["n"] or [row["generation_index"] for row in index] != expected_indices
            or any(row["split"] != specification["split"] or row["base_shipments"] != specification["tier"] for row in index)):
        raise ValueError("Source corpus metadata differs from its declared generation specification")
    for offset, case in enumerate(scale_iter_corpus(path, manifest)):
        if offset >= len(expected_indices):
            raise ValueError("Source corpus contains undeclared extra cases")
        expected_index = expected_indices[offset]
        if (case["generation_seed"] != specification["seed"] or case["generation_index"] != expected_index
                or case["split"] != specification["split"] or case["base_shipments"] != specification["tier"]):
            raise ValueError("Source corpus seed/index/split/tier differs from its declared generation specification")
    return manifest


def scale_load_case_subset(path, manifest, case_ids):
    expected = set(case_ids)
    found = {case["case_id"]: case for case in scale_iter_corpus(path, manifest) if case["case_id"] in expected}
    if set(found) != expected:
        raise ValueError("Requested source IDs missing from frozen compressed corpus")
    return [found[cid] for cid in case_ids]



def scale_run_jobs(jobs, directory, cfg, live=False, progress=None):
    jobs = [{**job, "request_key": scale_request_key(scale_job_request(job))} for job in jobs]
    if len(jobs) > cfg["max_physical_cli_requests"]:
        raise ValueError("Declared request cap would be exceeded")
    plan = [{"request_key": job["request_key"], "case_id": job["case"]["case_id"],
        "source_hash": job["case"]["content_hash"], "arm": job["arm"], "stage": job["stage"], "sample": job["sample"]} for job in jobs]
    scale_freeze_json(Path(directory) / "request_plans" / (scale_hash(plan) + ".json"), plan)
    def invoke(job):
        case = job["case"]
        request = scale_job_request(job)
        if job.get("original") and scale_hash(request["case_inputs"]) != job["original"]["request_input_hash"]:
            raise ValueError("Paired source/instructions changed before dispatch")
        response = scale_call_model(request, Path(directory) / "cache", live=live, timeout_s=900)
        key = response["request_key"]
        if key != job["request_key"]:
            raise ValueError("Full request identity changed after dispatch was frozen")
        answer, parse_error = scale_extract_single(response, case["case_id"])
        verification = scale_validate_answer(case, answer if not response.get("error") else None)
        reconnect = response.get("observed_reconnect_events", []) or []
        row = {field: case[field] for field in ("case_id", "family", "level", "split", "content_hash", "semantic_hash", "base_shipments", "generation_index")}
        row.update({"candidate_id": f"{case['case_id']}:{job['arm']}:{job['sample']}", "model": SCALE_MODEL,
            "reasoning_effort": "high", "arm": job["arm"], "stage": job["stage"], "sample": job["sample"],
            "request_key": key, "request_input_hash": scale_hash(request["case_inputs"]),
            "feedback_hash": scale_hash(request["feedback"]), "response": answer, "verification": verification,
            "transport_error": response.get("error"), "parse_error": response.get("parse_error") or parse_error,
            "error_kind": scale_error_kind(verification, response.get("error"), answer), "batch_position": 0,
            "batch_case_ids": [case["case_id"]], "observed_reconnect": bool(reconnect),
            "numeric_absolute_errors": scale_numeric_errors(case, answer),
            "raw_failure": response.get("final_assistant_response", "") if answer is None else None})
        if job.get("original"):
            old = job["original"]
            old_ok, new_ok = old["verification"]["field_correct"], verification["field_correct"]
            original_magnitudes = scale_numeric_errors(case, old["response"])
            if row["request_input_hash"] != old["request_input_hash"]:
                raise ValueError("Paired intervention source/instructions differ from original")
            row.update({"original_candidate_id": old["candidate_id"], "original_request_key": old["request_key"],
                "original_wrong_fields": [f for f in SCALE_FIELDS if not old_ok[f]],
                "original_wrong_fields_fixed": [f for f in SCALE_FIELDS if not old_ok[f] and new_ok[f]],
                "new_wrong_fields": [f for f in SCALE_FIELDS if old_ok[f] and not new_ok[f]],
                "original_numeric_absolute_errors": original_magnitudes,
                "worsened_numeric_fields": [f for f in original_magnitudes if original_magnitudes[f] is not None
                    and row["numeric_absolute_errors"][f] is not None and row["numeric_absolute_errors"][f] > original_magnitudes[f]],
                "answer_unchanged": type(answer) is dict and answer.get("answer") == old["response"].get("answer"),
                "feedback_supplied": job["arm"] == "feedback_repair"})
        entry = {"request_key": key, "candidate_id": row["candidate_id"], "case_id": case["case_id"],
            "source_hash": case["content_hash"], "request_input_hash": row["request_input_hash"], "feedback_hash": row["feedback_hash"],
            "arm": job["arm"], "stage": job["stage"], "sample": job["sample"], "split": case["split"],
            "model": SCALE_MODEL, "reasoning_effort": "high", "timeout_s": 900, "usage": response.get("usage", {}) or {},
            "transport_error": response.get("error"), "parse_error": row["parse_error"],
            "cli_error_events": response.get("cli_error_events", []) or [], "observed_reconnect_events": reconnect,
            "started_at": response.get("started_at"), "finished_at": response.get("finished_at"),
            "subprocess_elapsed_s": response.get("elapsed_s"), "return_code": response.get("return_code"),
            "resolved_model": response.get("resolved_model"), "cached_this_run": bool(response.get("cached")),
            "cache_file": f"cache/{key}.json.gz"}
        return row, entry
    return scale_dispatch_waves(jobs, invoke, directory, max_workers=cfg["max_workers"], progress=progress)


def scale_prepare_pilot(config=None, root=Path("."), prior_source_paths=None):
    cfg = scale_config(config, pilot=True)
    directory = Path(root) / "data" / "scale_v5" / "pilot"
    specifications = [{"name": f"tier_{tier}", "n": cfg["n_cases"], "seed": seed, "tier": tier,
        "split": "pilot", "start_index": 0} for tier, seed in zip(cfg["tiers"], cfg["seeds"])]
    scale_freeze_json(directory / "source_plan.json", {"config": cfg, "blocks": specifications})
    prior, inventory = scale_prior_inventory(root, prior_source_paths)
    scale_freeze_json(directory / "previous_corpora.json", inventory)
    blocks = []
    for spec in specifications:
        path = directory / "sources" / (spec["name"] + ".jsonl.gz")
        manifest = scale_prepare_source(path, spec)
        scale_check_previous_overlap(manifest, prior)
        blocks.append({"specification": spec, "source_path": "sources/" + path.name, "manifest": manifest})
    cross = scale_check_cohort_overlap([block["manifest"] for block in blocks])
    protocol = scale_profile_protocol(cfg, "pilot", blocks=blocks, previous_corpora_hash=scale_hash(inventory),
        cross_cohort_audit=cross,
        stopping_policy="First tier in 128,192 with at least min_value_failures genuine valid-schema wrong-value cases; no upper cutoff. If neither qualifies choose 192 and explicitly mark threshold failure. No intervention results exist or inform calibration.",
        max_pilot_requests=cfg["n_cases"] * len(cfg["tiers"]))
    scale_freeze_json(directory / "protocol.json", protocol)
    return {"config": cfg, "protocol": protocol, "directory": directory, "blocks": blocks}


def scale_run_pilot(config=None, root=Path("."), live=False, progress=None):
    prepared = scale_prepare_pilot(config, root)
    cfg, directory = prepared["config"], prepared["directory"]
    outcomes, bundles = [], []
    selected, met = 192, False
    for block in prepared["blocks"]:
        tier = block["specification"]["tier"]
        cases = list(scale_iter_corpus(directory / block["source_path"], block["manifest"]))
        output = directory / f"tier_{tier}"
        scale_freeze_json(output / "protocol.json", {"pilot_protocol_hash": scale_hash(prepared["protocol"]), "tier": tier})
        rows, ledger = scale_run_jobs([scale_make_job(case) for case in cases], output, cfg, live, progress)
        validation = {**scale_canonical_ledger(ledger), "offline": not live}
        failures = sum(scale_value_failure(row) for row in rows)
        metrics = {**scale_row_metrics(rows), "usage": scale_usage(ledger), "spend_usd": None}
        manifest = {"pilot_protocol_hash": scale_hash(prepared["protocol"]), "tier": tier,
            "n_cases": len(cases), "request_keys": [row["request_key"] for row in ledger],
            "candidate_hash": scale_hash(rows), "source_manifest_hash": scale_hash(block["manifest"])}
        scale_freeze_records(output / "candidates.jsonl", rows)
        scale_freeze_records(output / "request_ledger.jsonl", ledger)
        scale_freeze_json(output / "metrics.json", metrics)
        scale_freeze_json(output / "manifest.json", manifest)
        scale_write_json(output / "run_validation.json", validation)
        outcomes.append({"tier": tier, "n_cases": len(rows), "value_failure_cases": failures,
            "threshold_met": failures >= cfg["min_value_failures"], "request_keys": manifest["request_keys"]})
        bundles.append({"tier": tier, "candidates": rows, "metrics": metrics, "request_ledger": ledger, "manifest": manifest})
        if failures >= cfg["min_value_failures"]:
            selected, met = tier, True
            break
    ladder = {"protocol_hash": scale_hash(prepared["protocol"]), "config": cfg, "tiers": outcomes,
        "selected_tier": selected, "threshold_met": met,
        "selection_reason": "First predeclared threshold crossing" if met else "Fixed 192 fallback; calibration threshold was not reached",
        "physical_cli_requests": sum(len(row["request_keys"]) for row in outcomes),
        "uncalled_tiers": [tier for tier in cfg["tiers"] if tier not in {row["tier"] for row in outcomes}]}
    scale_freeze_json(directory / "ladder.json", ladder)
    return {"selected_tier": selected, "threshold_met": met, "ladder": ladder, "tiers": bundles}



def scale_prepare_main(config=None, root=Path(".")):
    cfg = scale_config(config)
    data = Path(root) / "data" / "scale_v5"
    pilot_protocol = json.loads((data / "pilot" / "protocol.json").read_text(encoding="utf-8"))
    ladder = json.loads((data / "pilot" / "ladder.json").read_text(encoding="utf-8"))
    if ladder["protocol_hash"] != scale_hash(pilot_protocol):
        raise ValueError("Frozen completed pilot differs from its declaration")
    tier = ladder["selected_tier"]
    directory = data / "main"
    specifications = [{"name": "collection", "n": cfg["collection_cap"], "seed": cfg["seed_collection"], "tier": tier, "split": "collection", "start_index": 0},
        {"name": "audit", "n": cfg["n_audit"], "seed": cfg["seed_audit"], "tier": tier, "split": "audit", "start_index": cfg["collection_cap"]}]
    scale_freeze_json(directory / "source_plan.json", {"config": cfg, "selected_tier": tier, "blocks": specifications, "pilot_ladder_hash": scale_hash(ladder)})
    prior, inventory = scale_prior_inventory(root)
    scale_freeze_json(directory / "previous_corpora.json", inventory)
    blocks = []
    for spec in specifications:
        path = directory / "sources" / (spec["name"] + ".jsonl.gz")
        manifest = scale_prepare_source(path, spec)
        scale_check_previous_overlap(manifest, prior)
        blocks.append({"specification": spec, "source_path": "sources/" + path.name, "manifest": manifest})
    cross = scale_check_cohort_overlap([block["manifest"] for block in pilot_protocol["blocks"] + blocks])
    collection_ids = [row["case_id"] for row in blocks[0]["manifest"]["case_index"]]
    ranking = list(collection_ids)
    random.Random(cfg["ranking_seed"]).shuffle(ranking)
    chunks = [collection_ids[:cfg["n_initial"]]]
    chunks.extend(collection_ids[start:start + cfg["chunk_size"]] for start in range(cfg["n_initial"], len(collection_ids), cfg["chunk_size"]))
    allocation = {"collection_case_ids": collection_ids, "audit_case_ids": [row["case_id"] for row in blocks[1]["manifest"]["case_index"]],
        "chunks": chunks, "failure_selection_ranking": ranking}
    upper = cfg["collection_cap"] + cfg["n_audit"] + 2 * cfg["target_failures"]
    if ladder["physical_cli_requests"] + upper > cfg["max_physical_cli_requests"]:
        raise ValueError("Declared pilot-plus-main request cap would be exceeded")
    protocol = scale_profile_protocol(cfg, "prepared_main", selected_tier=tier, pilot_threshold_met=ladder["threshold_met"],
        pilot_ladder_hash=scale_hash(ladder), blocks=blocks, allocation_hash=scale_hash(allocation),
        cross_cohort_audit=cross, previous_corpora_hash=scale_hash(inventory), main_request_upper_bound=upper,
        total_request_upper_bound=upper + ladder["physical_cli_requests"],
        accrual_policy="Collect the full initial cohort, then fixed complete chunks only while accrued genuine original value-failure cases are below target_failures and collection_cap is not exhausted. Never inspect intervention responses or an arm difference to continue or stop.",
        selection_policy="After collection closes, rank ALL accrued eligible failures by the frozen independent seeded ranking and take target_failures, or all if the cap yields a target shortfall. No severity-based selection.",
        intervention_policy="Separate explicit phase after original/source review. Shuffle selected source order with dispatch_seed; each four-job wave holds fresh and repair for two sources with seeded within-wave order. No cross-call result sharing. No recovery/advantage monitoring before every scheduled pair is terminal.",
        contrast="Repair package including prior answer and generic flags versus fresh attempt, not isolated feedback versus prior-answer exposure",
        primary_recovery="Successful single-case response with valid schema and all seven typed values correct; citation-content acceptance secondary",
        audit_boundary="All potential audit sources independently audited before any main call; audit answers called only after accrual and selection freeze, baseline only, never repair or accrue from audit outcomes",
        statistics={"bootstrap_draws": cfg["bootstrap_draws"], "bootstrap_seed": cfg["bootstrap_seed"],
            "primary_decision": "Positive repair-minus-fresh value-recovery difference AND two-sided exact McNemar p<0.05",
            "bootstrap": "Case-paired percentile 95% interval for repair-minus-fresh recovery difference",
            "mcnemar": "Exact conditional two-sided McNemar test on discordant paired cases",
            "shortfall": "Report actual pairs and target shortfall. No guaranteed significance, power, or model mistakes.",
            "caveat": "Conditional on calibration, stopped baseline accrual and original-failure selection. Shared templates can limit independent-case inference.",
            "reconnect_sensitivity": "Exclude a pair if original or either intervention has observed reconnect events; never silently exclude benign warnings"})
    scale_freeze_json(directory / "allocation.json", allocation)
    scale_freeze_json(directory / "protocol.json", protocol)
    return {"config": cfg, "protocol": protocol, "directory": directory, "allocation": allocation, "blocks": blocks}


def scale_load_prepared(root):
    directory = Path(root) / "data" / "scale_v5" / "main"
    protocol = json.loads((directory / "protocol.json").read_text(encoding="utf-8"))
    allocation = json.loads((directory / "allocation.json").read_text(encoding="utf-8"))
    if protocol["protocol"] != SCALE_PROTOCOL or protocol["instructions_hash"] != scale_hash(SCALE_TASK_INSTRUCTIONS):
        raise ValueError("Scale protocol or instructions changed")
    scale_config(protocol["config"])
    if protocol["allocation_hash"] != scale_hash(allocation):
        raise ValueError("Frozen collection chunks/ranking changed")
    for block in protocol["blocks"]:
        path = directory / block["source_path"]
        if scale_file_hash(path) != block["manifest"]["compressed_sha256"]:
            raise ValueError("Compressed source byte hash changed")
    return directory, protocol, allocation


def scale_collect_originals(root=Path("."), live=False, progress=None):
    directory, protocol, allocation = scale_load_prepared(root)
    cfg = protocol["config"]
    source, audit_source = protocol["blocks"]
    originals, ledger, history = [], [], []
    for index, ids in enumerate(allocation["chunks"]):
        if originals and sum(scale_value_failure(row) for row in originals) >= cfg["target_failures"]:
            break
        cases = scale_load_case_subset(directory / source["source_path"], source["manifest"], ids)
        rows, entries = scale_run_jobs([scale_make_job(case) for case in cases], directory, cfg, live, progress)
        validation = scale_canonical_ledger(entries)
        originals.extend(rows); ledger.extend(entries)
        history.append({"chunk_index": index, "n_chunk_cases": len(rows), "n_accrued_cases": len(originals),
            "n_accrued_value_failures": sum(scale_value_failure(row) for row in originals),
            "request_keys": [entry["request_key"] for entry in entries], "candidate_hash": scale_hash(rows)})
        checkpoint = directory / "original_chunks" / f"chunk_{index:03d}"
        scale_freeze_records(checkpoint / "candidates.jsonl", rows)
        scale_freeze_records(checkpoint / "request_ledger.jsonl", entries)
        scale_freeze_json(checkpoint / "manifest.json", history[-1])
        scale_write_json(checkpoint / "run_validation.json", {**validation, "offline": not live})
    eligible = {row["case_id"]: row for row in originals if scale_value_failure(row)}
    selected_ids = [cid for cid in allocation["failure_selection_ranking"] if cid in eligible][:cfg["target_failures"]]
    called = {row["case_id"] for row in originals}
    selection = {"protocol_hash": scale_hash(protocol), "target_failures": cfg["target_failures"],
        "n_accrued_collection": len(originals), "n_eligible_failures": len(eligible), "target_reached": len(eligible) >= cfg["target_failures"],
        "target_shortfall": max(0, cfg["target_failures"] - len(selected_ids)),
        "stopping_reason": "Predeclared genuine failure-count target reached after a complete chunk" if len(eligible) >= cfg["target_failures"] else "Fixed original collection cap exhausted; target shortfall",
        "accrual_history": history, "selected_case_ids": selected_ids,
        "selected_candidate_ids": [eligible[cid]["candidate_id"] for cid in selected_ids],
        "eligible_candidate_ids": [eligible[cid]["candidate_id"] for cid in allocation["failure_selection_ranking"] if cid in eligible],
        "uncalled_collection_case_ids": [cid for cid in allocation["collection_case_ids"] if cid not in called],
        "source_hashes": {cid: eligible[cid]["content_hash"] for cid in selected_ids},
        "input_hashes": {cid: eligible[cid]["request_input_hash"] for cid in selected_ids},
        "selection_ranking_hash": scale_hash(allocation["failure_selection_ranking"])}
    scale_freeze_json(directory / "selection.json", selection)
    audit_cases = list(scale_iter_corpus(directory / audit_source["source_path"], audit_source["manifest"]))
    audit_rows, audit_ledger = scale_run_jobs([scale_make_job(case) for case in audit_cases], directory, cfg, live, progress)
    validation = scale_canonical_ledger(audit_ledger)
    originals.extend(audit_rows); ledger.extend(audit_ledger)
    metrics = {"collection": scale_row_metrics([row for row in originals if row["split"] == "collection"]),
        "audit": scale_row_metrics(audit_rows), "target_shortfall": selection["target_shortfall"], "n_selected": len(selected_ids),
        "usage": scale_usage(ledger), "physical_cli_requests": len(ledger), "spend_usd": None}
    manifest = {"phase": "originals_complete", "protocol_hash": scale_hash(protocol), "selection_hash": scale_hash(selection),
        "candidate_hash": scale_hash(originals), "request_keys": [entry["request_key"] for entry in ledger],
        "n_collection": len(called), "n_audit": len(audit_rows), "n_selected": len(selected_ids)}
    scale_freeze_records(directory / "candidates.jsonl", originals)
    scale_freeze_records(directory / "original_request_ledger.jsonl", ledger)
    scale_freeze_json(directory / "original_metrics.json", metrics)
    scale_freeze_json(directory / "original_manifest.json", manifest)
    scale_write_json(directory / "original_run_validation.json", {**validation, "offline": not live, "note": "Per-chunk replay/new-call counts are in original_chunks/*/run_validation.json"})
    return {"config": cfg, "protocol": protocol, "candidates": originals, "selection": selection,
        "metrics": metrics, "manifest": manifest, "request_ledger": ledger}


def scale_load_originals(root):
    directory, protocol, allocation = scale_load_prepared(root)
    manifest = json.loads((directory / "original_manifest.json").read_text(encoding="utf-8"))
    originals = scale_read_records(directory / "candidates.jsonl")
    selection = json.loads((directory / "selection.json").read_text(encoding="utf-8"))
    ledger = scale_read_records(directory / "original_request_ledger.jsonl")
    if (manifest["phase"] != "originals_complete" or manifest["protocol_hash"] != scale_hash(protocol)
            or manifest["selection_hash"] != scale_hash(selection) or manifest["candidate_hash"] != scale_hash(originals)
            or manifest["request_keys"] != [entry["request_key"] for entry in ledger]):
        raise ValueError("Frozen original results or selection changed")
    eligible = {row["case_id"]: row for row in originals if row["split"] == "collection" and scale_value_failure(row)}
    expected = [cid for cid in allocation["failure_selection_ranking"] if cid in eligible][:protocol["config"]["target_failures"]]
    if selection["selected_case_ids"] != expected:
        raise ValueError("Failure selection differs from declared independent ranking")
    return directory, protocol, originals, selection, ledger



def scale_paired_dispatch_jobs(selected, by_case, cfg):
    rng = random.Random(cfg["dispatch_seed"])
    case_order = list(selected)
    rng.shuffle(case_order)
    pairs_per_wave = max(1, cfg["max_workers"] // 2)
    jobs = []
    for start in range(0, len(case_order), pairs_per_wave):
        block = case_order[start:start + pairs_per_wave]
        wave = [scale_make_job(by_case[row["case_id"]], arm, row) for row in block for arm in SCALE_ARMS]
        rng.shuffle(wave)
        jobs.extend(wave)
    return jobs


def scale_run_interventions(root=Path("."), live=False, progress=None):
    directory, protocol, originals, selection, original_ledger = scale_load_originals(root)
    cfg = protocol["config"]
    if cfg["max_workers"] not in (1, 2, 4):
        raise ValueError("Paired dispatch requires one, two or four workers")
    source = protocol["blocks"][0]
    selected_cases = scale_load_case_subset(directory / source["source_path"], source["manifest"], selection["selected_case_ids"])
    by_case = {case["case_id"]: case for case in selected_cases}
    by_original = {row["candidate_id"]: row for row in originals}
    selected = [by_original[cid] for cid in selection["selected_candidate_ids"]]
    if any(row["split"] != "collection" or not scale_value_failure(row) for row in selected):
        raise ValueError("An intervention target is not a genuine original collection value failure")
    jobs = scale_paired_dispatch_jobs(selected, by_case, cfg)
    dispatch = {"protocol_hash": scale_hash(protocol), "selection_hash": scale_hash(selection), "seed": cfg["dispatch_seed"],
        "paired_block_design": "Shuffle selected sources; each four-job wave contains both arms for two sources with seeded within-wave order. No call receives a sibling result.",
        "jobs": [{"case_id": job["case"]["case_id"], "arm": job["arm"], "request_key": scale_request_key(scale_job_request(job)),
            "input_hash": scale_hash(scale_job_request(job)["case_inputs"]), "feedback_hash": scale_hash(scale_job_request(job)["feedback"])} for job in jobs]}
    scale_freeze_json(directory / "dispatch.json", dispatch)
    # Completion callbacks carry no value/schema scores or arm recovery rates.
    # Efficacy is computed only after every scheduled call has settled successfully.
    interventions, new_ledger = scale_run_jobs(jobs, directory, cfg, live, progress)
    validation = scale_canonical_ledger(new_ledger)
    ledger = original_ledger + new_ledger
    if len({entry["request_key"] for entry in ledger}) != len(ledger):
        raise ValueError("A physical request was counted twice")
    for arm in SCALE_ARMS:
        if {row["case_id"] for row in interventions if row["arm"] == arm} != set(selection["selected_case_ids"]):
            raise ValueError("Paired arm coverage differs")
    called_ids = [row["case_id"] for row in originals if row["split"] == "collection"]
    called_cases = scale_load_case_subset(directory / source["source_path"], source["manifest"], called_ids)
    exports = scale_build_exports(called_cases, originals, interventions)
    metrics = scale_main_metrics(called_cases, originals, interventions, selection, ledger, cfg, exports)
    metrics.update(target_failures=cfg["target_failures"], target_reached=selection["target_reached"],
        target_shortfall=selection["target_shortfall"], n_uncalled_collection=len(selection["uncalled_collection_case_ids"]),
        by_family=[{"family": family, **scale_row_metrics([row for row in originals if row["split"] == "collection" and row["family"] == family])} for family in SCALE_FAMILIES])
    primary = metrics["paired_value_recovery"]
    metrics["primary_decision"] = {"rule": "Positive repair-minus-fresh difference AND two-sided exact McNemar p<0.05",
        "criterion_met": bool(primary["n_pairs"] and primary["repair_minus_fresh_difference"] > 0 and primary["exact_mcnemar_two_sided_p"] < .05),
        "target_pairs": cfg["target_failures"], "actual_pairs": len(selected),
        "caveat": "Nominal inference for case pairs within one shared generator, not independent task programs; target shortfall reduces planned power. Baseline collection accuracy is descriptive under failure-count stopping; the audit cohort is fixed."}
    manifest = {"phase": "interventions_complete", "protocol_hash": scale_hash(protocol), "selection_hash": scale_hash(selection),
        "dispatch_hash": scale_hash(dispatch), "candidate_hash": scale_hash(originals), "interventions_hash": scale_hash(interventions),
        "request_keys": [entry["request_key"] for entry in ledger], "n_selected": len(selected), "physical_cli_requests": len(ledger),
        "total_pilot_plus_main_requests": len(ledger) + json.loads((directory.parent / "pilot" / "ladder.json").read_text(encoding="utf-8"))["physical_cli_requests"],
        "target_shortfall": selection["target_shortfall"], "usage": metrics["usage"], "spend_usd": None}
    if manifest["total_pilot_plus_main_requests"] > cfg["max_physical_cli_requests"]:
        raise ValueError("Total declared physical call cap exceeded")
    scale_freeze_records(directory / "interventions.jsonl", interventions)
    scale_freeze_records(directory / "repairs.jsonl", [row for row in interventions if row["arm"] == "feedback_repair"])
    scale_freeze_records(directory / "retries.jsonl", [row for row in interventions if row["arm"] == "fresh_retry"])
    scale_freeze_records(directory / "request_ledger.jsonl", ledger)
    scale_freeze_json(directory / "metrics.json", metrics)
    scale_freeze_json(directory / "manifest.json", manifest)
    scale_write_json(directory / "intervention_run_validation.json", {**validation, "offline": not live})
    for arm, files in exports.items():
        for name, rows in files.items():
            scale_freeze_records(directory / "exports" / arm / (name + ".jsonl.gz"), rows)
    unique = {}
    for arm in ["original", "feedback_repair", "fresh_retry"]:
        for row in exports[arm]["accepted_examples"]:
            unique.setdefault(row["semantic_hash"], row)
    scale_freeze_records(directory / "exports" / "curated_unique.jsonl.gz", unique.values())
    return {"config": cfg, "protocol": protocol, "candidates": originals, "interventions": interventions,
        "selection": selection, "metrics": metrics, "manifest": manifest, "request_ledger": ledger,
        "exports": {arm: {name: len(rows) for name, rows in files.items()} for arm, files in exports.items()},
        "n_curated_unique_sources": len(unique)}


def scale_build_summary(bundle):
    return {"selected_tier": bundle["protocol"]["selected_tier"], "metrics": bundle["metrics"],
        "n_selected": len(bundle["selection"]["selected_case_ids"]), "target_shortfall": bundle["selection"]["target_shortfall"]}
