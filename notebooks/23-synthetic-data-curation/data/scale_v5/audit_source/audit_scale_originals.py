"""Independent pre-intervention audit of frozen scale-v5 original responses.

Run only after ``original_manifest.json`` declares ``originals_complete`` and
before the separate intervention phase. This script reads source packs, original
candidate/ledger/selection records, original-only cache files, and frozen protocol
files. It never enumerates or opens prospective/intervention cache files, and it
never calls a model. It writes only the two review reports beside this script.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
from typing import Any


AUTHORING = Path(__file__).resolve().parent
DEFAULT_NOTEBOOK_ROOT = AUTHORING.parent / "experiment_notebooks" / "notebooks" / "23-synthetic-data-curation"
JSON_REPORT = AUTHORING / "scale_original_failure_review.json"
MD_REPORT = AUTHORING / "scale_original_failure_review.md"
RESUME_AMENDMENT_SHA256 = "2caadd1316a8ef239453857c7107c275ef6325023129948f8c6329c6fac5fc82"
RESUME_IMPLEMENTATION_SHA256 = "62d55e98fd877d518c187650caaf9fbbde3c01cdd86da15d65d276352cecd7ef"
RESUME_TEST_SHA256 = "02d63e62c5ce1836f9bf01a3e090a915785cb01104600b33a37397e6373daf84"
RESUME_CAPACITY_MESSAGE = "Selected model is at capacity. Please try a different model."


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(text.encode("utf-8"))


def load_helpers() -> dict[str, Any]:
    namespace: dict[str, Any] = {"__name__": "scale_original_readonly_audit"}
    for name in ("scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py"):
        source = (AUTHORING / name).read_text(encoding="utf-8")
        exec(compile(source, name, "exec"), namespace)
    namespace["scale_load_cores"](core_dir=AUTHORING)
    return namespace


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _gzip_json(path: Path) -> Any:
    return json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))


def _append_check(checks: dict[str, bool], issues: list[str], name: str, passed: bool, detail: str | None = None) -> None:
    checks[name] = bool(passed)
    if not passed:
        issues.append(detail or name.replace("_", " "))


def _expected_original_candidate(ns: dict[str, Any], case: dict[str, Any], request: dict[str, Any],
                                 raw_response: dict[str, Any], stored: dict[str, Any]) -> dict[str, Any]:
    answer, parse_error = ns["scale_extract_single"](raw_response, case["case_id"])
    if raw_response.get("error"):
        answer = None
    verification = ns["scale_validate_answer"](case, answer)
    reconnect = raw_response.get("observed_reconnect_events", []) or []
    expected = {field: case[field] for field in ("case_id", "family", "level", "split", "content_hash", "semantic_hash",
        "base_shipments", "generation_index")}
    expected.update({
        "candidate_id": f"{case['case_id']}:original:0", "model": ns["SCALE_MODEL"],
        "reasoning_effort": "high", "arm": "original", "stage": "generate", "sample": 0,
        "request_key": raw_response["request_key"], "request_input_hash": ns["scale_hash"](request["case_inputs"]),
        "feedback_hash": ns["scale_hash"](request["feedback"]), "response": answer,
        "verification": verification, "transport_error": raw_response.get("error"),
        "parse_error": raw_response.get("parse_error") or parse_error, "error_kind": ns["scale_error_kind"](
            verification, raw_response.get("error"), answer), "batch_position": 0,
        "batch_case_ids": [case["case_id"]], "observed_reconnect": bool(reconnect),
        "numeric_absolute_errors": ns["scale_numeric_errors"](case, answer),
        "raw_failure": raw_response.get("final_assistant_response", "") if answer is None else None,
    })
    return expected


def _cache_response(ns: dict[str, Any], cache_path: Path, request: dict[str, Any], request_key: str,
                    capacity_error: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    cache = _gzip_json(cache_path)
    if cache.get("key") != request_key or cache.get("request") != request:
        raise ValueError(f"Original cache identity mismatch: {cache_path.name}")
    if ns["scale_request_key"](cache.get("request")) != request_key:
        raise ValueError(f"Original full request hash mismatch: {cache_path.name}")
    attempts = cache.get("attempts", [])
    if len(attempts) != 1 or attempts[0].get("pending"):
        raise ValueError(f"Original cache must contain exactly one terminal attempt: {cache_path.name}")
    attempt = attempts[0]
    events = attempt.get("events", [])
    messages = [event.get("item", {}).get("text", "") for event in events
        if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message"]
    if capacity_error is None:
        if not messages or messages[-1] != attempt.get("final_assistant_response", ""):
            raise ValueError(f"Final assistant text does not match the raw JSONL event stream: {cache_path.name}")
        parsed_from_text = ns["scale_parse_response"](messages[-1], request.get("expected_case_ids"))
        if parsed_from_text != attempt.get("parsed"):
            raise ValueError(f"Parsed cache content differs from final assistant raw text: {cache_path.name}")
    else:
        terminal = [event for event in events if event.get("type") in {"turn.failed", "turn.completed"}]
        if (messages or attempt.get("final_assistant_response") or attempt.get("parsed") is not None
                or attempt.get("error") != capacity_error or attempt.get("return_code") != 1
                or attempt.get("pending") is not False or attempt.get("timed_out")
                or attempt.get("unexpected_tools") or not terminal or terminal[-1].get("type") != "turn.failed"
                or terminal[-1].get("error", {}).get("message") != RESUME_CAPACITY_MESSAGE
                or any(event.get("type") == "turn.completed" for event in terminal)):
            raise ValueError(f"Retained capacity cache is not the reviewed terminal no-answer attempt: {cache_path.name}")
    response = ns["scale_transport_public_response"](attempt, request_key, cached=True)
    return cache, response


def _source_cases(ns: dict[str, Any], notebook_root: Path, main_root: Path, protocol: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, str]]:
    cases: dict[str, dict[str, Any]] = {}
    audits: dict[str, dict[str, Any]] = {}
    pack_hashes: dict[str, str] = {}
    for block in protocol["blocks"]:
        pack_path = main_root / block["source_path"]
        manifest = block["manifest"]
        if not manifest.get("complete") or not manifest.get("all_passed"):
            raise ValueError(f"Source block is not fully audited: {block['specification']['name']}")
        if sha256_file(pack_path) != manifest["corpus_gzip_sha256"]:
            raise ValueError(f"Source pack byte hash changed: {pack_path.name}")
        pack_hashes[str(pack_path.relative_to(notebook_root))] = sha256_file(pack_path)
        audit_path = pack_path.parent / manifest["audit_file"]
        if sha256_file(audit_path) != manifest["audit_gzip_sha256"]:
            raise ValueError(f"Source audit byte hash changed: {audit_path.name}")
        pack_hashes[str(audit_path.relative_to(notebook_root))] = sha256_file(audit_path)
        block_cases = list(ns["scale_iter_corpus"](pack_path, manifest))
        block_audits = [json.loads(line) for line in gzip.decompress(audit_path.read_bytes()).decode("utf-8").splitlines()]
        if len(block_cases) != len(block_audits):
            raise ValueError(f"Source and audit row counts differ: {pack_path.name}")
        for case, audit in zip(block_cases, block_audits):
            if case["case_id"] in cases or audit["case_id"] != case["case_id"]:
                raise ValueError(f"Duplicate or misaligned source audit ID: {case['case_id']}")
            fresh = ns["scale_audit_case"](case)
            if audit != fresh:
                raise ValueError(f"Saved visible-text audit differs from recomputation: {case['case_id']}")
            cases[case["case_id"]] = case
            audits[case["case_id"]] = audit
    return cases, audits, pack_hashes


def run_audit(notebook_root: Path) -> dict[str, Any]:
    notebook_root = Path(notebook_root).resolve()
    data_root = notebook_root / "data" / "scale_v5"
    main_root = data_root / "main"
    original_manifest_path = main_root / "original_manifest.json"
    if not original_manifest_path.is_file():
        return _write_blocked("blocked_originals_not_complete", "original_manifest.json is absent; waiting for originals_complete")
    original_manifest = _json(original_manifest_path)
    if original_manifest.get("phase") != "originals_complete":
        return _write_blocked("blocked_originals_not_complete", "Original manifest does not declare originals_complete")

    try:
        amendment, prior_cache_inventory = _resume_declaration(notebook_root, data_root)
    except Exception as exc:
        return _write_blocked("blocked_invalid_continuation_declaration",
            f"Reviewed infrastructure-continuation declaration failed verification: {type(exc).__name__}: {exc}")
    approved_capacity = amendment["reviewed_failures"][0]
    approved_capacity_key = approved_capacity["request_key"]

    # Deliberately do not open main/manifest.json, dispatch.json, intervention
    # records, or any cache entry other than those named by the original ledger.
    paths = [data_root / "source_freeze.json", data_root / "pilot" / "protocol.json",
        main_root / "protocol.json", main_root / "allocation.json", main_root / "selection.json",
        main_root / "candidates.jsonl", main_root / "original_request_ledger.jsonl",
        main_root / "original_metrics.json", original_manifest_path,
        AUTHORING / "scale_main_material_review.json",
        data_root / "infrastructure_resume" / "amendment_001.json",
        data_root / amendment["cache_inventory"]["path"]]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        return _write_blocked("blocked_missing_original_materials", "Missing frozen original artifacts: " + "; ".join(missing))

    ns = load_helpers()
    source_freeze = _json(data_root / "source_freeze.json")
    protocol = _json(main_root / "protocol.json")
    allocation = _json(main_root / "allocation.json")
    selection = _json(main_root / "selection.json")
    original_metrics = _json(main_root / "original_metrics.json")
    main_material_review = _json(AUTHORING / "scale_main_material_review.json")
    candidates = ns["scale_read_records"](main_root / "candidates.jsonl")
    ledger = ns["scale_read_records"](main_root / "original_request_ledger.jsonl")
    issues: list[str] = []
    checks: dict[str, bool] = {}

    runtime_hashes = {}
    for name, expected in source_freeze.get("source_sha256", {}).items():
        actual = sha256_file(AUTHORING / name) if (AUTHORING / name).is_file() else None
        runtime_hashes[name] = actual
        if actual != expected:
            issues.append(f"Frozen source hash changed: {name}")
    _append_check(checks, issues, "runtime_sources_match_committed_freeze", bool(runtime_hashes) and all(
        runtime_hashes.get(name) == digest for name, digest in source_freeze.get("source_sha256", {}).items()))
    _append_check(checks, issues, "independent_pre_call_source_gate_passed", main_material_review.get("passed") is True
        and main_material_review.get("phase") == "prepared_main_materials_review")

    _append_check(checks, issues, "original_manifest_matches_candidates_and_selection",
        original_manifest.get("phase") == "originals_complete"
        and protocol.get("phase") == "prepared_main"
        and protocol.get("protocol") == ns["SCALE_PROTOCOL"]
        and protocol.get("instructions_hash") == ns["scale_hash"](ns["SCALE_TASK_INSTRUCTIONS"])
        and original_manifest.get("protocol_hash") == ns["scale_hash"](protocol)
        and original_manifest.get("selection_hash") == ns["scale_hash"](selection)
        and original_manifest.get("candidate_hash") == ns["scale_hash"](candidates)
        and original_manifest.get("request_keys") == [item.get("request_key") for item in ledger])
    _append_check(checks, issues, "candidate_and_ledger_counts_match_manifest",
        len(candidates) == original_manifest.get("n_collection", -1) + original_manifest.get("n_audit", -1)
        and len(ledger) == len(candidates)
        and original_manifest.get("n_audit") == protocol["config"]["n_audit"])

    cases, audits, pack_hashes = _source_cases(ns, notebook_root, main_root, protocol)
    expected_pack_hashes: dict[str, str] = {}
    block_summaries = {row["name"]: row for row in main_material_review.get("block_summaries", [])}
    block_summary_matches = True
    for block in protocol["blocks"]:
        manifest = block["manifest"]
        pack_path = main_root / block["source_path"]
        audit_path = pack_path.parent / manifest["audit_file"]
        expected_pack_hashes[str(pack_path.relative_to(notebook_root))] = manifest["corpus_gzip_sha256"]
        expected_pack_hashes[str(audit_path.relative_to(notebook_root))] = manifest["audit_gzip_sha256"]
        block_name = block.get("specification", {}).get("name")
        summary = block_summaries.get(block_name, {})
        block_summary_matches = block_summary_matches and (
            summary.get("compressed_sha256") == manifest["corpus_gzip_sha256"]
            and summary.get("audit_compressed_sha256") == manifest["audit_gzip_sha256"]
            and summary.get("n_cases") == manifest["n_cases"])
    _append_check(checks, issues, "source_pack_hashes_match_pre_call_gate",
        pack_hashes == expected_pack_hashes and block_summary_matches
        and all(main_material_review.get("source_pack_sha256", {}).get(key) == value
            for key, value in expected_pack_hashes.items() if key.endswith(".jsonl.gz") and ".audit." not in key))
    cases_by_id = cases
    candidate_by_id: dict[str, dict[str, Any]] = {}
    for row in candidates:
        cid = row.get("case_id")
        if cid in candidate_by_id:
            issues.append(f"Duplicate original candidate for {cid}")
        candidate_by_id[cid] = row
    ledger_by_id = {row.get("case_id"): row for row in ledger}
    if len(ledger_by_id) != len(ledger):
        issues.append("Duplicate original request-ledger case IDs")

    collection_ids = set(allocation["collection_case_ids"])
    audit_ids = set(allocation["audit_case_ids"])
    called_collection_ids = [row["case_id"] for row in candidates if row.get("split") == "collection"]
    audit_candidate_ids = [row["case_id"] for row in candidates if row.get("split") == "audit"]
    called_set = set(called_collection_ids)
    chunks = allocation["chunks"]
    expected_prefix: list[str] = []
    for chunk in chunks:
        if set(expected_prefix) == called_set:
            break
        expected_prefix.extend(chunk)
    _append_check(checks, issues, "collection_originals_are_complete_frozen_chunk_prefix",
        called_set == set(expected_prefix) and len(called_collection_ids) == len(called_set)
        and set(called_collection_ids) <= collection_ids)
    _append_check(checks, issues, "all_audit_originals_are_present_and_excluded_from_accrual",
        set(audit_candidate_ids) == audit_ids and len(audit_candidate_ids) == len(audit_ids)
        and not (set(audit_candidate_ids) & set(selection.get("eligible_candidate_ids", [])))
        and original_manifest.get("n_audit") == len(audit_ids))

    eligible: dict[str, dict[str, Any]] = {}
    for row in candidates:
        cid = row.get("case_id")
        case = cases_by_id.get(cid)
        if case is None:
            issues.append(f"Original candidate has no corresponding visible source: {cid}")
            continue
        if case["split"] != row.get("split") or case["content_hash"] != row.get("content_hash"):
            issues.append(f"Original candidate/source lineage differs for {cid}")
        if audits[cid].get("content_hash") != case["content_hash"]:
            issues.append(f"Visible-text audit/source lineage differs for {cid}")
        if row.get("candidate_id") != f"{cid}:original:0" or row.get("arm") != "original" or row.get("stage") != "generate" or row.get("sample") != 0:
            issues.append(f"Non-original row appears in original candidate file: {cid}")
        if row.get("split") == "collection" and ns["scale_value_failure"](row):
            if row.get("error_kind") != "value_failure" or row.get("parse_error") is not None or row.get("transport_error") is not None:
                issues.append(f"Collection value-failure row has a parse/transport/schema classification conflict: {cid}")
            eligible[cid] = row

    _append_check(checks, issues, "every_saved_original_answer_matches_visible_source_and_verifier",
        len(candidates) == len(candidate_by_id) and all(row["case_id"] in cases_by_id for row in candidates))

    raw_cache_hashes: dict[str, str] = {}
    cache_checks = 0
    candidate_exact = True
    ledger_exact = True
    request_by_case: dict[str, dict[str, Any]] = {}
    for row in candidates:
        cid = row["case_id"]
        case = cases_by_id[cid]
        ledger_row = ledger_by_id.get(cid)
        if not ledger_row:
            issues.append(f"Missing original ledger row for {cid}")
            candidate_exact = ledger_exact = False
            continue
        if ledger_row.get("arm") != "original" or ledger_row.get("stage") != "generate" or ledger_row.get("sample") != 0:
            issues.append(f"Original ledger includes a non-original call for {cid}")
        job = ns["scale_make_job"](case, "original")
        request = ns["scale_job_request"](job)
        request_key = ns["scale_request_key"](request)
        request_by_case[cid] = request
        if (request_key != row.get("request_key") or request_key != ledger_row.get("request_key")
                or ns["scale_hash"](request["case_inputs"]) != row.get("request_input_hash")
                or request["feedback"] is not None):
            issues.append(f"Original request identity/input contract differs for {cid}")
            candidate_exact = ledger_exact = False
        if set(request["case_inputs"][0]) != {"case_id", "task_instructions", "documents"}:
            issues.append(f"Original request contains non-source fields for {cid}")
            candidate_exact = False
        cache_file = ledger_row.get("cache_file")
        if not isinstance(cache_file, str) or Path(cache_file).name != f"{request_key}.json.gz" or Path(cache_file).parts[0] != "cache":
            issues.append(f"Original ledger cache path is not keyed to its full request for {cid}")
            candidate_exact = ledger_exact = False
            continue
        cache_path = main_root / cache_file
        if not cache_path.is_file():
            issues.append(f"Original raw cache is missing for {cid}")
            candidate_exact = ledger_exact = False
            continue
        raw_cache_hashes[request_key] = sha256_file(cache_path)
        is_approved_capacity = request_key == approved_capacity_key
        try:
            cache, raw = _cache_response(ns, cache_path, request, request_key,
                capacity_error=approved_capacity["transport_error"] if is_approved_capacity else None)
        except Exception as exc:
            issues.append(f"Original cache failed integrity checks for {cid}: {type(exc).__name__}: {exc}")
            candidate_exact = ledger_exact = False
            continue
        cache_checks += 1
        cached_sha = raw_cache_hashes[request_key]
        if request_key in prior_cache_inventory and cached_sha != prior_cache_inventory[request_key]:
            issues.append(f"Pre-continuation cache bytes changed for {cid}")
            candidate_exact = ledger_exact = False
        if is_approved_capacity:
            if (case.get("split") != "collection" or cached_sha != approved_capacity["cache_sha256"] or cid != approved_capacity["case_id"]
                    or row.get("content_hash") != approved_capacity["content_hash"]
                    or row.get("request_input_hash") != approved_capacity["request_input_hash"]
                    or row.get("transport_error") != approved_capacity["transport_error"]
                    or row.get("response") is not None or row.get("error_kind") != "transport_failure"):
                issues.append(f"Retained capacity row differs from the explicitly approved no-answer cache for {cid}")
                candidate_exact = ledger_exact = False
        attempt = cache["attempts"][0]
        events = attempt.get("events", [])
        terminal_types = [event.get("type") for event in events if event.get("type") in {"turn.completed", "turn.failed"}]
        if is_approved_capacity:
            terminal_failure = (terminal_types and terminal_types[-1] == "turn.failed"
                and not terminal_types.count("turn.completed")
                and any(event.get("type") == "turn.failed"
                    and event.get("error", {}).get("message") == RESUME_CAPACITY_MESSAGE for event in events))
            if (attempt.get("error") != approved_capacity["transport_error"] or attempt.get("return_code") != 1
                    or not terminal_failure or attempt.get("unexpected_tools") or raw.get("error") != approved_capacity["transport_error"]
                    or attempt.get("final_assistant_response") or attempt.get("parsed") is not None):
                issues.append(f"Retained capacity attempt is not the exact terminal no-answer failure for {cid}")
                candidate_exact = ledger_exact = False
        elif (attempt.get("error") is not None or attempt.get("return_code") != 0
                or terminal_types.count("turn.completed") != 1 or "turn.failed" in terminal_types
                or attempt.get("unexpected_tools") or raw.get("error") is not None):
            issues.append(f"Original CLI attempt is not one clean successful terminal response for {cid}")
            candidate_exact = ledger_exact = False
        expected_candidate = _expected_original_candidate(ns, case, request, raw, row)
        if row != expected_candidate:
            issues.append(f"Saved candidate differs from exact recomputation from raw response for {cid}")
            candidate_exact = False
        expected_ledger = {
            "request_key": request_key, "candidate_id": row["candidate_id"], "case_id": cid,
            "source_hash": case["content_hash"], "request_input_hash": ns["scale_hash"](request["case_inputs"]),
            "feedback_hash": ns["scale_hash"](request["feedback"]), "arm": "original", "stage": "generate",
            "sample": 0, "split": case["split"], "model": ns["SCALE_MODEL"], "reasoning_effort": "high",
            "timeout_s": 900, "usage": raw.get("usage", {}) or {}, "transport_error": raw.get("error"),
            "parse_error": raw.get("parse_error") or row.get("parse_error"),
            "cli_error_events": raw.get("cli_error_events", []) or [],
            "observed_reconnect_events": raw.get("observed_reconnect_events", []) or [],
            "started_at": raw.get("started_at"), "finished_at": raw.get("finished_at"),
            "subprocess_elapsed_s": raw.get("elapsed_s"), "return_code": raw.get("return_code"),
            "resolved_model": raw.get("resolved_model"), "cache_file": f"cache/{request_key}.json.gz"}
        if ledger_row != expected_ledger:
            issues.append(f"Original ledger differs from raw CLI cache for {cid}")
            ledger_exact = False

    _append_check(checks, issues, "all_original_cache_entries_are_terminal_and_match_full_requests",
        cache_checks == len(candidates) and candidate_exact and ledger_exact)
    _append_check(checks, issues, "saved_candidates_and_ledger_recompute_exactly_from_raw_cache",
        candidate_exact and ledger_exact)
    capacity_rows = [row for row in candidates if row.get("request_key") == approved_capacity_key]
    _append_check(checks, issues, "exactly_one_approved_capacity_failure_is_retained_and_ineligible",
        len(capacity_rows) == 1 and capacity_rows[0].get("response") is None
        and capacity_rows[0].get("transport_error") == approved_capacity["transport_error"]
        and capacity_rows[0].get("error_kind") == "transport_failure"
        and not ns["scale_value_failure"](capacity_rows[0]))
    original_request_keys = {row.get("request_key") for row in ledger}
    _append_check(checks, issues, "all_696_pre_continuation_cache_keys_are_preserved_in_originals",
        len(prior_cache_inventory) == 696 and set(prior_cache_inventory).issubset(original_request_keys)
        and all(raw_cache_hashes.get(key) == digest for key, digest in prior_cache_inventory.items()))

    expected_eligible_ids = [cid for cid in allocation["failure_selection_ranking"] if cid in eligible]
    target = protocol["config"]["target_failures"]
    expected_selected = expected_eligible_ids[:target]
    selection_valid = (selection.get("selected_case_ids") == expected_selected
        and selection.get("eligible_candidate_ids") == [eligible[cid]["candidate_id"] for cid in expected_eligible_ids]
        and selection.get("selected_candidate_ids") == [eligible[cid]["candidate_id"] for cid in expected_selected]
        and selection.get("n_eligible_failures") == len(eligible)
        and selection.get("target_shortfall") == max(0, target - len(expected_selected))
        and selection.get("target_reached") == (len(eligible) >= target)
        and selection.get("source_hashes") == {cid: eligible[cid]["content_hash"] for cid in expected_selected}
        and selection.get("input_hashes") == {cid: eligible[cid]["request_input_hash"] for cid in expected_selected})
    _append_check(checks, issues, "seeded_failure_selection_matches_all_accrued_genuine_value_failures", selection_valid)

    # Check that collection accrual stopped only at the predeclared target or cap,
    # with no inspection of later repair outcomes.
    chunk_counts = [len(chunk) for chunk in allocation["chunks"]]
    called_n = len(called_collection_ids)
    whole_chunk_prefix = 0
    for size in chunk_counts:
        whole_chunk_prefix += size
        if whole_chunk_prefix >= called_n:
            break
    expected_stop = (called_n == protocol["config"]["collection_cap"]
        or (len(eligible) >= target and called_n == whole_chunk_prefix))
    if called_n > protocol["config"]["n_initial"]:
        previous_n = called_n - protocol["config"]["chunk_size"]
        prior_ids = set(allocation["collection_case_ids"][:previous_n])
        prior_failures = sum(ns["scale_value_failure"](candidate_by_id[cid]) for cid in prior_ids if cid in candidate_by_id)
        expected_stop = expected_stop and prior_failures < target
    else:
        expected_stop = expected_stop and called_n == protocol["config"]["n_initial"]
    _append_check(checks, issues, "collection_stopping_rule_matches_fixed_chunks_and_failure_target", expected_stop)

    selected_rows = [eligible[cid] for cid in expected_selected]
    selected_cases = [cases_by_id[cid] for cid in expected_selected]
    by_case = {case["case_id"]: case for case in selected_cases}
    dispatch_jobs = ns["scale_paired_dispatch_jobs"](selected_rows, {**cases_by_id}, protocol["config"])
    prospective: dict[str, dict[str, Any]] = {arm: {} for arm in ns["SCALE_ARMS"]}
    prospective_keys: dict[str, list[str]] = {arm: [] for arm in ns["SCALE_ARMS"]}
    prospective_contract = True
    for old in selected_rows:
        cid = old["case_id"]
        case = by_case[cid]
        if not ns["scale_value_failure"](old) or old["split"] != "collection":
            issues.append(f"Selected intervention source is not a usable schema-valid value failure: {cid}")
            prospective_contract = False
        for arm in ("fresh_retry", "feedback_repair"):
            job = ns["scale_make_job"](case, arm, old if arm == "feedback_repair" else None)
            request = ns["scale_job_request"](job)
            key = ns["scale_request_key"](request)
            prospective[arm][cid] = request
            prospective_keys[arm].append(key)
            if (key == old["request_key"] or request["case_inputs"] != request_by_case[cid]["case_inputs"]
                    or ns["scale_hash"](request["case_inputs"]) != old["request_input_hash"]):
                issues.append(f"Prospective {arm} request is not a unique same-source request for {cid}")
                prospective_contract = False
            if arm == "fresh_retry":
                if (request["stage"] != "generate" or request["sample"] != 1 or request["feedback"] is not None
                        or "repair" in request["messages"][0]["content"]):
                    issues.append(f"Fresh retry contains original feedback or has wrong stage/sample for {cid}")
                    prospective_contract = False
            else:
                expected_feedback = {cid: {"original_output": old["response"], "validator_feedback": ns["scale_generic_feedback"](old)}}
                if request["stage"] != "repair" or request["sample"] != 0 or request["feedback"] != expected_feedback:
                    issues.append(f"Repair does not contain exactly the selected sample-0 original and derived flags for {cid}")
                    prospective_contract = False
                fb = request["feedback"][cid]
                if set(fb) != {"original_output", "validator_feedback"}:
                    prospective_contract = False
                flags = fb.get("validator_feedback", {})
                if set(flags) != {"wrong_fields", "schema_failed", "evidence_failed_fields"}:
                    prospective_contract = False
                if (flags.get("wrong_fields") != [field for field in ns["SCALE_FIELDS"] if not old["verification"]["field_correct"][field]]
                        or flags.get("schema_failed") != (not old["verification"]["valid_schema"])
                        or flags.get("evidence_failed_fields") != [field for field in ns["SCALE_FIELDS"] if not old["verification"]["evidence_correct"][field]]):
                    issues.append(f"Repair flags are not exact generic validator flags for {cid}")
                    prospective_contract = False
                # Gold is forbidden by structure. The original_output itself may
                # naturally contain numeric values equal to gold, so do not use
                # substring/value equality as a false-positive leak test.
                if any(k in fb for k in ("gold", "answer_key", "expected_answer", "trace", "calculation")):
                    issues.append(f"Repair feedback has a forbidden evaluator key for {cid}")
                    prospective_contract = False

    all_new_keys = prospective_keys["fresh_retry"] + prospective_keys["feedback_repair"]
    original_keys = {row["request_key"] for row in ledger}
    if (len(all_new_keys) != len(set(all_new_keys)) or set(all_new_keys) & original_keys
            or len(prospective_keys["fresh_retry"]) != len(expected_selected)
            or len(prospective_keys["feedback_repair"]) != len(expected_selected)):
        issues.append("Prospective arm request keys are not unique, paired, and distinct from originals")
        prospective_contract = False

    wave_plan: list[dict[str, Any]] = []
    for wave_index, start in enumerate(range(0, len(dispatch_jobs), protocol["config"]["max_workers"])):
        jobs = dispatch_jobs[start:start + protocol["config"]["max_workers"]]
        pairs: dict[str, set[str]] = {}
        wave_keys = []
        for job in jobs:
            cid, arm = job["case"]["case_id"], job["arm"]
            pairs.setdefault(cid, set()).add(arm)
            request = ns["scale_job_request"](job)
            key = ns["scale_request_key"](request)
            if key != ns["scale_request_key"](prospective[arm][cid]):
                issues.append(f"Dispatched wave key mismatch for {cid}/{arm}")
                prospective_contract = False
            wave_keys.append(key)
        expected_pairs = {cid: set(ns["SCALE_ARMS"]) for cid in pairs}
        if pairs != expected_pairs or len(jobs) not in (2, protocol["config"]["max_workers"]):
            issues.append(f"Dispatch wave {wave_index} does not contain complete arm pairs")
            prospective_contract = False
        wave_plan.append({"wave_index": wave_index, "n_requests": len(jobs),
            "case_ids": list(dict.fromkeys(job["case"]["case_id"] for job in jobs)),
            "arms_by_case": {cid: sorted(arms) for cid, arms in pairs.items()},
            "request_key_set_sha256": canonical_hash(sorted(wave_keys))})
    _append_check(checks, issues, "prospective_interventions_are_paired_same_source_generic_feedback_only",
        prospective_contract)

    _append_check(checks, issues, "four_request_waves_pair_both_arms_for_two_sources",
        protocol["config"].get("max_workers") == 4
        and all(row["n_requests"] == 4 and len(row["case_ids"]) == 2 for row in wave_plan[:-1])
        and (not wave_plan or (wave_plan[-1]["n_requests"] in (2, 4)
            and len(wave_plan[-1]["case_ids"]) == wave_plan[-1]["n_requests"] // 2)))

    checks["all_saved_source_audits_recompute"] = len(audits) == len(cases)
    checks["audit_split_never_enters_failure_accrual"] = not (audit_ids & set(eligible))
    checks["original_metrics_match_candidate_counts"] = (
        original_metrics.get("physical_cli_requests") == len(ledger)
        and original_metrics.get("n_selected") == len(expected_selected)
        and original_metrics.get("target_shortfall") == max(0, target - len(expected_selected)))
    if not checks["original_metrics_match_candidate_counts"]:
        issues.append("Saved original metrics disagree with candidate, selection or ledger counts")

    overall = all(checks.values()) and not issues
    report = {
        "passed": overall,
        "phase": "pre_intervention_originals_review",
        "completion_state": "originals_complete_pre_intervention" if overall else "blocked_or_failed",
        "model_calls": 0,
        "intervention_outcomes_or_cache_files_read": False,
        "continuation_intervention_outcomes_or_cache_files_read": False,
        "frozen_runtime_or_study_data_modified": False,
        "checks": checks,
        "issues": issues,
        "counts": {"main_original_candidates": len(candidates), "collection_originals": len(called_collection_ids),
            "audit_originals": len(audit_candidate_ids), "eligible_collection_value_failures": len(eligible),
            "selected_failure_cases": len(expected_selected), "original_cache_entries_checked": cache_checks,
            "prospective_fresh_retry_requests": len(prospective_keys["fresh_retry"]),
            "prospective_feedback_repair_requests": len(prospective_keys["feedback_repair"]),
            "prospective_four_request_waves": sum(row["n_requests"] == 4 for row in wave_plan),
            "prospective_partial_waves": sum(row["n_requests"] != 4 for row in wave_plan),
            "source_cases_reaudited": len(audits)},
        "selection": {"target": target, "shortfall": selection.get("target_shortfall"),
            "selected_case_ids_sha256": canonical_hash(expected_selected),
            "selected_candidate_ids_sha256": canonical_hash(selection.get("selected_candidate_ids", [])),
            "failure_ranking_sha256": canonical_hash(allocation["failure_selection_ranking"])},
        "prospective_requests": {"request_keys_by_arm_sha256": {arm: canonical_hash(sorted(keys)) for arm, keys in prospective_keys.items()},
            "all_new_request_keys_sha256": canonical_hash(sorted(all_new_keys)),
            "all_original_request_keys_sha256": canonical_hash(sorted(original_keys)),
            "wave_plan": wave_plan,
            "note": "Full prospective request bodies are not written. Feedback was checked structurally; original answers may naturally contain values equal to the fixture gold, so no substring-based gold test was used."},
        "source_pack_sha256": pack_hashes,
        "continuation": {"amendment_sha256": sha256_file(data_root / "infrastructure_resume" / "amendment_001.json"),
            "prior_inventory_sha256": sha256_file(data_root / amendment["cache_inventory"]["path"]),
            "prior_inventory_count": len(prior_cache_inventory), "approved_capacity_request_key": approved_capacity_key,
            "approved_capacity_case_id": approved_capacity["case_id"], "approved_capacity_cache_sha256": approved_capacity["cache_sha256"]},
        "original_cache_sha256_by_request_key": raw_cache_hashes,
        "frozen_inputs_sha256": {str(path.relative_to(notebook_root) if path.is_relative_to(notebook_root)
            else path.relative_to(AUTHORING.parent)): sha256_file(path) for path in paths},
        "runtime_source_sha256": runtime_hashes,
        "original_manifest_sha256": sha256_file(original_manifest_path),
    }
    _write_reports(report)
    return report


def _write_blocked(phase: str, issue: str) -> dict[str, Any]:
    report = {"passed": False, "phase": phase, "completion_state": phase, "model_calls": 0,
        "intervention_outcomes_or_cache_files_read": False, "frozen_runtime_or_study_data_modified": False,
        "checks": {}, "issues": [issue]}
    _write_reports(report)
    return report


def _resume_declaration(notebook_root: Path, data_root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate the separately approved continuation and its unchanged 696-cache prefix."""
    amendment_path = data_root / "infrastructure_resume" / "amendment_001.json"
    if sha256_file(amendment_path) != RESUME_AMENDMENT_SHA256:
        raise ValueError("Committed infrastructure-continuation amendment hash differs")
    amendment = _json(amendment_path)
    if (amendment.get("protocol") != "23-scale-v5"
            or amendment.get("phase") != "reviewed_originals_continuation_before_interventions"
            or amendment.get("amendment_version") != "23-scale-capacity-continuation-v1"):
        raise ValueError("Continuation amendment protocol or phase differs")
    if sha256_file(data_root / "source_freeze.json") != amendment.get("source_freeze_sha256"):
        raise ValueError("Frozen runtime-source manifest differs from the amendment")
    failures = amendment.get("reviewed_failures", [])
    if (len(failures) != 1 or failures[0].get("request_key") != "914927327569cbc503218237464f5b516a3caeff4b3e5b4ce82e57c98ae1311d"
            or failures[0].get("case_id") != "account-bbbc0014d5d85695cce9"):
        raise ValueError("Amendment does not authorize exactly the one reviewed no-answer capacity request")
    implementation = amendment.get("implementation", {})
    if (implementation.get("sha256") != RESUME_IMPLEMENTATION_SHA256
            or implementation.get("tests_sha256") != RESUME_TEST_SHA256
            or implementation.get("mocked_tests_passed") != 13):
        raise ValueError("Continuation helper/test version is not the independently reviewed build")
    inventory_path = data_root / amendment.get("cache_inventory", {}).get("path", "")
    if (not inventory_path.is_file()
            or sha256_file(inventory_path) != amendment.get("cache_inventory", {}).get("sha256")):
        raise ValueError("Pre-continuation cache inventory hash differs")
    inventory = _json(inventory_path)
    requests = inventory.get("requests")
    if (inventory.get("protocol") != "23-scale-v5" or inventory.get("count") != 696
            or not isinstance(requests, dict) or len(requests) != 696):
        raise ValueError("Frozen pre-continuation inventory must list exactly 696 request keys")
    if any(not re.fullmatch(r"[0-9a-f]{64}", key) or not re.fullmatch(r"[0-9a-f]{64}", digest)
           for key, digest in requests.items()):
        raise ValueError("Pre-continuation inventory has malformed request keys or cache hashes")
    main_root = data_root / "main"
    for key, expected in requests.items():
        if len(key) != 64 or sha256_file(main_root / "cache" / f"{key}.json.gz") != expected:
            raise ValueError(f"Pre-continuation raw cache bytes differ or are missing: {key}")
    if (failures[0].get("request_key") not in requests
            or requests[failures[0]["request_key"]] != failures[0].get("cache_sha256")):
        raise ValueError("Reviewed capacity failure is not the exact inventoried cache entry")
    declared = amendment.get("declared_at_utc")
    from datetime import datetime
    declared_at = datetime.fromisoformat(declared)
    if declared_at.tzinfo is None:
        raise ValueError("Continuation declaration timestamp has no timezone")
    for key in requests:
        cached = _gzip_json(main_root / "cache" / f"{key}.json.gz")
        attempts = cached.get("attempts", [])
        if (cached.get("key") != key or len(attempts) != 1 or attempts[0].get("pending") is not False
                or datetime.fromisoformat(attempts[0]["finished_at"]) > declared_at):
            raise ValueError(f"Prior cache was not terminal before the continuation declaration: {key}")
    for item in amendment.get("protected_files", []):
        path = data_root / item["path"]
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            raise ValueError(f"Protected pre-call input changed: {item['path']}")
    for relative, expected in amendment.get("provenance_sha256", {}).items():
        path = data_root / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"Continuation provenance artifact changed: {relative}")
    for item in amendment.get("request_plans", []):
        path = data_root / item["path"]
        if path.parent != (main_root / "request_plans") or sha256_file(path) != item["sha256"]:
            raise ValueError("Frozen request-plan artifact changed")
    if len(amendment.get("archived_stops", [])) != 1:
        raise ValueError("Exactly one byte-exact stop archive is expected for this continuation")
    original_stop = main_root / "infrastructure_stop.json"
    archived_stop = data_root / amendment["archived_stops"][0]["path"]
    stop_hash = amendment.get("original_stop_sha256")
    if (sha256_file(original_stop) != stop_hash or sha256_file(archived_stop) != stop_hash
            or stop_hash != failures[0].get("stop_sha256")):
        raise ValueError("Original and archived capacity-stop bytes do not match amendment")
    return amendment, requests


def _write_reports(report: dict[str, Any]) -> None:
    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    counts = report.get("counts", {})
    lines = [
        "# Scale-v5 original failure and intervention-input review", "",
        f"**Gate: {'passed' if report.get('passed') else 'blocked'}.** This audit covers the frozen original phase before any intervention outcomes are examined.", "",
        "The audit reads only the original candidate file, original request ledger, original-only cache entries named by that ledger, frozen source packs and their saved audit rows, and original-phase protocol/selection files. It does not enumerate or open intervention caches or outputs. It makes no model calls and writes only these two review files.", "",
        "The committed continuation amendment permits one terminal capacity failure to remain as an original row with no answer. The audit checks its exact request/cache identity, confirms the old 696-key cache prefix is unchanged, and keeps the transport failure out of value-failure accrual.", "",
        f"It rechecks {counts.get('main_original_candidates', 0)} saved answers against their visible source text and independently recomputed source audits. It verifies the frozen accrual stopping rule, seeded ranking over every accrued usable schema-valid value failure, and separation of the 96-case audit. It also constructs prospective fresh and repair request identities in memory. For each selected case the inputs are identical; fresh has no feedback, and repair contains only the exact sample-0 answer and generic verifier flags. Full prompt bodies are not saved here.", "",
        f"The prospective plan has {counts.get('selected_failure_cases', 0)} paired cases, {counts.get('prospective_fresh_retry_requests', 0)} fresh requests, {counts.get('prospective_feedback_repair_requests', 0)} repair requests, and {counts.get('prospective_four_request_waves', 0)} complete four-request waves.", "",
        "| Check | Result |", "|---|---|"
    ]
    for name, passed in report.get("checks", {}).items():
        lines.append(f"| {name.replace('_', ' ')} | {'pass' if passed else 'FAIL'} |")
    lines += ["", "Request and source hashes, raw cache hashes, selected IDs, and wave plan hashes are in [scale_original_failure_review.json](scale_original_failure_review.json)."]
    if report.get("issues"):
        lines += ["", "## Issues", ""]
        lines.extend(f"- {issue}" for issue in report["issues"])
    MD_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook-root", type=Path, default=DEFAULT_NOTEBOOK_ROOT)
    args = parser.parse_args()
    report = run_audit(args.notebook_root)
    summary = {key: report.get(key) for key in ("passed", "phase", "completion_state", "issues", "counts")}
    summary["json_report"] = str(JSON_REPORT)
    summary["markdown_report"] = str(MD_REPORT)
    print(json.dumps(summary, indent=2))
    if not report.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
