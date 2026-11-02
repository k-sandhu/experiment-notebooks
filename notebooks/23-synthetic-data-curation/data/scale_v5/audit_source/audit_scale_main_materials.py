"""Read-only full source-material gate for the scale-v5 main cohort.

Run only after collect_scale.py prepare-main has frozen the selected-tier
collection and audit packs. The script builds prospective requests and evaluator
controls in memory; it never calls Codex or writes under the notebook data tree.
It writes only the two review reports beside this script.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any


AUTHORING = Path(__file__).resolve().parent
DEFAULT_NOTEBOOK_ROOT = AUTHORING.parent / "experiment_notebooks" / "notebooks" / "23-synthetic-data-curation"
JSON_REPORT = AUTHORING / "scale_main_material_review.json"
MD_REPORT = AUTHORING / "scale_main_material_review.md"
EXPECTED_COLLECTION = 2048
EXPECTED_AUDIT = 96
EXPECTED_TOTAL = EXPECTED_COLLECTION + EXPECTED_AUDIT
SENTINEL_ANSWER = {
    "order_id": "__SCALE_TEST_NOT_GOLD_ORDER__",
    "sku": "__SCALE_TEST_NOT_GOLD_SKU__",
    "quantity_units": -987654321,
    "unit_price_cents": -987654321,
    "currency": "ZZZ",
    "ship_date": "1900-01-01",
    "status": "__SCALE_TEST_INVALID_STATUS__",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def load_helpers() -> dict[str, Any]:
    namespace: dict[str, Any] = {"__name__": "scale_main_readonly_material_audit"}
    names = ("scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py")
    for name in names:
        source = (AUTHORING / name).read_text(encoding="utf-8")
        exec(compile(source, name, "exec"), namespace)
    namespace["scale_load_cores"](core_dir=AUTHORING)
    return namespace


def fail_if(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def run_audit(notebook_root: Path) -> dict[str, Any]:
    notebook_root = Path(notebook_root).resolve()
    data_root = notebook_root / "data" / "scale_v5"
    main_root = data_root / "main"
    issues: list[str] = []

    required = [
        data_root / "source_freeze.json",
        data_root / "pilot" / "protocol.json",
        data_root / "pilot" / "ladder.json",
        data_root / "pilot" / "previous_corpora.json",
        main_root / "source_plan.json",
        main_root / "protocol.json",
        main_root / "previous_corpora.json",
    ]
    required.extend(main_root / "sources" / name for name in (
        "collection.jsonl.gz", "collection.jsonl.gz.manifest.json",
        "collection.jsonl.gz.audit.jsonl.gz", "audit.jsonl.gz",
        "audit.jsonl.gz.manifest.json", "audit.jsonl.gz.audit.jsonl.gz",
    ))
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        return {
            "passed": False,
            "phase": "blocked_missing_prepared_main_materials",
            "issues": ["prepare-main has not frozen all expected source packs: " + ", ".join(missing)],
            "model_calls": 0,
            "frozen_files_modified": False,
        }

    ns = load_helpers()
    freeze = json.loads((data_root / "source_freeze.json").read_text(encoding="utf-8"))
    pilot_protocol = json.loads((data_root / "pilot" / "protocol.json").read_text(encoding="utf-8"))
    pilot_ladder = json.loads((data_root / "pilot" / "ladder.json").read_text(encoding="utf-8"))
    pilot_prior = json.loads((data_root / "pilot" / "previous_corpora.json").read_text(encoding="utf-8"))
    source_plan = json.loads((main_root / "source_plan.json").read_text(encoding="utf-8"))
    protocol = json.loads((main_root / "protocol.json").read_text(encoding="utf-8"))
    saved_prior = json.loads((main_root / "previous_corpora.json").read_text(encoding="utf-8"))

    # Runtime and byte-frozen helper identities must still match the commit-time freeze.
    runtime_hashes_match = True
    for name, expected in freeze.get("source_sha256", {}).items():
        path = AUTHORING / name
        if not path.is_file() or sha256_file(path) != expected:
            runtime_hashes_match = False
            issues.append(f"Runtime source hash differs from source_freeze.json: {name}")
    fail_if(runtime_hashes_match, "Runtime source hashes match source freeze", issues)
    fail_if(protocol.get("protocol") == ns["SCALE_PROTOCOL"], "Main protocol version matches frozen code", issues)
    fail_if(protocol.get("fixture_version") == ns["SCALE_VERSION"], "Main fixture version matches frozen wrapper", issues)
    fail_if(protocol.get("frozen_rule_source_sha256") == ns["SCALE_CORE_SHA256"], "Frozen core hashes match wrapper declarations", issues)
    fail_if(pilot_ladder.get("protocol_hash") == canonical_hash(pilot_protocol), "Pilot ladder references frozen pilot protocol", issues)
    fail_if(source_plan.get("pilot_ladder_hash") == canonical_hash(pilot_ladder), "Main source plan references frozen pilot ladder", issues)
    fail_if(source_plan.get("selected_tier") == pilot_ladder.get("selected_tier") == protocol.get("selected_tier"), "Main tier equals the selected pilot tier", issues)
    fail_if(source_plan.get("blocks") == [b["specification"] for b in protocol.get("blocks", [])], "Source plan blocks match prepared protocol", issues)

    config = protocol.get("config", {})
    expected_config = {
        "target_failures": 600,
        "n_initial": 512,
        "chunk_size": 256,
        "collection_cap": 2048,
        "n_audit": 96,
        "seed_collection": 255600,
        "seed_audit": 255096,
        "ranking_seed": 255777,
        "dispatch_seed": 255888,
        "bootstrap_seed": 246600,
        "bootstrap_draws": 20000,
    }
    config_matches = all(config.get(key) == value for key, value in expected_config.items())
    fail_if(config_matches, "Main accrual sizes and fixed seeds match preregistered defaults", issues)

    blocks = protocol.get("blocks", [])
    fail_if(len(blocks) == 2, "Prepared main has collection and audit blocks", issues)
    expected_sizes = {"collection": EXPECTED_COLLECTION, "audit": EXPECTED_AUDIT}
    expected_seeds = {"collection": 255600, "audit": 255096}
    selected_tier = protocol.get("selected_tier")
    all_cases: list[dict[str, Any]] = []
    block_reports: list[dict[str, Any]] = []
    source_hashes: dict[str, str] = {}
    request_key_hashes: dict[str, list[str]] = {"original": [], "repair_no_gold_control": []}
    generic_control_count = 0
    generic_control_cases: set[str] = set()
    generated_count = 0
    audit_rows_match = True
    regeneration_matches = True
    request_contract_matches = True
    repair_control_matches = True

    for block in blocks:
        spec = block["specification"]
        name = spec["name"]
        path = main_root / block["source_path"]
        manifest_path = path.with_name(path.name + ".manifest.json")
        if not path.is_file() or not manifest_path.is_file():
            issues.append(f"Missing prepared source material for block {name}")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_hash = sha256_file(path)
        source_hashes[str(path.relative_to(notebook_root))] = source_hash
        fail_if(source_hash == manifest.get("corpus_gzip_sha256") == block.get("manifest", {}).get("corpus_gzip_sha256"),
                f"{name} compressed source hash matches file, manifest and protocol", issues)
        fail_if(block.get("manifest") == manifest, f"{name} in-protocol manifest matches saved manifest", issues)
        fail_if(spec.get("n") == expected_sizes.get(name), f"{name} count matches adopted protocol", issues)
        fail_if(spec.get("seed") == expected_seeds.get(name), f"{name} seed matches adopted protocol", issues)
        fail_if(spec.get("tier") == selected_tier, f"{name} tier matches selected pilot tier", issues)
        fail_if(spec.get("split") == name, f"{name} split label matches its block", issues)
        expected_start = 0 if name == "collection" else EXPECTED_COLLECTION
        fail_if(spec.get("start_index") == expected_start, f"{name} stable index range starts at {expected_start}", issues)

        verified = ns["scale_verify_corpus"](path, manifest_path=manifest_path, full_audit=False)
        fail_if(verified.get("passed") and verified.get("n_cases") == expected_sizes.get(name),
                f"{name} compressed corpus/content/identity hashes verify", issues)
        saved_audit_path = path.parent / manifest["audit_file"]
        audit_hash = sha256_file(saved_audit_path)
        fail_if(audit_hash == manifest.get("audit_gzip_sha256"), f"{name} saved audit gzip hash matches manifest", issues)

        case_iterator = ns["scale_iter_corpus"](path, manifest)
        generation_iterator = ns["scale_iter_cases"](spec["n"], spec["seed"], tier=spec["tier"],
            split=spec["split"], start_index=spec["start_index"])
        with gzip.open(saved_audit_path, "rt", encoding="utf-8") as audit_stream:
            audit_iterator = (json.loads(line) for line in audit_stream if line.strip())
            sentinel = object()
            block_cases: list[dict[str, Any]] = []
            for case, regenerated, saved_audit in itertools.zip_longest(case_iterator, generation_iterator, audit_iterator, fillvalue=sentinel):
                if case is sentinel or regenerated is sentinel or saved_audit is sentinel:
                    issues.append(f"{name} source, regeneration and audit row counts differ")
                    audit_rows_match = False
                    regeneration_matches = False
                    break
                generated_count += 1
                if case != regenerated:
                    regeneration_matches = False
                    issues.append(f"{name} source differs from exact generator output at index {case.get('generation_index')}")
                # Full visible-source audit recomputes the independent SQL/Decimal and text/Fraction results.
                recomputed_audit = ns["scale_audit_case"](case)
                if saved_audit != recomputed_audit:
                    audit_rows_match = False
                    issues.append(f"{name} saved independent audit differs at case {case.get('case_id')}")
                block_cases.append(case)
                all_cases.append(case)

                model_input = ns["scale_model_input"](case)
                if set(model_input) != {"case_id", "task_instructions", "documents"} or model_input["case_id"] != case["case_id"]:
                    request_contract_matches = False
                    issues.append(f"Source-only model-input contract failed for {case.get('case_id')}")
                    continue
                source_request = ns["scale_make_request"](ns["SCALE_MODEL"], "generate", [model_input], sample=0,
                    protocol=ns["SCALE_PROTOCOL"])
                if (source_request["case_inputs"] != [model_input] or source_request["feedback"] is not None
                        or source_request["model"] != ns["SCALE_MODEL"] or source_request["reasoning_effort"] != "high"):
                    request_contract_matches = False
                    issues.append(f"Prospective original request contract failed for {case.get('case_id')}")
                request_key_hashes["original"].append(ns["scale_request_key"](source_request))

                # Test the exact generic-feedback request path with unmistakable synthetic sentinels.
                # This is a transport/input-contract test, not a candidate, score, or model output.
                sentinel_response = {"case_id": case["case_id"], "answer": dict(SENTINEL_ANSWER),
                    "evidence": {field: ["P01"] for field in ns["SCALE_FIELDS"]}}
                sentinel_verification = ns["scale_validate_answer"](case, sentinel_response)
                sentinel_row = {"response": sentinel_response, "verification": sentinel_verification}
                flags = ns["scale_generic_feedback"](sentinel_row)
                feedback = {case["case_id"]: {"original_output": sentinel_response, "validator_feedback": flags}}
                repair_request = ns["scale_make_request"](ns["SCALE_MODEL"], "repair", [model_input], sample=0,
                    feedback=feedback, protocol=ns["SCALE_PROTOCOL"])
                if (repair_request["case_inputs"] != [model_input] or repair_request["feedback"] != feedback
                        or set(flags) != {"wrong_fields", "schema_failed", "evidence_failed_fields"}
                        or set(flags["wrong_fields"]) - set(ns["SCALE_FIELDS"])
                        or set(flags["evidence_failed_fields"]) - set(ns["SCALE_FIELDS"])):
                    repair_control_matches = False
                    issues.append(f"No-gold generic feedback request contract failed for {case.get('case_id')}")
                # Check evaluator leakage by object structure, not by searching
                # values. The sentinel answer strings deliberately contain the
                # word "NOT_GOLD" to make the test-only fixtures recognizable.
                output_keys = set(sentinel_response)
                answer_keys = set(sentinel_response.get("answer", {}))
                evidence_keys = set(sentinel_response.get("evidence", {}))
                feedback_keys = set(repair_request.get("feedback", {}).get(case["case_id"], {}))
                evaluator_keys = {"gold", "answer_key", "expected_answer", "calculation_trace", "independent_reference"}
                if (output_keys != {"case_id", "answer", "evidence"} or answer_keys != set(ns["SCALE_FIELDS"])
                        or evidence_keys != set(ns["SCALE_FIELDS"])
                        or feedback_keys != {"original_output", "validator_feedback"}
                        or output_keys & evaluator_keys or answer_keys & evaluator_keys or evidence_keys & evaluator_keys):
                    repair_control_matches = False
                    issues.append(f"Repair feedback included evaluator-only key for {case.get('case_id')}")
                request_key_hashes["repair_no_gold_control"].append(ns["scale_request_key"](repair_request))

            for start in range(0, len(block_cases), 16):
                group = block_cases[start:start + 16]
                controls = ns["scale_make_verifier_controls"](group)
                generic_control_count += len(controls)
                generic_control_cases.update(row.get("case_id") for row in controls if isinstance(row, dict))

        block_reports.append({"name": name, "n_cases": len(block_cases), "tier": spec.get("tier"),
            "seed": spec.get("seed"), "split": spec.get("split"), "start_index": spec.get("start_index"),
            "compressed_sha256": source_hash, "manifest_content_sha256": manifest.get("corpus_jsonl_sha256"),
            "audit_compressed_sha256": audit_hash, "family_counts": manifest.get("family_counts"),
            "word_range": [manifest.get("min_document_words"), manifest.get("max_document_words")]})

    collection_block = next((b for b in blocks if b.get("specification", {}).get("name") == "collection"), None)
    audit_block = next((b for b in blocks if b.get("specification", {}).get("name") == "audit"), None)
    if collection_block and audit_block:
        # Pilot and audit sets must be disjoint, and prior source inventory must match its frozen snapshot.
        all_manifests = [b["manifest"] for b in pilot_protocol.get("blocks", []) + blocks]
        try:
            cross = ns["scale_check_cohort_overlap"](all_manifests)
        except Exception as exc:
            cross = {"passed": False, "error": f"{type(exc).__name__}: {exc}"}
            issues.append("Pilot/main/audit source cohorts overlap or have incomplete indexes")
    else:
        cross = {"passed": False, "error": "Expected collection and audit blocks are missing"}

    # Recompute the recorded source inventory from exactly its named files.
    prior_paths = [notebook_root / Path(row["path"]) for row in saved_prior.get("source_files", [])]
    recomputed_prior = ns["scale_previous_corpus_keys"](prior_paths)
    recomputed_files = [{"path": Path(row["path"]).relative_to(notebook_root).as_posix(),
        "sha256": row["sha256"], "n_rows": row["n_rows"]} for row in recomputed_prior["source_files"]]
    saved_inventory_matches = (recomputed_files == saved_prior.get("source_files")
        and sorted(recomputed_prior["case_ids"]) == saved_prior.get("case_ids")
        and sorted(recomputed_prior["semantic_hashes"]) == saved_prior.get("semantic_hashes"))
    fail_if(saved_inventory_matches, "Prepared main prior inventory exactly matches its named sources and hashes", issues)
    fail_if(saved_prior == pilot_prior, "Prior inventory is unchanged between pilot and main preparation", issues)

    prior_ids = set(recomputed_prior["case_ids"])
    prior_semantics = set(recomputed_prior["semantic_hashes"])
    id_overlaps = sorted(case["case_id"] for case in all_cases if case["case_id"] in prior_ids)
    semantic_overlaps = sorted(case["semantic_hash"] for case in all_cases if case["semantic_hash"] in prior_semantics)
    fail_if(not id_overlaps, "All main source IDs are disjoint from the prior inventory", issues)
    fail_if(not semantic_overlaps, "All main semantic hashes are disjoint from the prior inventory", issues)
    fail_if(generated_count == EXPECTED_TOTAL and len(all_cases) == EXPECTED_TOTAL,
        "All 2,144 cases were streamed and audited", issues)
    fail_if(audit_rows_match, "Every frozen audit row equals an independently recomputed visible-text audit", issues)
    fail_if(regeneration_matches, "Every frozen source exactly regenerates from its declared parameters", issues)
    fail_if(request_contract_matches, "Every prospective original request contains source-only model inputs", issues)
    fail_if(repair_control_matches, "Every no-gold generic-feedback control passes the repair request builder", issues)
    fail_if(len(request_key_hashes["original"]) == EXPECTED_TOTAL and len(set(request_key_hashes["original"])) == EXPECTED_TOTAL,
        "Every prospective original request has a unique full-request hash", issues)
    fail_if(len(request_key_hashes["repair_no_gold_control"]) == EXPECTED_TOTAL and len(set(request_key_hashes["repair_no_gold_control"])) == EXPECTED_TOTAL,
        "Every synthetic no-gold repair control has a unique full-request hash", issues)
    fail_if(generic_control_count == 6 * EXPECTED_TOTAL and len(generic_control_cases) == EXPECTED_TOTAL,
        "Six offline verifier controls were built for each source", issues)

    checks = {
        "source_and_core_freeze_matches": runtime_hashes_match and protocol.get("frozen_rule_source_sha256") == ns["SCALE_CORE_SHA256"],
        "pilot_selected_tier_matches_main": source_plan.get("selected_tier") == pilot_ladder.get("selected_tier") == protocol.get("selected_tier"),
        "accrual_size_and_seed_protocol_matches": config_matches,
        "pilot_main_audit_cohorts_disjoint": bool(cross.get("passed")),
        "saved_prior_inventory_recomputes_exactly": saved_inventory_matches,
        "pilot_inventory_matches_main_inventory": saved_prior == pilot_prior,
        "all_main_ids_and_semantics_novel": not id_overlaps and not semantic_overlaps,
        "all_2144_sources_pass_complete_material_gate": generated_count == EXPECTED_TOTAL and audit_rows_match and regeneration_matches,
        "prospective_original_requests_source_only": request_contract_matches,
        "synthetic_repair_controls_pass_no_gold_contract": repair_control_matches,
        "all_prospective_request_keys_unique": len(request_key_hashes["original"]) == EXPECTED_TOTAL and len(set(request_key_hashes["original"])) == EXPECTED_TOTAL,
        "all_generic_controls_built": generic_control_count == 6 * EXPECTED_TOTAL and len(generic_control_cases) == EXPECTED_TOTAL,
    }
    overall = all(checks.values()) and not issues
    report = {
        "passed": overall,
        "phase": "prepared_main_materials_review",
        "reviewed_files": ["scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py", "collect_scale.py"],
        "model_calls": 0,
        "frozen_files_modified": False,
        "counts": {"main_sources": len(all_cases), "collection_blocks": sum(b.get("name") == "collection" for b in block_reports),
            "collection_source_count": next((b["n_cases"] for b in block_reports if b["name"] == "collection"), 0),
            "audit_source_count": next((b["n_cases"] for b in block_reports if b["name"] == "audit"), 0),
            "prospective_original_requests": len(request_key_hashes["original"]),
            "synthetic_no_gold_repair_requests": len(request_key_hashes["repair_no_gold_control"]),
            "offline_verifier_controls": generic_control_count,
            "cases_with_controls": len(generic_control_cases),
            "prior_rows": saved_prior.get("n_rows"), "prior_unique_ids": saved_prior.get("n_unique_ids"),
            "prior_unique_semantics": saved_prior.get("n_unique_semantics")},
        "checks": checks,
        "issues": issues,
        "block_summaries": block_reports,
        "overlap_counts": {"prior_case_id": len(id_overlaps), "prior_semantic_hash": len(semantic_overlaps),
            "pilot_main_audit": cross.get("n_cases") if cross.get("passed") else None},
        "request_key_set_sha256": {arm: canonical_hash(sorted(keys)) for arm, keys in request_key_hashes.items()},
        "protocol": {"name": protocol.get("protocol"), "selected_tier": selected_tier,
            "model": protocol.get("model"), "reasoning_effort": protocol.get("reasoning_effort"),
            "sha256": canonical_hash(protocol)},
        "source_code_sha256": freeze.get("source_sha256", {}),
        "source_pack_sha256": source_hashes,
        "prior_inventory_sha256": {row["path"]: row["sha256"] for row in saved_prior.get("source_files", [])},
        "synthetic_control_note": "Sentinel wrong answers are test-only in-memory controls for the request builder, not model outputs, candidates, scores or repair data. No evaluator values or traces are passed to a request.",
    }

    JSON_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    lines = [
        "# Scale-v5 main source material review",
        "",
        "**Gate: " + ("passed" if overall else "blocked") + ".** This is a read-only pre-call audit of the frozen source packs. It does not read candidate responses or intervention outcomes, makes no model calls, and writes only its two reports under `authoring/`.",
        "",
        f"The prepared main cohort contains {report['counts']['collection_source_count']} collection sources and {report['counts']['audit_source_count']} separate audit sources. The collection cap, audit count, seeds and tier match the adopted protocol. Each source was streamed through a complete integrity check, re-generated from the exact seed/tier/split/index specification, and re-audited from its rendered text with the separate SQL/Decimal and text/Fraction implementations. Each saved compact audit row was compared with a fresh recomputation.",
        "",
        f"The pilot, main collection and audit blocks have no duplicate case IDs or normalized semantic hashes. The main prior-corpus inventory recomputes exactly from its listed files and equals the pilot inventory. The main sources have zero ID or semantic-hash overlap with that inventory.",
        "",
        f"I constructed {report['counts']['prospective_original_requests']} source-only prospective requests and {report['counts']['synthetic_no_gold_repair_requests']} synthetic no-gold repair-request controls in memory. Each source input contains only `case_id`, `task_instructions` and `documents`. Six offline verifier controls were built for each source; they remained in evaluator memory and were not included in requests. The synthetic sentinel outputs only test the generic-feedback builder and are not study responses.",
        "",
        "| Pack | Sources | Tier | Seed | Index range | Source SHA256 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for block in block_reports:
        first = block["start_index"]
        last = first + block["n_cases"] - 1
        lines.append(f"| {block['name']} | {block['n_cases']} | {block['tier']} | {block['seed']} | {first}–{last} | `{block['compressed_sha256']}` |")
    if issues:
        lines += ["", "## Issues", ""]
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines += ["", "All pre-call material checks passed. The main source gate is clear. The detailed hashes and individual checks are in [scale_main_material_review.json](scale_main_material_review.json)."]
    MD_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook-root", type=Path, default=DEFAULT_NOTEBOOK_ROOT)
    args = parser.parse_args()
    report = run_audit(args.notebook_root)
    print(json.dumps({"passed": report["passed"], "phase": report.get("phase"),
        "issues": report.get("issues", []), "counts": report.get("counts", {}),
        "json_report": str(JSON_REPORT), "markdown_report": str(MD_REPORT)}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
