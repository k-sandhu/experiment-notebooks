"""Reviewed infrastructure continuation for frozen scale-v5 originals.

This companion never changes a request, scorer, source, or failure-selection rule.
It retains reviewed cached capacity failures and only bypasses their dispatch-stop
trigger. CLI use is originals-only and offline unless --live is explicit.
"""
import argparse as _sr_argparse
from concurrent.futures import ThreadPoolExecutor as _SRExecutor
from datetime import datetime as _SRDatetime
import gzip as _sr_gzip
import hashlib as _sr_hashlib
import json as _sr_json
from pathlib import Path as _SRPath
import re as _sr_re
import threading as _sr_threading

SCALE_RESUME_VERSION = "23-scale-capacity-continuation-v1"
SCALE_RESUME_CAPACITY_MESSAGE = "Selected model is at capacity. Please try a different model."


def scale_resume_hash(value):
    raw = _sr_json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _sr_hashlib.sha256(raw).hexdigest()


def scale_resume_sha(path):
    return _sr_hashlib.sha256(_SRPath(path).read_bytes()).hexdigest()


def scale_resume_read(path):
    path = _SRPath(path)
    raw = path.read_bytes()
    return _sr_json.loads(_sr_gzip.decompress(raw) if path.suffix == ".gz" else raw)


def scale_resume_path(data, relative):
    relative = _SRPath(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Amendment paths must remain inside data/scale_v5")
    path = (data / relative).resolve()
    if not path.is_relative_to(data.resolve()):
        raise ValueError("Amendment path escapes data/scale_v5")
    return path


def scale_resume_write(path, value, unique=False):
    """Exclusive new receipts; never replace an existing stop or diagnostic."""
    path = _SRPath(path)
    raw = (_sr_json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in range(100000):
        target = path if not suffix else path.with_name(path.stem + f"_{suffix:04d}" + path.suffix)
        try:
            with target.open("xb") as stream:
                stream.write(raw)
            return target
        except FileExistsError:
            if not unique and target.read_bytes() == raw:
                return target
            if not unique:
                raise ValueError("Existing continuation diagnostic bytes changed")
    raise RuntimeError("Continuation receipt namespace exhausted")


def scale_resume_verify(root, amendment_path, namespace):
    """Read-only verification. No model calls, directories, or receipts created."""
    root = _SRPath(root).resolve()
    data, main = root / "data" / "scale_v5", root / "data" / "scale_v5" / "main"
    amendment_path = _SRPath(amendment_path).resolve()
    amendment = scale_resume_read(amendment_path)
    if amendment.get("amendment_version") != SCALE_RESUME_VERSION or amendment.get("protocol") != "23-scale-v5":
        raise ValueError("Unsupported explicit infrastructure amendment")
    declared = _SRDatetime.fromisoformat(amendment["declared_at_utc"])
    if declared.tzinfo is None:
        raise ValueError("Amendment declaration must include a timezone")
    freeze_path = data / "source_freeze.json"
    if scale_resume_sha(freeze_path) != amendment["source_freeze_sha256"]:
        raise ValueError("Frozen source/config metadata hash changed")
    freeze = scale_resume_read(freeze_path)
    expected = freeze["source_sha256"]
    if freeze["protocol"] != "23-scale-v5" or namespace.get("SCALE_RUNTIME_SOURCE_HASHES") != expected:
        raise ValueError("Loaded frozen helper metadata differs from source_freeze")
    for name, digest in expected.items():
        if scale_resume_sha(scale_resume_path(data, "source_snapshot/" + name)) != digest:
            raise ValueError("Frozen helper snapshot bytes changed: " + name)
    protected = {item["path"]: item["sha256"] for item in amendment["protected_files"]}
    if len(protected) != len(amendment["protected_files"]) or not {
            "main_start_declaration.json", "main/protocol.json", "main/allocation.json"}.issubset(protected):
        raise ValueError("Bind the main start gate, protocol, and allocation bytes explicitly")
    for name, digest in protected.items():
        if scale_resume_sha(scale_resume_path(data, name)) != digest:
            raise ValueError("Protected pre-continuation input bytes changed: " + name)
    gate = scale_resume_read(data / "main_start_declaration.json")
    for name, digest in gate["sha256"].items():
        if scale_resume_sha(scale_resume_path(data, name)) != digest:
            raise ValueError("Immutable pre-call main-start gate lineage changed: " + name)
    plans = {}
    for item in amendment["request_plans"]:
        path = scale_resume_path(data, item["path"])
        if path.parent != (main / "request_plans").resolve() or scale_resume_sha(path) != item["sha256"]:
            raise ValueError("Frozen original request-plan bytes changed")
        for job in scale_resume_read(path):
            if job["request_key"] in plans:
                raise ValueError("Repeated request in bound plans")
            plans[job["request_key"]] = job
    if not plans:
        raise ValueError("Bind at least the interrupted original request plan")
    original_stop = main / "infrastructure_stop.json"
    if scale_resume_sha(original_stop) != amendment["original_stop_sha256"]:
        raise ValueError("Original infrastructure stop bytes changed")
    stops, recorded = {}, set()
    for item in amendment["archived_stops"]:
        path = scale_resume_path(data, item["path"])
        if path == original_stop.resolve() or scale_resume_sha(path) != item["sha256"]:
            raise ValueError("A separate byte-exact archived stop is required")
        stop = scale_resume_read(path)
        if stop.get("protocol") != "23-scale-v5" or stop.get("phase_complete") is not False:
            raise ValueError("Archived stop is not an incomplete scale-v5 dispatch")
        stops[item["sha256"]] = stop
        recorded.update(stop["completed_prior_wave_request_keys"])
        recorded.update(result["request_key"] for result in stop["wave_results"] if result.get("request_key"))
    if amendment["original_stop_sha256"] not in stops:
        raise ValueError("Original stop has not been archived")
    # The two optional provenance records bind bytes, not outcome decisions.
    for name in ("implementation", "cache_inventory"):
        if name in amendment:
            item = amendment[name]
            if scale_resume_sha(scale_resume_path(data, item["path"])) != item["sha256"]:
                raise ValueError("Amendment provenance bytes changed: " + name)
    for path in (main / "original_chunks").glob("chunk_*/manifest.json"):
        recorded.update(scale_resume_read(path)["request_keys"])
    original_manifest = main / "original_manifest.json"
    if original_manifest.exists():
        recorded.update(scale_resume_read(original_manifest)["request_keys"])
    cache_hashes = {path.stem.split(".")[0]: scale_resume_sha(path) for path in (main / "cache").glob("*.json.gz")}
    if not recorded.issubset(cache_hashes):
        raise ValueError("A previously recorded request cache is missing; resubmission is forbidden")
    if "cache_inventory" not in amendment:
        raise ValueError("A byte-bound pre-continuation cache inventory is required")
    inventory = scale_resume_read(scale_resume_path(data, amendment["cache_inventory"]["path"]))
    prefix = inventory.get("requests")
    if (inventory.get("protocol") != "23-scale-v5" or not isinstance(prefix, dict)
            or type(inventory.get("count")) is not int or inventory["count"] != len(prefix)
            or any(not _sr_re.fullmatch(r"[0-9a-f]{64}", key) or
                   not isinstance(digest, str) or not _sr_re.fullmatch(r"[0-9a-f]{64}", digest)
                   for key, digest in prefix.items())):
        raise ValueError("Invalid pre-continuation cache inventory")
    if any(cache_hashes.get(key) != digest for key, digest in prefix.items()):
        raise ValueError("An inventoried prior cache is missing or its raw bytes changed")
    for key in prefix:
        cached = scale_resume_read(main / "cache" / (key + ".json.gz"))
        if len(cached.get("attempts", [])) != 1 or cached["attempts"][0].get("pending") is not False:
            raise ValueError("Prior cache inventory contains a pending or resubmitted request")
        if _SRDatetime.fromisoformat(cached["attempts"][0]["finished_at"]) > declared:
            raise ValueError("Amendment declaration predates a terminal inventoried request")
    approved = {}
    required_profile = {"model": "gpt-6.1-sol", "reasoning_effort": "high", "stage": "generate",
                        "sample": 0, "protocol": "23-scale-v5", "timeout_s": 900}
    for item in amendment["reviewed_failures"]:
        key = item["request_key"]
        if not _sr_re.fullmatch(r"[0-9a-f]{64}", key) or key in approved or item["profile"] != required_profile:
            raise ValueError("Invalid/duplicate reviewed request or changed original profile")
        if key not in prefix:
            raise ValueError("Reviewed failure must be in the byte-bound prior cache inventory")
        plan = plans.get(key)
        if (not plan or plan["case_id"] != item["case_id"] or plan["source_hash"] != item["content_hash"]
                or plan["arm"] != "original" or plan["stage"] != "generate" or plan["sample"] != 0):
            raise ValueError("Reviewed failure is not the exact bound original plan entry")
        path = main / "cache" / (key + ".json.gz")
        if scale_resume_sha(path) != item["cache_sha256"]:
            raise ValueError("Reviewed raw cache bytes changed")
        cached = scale_resume_read(path)
        request = cached["request"]
        if cached["key"] != key or scale_resume_hash(request) != key or len(cached["attempts"]) != 1:
            raise ValueError("Reviewed request identity/attempt history changed")
        attempt = cached["attempts"][0]
        if _SRDatetime.fromisoformat(attempt["finished_at"]) > declared:
            raise ValueError("Review declaration predates the terminal failure")
        profile = {name: request.get(name) for name in required_profile if name != "timeout_s"}
        profile["timeout_s"] = request.get("runner_limits", {}).get("timeout_s")
        if profile != required_profile or request.get("feedback") is not None:
            raise ValueError("Reviewed cache is not an unchanged high-reasoning original")
        if (request["expected_case_ids"] != [item["case_id"]] or len(request["case_inputs"]) != 1
                or request["case_inputs"][0]["case_id"] != item["case_id"]
                or scale_resume_hash(request["case_inputs"]) != item["request_input_hash"]):
            raise ValueError("Reviewed case/source input identity changed")
        if (attempt.get("pending") is not False or attempt.get("final_assistant_response")
                or attempt.get("parsed") is not None or attempt.get("error") != item["transport_error"]
                or attempt.get("timed_out") or attempt.get("unexpected_tools")):
            raise ValueError("Reviewed failure has pending state, output, or a different failure")
        terminals = [event for event in attempt.get("events", []) if event.get("type") in {"turn.failed", "turn.completed"}]
        terminal_capacity = (terminals and terminals[-1].get("type") == "turn.failed" and
            terminals[-1].get("error", {}).get("message") == SCALE_RESUME_CAPACITY_MESSAGE)
        if (not terminal_capacity or any(event.get("type") == "turn.completed" for event in terminals)
                or attempt.get("return_code") != 1 or SCALE_RESUME_CAPACITY_MESSAGE not in item["transport_error"]):
            raise ValueError("Only explicitly reviewed terminal capacity failures qualify")
        stop = stops[item["stop_sha256"]]
        matches = [result for result in stop["wave_results"] if result.get("request_key") == key]
        if len(matches) != 1:
            raise ValueError("Reviewed failure is absent from its archived failed wave")
        result = matches[0]
        row, ledger = result["row"], result["ledger"]
        if (result.get("exception") or row["case_id"] != item["case_id"] or row["arm"] != "original"
                or row["split"] != "collection" or row["content_hash"] != item["content_hash"]
                or row["request_input_hash"] != item["request_input_hash"] or row["response"] is not None
                or row["transport_error"] != item["transport_error"] or ledger["request_key"] != key
                or ledger["transport_error"] != item["transport_error"]):
            raise ValueError("Archived original failure row/profile differs from the amendment")
        approved[key] = item
    if not approved:
        raise ValueError("An explicit nonempty reviewed-failure list is required")
    return {"root": root, "data": data, "main": main, "amendment": amendment,
            "amendment_sha256": scale_resume_sha(amendment_path), "approved": approved,
            "cache_hashes": cache_hashes, "freeze": freeze}


def scale_resume_install(root, amendment_path, namespace=None):
    """Install into shared notebook globals, or pass an explicit helper namespace."""
    namespace = globals() if namespace is None else namespace
    state = scale_resume_verify(root, amendment_path, namespace)
    old = namespace.get("SCALE_RESUME_INSTALLED")
    if old:
        if old["root"] != state["root"] or old["amendment_sha256"] != state["amendment_sha256"]:
            raise ValueError("Load a fresh frozen namespace for a different amendment")
        return old
    original_dispatch = namespace["scale_dispatch_waves"]
    original_write = namespace["scale_write_json"]
    original_collect = namespace["scale_collect_originals"]
    state.update({"version": SCALE_RESUME_VERSION, "bypassed_cached_failure_keys": [],
                  "preserved_validation_paths": [], "diagnostic_paths": [], "new_stop_paths": []})
    lock = _sr_threading.Lock()

    def write_json(path, value):
        path = _SRPath(path).resolve()
        try:
            relative = path.relative_to(state["main"]).as_posix()
        except ValueError:
            return original_write(path, value)
        operational = relative == "original_run_validation.json" or bool(_sr_re.fullmatch(
            r"original_chunks/chunk_\d+/run_validation\.json", relative))
        if not operational or not path.exists():
            return original_write(path, value)
        if set(value) - {"new_cli_subprocesses_this_run", "replayed_requests_this_run", "offline", "note"}:
            raise ValueError("Only operational validation counters may enter continuation diagnostics")
        label = path.parent.name if path.name == "run_validation.json" else "original"
        target = state["main"] / "continuation_diagnostics" / state["amendment_sha256"][:12]
        target = target / (label + "_" + scale_resume_hash(value)[:12] + ".json")
        receipt = scale_resume_write(target, value)
        state["preserved_validation_paths"].append(relative)
        state["diagnostic_paths"].append(str(receipt))
        # Existing committed/copied operational bytes remain untouched.

    def dispatch(jobs, invoke, directory, max_workers=4, progress=None):
        if _SRPath(directory).resolve() != state["main"]:
            return original_dispatch(jobs, invoke, directory, max_workers, progress)
        if type(max_workers) is not int or not 1 <= max_workers <= 4:
            raise ValueError("One to four workers are allowed")
        jobs = list(jobs)
        def run(job):
            try:
                key = job.get("request_key")
                if key in state["cache_hashes"] and scale_resume_sha(state["main"] / "cache" / (key + ".json.gz")) != state["cache_hashes"][key]:
                    raise ValueError("Recorded request cache changed; no resubmission allowed")
                row, entry = invoke(job)
                if progress:
                    with lock:
                        progress({"arm": row["arm"], "case_id": row["case_id"],
                                  "cached": entry["cached_this_run"], "transport_failure": bool(row["transport_error"])})
                return {"row": row, "ledger": entry, "exception": None,
                        "request_key": row["request_key"], "case_id": row["case_id"], "arm": row["arm"]}
            except Exception as exc:
                return {"row": None, "ledger": None, "exception": {"type": type(exc).__name__, "message": str(exc)},
                        "request_key": job.get("request_key"), "case_id": job["case"]["case_id"], "arm": job["arm"]}
        rows, ledger = [], []
        with _SRExecutor(max_workers=max_workers) as executor:
            for start in range(0, len(jobs), max_workers):
                wave = jobs[start:start + max_workers]
                results = [future.result() for future in [executor.submit(run, job) for job in wave]]
                failed = []
                for result in results:
                    row, entry = result["row"], result["ledger"]
                    if result["exception"]:
                        failed.append(result)
                    elif row["transport_error"]:
                        known = state["approved"].get(result["request_key"])
                        bypass = (known and entry["cached_this_run"] is True and row["arm"] == "original"
                            and row["stage"] == "generate" and row["sample"] == 0 and row["split"] == "collection"
                            and row["case_id"] == known["case_id"] and row["transport_error"] == known["transport_error"]
                            and row["request_input_hash"] == known["request_input_hash"]
                            and row["content_hash"] == known["content_hash"] and row["response"] is None)
                        if bypass:
                            state["bypassed_cached_failure_keys"].append(result["request_key"])
                        else:
                            failed.append(result)
                if failed:
                    payload = {"protocol": namespace["SCALE_PROTOCOL"], "dispatch_version": SCALE_RESUME_VERSION,
                        "amendment_sha256": state["amendment_sha256"], "phase_complete": False,
                        "max_workers": max_workers, "wave_index": start // max_workers,
                        "jobs_submitted_this_dispatch": start + len(wave), "jobs_in_failed_wave": len(wave),
                        "completed_prior_wave_request_keys": [row["request_key"] for row in ledger],
                        "remaining_jobs_not_dispatched": len(jobs) - start - len(wave), "wave_results": results,
                        "resolution": "All current-wave tasks settled. Original stop and raw caches retained. No next wave or automatic resubmission."}
                    path = scale_resume_write(state["main"] / ("infrastructure_stop_resume_" + state["amendment_sha256"][:12] + ".json"), payload, unique=True)
                    state["new_stop_paths"].append(str(path))
                    raise namespace["SCALE_InfrastructureStop"](f"Reviewed continuation stopped in wave {start // max_workers}; {len(failed)} failures; stop={path}")
                rows.extend(result["row"] for result in results)
                ledger.extend(result["ledger"] for result in results)
        return rows, ledger

    def collect(root=_SRPath("."), live=False, progress=None):
        if _SRPath(root).resolve() != state["root"]:
            raise ValueError("Reviewed continuation is bound to one main root")
        if live and (state["main"] / "original_manifest.json").exists():
            raise ValueError("Live originals continuation is forbidden after originals_complete")
        return original_collect(root=root, live=live, progress=progress)

    namespace["scale_dispatch_waves"] = dispatch
    namespace["scale_write_json"] = write_json
    namespace["scale_collect_originals"] = collect
    namespace["SCALE_RESUME_INSTALLED"] = state
    return state


def scale_resume_load(root):
    """CLI loader uses only byte-checked frozen data snapshots."""
    data = _SRPath(root) / "data" / "scale_v5"
    freeze = scale_resume_read(data / "source_freeze.json")
    sources = {}
    for name, expected in freeze["source_sha256"].items():
        path = data / "source_snapshot" / name
        if scale_resume_sha(path) != expected:
            raise ValueError("Frozen helper snapshot changed: " + name)
        sources[name] = path.read_text(encoding="utf-8")
    namespace = {"__name__": "scale_reviewed_originals_continuation"}
    for name in ("scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py"):
        exec(compile(sources[name], name, "exec"), namespace)
    namespace["scale_load_cores"](core_sources={name: sources[name] for name in namespace["SCALE_CORE_SHA256"]})
    namespace["SCALE_RUNTIME_SOURCE_HASHES"] = freeze["source_sha256"]
    return namespace


def main():
    parser = _sr_argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["originals"])
    parser.add_argument("--root", type=_SRPath, required=True)
    parser.add_argument("--amendment", type=_SRPath, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    namespace = scale_resume_load(args.root)
    state = scale_resume_install(args.root, args.amendment, namespace)
    count = [0]
    def progress(event):
        count[0] += 1
        print(_sr_json.dumps({"completed_this_phase": count[0], **event}), flush=True)
    result = namespace["scale_collect_originals"](root=args.root, live=args.live, progress=progress)
    print(_sr_json.dumps({"phase": "originals", "continuation": SCALE_RESUME_VERSION,
        "amendment_sha256": state["amendment_sha256"], "metrics": result["metrics"],
        "manifest": result["manifest"], "preserved_validation_paths": state["preserved_validation_paths"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
