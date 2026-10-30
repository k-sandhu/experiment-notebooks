"""Independently pre-audit every possible v4 main packet before any calls.

Answers and citations are derived from rendered P01-P06 text by the separate
Fraction-based audit helper. Fixture metadata is used only to recreate the
frozen cohort, group cases, and compare the finished derivation with keys.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_high_rendered_sources import audit_cases
from high_fixtures import HIGH_TASK_INSTRUCTIONS, high_make_cases


BLOCKS = (
    ("initial", 160, 244160, 0, "collection"),
    ("extension", 80, 244080, 160, "collection"),
    ("audit", 24, 244024, 240, "audit"),
)
LEVELS = (1, 2, 3, 4)

level_reports = []
all_ids = set()
all_semantic_hashes = set()
grand_total = 0
grand_mismatches = 0

for level in LEVELS:
    grouped_cases = []
    case_blocks = []
    for block_name, count, seed, start_index, split in BLOCKS:
        made = high_make_cases(count, seed, level=level, split=split, start_index=start_index)
        grouped_cases.extend(made)
        case_blocks.extend([block_name] * len(made))

    ids = [case["case_id"] for case in grouped_cases]
    semantics = [case["semantic_hash"] for case in grouped_cases]
    if len(set(ids)) != len(ids):
        raise AssertionError(f"Duplicate case IDs in level {level}")
    if len(set(semantics)) != len(semantics):
        raise AssertionError(f"Duplicate semantic hashes in level {level}")
    collisions = all_ids.intersection(ids)
    if collisions:
        raise AssertionError(f"Case IDs repeat across levels: {sorted(collisions)[:3]}")
    semantic_collisions = all_semantic_hashes.intersection(semantics)
    if semantic_collisions:
        raise AssertionError(f"Semantic hashes repeat across levels: {sorted(semantic_collisions)[:3]}")
    all_ids.update(ids)
    all_semantic_hashes.update(semantics)

    checked = audit_cases(grouped_cases)
    grand_total += checked["n_cases"]
    grand_mismatches += checked["n_answer_or_evidence_key_mismatches"]
    compact_cases = []
    for case, block_name, row in zip(grouped_cases, case_blocks, checked["cases"]):
        trace = row["audit"]
        compact_cases.append({
            "case_id": row["case_id"],
            "block": block_name,
            "split": case["split"],
            "family": case["family"],
            "level": level,
            "content_hash": case["content_hash"],
            "semantic_hash": case["semantic_hash"],
            "document_sha256": row["document_sha256"],
            "document_words": row["document_words"],
            "answer_from_rendered_text": trace["answer_from_rendered_text"],
            "answer_matches_stored_key": row["gold_match"],
            "evidence_needs_from_rendered_text": trace["evidence_needs_from_rendered_text"],
            "evidence_matches_stored_key": row["evidence_gold_match"],
            "resolved_terms": trace["resolved_terms"],
            "term_source_groups": trace["term_sources"],
            "selected_logical_event_count": trace["ledger"]["selected_event_count"],
            "net_target_dispatch_units": sum(e["net_units"] for e in trace["ledger"]["events"]),
            "active_reversal_count": len(trace["ledger"]["active_reversals"]),
            "exact_price_trace": trace["price"],
            "integrity": row["integrity"],
        })

    level_reports.append({
        "level": level,
        "n_cases": checked["n_cases"],
        "n_unique_cases": checked["n_unique_cases"],
        "n_answer_or_evidence_mismatches": checked["n_answer_or_evidence_key_mismatches"],
        "all_text_answers_and_evidence_needs_match_keys": checked[
            "all_rendered_text_answers_and_evidence_needs_match_keys"],
        "word_count_min": min(row["document_words"] for row in checked["cases"]),
        "word_count_max": max(row["document_words"] for row in checked["cases"]),
        "counts_by_block": {name: sum(block == name for block in case_blocks) for name, *_ in BLOCKS},
        "counts_by_family": {
            family: sum(case["family"] == family for case in grouped_cases)
            for family in sorted({case["family"] for case in grouped_cases})
        },
        "cases": compact_cases,
    })

report = {
    "protocol": "v4_all_possible_main_cohorts_rendered_text_audit",
    "audit_method": "Separate parser and Fraction arithmetic from model-visible P01-P06 text; compare stored answer/evidence keys only after derivation.",
    "instruction_sha256": hashlib.sha256(HIGH_TASK_INSTRUCTIONS.encode("utf-8")).hexdigest(),
    "level_generation": "All four levels are audited because pilot service failures have not selected a main level.",
    "blocks": [
        {"name": name, "n": n, "seed": seed, "start_index": start, "split": split}
        for name, n, seed, start, split in BLOCKS
    ],
    "n_levels": len(LEVELS),
    "n_cases_total": grand_total,
    "n_unique_case_ids_total": len(all_ids),
    "n_unique_semantic_hashes_total": len(all_semantic_hashes),
    "n_answer_or_evidence_mismatches_total": grand_mismatches,
    "all_level_cohorts_pass": all(level["all_text_answers_and_evidence_needs_match_keys"] for level in level_reports),
    "levels": level_reports,
}
target = Path(__file__).with_name("high_all_main_source_audit.json")
target.write_text(json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({
    "protocol": report["protocol"],
    "instruction_sha256": report["instruction_sha256"],
    "n_cases_total": grand_total,
    "n_unique_case_ids_total": len(all_ids),
    "n_unique_semantic_hashes_total": len(all_semantic_hashes),
    "n_answer_or_evidence_mismatches_total": grand_mismatches,
    "all_level_cohorts_pass": report["all_level_cohorts_pass"],
    "levels": [{k: level[k] for k in (
        "level", "n_cases", "n_answer_or_evidence_mismatches", "word_count_min", "word_count_max",
        "counts_by_block", "counts_by_family") } for level in level_reports],
}, indent=2))
if not report["all_level_cohorts_pass"]:
    raise SystemExit("Rendered-text source audit found answer or evidence key mismatches")
