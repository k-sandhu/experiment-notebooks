"""Package a completed and independently audited v4d/v4e run, without model calls.

Incomplete or stale audits fail before any destination file is changed. Importing
this module is read-only; call high_package_run after the completion checks pass.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


HIGH_PACKAGE_VERSION = "23-high-completed-package-v2"
HIGH_PACKAGE_SERVICE_PROTOCOLS = {"23-high-v4": 28, "23-high-v4b": 1, "23-high-v4c": 2}
HIGH_PACKAGE_TESTS = {"passed": 34, "distinct_tests": 34, "fixture_tests": 17,
    "transport_and_engine_tests": 12, "parallel_dispatch_tests": 5, "live_calls_in_tests": 0,
    "counting_note": "17 fixture tests + 12 transport/serial-engine tests + 5 parallel tests. The combined17-test dispatch suite includes the same12 core tests; they are counted once."}


def high_package_read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def high_package_lines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line]


def high_package_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def high_package_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def high_package_require(condition, message):
    if not condition:
        raise RuntimeError("Packaging pending/refused: " + message + ". Existing provenance and snapshots were left unchanged.")


def high_package_usage(root, records):
    """Retain the audited attempt denominator, including missing historical usage."""
    groups = defaultdict(list)
    resolved = set()
    seen = set()
    for record in records:
        key = record["request_key"]
        high_package_require(key not in seen, "duplicate audited physical request")
        seen.add(key)
        cache = high_package_read(Path(root) / record["cache_file"])
        request = cache["request"]
        high_package_require(cache["key"] == key == high_package_hash(request), "raw request hash differs from the audit")
        high_package_require(len(cache["attempts"]) == 1, "unexpected orchestration retry in a cached request")
        high_package_require(request["model"] == "gpt-6.1-sol" and request["reasoning_effort"] == "high", "a request uses another model or effort")
        high_package_require('model_reasoning_effort="high"' in request["cli_options"] and len(request["case_inputs"]) == 1,
            "a request lacks the one-case high-effort CLI profile")
        high_package_require(request["protocol"] == record["protocol"], "request protocol differs from its audit row")
        attempt = cache["attempts"][0]
        if attempt.get("resolved_model"):
            resolved.add(attempt["resolved_model"])
        groups[record["protocol"]].append((record, attempt))
    totals, sequences = Counter(), []
    for protocol, rows in sorted(groups.items()):
        usage = Counter()
        for _, attempt in rows:
            usage.update({k: v for k, v in (attempt.get("token_usage") or {}).items() if type(v) in (int, float)})
        totals.update(usage)
        sequences.append({"protocol": protocol, "physical_cli_subprocesses": len(rows),
            "outcomes": dict(Counter(row["outcome"] for row, _ in rows)),
            "requests_with_usage": sum(bool(attempt.get("token_usage")) for _, attempt in rows),
            "requests_missing_usage": sum(not bool(attempt.get("token_usage")) for _, attempt in rows),
            "observed_usage": dict(usage),
            "requests_with_observed_reconnect_events": sum(bool(attempt.get("observed_reconnect_events")) for _, attempt in rows),
            "requests_with_cli_error_events": sum(bool(attempt.get("cli_error_events", attempt.get("errors"))) for _, attempt in rows),
            "max_workers": 4 if protocol == "23-high-v4" else 2 if protocol == "23-high-v4e" else 1,
            "included_in_healthy_comparison": protocol in {"23-high-v4d", "23-high-v4e"}})
    return {"observed_usage": dict(totals), "service_sequence": sequences,
        "resolved_model_labels_observed": sorted(resolved),
        "requests_with_usage": sum(row["requests_with_usage"] for row in sequences),
        "requests_missing_usage": sum(row["requests_missing_usage"] for row in sequences)}


def high_package_validate(base, root):
    """Read-only completion gate. A stale31-attempt service audit cannot pass."""
    base, root = Path(base), Path(root)
    data, main = root / "data" / "high_v4", root / "data" / "high_v4" / "main"
    required = [data / "artifact_audit.json", data / "pilot" / "ladder.json", data / "pilot" / "protocol.json",
        data / "main_source_freeze.json", data / "main_dispatch_declaration.json", main / "manifest.json",
        main / "metrics.json", main / "protocol.json", main / "selection.json", main / "request_ledger.jsonl",
        main / "candidates.jsonl", main / "interventions.jsonl", main / "exports" / "curated_unique.jsonl"]
    missing = [path.relative_to(root).as_posix() for path in required if not path.exists()]
    high_package_require(not missing, "required completion artifacts are absent: " + ", ".join(missing))
    audit, manifest = high_package_read(required[0]), high_package_read(main / "manifest.json")
    high_package_require(audit.get("passed") is True and audit.get("main_complete") is True,
        "the final independent artifact audit has not certified completed main")
    high_package_require(manifest.get("phase") == "interventions_complete", "paired interventions are incomplete")
    metrics, protocol, selection = [high_package_read(main / name) for name in ("metrics.json", "protocol.json", "selection.json")]
    ladder, pilot_protocol = high_package_read(data / "pilot" / "ladder.json"), high_package_read(data / "pilot" / "protocol.json")
    high_package_require(protocol["protocol"] == "23-high-v4e" and protocol["max_workers"] == 2,
        "main is not the declared two-worker v4e fork")
    high_package_require(pilot_protocol["protocol"] == "23-high-v4d" and ladder["physical_cli_requests"] == 16,
        "healthy serial v4d pilot is not the completed16-call pilot")
    high_package_require(ladder["protocol_hash"] == high_package_hash(pilot_protocol)
        and protocol["pilot_ladder_hash"] == high_package_hash(ladder), "healthy pilot lineage changed")
    high_package_require(manifest["protocol_hash"] == high_package_hash(protocol)
        and manifest["selection_hash"] == high_package_hash(selection), "final manifest protocol or selection hash differs")
    records = audit["requests"]
    high_package_require(audit["counts"]["request_records"] == len(records), "audit request denominator differs")
    service = Counter(row["protocol"] for row in records if row["protocol"] in HIGH_PACKAGE_SERVICE_PROTOCOLS)
    high_package_require(dict(service) == HIGH_PACKAGE_SERVICE_PROTOCOLS, "all31 historical service attempts are not preserved")
    ledger = high_package_lines(main / "request_ledger.jsonl")
    originals, interventions = high_package_lines(main / "candidates.jsonl"), high_package_lines(main / "interventions.jsonl")
    keys = [row["request_key"] for row in ledger]
    high_package_require(len(set(keys)) == len(keys) and keys == manifest["request_keys"], "main ledger or physical request identity differs")
    high_package_require(set(keys) == {row["request_key"] for row in records if row["protocol"] == "23-high-v4e"},
        "artifact audit is stale or does not cover every main request")
    high_package_require(set(keys) == {row["request_key"] for row in originals + interventions}, "candidate/ledger request coverage differs")
    high_package_require(metrics["physical_cli_requests"] == manifest["physical_cli_requests"] == len(keys), "main physical request counts differ")
    high_package_require(metrics["n_selected"] == manifest["n_selected"] == len(selection["selected_case_ids"]), "paired selected-case counts differ")
    check = audit.get("paired_lineage_check") or {}
    high_package_require(check.get("n_pairs") == metrics["n_selected"]
        and check.get("feedback_has_field_names_and_original_answer_only") is True
        and check.get("selection_matches_predeclared_ranking") is True, "final paired source/feedback audit is incomplete")
    observed = metrics["paired_value_recovery"]
    high_package_require([check.get(name) for name in ("both", "repair_only", "fresh_only", "neither")] ==
        [observed[name] for name in ("both_success", "repair_only", "fresh_only", "neither_success")], "paired outcomes differ between metrics and audit")
    pilot_keys = [key for block in ladder["levels"] for key in block["request_keys"]]
    high_package_require(len(pilot_keys) == 16 and set(pilot_keys) ==
        {row["request_key"] for row in records if row["protocol"] == "23-high-v4d"}, "healthy pilot request audit coverage differs")
    high_package_require(len(records) == 31 + len(pilot_keys) + len(keys), "an unexpected protocol is included or a physical attempt is missing")
    usage = high_package_usage(root, records)
    high_package_require(usage["observed_usage"] == audit["observed_usage"], "raw observed usage differs from the audit")
    high_package_require(usage["requests_with_usage"] == audit["counts"]["requests_with_usage"], "known/missing usage counts differ")
    freeze = high_package_read(data / "main_source_freeze.json")
    for name, item in freeze["core_freeze"]["sources"].items():
        high_package_require(high_package_sha(base / name) == item["raw_sha256"], "frozen core changed: " + name)
    for name, frozen_hash in freeze["files"].items():
        high_package_require(high_package_sha(base / name) == frozen_hash, "pre-main source snapshot changed: " + name)
    high_package_require(freeze["tests_passed"] == {"fixtures": 17, "transport_and_serial_engine": 12, "parallel_dispatch": 5},
        "the declared34 distinct test count differs")
    high_package_require(protocol["config"]["max_workers"] == 2 and protocol["reasoning_effort"] == "high", "actual main effort/worker metadata differs")
    failure_path = base / "high_failure_material_review.json"
    if failure_path.exists():
        failure_report = high_package_read(failure_path)
        high_package_require(failure_report.get("status") == "complete"
            and failure_report.get("cache_audit", {}).get("cache_files") == len(keys),
            "the posthoc source-material report is partial or stale")
        high_package_require(not failure_report["source_gate"]["source_check_failures"]
            and not failure_report["cache_audit"]["request_hash_errors"]
            and not failure_report["cache_audit"]["request_input_errors"],
            "the posthoc source-material report contains source/request mismatches")
    return {"audit": audit, "manifest": manifest, "metrics": metrics, "protocol": protocol, "selection": selection,
        "pilot_ladder": ladder, "pilot_protocol": pilot_protocol, "freeze": freeze, "usage": usage,
        "input_sha256": {path.relative_to(root).as_posix(): high_package_sha(path) for path in required}}


def high_package_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def high_package_run(base, root):
    base, root = Path(base), Path(root)
    checked = high_package_validate(base, root)  # No writes occur before this gate.
    data = root / "data" / "high_v4"
    audit, metrics, protocol = checked["audit"], checked["metrics"], checked["protocol"]
    prior = high_package_read(root / "data" / "provenance.json")
    previous_path = data / "provenance.json"
    previous = high_package_read(previous_path) if previous_path.exists() else {}
    old_service_path = data / "service_blocked_provenance.json"
    prior_service = high_package_read(old_service_path) if old_service_path.exists() else previous
    sources = set(checked["freeze"]["core_freeze"]["sources"]) | {
        "high_parallel.py", "test_high_parallel.py", "collect_high_main.py", "collect_high_continue.py",
        "test_high_fixtures.py", "test_high_transport.py", "test_high_experiment.py", "high_source_frozen_v4b.json",
        "high_source_frozen.json", "collect_high.py", "collect_high_recovery.py", "package_high.py",
        "audit_high_all_main_sql.py", "run_high_all_main_audit.py", "audit_high_complete.py", "audit_high_saved.py",
        "high_reporting.py", "high_complete_reporting.py", "audit_high_failure_materials.py",
        "high_failure_material_review.json", "high_failure_material_review.md", "high_main_source_review.json",
        "high_main_source_review.md", "high_all_main_source_audit.json", "audit_high_rendered_sources.py",
        "build_high_extension.py", "integrate_high.py", "finalize_high_complete.py", "refresh_high_complete.py",
        "declare_high_interventions.py", "run_high_offline_replay.py", "verify_high_delivery.py", "save_high_reference_checks.py"}
    sources.update({"audit_high_nonround_errors.py", "high_nonround_error_review.json", "high_nonround_error_review.md",
                    "fix_high_notebook_anchors.py", "render_high_review.py"})
    available = sorted(name for name in sources if (base / name).is_file())
    source_hashes = {name: high_package_sha(base / name) for name in available}
    failure_report = high_package_read(base / "high_failure_material_review.json") if (base / "high_failure_material_review.json").exists() else None
    source_model = next(model for model in prior["models"] if model["id"] == "gpt-6.1-sol")
    usage = checked["usage"]
    service_rows = [row for row in usage["service_sequence"] if row["protocol"] in HIGH_PACKAGE_SERVICE_PROTOCOLS]
    provenance = {
        "package_version": HIGH_PACKAGE_VERSION, "checked_on": audit["audited_at_utc"][:10], "status": "completed_and_independently_audited",
        "purpose": "Collect verified extraction examples and compare a prior-answer-plus-diagnostic repair package with fresh retry on genuine original high-effort Sol value failures. Frozen models; no training or downstream training destination.",
        "model": {**source_model, "reasoning_effort": "high", "requested_alias": "gpt-6.1-sol",
            "resolved_model_labels_observed": usage["resolved_model_labels_observed"],
            "resolved_model_snapshot": None,
            "resolution_note": "The actual requested alias and high CLI flag are retained in every full hashed request. A dated immutable model snapshot is not established by this subscription CLI."},
        "cli_version": prior_service.get("cli_version"), "cli_version_source": "Preserved earlier run provenance; full actual CLI options are cached per request",
        "sources": {"origin": "Fresh programmatically generated fictional procurement packets; models do not write the source packets.",
            "created_on": "2026-10-26", "date_filter": "All packets postdate the documented 2026-04-30 Sol cutoff.",
            "n_pilot_potential": audit["n_pilot_cases"], "n_healthy_pilot_called": checked["pilot_ladder"]["physical_cli_requests"],
            "n_all_level_preflight_main": audit["n_preflight_main_cases"],
            "n_selected_level_potential_main": protocol["config"]["n_initial"] + protocol["config"]["n_expansion"] + protocol["config"]["n_audit"],
            "selected_level": protocol["selected_level"], "pilot_threshold_met": checked["pilot_ladder"]["threshold_met"],
            "independent_source_answers_and_evidence_agree": audit["independent_source_answers_and_evidence_agree"],
            "limitations": "Clean fictional tables with explicit local rules, active statuses, no OCR or missing material, and shared scenario templates."},
        "protocols": {"healthy_pilot": "23-high-v4d", "main": "23-high-v4e", "pilot_max_workers": 1,
            "main_max_workers": 2, "main_dispatch": protocol["protocol_dispatch_fork"],
            "audit_boundary": protocol["audit_boundary"], "pre_main_source_freeze": "main_source_freeze.json",
            "restart_and_parallel_declarations": ["continue_declaration.json", "main_dispatch_declaration.json", "main_parallel_declaration.json"]},
        "actual_main": {"completed": True, "collection": metrics["original_collection"], "sealed_audit": metrics["audit"],
            "n_selected": metrics["n_selected"], "interventions": metrics["interventions"], "exports": metrics["exports"],
            "paired_value_recovery": metrics["paired_value_recovery"], "paired_accepted_recovery": metrics["paired_accepted_recovery"],
            "reconnect_sensitivity": metrics["reconnect_sensitivity"], "selection": checked["selection"],
            "contrast": "Repair package including the original answer and failed-field flags versus fresh retry; this does not isolate feedback from prior-answer exposure."},
        "attempts": audit["counts"], "observed_usage": usage["observed_usage"],
        "requests_with_usage": usage["requests_with_usage"], "requests_missing_usage": usage["requests_missing_usage"],
        "usage_incomplete": audit["usage_incomplete"], "spend_usd": None,
        "cost_note": "All physical CLI attempts, including 31 archived service-history requests, remain in the denominator. Missing/interrupted usage is unknown, not zero. Token components can overlap and must not be added twice. Subscription CLI dollar billing is unavailable.",
        "service_sequence": usage["service_sequence"], "archived_service_history": {"physical_requests": 31,
            "included_in_healthy_accuracy_or_difficulty_selection": False, "runs": service_rows,
            "prior_provenance": "service_blocked_provenance.json"},
        "retry_boundary": "One CLI subprocess per cached request, no orchestration retries. Internal CLI network retries and exact inference draw counts are not independently disabled or guaranteed; observed reconnect/error events are preserved. Parallel main dispatch stops before the next bounded wave on any transport failure.",
        "source_freeze": checked["freeze"], "source_snapshot_sha256": source_hashes, "completion_input_sha256": checked["input_sha256"],
        "source_snapshot_note": "Frozen collection scripts and posthoc authoring scripts are preserved as source provenance. Some collector/audit defaults are authoring-relative and are not portable launchers from this snapshot. Use the self-contained notebook for reproduction. The four test modules and their helper dependencies are colocated here for local unittest execution.",
        "artifact_audit": {"path": "artifact_audit.json", "sha256": high_package_sha(data / "artifact_audit.json"),
            "passed": True, "main_complete": True, "paired_lineage_check": audit["paired_lineage_check"]},
        "posthoc_failure_material_review": {"path": "source_snapshot/high_failure_material_review.json", "report": failure_report} if failure_report else None,
        "tests": HIGH_PACKAGE_TESTS, "rights_note": prior["rights_note"], "terms_source": prior["terms_source"],
        "further_reading_checked_on": prior_service.get("further_reading_checked_on"),
        "historical_preservation": "Previous v1, hard_v2, sol_v3 and archived high-v4 service files remain untouched. This package writes only high_v4 provenance, test summary, source snapshots and review copies."}
    # Every read, source-hash assertion and scientific completion check precedes writes.
    if not old_service_path.exists() and previous:
        high_package_write(old_service_path, previous)
    snapshot = data / "source_snapshot"
    snapshot.mkdir(parents=True, exist_ok=True)
    for name in available:
        (snapshot / name).write_bytes((base / name).read_bytes())
    for source, destination in (("high_design_review.md", "design_review.md"), ("high_fixture_contract.md", "fixture_contract.md"),
                                ("high_pipeline_review.md", "pipeline_review.md")):
        if (base / source).exists():
            (data / destination).write_bytes((base / source).read_bytes())
    high_package_write(data / "provenance.json", provenance)
    high_package_write(data / "test_summary.json", HIGH_PACKAGE_TESTS)
    return provenance


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=base.parent / "experiment_notebooks" / "notebooks" / "23-synthetic-data-curation")
    args = parser.parse_args()
    provenance = high_package_run(base, args.root)
    print(json.dumps({"status": provenance["status"], "attempts": provenance["attempts"],
        "observed_usage": provenance["observed_usage"], "spend_usd": None, "distinct_tests": 34}, indent=2))


if __name__ == "__main__":
    main()
