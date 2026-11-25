"""Completion-gated Notebook23 preservation and guarded folder-only delivery.

Importing is read-only. Nothing opens response caches until the v5 final manifest
certifies completed interventions. Delivery is opt-in and never copies repo roots.
"""
import argparse
import gzip
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


SCALE_QA_VERSION = "23-scale-postcollection-qa-v1"
SCALE_QA_NOTEBOOK = "23_synthetic_data_curation.ipynb"
SCALE_QA_ALLOWED = {"README.md", SCALE_QA_NOTEBOOK, ".gitattributes"}
SCALE_QA_FOLDER = "23-synthetic-data-curation"


def scale_qa_read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def scale_qa_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scale_qa_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def scale_qa_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)
    temporary.replace(path)


def scale_qa_ignored(relative):
    parts = [part.lower() for part in Path(relative).parts]
    return (any(part in {"__pycache__", ".ipynb_checkpoints"} for part in parts)
        or parts[:2] == ["data", "tmp"] or (parts and parts[-1].endswith(".pyc")))


def scale_qa_child(folder, relative):
    folder = Path(folder).resolve()
    supplied = Path(relative)
    if supplied.is_absolute() or ".." in supplied.parts or supplied.drive:
        raise ValueError("Unsafe notebook-relative path: " + str(relative))
    path = folder / supplied
    try:
        path.resolve().relative_to(folder)
    except ValueError as exc:
        raise ValueError("Notebook path resolves outside its folder: " + str(relative)) from exc
    return path


def scale_qa_files(folder):
    folder = Path(folder).resolve()
    output = {}
    for path in sorted(folder.rglob("*")):
        relative = path.relative_to(folder)
        if scale_qa_ignored(relative):
            continue
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("Symlinks/junctions are not allowed inside the delivered clone: " + relative.as_posix())
        if path.is_file():
            scale_qa_child(folder, relative)
            output[relative.as_posix()] = path
    return output


def scale_qa_complete(folder):
    # This check must precede protected-file/cache inventories or notebook parsing.
    path = Path(folder) / "data" / "scale_v5" / "main" / "manifest.json"
    if not path.is_file():
        raise RuntimeError("V5 is incomplete. No cache inspection, replay or delivery is permitted yet.")
    manifest = scale_qa_read(path)
    if manifest.get("phase") != "interventions_complete":
        raise RuntimeError("V5 interventions are incomplete. No cache inspection, replay or delivery is permitted yet.")
    return manifest


def scale_qa_baseline(path):
    baseline = scale_qa_read(path)
    if (set(baseline["allowed_existing_changes"]) != SCALE_QA_ALLOWED
            or len(baseline["source_files"]) != 988 or len(baseline["destination_files"]) != 988
            or baseline["protected_files"] != 985):
        raise ValueError("Expected the declared988-source/988-destination baseline with985 protected files")
    return baseline


def scale_qa_protected(folder, baseline):
    scale_qa_complete(folder)
    protected = {name: value for name, value in baseline["source_files"].items() if name not in SCALE_QA_ALLOWED}
    failures = [name for name, expected in protected.items()
        if not scale_qa_child(folder, name).is_file() or scale_qa_sha(scale_qa_child(folder, name)) != expected]
    if failures:
        raise RuntimeError("Protected historical files differ: " + ", ".join(failures[:20]))
    return {"protected_files_checked": len(protected), "protected_hash_index": scale_qa_hash(protected)}


def scale_qa_cache_hashes(folder):
    scale_qa_complete(folder)
    return {name: scale_qa_sha(path) for name, path in scale_qa_files(folder).items()
        if name.startswith("data/") and any(part.lower() in {"cache", "caches"} for part in Path(name).parts)}


def scale_qa_notebook(folder):
    import nbformat
    notebook = nbformat.read(Path(folder) / SCALE_QA_NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    cells = [cell for cell in notebook.cells if cell.cell_type == "code" and cell.source.strip()]
    if [cell.execution_count for cell in cells] != list(range(1, len(cells) + 1)):
        raise RuntimeError("Notebook execution counts do not show one top-to-bottom run")
    if any(output.output_type == "error" for cell in cells for output in cell.outputs):
        raise RuntimeError("Notebook contains error outputs")
    return {"code_cells_executed_in_order": len(cells), "error_outputs": 0}


def scale_qa_verify(folder, baseline, require_notebook=True):
    final = scale_qa_complete(folder)
    recovery = scale_qa_recovery_bindings(folder)
    preservation = scale_qa_protected(folder, baseline)
    audit_path = Path(folder) / "data" / "scale_v5" / "artifact_audit.json"
    if not audit_path.exists():
        raise RuntimeError("The final independent V5 artifact audit is absent")
    audit = scale_qa_read(audit_path)
    if audit.get("passed") is not True or audit.get("main_complete", True) is not True:
        raise RuntimeError("The final independent V5 artifact audit has not passed")
    return {"qa_version": SCALE_QA_VERSION, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        **preservation, **(scale_qa_notebook(folder) if require_notebook else {}),
        "main_manifest_sha256": scale_qa_sha(Path(folder) / "data/scale_v5/main/manifest.json"),
        "recovery_bindings": recovery,
        "artifact_audit_sha256": scale_qa_sha(audit_path), "main_requests": final["physical_cli_requests"],
        "artifact_audit_passed": True}


def scale_qa_recovery_bindings(folder):
    """Completion-gated metadata bindings for continuation packages003–005."""
    scale_qa_complete(folder)
    data = Path(folder) / "data/scale_v5"
    path = data / "intervention_resume_003/amendment_003.json"
    if not path.exists():
        if any((data / name).exists() for name in ("intervention_resume_004/amendment_004.json", "intervention_resume_005/amendment_005.json")):
            raise RuntimeError("Later continuation lacks its required third predecessor")
        return {}
    amendment = scale_qa_read(path)
    if amendment.get("protocol") != "23-scale-v5" or amendment.get("amendment_version") != "23-scale-intervention-interruption-v2":
        raise RuntimeError("Unrecognized third continuation package")
    def bound(item):
        target = scale_qa_child(data, item["path"])
        if scale_qa_sha(target) != item["sha256"]:
            raise RuntimeError("Third continuation package binding changed: " + item["path"])
        return target
    if amendment["predecessor"]["path"] != "intervention_resume/amendment_002.json":
        raise RuntimeError("Wrong third continuation predecessor")
    bound(amendment["predecessor"])
    for name in ("implementation", "analysis_plan", "process_proof", "cache_inventory"):
        bound(amendment[name])
    for item in amendment["protected_files"] + amendment.get("tests", []):
        bound(item)
    inventory = scale_qa_read(bound(amendment["cache_inventory"]))
    if inventory.get("count") != 1540 or len(inventory.get("requests", {})) != 1540:
        raise RuntimeError("Third continuation cache prefix count differs")
    for key, digest in inventory["requests"].items():
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise RuntimeError("Unsafe prefix cache key")
        if scale_qa_sha(data / "main/cache" / (key + ".json.gz")) != digest:
            raise RuntimeError("Recorded third-continuation prefix cache changed")
    result = {"amendment_003_sha256": scale_qa_sha(path), "raw_prefix_files_verified": 1540}
    fourth_path = data / "intervention_resume_004/amendment_004.json"
    if fourth_path.exists():
        fourth = scale_qa_read(fourth_path)
        if (fourth.get("protocol") != "23-scale-v5" or fourth.get("amendment_version") != "23-scale-intervention-timeout-continuation-v1"
                or fourth.get("predecessor") != {"path": "intervention_resume_003/amendment_003.json", "sha256": result["amendment_003_sha256"]}
                or fourth.get("analysis_plan") != amendment["analysis_plan"]):
            raise RuntimeError("Fourth continuation package changed predecessor/version/analysis")
        for name in ("predecessor", "implementation", "analysis_plan", "process_proof", "cache_inventory", "stop_record", "sleep_event", "error_metadata", "handling_plan"):
            bound(fourth[name])
        for relative, digest in fourth["provenance_sha256"].items():
            bound({"path": relative, "sha256": digest})
        for item in fourth["protected_files"] + fourth.get("tests", []):
            bound(item)
        fourth_inventory = scale_qa_read(bound(fourth["cache_inventory"]))
        requests = fourth_inventory.get("requests", {})
        if (fourth_inventory.get("count") != 1656 or len(requests) != 1656
                or any(requests.get(key) != digest for key, digest in inventory["requests"].items())):
            raise RuntimeError("Fourth continuation prefix count/predecessor bytes differ")
        for key, digest in requests.items():
            if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
                raise RuntimeError("Unsafe fourth-continuation cache key")
            if scale_qa_sha(data / "main/cache" / (key + ".json.gz")) != digest:
                raise RuntimeError("Recorded fourth-continuation prefix cache changed")
        result.update(amendment_004_sha256=scale_qa_sha(fourth_path), raw_prefix_files_verified=1656)
    fifth_path = data / "intervention_resume_005/amendment_005.json"
    if fifth_path.exists():
        if not fourth_path.exists():
            raise RuntimeError("Fifth continuation lacks its fourth predecessor")
        fifth = scale_qa_read(fifth_path)
        if (fifth.get("protocol") != "23-scale-v5" or fifth.get("amendment_version") != "23-scale-intervention-transport-continuation-v2"
                or fifth.get("predecessor") != {"path": "intervention_resume_004/amendment_004.json", "sha256": result["amendment_004_sha256"]}
                or fifth.get("analysis_plan") != amendment["analysis_plan"]):
            raise RuntimeError("Fifth continuation package changed predecessor/version/analysis")
        for name in ("predecessor", "implementation", "analysis_plan", "process_proof", "cache_inventory", "stop_record", "error_metadata", "handling_plan"):
            bound(fifth[name])
        for relative, digest in fifth["provenance_sha256"].items():
            bound({"path": relative, "sha256": digest})
        for item in fifth["protected_files"] + fifth.get("tests", []):
            bound(item)
        fifth_inventory = scale_qa_read(bound(fifth["cache_inventory"]))
        requests = fifth_inventory.get("requests", {})
        if (fifth_inventory.get("count") != 2124 or len(requests) != 2124
                or any(requests.get(key) != digest for key, digest in fourth_inventory["requests"].items())):
            raise RuntimeError("Fifth continuation prefix count/predecessor bytes differ")
        for key, digest in requests.items():
            if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
                raise RuntimeError("Unsafe fifth-continuation cache key")
            if scale_qa_sha(data / "main/cache" / (key + ".json.gz")) != digest:
                raise RuntimeError("Recorded fifth-continuation prefix cache changed")
        result.update(amendment_005_sha256=scale_qa_sha(fifth_path), raw_prefix_files_verified=2124)
    return result


def scale_qa_delivery_plan(folder, destination, baseline):
    scale_qa_complete(folder)
    folder, destination = Path(folder).resolve(), Path(destination).resolve()
    for path in (folder, destination):
        if path.name != SCALE_QA_FOLDER or path.parent.name.lower() != "notebooks":
            raise ValueError("Delivery is restricted to the Notebook23 folder under notebooks/")
    if folder == destination or destination != Path(baseline["destination"]).resolve():
        raise ValueError("Destination must be the distinct exact folder named in the baseline")
    source_files = scale_qa_files(folder)
    destination_files = scale_qa_files(destination) if destination.exists() else {}
    source_hashes = {name: scale_qa_sha(path) for name, path in source_files.items()}
    destination_hashes = {name: scale_qa_sha(path) for name, path in destination_files.items()}
    conflicts = []
    for name, expected in baseline["destination_files"].items():
        actual = destination_hashes.get(name)
        if actual is None:
            conflicts.append(name + " (baseline destination file missing)")
        elif actual not in {expected, source_hashes.get(name)}:
            conflicts.append(name + " (destination user edit)")
    for name in source_files:
        destination_path = scale_qa_child(destination, name)
        if destination_path.with_name(destination_path.name + ".scale-delivery.tmp").exists():
            conflicts.append(name + " (delivery staging path already exists)")
        if name not in baseline["destination_files"] and name in destination_hashes and destination_hashes[name] != source_hashes[name]:
            conflicts.append(name + " (new-path collision)")
        if destination_path.exists() and not destination_path.is_file():
            conflicts.append(name + " (destination is not a regular file)")
        for parent in destination_path.parents:
            if parent == destination:
                break
            if parent.exists() and not parent.is_dir():
                conflicts.append(name + " (ancestor is a file)")
    receipt = "data/scale_v5/delivery_validation.json"
    if receipt not in source_files and receipt in destination_files:
        conflicts.append(receipt + " (new receipt-path collision)")
    if conflicts:
        raise RuntimeError("Delivery refused before copying: " + "; ".join(conflicts[:20]))
    return {"source_files": source_files, "source_hashes": source_hashes, "destination_hashes": destination_hashes,
        "destination": destination, "unrelated_destination_files_preserved": len(set(destination_files) - set(source_files))}


def scale_qa_deliver(folder, baseline):
    result = scale_qa_verify(folder, baseline)
    destination = Path(baseline["destination"])
    plan = scale_qa_delivery_plan(folder, destination, baseline)
    copied = 0
    for name, source in plan["source_files"].items():
        target = scale_qa_child(destination, name)
        if scale_qa_sha(source) != plan["source_hashes"][name]:
            raise RuntimeError("Source changed during delivery: " + name)
        actual = scale_qa_sha(target) if target.is_file() else None
        if actual != plan["destination_hashes"].get(name):
            raise RuntimeError("Destination changed after preflight: " + name)
        if actual != plan["source_hashes"][name]:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".scale-delivery.tmp")
            if temporary.exists():
                raise RuntimeError("Delivery temporary path already exists: " + str(temporary))
            shutil.copy2(source, temporary)
            if scale_qa_sha(temporary) != plan["source_hashes"][name]:
                raise RuntimeError("Staged delivery bytes differ: " + name)
            os.replace(temporary, target)
            copied += 1
    mismatches = [name for name, expected in plan["source_hashes"].items()
        if not scale_qa_child(destination, name).is_file() or scale_qa_sha(scale_qa_child(destination, name)) != expected]
    if mismatches:
        raise RuntimeError("Delivery byte mismatch: " + ", ".join(mismatches[:20]))
    report = {**result, "destination": str(destination.resolve()), "files_byte_verified": len(plan["source_files"]),
        "files_copied": copied, "all_source_files_match_delivery": True,
        "unrelated_destination_files_preserved": plan["unrelated_destination_files_preserved"],
        "boundary": "Only Notebook23 folder files copied. No destination repository-root files changed."}
    relative = "data/scale_v5/delivery_validation.json"
    source_report = scale_qa_child(folder, relative)
    target_report = scale_qa_child(destination, relative)
    expected_report = plan["source_hashes"].get(relative)
    current_report = scale_qa_sha(target_report) if target_report.is_file() else None
    if current_report != expected_report:
        raise RuntimeError("Delivery receipt destination changed after preflight")
    scale_qa_write(source_report, report)
    target_report.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_report, target_report)
    if scale_qa_sha(source_report) != scale_qa_sha(target_report):
        raise RuntimeError("Delivery receipt byte mismatch")
    scale_qa_protected(folder, baseline)
    return report


def main():
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=base / "scale_baseline_manifest.json")
    parser.add_argument("--deliver", action="store_true", help="Explicitly perform guardedNotebook23-only D: copy")
    args = parser.parse_args()
    baseline = scale_qa_baseline(args.baseline)
    folder = Path(baseline["source"])
    report = scale_qa_deliver(folder, baseline) if args.deliver else scale_qa_verify(folder, baseline)
    if not args.deliver:
        scale_qa_write(folder / "data/scale_v5/delivery_preflight_validation.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
