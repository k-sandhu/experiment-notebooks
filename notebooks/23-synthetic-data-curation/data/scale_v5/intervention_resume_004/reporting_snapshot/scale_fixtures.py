"""V5 authoring wrapper around byte-frozen v4 procurement rules; no live path.

Authoring uses isolated exec namespaces. For a self-contained notebook, pass the
three embedded source strings to scale_load_cores(core_sources=...) explicitly.
"""
import copy as _scale_copy
import gzip as _scale_gzip
import hashlib as _scale_hashlib
import io as _scale_io
import json as _scale_json
import random as _scale_random
import os as _scale_os
from contextlib import contextmanager as _scale_contextmanager
from collections import Counter as _ScaleCounter
from pathlib import Path as _ScalePath

SCALE_VERSION = "23-procurement-scale-v5"
SCALE_TIERS = (128, 192)
SCALE_CREATED_AT = "2026-10-26"
SCALE_TASK_INSTRUCTIONS = "Reconcile the target ORDER and LINE as of the packet cutoff. Return exactly\n{case_id, answer, evidence}; answer has exactly order_id (string), sku (string),\nquantity_units (integer or null), unit_price_cents (integer or null), currency\n(three-letter string or null), ship_date (YYYY-MM-DD or null), status\n(active/cancelled/ambiguous). evidence has the same seven keys; each value is a\nnonempty list of distinct document IDs P01 through P06. A batch wrapper may ask\nfor a results array.\n\nRead all tables and use only the requested order/line. The same SKU can occur\non another line or order. quantity_units is OPEN individual units: current\napproved ordered demand minus NET allocated dispatched units, where accepted\nreturns reduce net dispatch. This packet's order remains active; shipment VOID,\nREVERSAL and RETURN do not cancel the purchase order.\n\nCommercial terms: resolve every field independently. An approved row qualifies\nonly if BOTH recorded and effective UTC timestamps are at or before cutoff\n(inclusive). Within a field: a line override beats an order default, then higher\nauthority wins (3 Controller, 2 Buyer, 1 Planner), then later effective timestamp,\nthen higher revision. Recorded timestamp filters availability only. INHERIT or\nunstated fields do not clear old values. The signed order has authority 0 and\nits issue timestamp. Other-line, unapproved, recorded-late and future-effective\nrows do not apply. This packet has no unresolved equal-priority conflicts.\n\nPhysical movements: group by logical Event ID across ingestion copies. Select\nthe HIGHEST ROW REVISION among copies recorded by cutoff; exact same-revision\ncopies count once. That selected row wholly replaces prior rows. Only then test\nits state, order and occurred timestamp. Selected VOID, another order and\noccurred-after-cutoff rows contribute zero; never fall back to an older revision.\nA POSTED, timely REVERSAL removes the referenced logical shipment, including its\nselected correction, ONCE. Multiple active reversals of the same shipment do not\nremove it twice. A VOID reversal has no effect. It is a control record, not a\nsecond negative quantity. Returns against removed/VOID shipments contribute zero.\n\nFor an active SHIP, select the exact SKU/UOM factor with latest effective_from\ndate on or before the SELECTED shipment's occurred calendar date. Select the\nallocation key's latest effective_from date on or before that SAME date. Multiply\nshipment quantity by individual-units-per-UOM and the target line's percent/100.\nAn allocation entirely to another line contributes zero. All contributions are\nwhole individual units; do not round allocations. Allocation shares total 100%.\nA RETURN is a positive accepted quantity in its ORIGINAL shipment handling units.\nUse the referenced SELECTED shipment's SKU, UOM, occurred date and allocation key,\nincluding that date's UOM and allocation versions, irrespective of return date.\nSubtract its converted allocated units from net dispatch. Do not use the original\nsuperseded row or the return date's new packaging/allocation schedule.\n\nPricing: use the resolved price plan and the highest tier minimum not exceeding\nCURRENT ORDERED demand, BEFORE movements. gross_cents is for an entire price pack\nof pack_units individual units, independent of warehouse UOM. Divide by pack_units;\napply tier rebate A then rebate B sequentially to that gross unit amount, using\nbasis points (100 bps = 1%). Then ADD fee_cents per individual unit and\npack_fee_cents/pack_units and SUBTRACT credit_cents per individual unit. These fees\nand credits are after rebates. Keep exact rational/decimal precision and round\nONCE at the final per-unit result to the nearest integer cent, exact halves UP.\nNever round a pack conversion, rebate or fractional-cent adjustment earlier.\nCurrency and requested ship date come from independently resolved commercial terms.\n\nEvidence: sources are P01 signed order/defaults/status, P02 approvals, P03 UOM,\nP04 dated allocations, P05 price schedules, P06 movement history. Cite sources\nneeded for current fields and arithmetic. Quantity requires current ordered\nterms plus P03/P04/P06; P01 is also needed if its ordered demand remains current.\nPrice requires the resolved plan, ordered demand for its tier and P05. SKU and\nactive order status are in P01. Order ID is stated in the packet header and P01.\nRelevant additional P01-P06 context is allowed without penalty; cite whole source\ngroups, not individual row IDs. Citation ordering is irrelevant. Do not omit\nneeded calculation sources merely because the numeric answer is correct.\n"
SCALE_FIELDS = ['order_id', 'sku', 'quantity_units', 'unit_price_cents', 'currency', 'ship_date', 'status']
SCALE_FAMILIES = ['shipment_revisions', 'dated_uom_returns', 'split_allocations', 'tier_sequential_pricing', 'effective_authority', 'compound']
SCALE_CUTOFF = '2026-10-26T12:00:00Z'
SCALE_CORE_SHA256 = {'high_fixtures.py': 'ff9479d80c93327d3cf0f4f854b1da89e5bd8d8b0db48707509f9cfe77e15547', 'high_material_audit.py': 'cb8d8d6242936886b4f8ff865d7375d02a79d9562d29fc601650da9c6d584bb0', 'audit_high_rendered_sources.py': 'b033e8ca7a90a385390155e4ee5e26fb2c8eed36f41129c30d9727e446560bf3'}
_SCALE_NAMESPACES = None

SCALE_CORE_LF_SHA256 = {'high_fixtures.py': 'ff9479d80c93327d3cf0f4f854b1da89e5bd8d8b0db48707509f9cfe77e15547', 'high_material_audit.py': 'cb8d8d6242936886b4f8ff865d7375d02a79d9562d29fc601650da9c6d584bb0', 'audit_high_rendered_sources.py': 'b033e8ca7a90a385390155e4ee5e26fb2c8eed36f41129c30d9727e446560bf3'}

def _scale_canonical(value):
    return _scale_json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _scale_hash(value):
    return _scale_hashlib.sha256(_scale_canonical(value).encode("utf-8")).hexdigest()


def _scale_file_hash(path):
    digest = _scale_hashlib.sha256()
    with _ScalePath(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scale_load_cores(core_dir=None, core_sources=None):
    """Load exact frozen authoring cores, or explicit source strings when embedded.

    Filesystem loading validates original bytes. Embedded strings validate the
    LF-normalized digest, allowing a notebook to preserve source portably.
    """
    global _SCALE_NAMESPACES
    if core_sources is None:
        directory = _ScalePath(core_dir) if core_dir is not None else _ScalePath(__file__).resolve().parent
        raw_sources = {name: (directory / name).read_bytes() for name in SCALE_CORE_SHA256}
        for name, raw in raw_sources.items():
            if _scale_hashlib.sha256(raw).hexdigest() != SCALE_CORE_SHA256[name]:
                raise ValueError("Frozen core byte hash changed: " + name)
        sources = {name: raw.decode("utf-8-sig") for name, raw in raw_sources.items()}
    else:
        if set(core_sources) != set(SCALE_CORE_SHA256):
            raise ValueError("All three explicit frozen source strings are required")
        sources = dict(core_sources)
        for name, text in sources.items():
            normalized = text.lstrip("\ufeff").replace("\r\n", "\n")
            if _scale_hashlib.sha256(normalized.encode("utf-8")).hexdigest() != SCALE_CORE_LF_SHA256[name]:
                raise ValueError("Frozen embedded source changed: " + name)
    namespaces = {}
    for name, source in sources.items():
        namespace = {"__name__": "scale_frozen_" + name.replace(".", "_")}
        exec(compile(source, name, "exec"), namespace)
        namespaces[name] = namespace
    fixture = namespaces["high_fixtures.py"]
    if fixture["HIGH_TASK_INSTRUCTIONS"] != SCALE_TASK_INSTRUCTIONS:
        raise ValueError("Scale instructions differ from frozen business rules")
    _SCALE_NAMESPACES = namespaces
    return {"byte_sha256": dict(SCALE_CORE_SHA256), "normalized_sha256": dict(SCALE_CORE_LF_SHA256),
            "isolated_namespaces": True, "business_rules_unchanged": True}


def _scale_cores():
    if _SCALE_NAMESPACES is None:
        scale_load_cores()
    return (_SCALE_NAMESPACES["high_fixtures.py"], _SCALE_NAMESPACES["high_material_audit.py"],
            _SCALE_NAMESPACES["audit_high_rendered_sources.py"])


def _scale_validate_generation(n, seed, tier, split, start_index):
    if type(n) is not int or n < 0 or type(seed) is not int:
        raise ValueError("n must be nonnegative integer; seed must be integer")
    if type(tier) is not int or tier not in SCALE_TIERS:
        raise ValueError("tier must be 128 or 192 base shipments")
    if split not in {"pilot", "collection", "audit"}:
        raise ValueError("Unknown split")
    if type(start_index) is not int or start_index < 0:
        raise ValueError("start_index must be nonnegative integer")


def scale_iter_cases(n, seed, tier=128, split="pilot", start_index=0):
    """Yield index-stable fresh cases; changing batch boundaries changes no case."""
    _scale_validate_generation(n, seed, tier, split, start_index)
    if not n:
        return
    fixture, _, _ = _scale_cores()
    level = {128: 3, 192: 4}[tier]
    for index in range(start_index, start_index + n):
        # Permute each complete six-case block, so contiguous cohorts are balanced.
        block_seed = int(_scale_hash([SCALE_VERSION, "family-block", seed, tier, split, index // len(SCALE_FAMILIES)]), 16)
        families = list(SCALE_FAMILIES)
        _scale_random.Random(block_seed).shuffle(families)
        family = families[index % len(families)]
        case_seed = int(_scale_hash([SCALE_VERSION, "case", seed, tier, split, index]), 16)
        case = fixture["_high_build"](_scale_random.Random(case_seed), family, case_seed, level, split, index)
        case.update(scale_version=SCALE_VERSION, base_shipments=tier, generation_index=index,
                    generation_seed=seed, created_at=SCALE_CREATED_AT)
        yield case


def scale_make_cases(n, seed, tier=128, split="pilot", start_index=0):
    return list(scale_iter_cases(n, seed, tier, split, start_index))


def scale_model_input(case):
    """Only these three keys may enter a solver request; no evaluator metadata."""
    return {"case_id": case["case_id"], "task_instructions": SCALE_TASK_INSTRUCTIONS, "documents": case["document"]}


def scale_validate_answer(case, response):
    return _scale_cores()[0]["high_validate_answer"](case, response)


def scale_correct_response(case):
    return _scale_cores()[0]["high_correct_response"](case)


def scale_calculation_trace(case):
    return _scale_cores()[0]["high_calculation_trace"](case)


def scale_independent_reference(case):
    return _scale_cores()[0]["high_independent_reference"](case)


def scale_make_verifier_controls(cases):
    return _scale_cores()[0]["high_make_verifier_controls"](cases)


def scale_audit_case(case, include_traces=False):
    """Fully inspect visible text before comparing independently derived answers."""
    fixture, sql, fraction = _scale_cores()
    if case.get("scale_version") != SCALE_VERSION or case.get("base_shipments") not in SCALE_TIERS:
        raise ValueError("Not a scale case")
    if case["level"] != {128: 3, 192: 4}[case["base_shipments"]] or case["created_at"] != SCALE_CREATED_AT:
        raise ValueError("Scale level/date metadata mismatch")
    fixture["high_audit_fixtures"]([case])
    sql_answer, sql_trace = sql["high_material_answer"](case["document"])
    fraction_audit = fraction["audit_cases"]([case])
    row = fraction_audit["cases"][0]
    if sql_answer != case["gold"] or not fraction_audit["all_rendered_text_answers_and_evidence_needs_match_keys"]:
        raise ValueError("Independent visible-text answer/evidence mismatch: " + case["case_id"])
    trace = fixture["high_calculation_trace"](case)
    result = {"case_id": case["case_id"], "family": case["family"], "tier": case["base_shipments"], "split": case["split"],
              "created_at": case["created_at"], "content_hash": case["content_hash"], "semantic_hash": case["semantic_hash"],
              "document_words": len(case["document"].split()), "document_utf8_bytes": len(case["document"].encode("utf-8")),
              "passed": True, "answer": sql_answer, "ordered_units": sql_trace["ordered_units"],
              "net_dispatch_units": sql_trace["net_dispatched_units"], "open_units": sql_trace["open_units"],
              "unrounded_price_cents": sql_trace["unrounded_price_cents"], "source_integrity": row["integrity"],
              "source_record_reconstructed": True, "fraction_and_decimal_agree": True,
              "evidence_needs_match": True, "full_trace_hash": _scale_hash(trace),
              "independent_fraction_trace_hash": _scale_hash(row["audit"])}
    if include_traces:
        result.update(fixture_trace=trace, independent_sql_decimal_trace=sql_trace,
                      independent_text_fraction_trace=row["audit"])
    return result


def scale_audit_fixtures(cases):
    """Streaming all-case audit with exact ID/semantic uniqueness, bounded memory."""
    ids, semantics, families, tiers, n = set(), set(), _ScaleCounter(), _ScaleCounter(), 0
    for case in cases:
        if case["case_id"] in ids or case["semantic_hash"] in semantics:
            raise ValueError("Duplicate identity or semantic facts")
        scale_audit_case(case)
        ids.add(case["case_id"]); semantics.add(case["semantic_hash"])
        families[case["family"]] += 1; tiers[case["base_shipments"]] += 1; n += 1
    return {"version": SCALE_VERSION, "n_cases": n, "passed": True,
            "n_unique_ids": len(ids), "n_unique_semantics": len(semantics),
            "family_counts": dict(families), "tier_counts": dict(tiers), "core_sha256": dict(SCALE_CORE_SHA256)}


@_scale_contextmanager
def _scale_open_gzip_writer(path):
    # Blank filename and mtime=0 make identical JSONL bytes produce identical gzip.
    with path.open("wb") as raw:
        with _scale_gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as compressed:
            yield compressed


def scale_iter_corpus(path, manifest=None):
    """Read one complete case per LF JSON line; no uncompressed source copy."""
    path = _ScalePath(path)
    if manifest is not None:
        info = _scale_json.loads(_ScalePath(manifest).read_text(encoding="utf-8")) if not isinstance(manifest, dict) else manifest
        if _scale_file_hash(path) != info["corpus_gzip_sha256"]:
            raise ValueError("Compressed corpus hash mismatch")
    count = 0
    with _scale_gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for line in stream:
            if not line.endswith("\n") or line.endswith("\r\n"):
                raise ValueError("Corpus requires explicit LF line serialization")
            case = _scale_json.loads(line)
            if not isinstance(case, dict):
                raise ValueError("Each corpus line must be one case object")
            count += 1
            yield case
    if manifest is not None and count != info["n_cases"]:
        raise ValueError("Corpus count differs from manifest")


def scale_write_corpus(path, cases, audit_path=None, manifest_path=None):
    """Freeze a fully audited compressed cohort. Explicit destination; never live.

    Existing artifacts are never overwritten. A failed stream is removed rather
    than leaving a plausible completed corpus. Caller chooses authoring staging.
    """
    path = _ScalePath(path)
    audit_path = _ScalePath(audit_path) if audit_path else path.with_name(path.name + ".audit.jsonl.gz")
    manifest_path = _ScalePath(manifest_path) if manifest_path else path.with_name(path.name + ".manifest.json")
    outputs = [path, audit_path, manifest_path]
    if len({str(p.resolve()) for p in outputs}) != 3 or any(p.exists() for p in outputs):
        raise ValueError("New distinct corpus/audit/manifest paths required")
    if not all(p.parent.is_dir() for p in outputs):
        raise ValueError("Output parent directories must already exist")
    ids, semantics, families, tiers = set(), set(), _ScaleCounter(), _ScaleCounter()
    content_digest = _scale_hashlib.sha256()
    audit_digest = _scale_hashlib.sha256()
    minimum, maximum, n, case_index = None, 0, 0, []
    try:
        with _scale_open_gzip_writer(path) as corpus, _scale_open_gzip_writer(audit_path) as audits:
            for case in cases:
                if case["case_id"] in ids or case["semantic_hash"] in semantics:
                    raise ValueError("Duplicate identity or semantic facts within cohort")
                checked = scale_audit_case(case)
                raw = (_scale_canonical(case) + "\n").encode("utf-8")
                audit_raw = (_scale_canonical(checked) + "\n").encode("utf-8")
                corpus.write(raw); audits.write(audit_raw)
                content_digest.update(raw); audit_digest.update(audit_raw)
                ids.add(case["case_id"]); semantics.add(case["semantic_hash"])
                families[case["family"]] += 1; tiers[case["base_shipments"]] += 1; n += 1
                case_index.append({key: case[key] for key in
                                   ("case_id", "content_hash", "semantic_hash", "generation_index", "split", "base_shipments")})
                words = checked["document_words"]
                minimum = words if minimum is None else min(minimum, words); maximum = max(maximum, words)
        manifest = {"version": SCALE_VERSION, "complete": True, "n_cases": n,
                    "corpus_file": path.name,
                    "audit_file": _scale_os.path.relpath(audit_path.resolve(), path.parent.resolve()).replace("\\", "/"),
                    "corpus_gzip_sha256": _scale_file_hash(path),
                    "audit_gzip_sha256": _scale_file_hash(audit_path),
                    "corpus_jsonl_sha256": content_digest.hexdigest(), "audit_jsonl_sha256": audit_digest.hexdigest(),
                    "case_ids_hash": _scale_hash(sorted(ids)), "semantic_hashes_hash": _scale_hash(sorted(semantics)),
                    "n_unique_ids": len(ids), "n_unique_semantics": len(semantics),
                    "family_counts": dict(families), "tier_counts": dict(tiers),
                    "min_document_words": minimum or 0, "max_document_words": maximum,
                    "instructions_sha256": _scale_hashlib.sha256(SCALE_TASK_INSTRUCTIONS.encode()).hexdigest(),
                    "core_sha256": dict(SCALE_CORE_SHA256), "core_lf_sha256": dict(SCALE_CORE_LF_SHA256),
                    "full_visible_text_audit": True, "created_at": SCALE_CREATED_AT,
                    "case_index": case_index, "all_passed": True,
                    "audit_path": _scale_os.path.relpath(audit_path.resolve(), path.parent.resolve()).replace("\\", "/")}
        manifest.update(compressed_sha256=manifest["corpus_gzip_sha256"],
                        uncompressed_sha256=manifest["corpus_jsonl_sha256"],
                        audit_compressed_sha256=manifest["audit_gzip_sha256"],
                        audit_uncompressed_sha256=manifest["audit_jsonl_sha256"])
        manifest_path.write_text(_scale_json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return manifest
    except BaseException:
        for output in outputs:
            if output.exists():
                output.unlink()
        raise


def scale_verify_corpus(path, manifest_path=None, full_audit=True):
    path = _ScalePath(path)
    manifest_path = _ScalePath(manifest_path) if manifest_path else path.with_name(path.name + ".manifest.json")
    manifest = _scale_json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != SCALE_VERSION or not manifest.get("complete") or manifest["core_sha256"] != SCALE_CORE_SHA256:
        raise ValueError("Unknown/incomplete corpus or changed frozen cores")
    digest = _scale_hashlib.sha256(); ids = set(); semantics = set(); n = 0; case_index = []
    for case in scale_iter_corpus(path, manifest):
        if case["case_id"] in ids or case["semantic_hash"] in semantics:
            raise ValueError("Duplicate identity or semantic facts")
        if full_audit:
            scale_audit_case(case)
        digest.update((_scale_canonical(case) + "\n").encode("utf-8"))
        case_index.append({key: case[key] for key in
                           ("case_id", "content_hash", "semantic_hash", "generation_index", "split", "base_shipments")})
        ids.add(case["case_id"]); semantics.add(case["semantic_hash"]); n += 1
    if (digest.hexdigest() != manifest["corpus_jsonl_sha256"] or _scale_hash(sorted(ids)) != manifest["case_ids_hash"]
            or _scale_hash(sorted(semantics)) != manifest["semantic_hashes_hash"] or case_index != manifest["case_index"]):
        raise ValueError("Corpus content/identity manifest mismatch")
    audit_path = path.parent / manifest["audit_file"]
    if _scale_file_hash(audit_path) != manifest["audit_gzip_sha256"]:
        raise ValueError("Compressed source-audit hash mismatch")
    return {"passed": True, "n_cases": n, "full_audit": bool(full_audit), "manifest": manifest}


def scale_check_cohort_overlap(manifests):
    """Check frozen metadata indexes across pilot/tier/main/audit cohorts."""
    ids, semantics, n = set(), set(), 0
    for item in manifests:
        manifest = _scale_json.loads(_ScalePath(item).read_text(encoding="utf-8")) if not isinstance(item, dict) else item
        if not manifest.get("complete") or not manifest.get("all_passed"):
            raise ValueError("Incomplete source cohort")
        if len(manifest["case_index"]) != manifest["n_cases"]:
            raise ValueError("Incomplete metadata index")
        for row in manifest["case_index"]:
            if row["case_id"] in ids or row["semantic_hash"] in semantics:
                raise ValueError("Cross-cohort identity or semantic overlap")
            ids.add(row["case_id"]); semantics.add(row["semantic_hash"]); n += 1
    return {"passed": True, "n_cases": n, "n_unique_ids": len(ids), "n_unique_semantics": len(semantics),
            "scope": "Exact normalized source facts, not task-family or arbitrary outcome equivalence"}


def scale_previous_corpus_keys(paths):
    """Inventory explicit prior source JSONL/gzip paths without copying documents.

    Repeated old records across earlier snapshots are allowed and deduplicated.
    Each nonempty input line must be an actual source case with both hashes.
    This checks exact identity/normalized-fact overlap, not prose/task novelty.
    """
    ids, semantics, files, count = set(), set(), [], 0
    for supplied in paths:
        path = _ScalePath(supplied)
        opener = _scale_gzip.open if path.suffix == ".gz" else open
        file_count = 0
        with opener(path, "rt", encoding="utf-8-sig") as stream:
            for line in stream:
                if not line.strip():
                    continue
                case = _scale_json.loads(line)
                if not isinstance(case, dict) or not all(type(case.get(k)) is str for k in ("case_id", "semantic_hash")):
                    raise ValueError("Expected prior source-case JSONL: " + str(path))
                ids.add(case["case_id"]); semantics.add(case["semantic_hash"]); count += 1; file_count += 1
        files.append({"path": str(path), "sha256": _scale_file_hash(path), "n_rows": file_count})
    return {"case_ids": ids, "semantic_hashes": semantics, "source_files": files,
            "n_rows": count, "n_unique_ids": len(ids), "n_unique_semantics": len(semantics)}


def scale_check_previous_overlap(case_index, prior):
    """Check a cheap manifest index against inventory keys before any calls."""
    rows = case_index["case_index"] if isinstance(case_index, dict) else case_index
    checked, ids, semantics = 0, set(), set()
    for row in rows:
        if row["case_id"] in prior["case_ids"] or row["semantic_hash"] in prior["semantic_hashes"]:
            raise ValueError("Scale source overlaps a prior corpus: " + row["case_id"])
        if row["case_id"] in ids or row["semantic_hash"] in semantics:
            raise ValueError("Repeated scale identity/semantic facts")
        ids.add(row["case_id"]); semantics.add(row["semantic_hash"]); checked += 1
    return {"passed": True, "n_scale_cases_checked": checked,
            "n_prior_unique_ids": prior["n_unique_ids"], "n_prior_unique_semantics": prior["n_unique_semantics"],
            "scope": "All explicitly supplied previous corpora; normalized source facts, not broad novelty"}


def scale_preflight_cohorts(output_dir, blocks):
    """Explicit authoring preflight, without fixed cohort sizes or any live calls.

    Each block supplies name,n,seed,tier,split,start_index. Compressed sources are
    written once, alongside compressed compact audits and a small index manifest.
    Fully independent event traces can be derived later from any streamed case.
    """
    output_dir = _ScalePath(output_dir)
    blocks = list(blocks)
    names = [block["name"] for block in blocks]
    if len(names) != len(set(names)) or any(_ScalePath(name).name != name or name in {"", ".", ".."} for name in names):
        raise ValueError("Distinct simple cohort names required")
    manifests = []
    for block in blocks:
        cases = scale_iter_cases(block["n"], block["seed"], tier=block["tier"], split=block["split"],
                                 start_index=block.get("start_index", 0))
        manifests.append(scale_write_corpus(output_dir / (block["name"] + ".jsonl.gz"), cases))
    return {"version": SCALE_VERSION, "blocks": blocks, "manifests": manifests,
            "cross_cohort_audit": scale_check_cohort_overlap(manifests), "live_calls": 0}
