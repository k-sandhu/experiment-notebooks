"""Explicit reviewed overlay for four lost scale-v5 intervention outcomes.

Raw pending caches are immutable. No recorded request is ever resubmitted.
The unavailable projection is an observation about lost telemetry, not a model
answer or a provider failure. CLI execution is offline unless --live is explicit.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import threading

SCALE_INTERVENTION_RESUME_VERSION = "23-scale-intervention-interruption-v1"
SCALE_INTERVENTION_UNAVAILABLE = "Outcome unavailable after collector interruption; recorded attempt will not be resubmitted."


def sir_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def sir_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sir_read(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def sir_path(data, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Amendment paths must stay inside scale_v5")
    result = (data / path).resolve()
    if not result.is_relative_to(data.resolve()):
        raise ValueError("Amendment path escapes scale_v5")
    return result


def sir_time(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Explicit timezone required")
    return result


def sir_bound(data, item):
    path = sir_path(data, item["path"])
    if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) or sir_sha(path) != item["sha256"]:
        raise ValueError("Bound infrastructure provenance changed: " + item["path"])
    return path


def sir_write(path, value, unique=False):
    """Create a new stop/receipt exclusively; never overwrite prior bytes."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)+"\n").encode()
    for index in range(100000):
        target = path if not index else path.with_name(path.stem+f"_{index:04d}"+path.suffix)
        try:
            with target.open("xb") as stream: stream.write(raw)
            return target
        except FileExistsError:
            if not unique and target.read_bytes() == raw: return target
            if not unique: raise ValueError("Existing continuation receipt changed")
    raise RuntimeError("Continuation receipt namespace exhausted")


def scale_intervention_resume_verify(root, amendment_path):
    """Metadata/request-identity validation only; never inspect arm answers."""
    root = Path(root).resolve(); data = root / "data/scale_v5"; main = data / "main"
    amendment_path = Path(amendment_path).resolve()
    if not amendment_path.is_relative_to(data.resolve()):
        raise ValueError("Amendment must be archived inside scale_v5")
    amendment = sir_read(amendment_path)
    if amendment.get("protocol") != "23-scale-v5" or amendment.get("amendment_version") != SCALE_INTERVENTION_RESUME_VERSION:
        raise ValueError("Unsupported interruption amendment")
    declared = sir_time(amendment["declared_at_utc"])
    lost = sir_time(amendment["loss_observed_at_utc"])
    if declared <= lost or declared > datetime.now(timezone.utc):
        raise ValueError("Amendment must be declared after observed loss and before execution")
    protected = {item["path"]: item for item in amendment["protected_files"]}
    required = {"source_freeze.json", "intervention_start_declaration.json", "infrastructure_resume/amendment_001.json", "main/dispatch.json"}
    if len(protected) != len(amendment["protected_files"]) or not required.issubset(protected):
        raise ValueError("Missing immutable protocol/dispatch/gate bindings")
    for item in protected.values(): sir_bound(data, item)
    gate = sir_read(data / "intervention_start_declaration.json")
    if gate.get("phase") != "interventions_authorized_after_independent_audit" or len(gate["sha256"]) != 38:
        raise ValueError("Require the original 38-binding intervention gate")
    for path, digest in gate["sha256"].items(): sir_bound(data, {"path": path, "sha256": digest})
    implementation = sir_bound(data, amendment["implementation"])
    sir_bound(data, amendment["analysis_plan"])
    for item in amendment.get("tests", []): sir_bound(data, item)
    proof = sir_read(sir_bound(data, amendment["process_proof"]))
    if (type(proof.get("owned_workers")) is not int or proof["owned_workers"] != 0 or proof.get("collector_session_available") is not False
            or sir_time(proof["checked_at_utc"]) < lost or sir_time(proof["checked_at_utc"]) >= declared):
        raise ValueError("Require byte-bound post-loss proof that no owned workers/session remain")
    inventory = sir_read(sir_bound(data, amendment["cache_inventory"]))
    prefix = inventory.get("requests")
    if (inventory.get("protocol") != "23-scale-v5" or inventory.get("count") != 1240
            or not isinstance(prefix, dict) or len(prefix) != 1240
            or any(not re.fullmatch(r"[0-9a-f]{64}", k) or not isinstance(v, str)
                   or not re.fullmatch(r"[0-9a-f]{64}", v) for k, v in prefix.items())):
        raise ValueError("Bind all 1240 pre-interruption raw caches")
    for key, digest in prefix.items():
        if sir_sha(main / "cache" / (key + ".json.gz")) != digest:
            raise ValueError("A recorded cache changed or disappeared; resubmission forbidden")
    dispatch = sir_read(main / "dispatch.json")["jobs"]
    if len(dispatch) != 1200 or len({x["request_key"] for x in dispatch}) != 1200:
        raise ValueError("Require unchanged 1200-job dispatch")
    plans = []
    for item in amendment["request_plans"]:
        path = sir_bound(data, item)
        if path.parent != (main / "request_plans").resolve(): raise ValueError("Invalid request-plan path")
        plans.extend(sir_read(path))
    plan = {x["request_key"]: x for x in plans}
    if len(plans) != 1200 or len(plan) != 1200 or set(plan) != {x["request_key"] for x in dispatch}:
        raise ValueError("Bind the exact intervention request plan")
    indexed = {x["request_key"]: x for x in dispatch}
    original_keys = set(sir_read(main / "original_manifest.json")["request_keys"])
    if (len(original_keys) != 1120 or set(prefix) != original_keys | {x["request_key"] for x in dispatch[:120]}):
        raise ValueError("Inventory must be all originals plus exactly the first 120 dispatched arm slots")
    approved = {}; pairs = {}; pending_keys = set(); terminal_arms = 0
    for key in prefix:
        cache = sir_read(main / "cache" / (key + ".json.gz"))
        if cache.get("key") != key or sir_hash(cache["request"]) != key or len(cache.get("attempts", [])) != 1:
            raise ValueError("Recorded request identity/attempt history changed")
        attempt = cache["attempts"][0]
        if attempt.get("pending") is True:
            pending_keys.add(key)
        elif attempt.get("pending") is not False or not attempt.get("finished_at") or sir_time(attempt["finished_at"]) >= declared:
            raise ValueError("Invalid prior terminal cache metadata")
        elif key in indexed:
            terminal_arms += 1
    items = amendment["unavailable_requests"]
    if len(items) != 4 or len(pending_keys) != 4 or terminal_arms != 116:
        raise ValueError("Only the reviewed 116-terminal/four-pending interruption qualifies")
    for item in items:
        key = item["request_key"]
        if key in approved or key not in pending_keys or prefix.get(key) != item["cache_sha256"]:
            raise ValueError("Unknown/duplicate/unbound unavailable request")
        cache = sir_read(main / "cache" / (key + ".json.gz")); req = cache["request"]; attempt = cache["attempts"][0]
        if set(attempt) != {"pending", "started_at", "timeout_s"} or attempt["timeout_s"] != 900 or sir_time(attempt["started_at"]) >= lost:
            raise ValueError("Reviewed lost attempt must contain only original pending telemetry")
        arm = item["arm"]; stage, sample = ("generate", 1) if arm == "fresh_retry" else ("repair", 0)
        expected_profile = {"model": "gpt-6.1-sol", "reasoning_effort": "high", "protocol": "23-scale-v5", "timeout_s": 900}
        actual_profile = {k: req.get(k) for k in expected_profile if k != "timeout_s"}
        actual_profile["timeout_s"] = req.get("runner_limits", {}).get("timeout_s")
        p, d = plan[key], indexed[key]
        if (arm not in {"fresh_retry", "feedback_repair"} or item["profile"] != expected_profile or actual_profile != expected_profile
                or req["stage"] != stage or req["sample"] != sample or item["stage"] != stage or item["sample"] != sample
                or req["expected_case_ids"] != [item["case_id"]] or len(req["case_inputs"]) != 1
                or req["case_inputs"][0]["case_id"] != item["case_id"]
                or sir_hash(req["case_inputs"]) != item["request_input_hash"] or sir_hash(req["feedback"]) != item["feedback_hash"]
                or any(p[k] != item[k] for k in ("case_id", "arm", "stage", "sample")) or p["source_hash"] != item["content_hash"]
                or d["case_id"] != item["case_id"] or d["arm"] != arm or d["input_hash"] != item["request_input_hash"] or d["feedback_hash"] != item["feedback_hash"]):
            raise ValueError("Unavailable request differs from exact frozen source/profile/feedback identity")
        approved[key] = item; pairs.setdefault(item["case_id"], set()).add(arm)
    if (set(approved) != pending_keys or pending_keys != {x["request_key"] for x in dispatch[116:120]}
            or len(pairs) != 2 or any(v != {"fresh_retry", "feedback_repair"} for v in pairs.values())):
        raise ValueError("Unavailable requests must be both arms of exactly two source pairs")
    return {"root": root, "data": data, "main": main, "amendment": amendment,
            "amendment_sha256": sir_sha(amendment_path), "inventory": prefix, "approved": approved,
            "implementation_path": implementation}


def scale_intervention_resume_load(root):
    data = Path(root) / "data/scale_v5"
    first = sir_read(data / "infrastructure_resume/amendment_001.json")
    path = sir_bound(data, first["implementation"])
    companion = {"__name__": "scale_reviewed_first_companion"}
    exec(compile(path.read_bytes(), str(path), "exec"), companion)
    namespace = companion["scale_resume_load"](root)
    companion["scale_resume_install"](root, data / "infrastructure_resume/amendment_001.json", namespace)
    return namespace, companion


def scale_intervention_resume_install(root, amendment_path, namespace=None):
    state = scale_intervention_resume_verify(root, amendment_path)
    if namespace is None:
        namespace, _ = scale_intervention_resume_load(root)
    # Notebook callers already defined and installed the first companion inside
    # notebook cells. Reuse those closures; do not import/execute a repo file.
    first_state = namespace.get("SCALE_RESUME_INSTALLED")
    if (not first_state or first_state.get("version") != "23-scale-capacity-continuation-v1"
            or Path(first_state["root"]).resolve() != state["root"]
            or first_state["amendment_sha256"] != sir_sha(state["data"] / "infrastructure_resume/amendment_001.json")):
        raise ValueError("Install the approved first companion in this namespace before the second overlay")
    expected = sir_read(state["data"] / "source_freeze.json")["source_sha256"]
    if namespace.get("SCALE_RUNTIME_SOURCE_HASHES") != expected:
        raise ValueError("Loaded frozen helper metadata differs from source_freeze")
    for name, digest in expected.items():
        sir_bound(state["data"], {"path": "source_snapshot/"+name, "sha256": digest})
    old = namespace.get("SCALE_INTERVENTION_RESUME_INSTALLED")
    if old:
        if old["amendment_sha256"] != state["amendment_sha256"]: raise ValueError("Different amendment requires fresh namespace")
        return old
    original_call = namespace["scale_call_model"]; original_dispatch = namespace["scale_dispatch_waves"]
    original_run = namespace["scale_run_interventions"]; original_write = namespace["scale_write_json"]
    lock = threading.Lock(); state["namespace"] = namespace; state["live_started"] = False

    def call(request, cache_dir, live=False, timeout_s=900, _runner=None):
        key = namespace["scale_request_key"](request)
        scoped = Path(cache_dir).resolve() == (state["main"] / "cache").resolve()
        if scoped and key in state["inventory"] and sir_sha(Path(cache_dir) / (key + ".json.gz")) != state["inventory"][key]:
            raise ValueError("Recorded cache changed or disappeared; resubmission forbidden")
        if scoped and key in state["approved"]:
            path = Path(cache_dir) / (key + ".json.gz")
            if timeout_s != 900 or sir_sha(path) != state["inventory"][key] or sir_read(path)["request"] != request:
                raise ValueError("Reviewed pending request bytes/identity changed")
            attempt = sir_read(path)["attempts"][0]
            return {"key": key, "request_key": key, "cached": True, "parsed": None,
                    "error": SCALE_INTERVENTION_UNAVAILABLE, "outcome_unavailable": True,
                    "started_at": attempt["started_at"], "timeout_s": attempt["timeout_s"]}
        return original_call(request, cache_dir, live=live, timeout_s=timeout_s, _runner=_runner)

    def dispatch(jobs, invoke, directory, max_workers=4, progress=None):
        if Path(directory).resolve() != state["main"]:
            return original_dispatch(jobs, invoke, directory, max_workers, progress)
        if max_workers != 4: raise ValueError("Reviewed intervention continuation requires four-worker waves")
        jobs = list(jobs); rows = []; ledger = []
        def run(job):
            key = job.get("request_key")
            try:
                if key in state["inventory"] and sir_sha(state["main"] / "cache" / (key + ".json.gz")) != state["inventory"][key]:
                    raise ValueError("Prior cache changed; no resubmission")
                row, entry = invoke(job)
                known = state["approved"].get(key)
                if known:
                    if (entry["cached_this_run"] is not True or row["transport_error"] != SCALE_INTERVENTION_UNAVAILABLE
                            or row["response"] is not None or any(row[k] != known[k] for k in ("case_id", "arm", "stage", "sample", "content_hash", "request_input_hash", "feedback_hash"))):
                        raise ValueError("Unavailable projection differs from reviewed identity")
                    row.update(outcome_unavailable=True, error_kind="outcome_unavailable")
                    entry.update(outcome_unavailable=True, telemetry_status="raw_pending_preserved")
                if progress:
                    with lock: progress({"arm": row["arm"], "case_id": row["case_id"], "cached": entry["cached_this_run"],
                                         "transport_failure": bool(row["transport_error"]) and not bool(known), "outcome_unavailable": bool(known)})
                return {"row": row, "ledger": entry, "exception": None, "request_key": key, "case_id": row["case_id"], "arm": row["arm"]}
            except Exception as exc:
                return {"row": None, "ledger": None, "exception": {"type": type(exc).__name__, "message": str(exc)},
                        "request_key": key, "case_id": job["case"]["case_id"], "arm": job["arm"]}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for start in range(0, len(jobs), 4):
                wave = jobs[start:start+4]; results = [f.result() for f in [pool.submit(run, job) for job in wave]]
                failed = []
                for result in results:
                    row, entry = result["row"], result["ledger"]
                    if result["exception"]: failed.append(result); continue
                    if not row["transport_error"]: continue
                    known = state["approved"].get(result["request_key"])
                    capacity = namespace["SCALE_RESUME_INSTALLED"]["approved"].get(result["request_key"])
                    allowed_capacity = (capacity and entry["cached_this_run"] is True and row["arm"] == "original"
                        and row["stage"] == "generate" and row["sample"] == 0 and row["split"] == "collection"
                        and row["transport_error"] == capacity["transport_error"] and row["response"] is None
                        and all(row[k] == capacity[k] for k in ("case_id", "content_hash", "request_input_hash")))
                    if not known and not allowed_capacity: failed.append(result)
                if failed:
                    payload = {"protocol": "23-scale-v5", "dispatch_version": SCALE_INTERVENTION_RESUME_VERSION,
                        "amendment_sha256": state["amendment_sha256"], "phase_complete": False, "max_workers": 4,
                        "wave_index": start//4, "jobs_submitted_this_dispatch": start+len(wave), "jobs_in_failed_wave": len(wave),
                        "completed_prior_wave_request_keys": [x["request_key"] for x in ledger],
                        "remaining_jobs_not_dispatched": len(jobs)-start-len(wave), "wave_results": results}
                    path = sir_write(state["main"] / ("infrastructure_stop_intervention_resume_"+state["amendment_sha256"][:12]+".json"), payload, unique=True)
                    raise namespace["SCALE_InfrastructureStop"]("Reviewed interruption continuation stopped; stop="+str(path))
                rows.extend(x["row"] for x in results); ledger.extend(x["ledger"] for x in results)
        return rows, ledger

    def run(root=Path("."), live=False, progress=None):
        if Path(root).resolve() != state["root"]: raise ValueError("Continuation bound to one root")
        if live:
            if state["live_started"] or (state["main"] / "manifest.json").exists(): raise ValueError("No automatic live restart or completed replay")
            current = {p.name.removesuffix(".json.gz") for p in (state["main"] / "cache").glob("*.json.gz")}
            if current != set(state["inventory"]): raise ValueError("Live first continuation requires exact pre-interruption inventory")
            state["live_started"] = True
        return original_run(root=root, live=live, progress=progress)

    def write(path, value):
        path = Path(path).resolve()
        if path == state["main"] / "intervention_run_validation.json" and path.exists():
            if set(value)-{"new_cli_subprocesses_this_run", "replayed_requests_this_run", "offline", "note"}: raise ValueError("Operational receipts only")
            target = state["main"] / "intervention_continuation_diagnostics" / state["amendment_sha256"][:12] / ("validation_"+sir_hash(value)[:12]+".json")
            return sir_write(target, value)
        return original_write(path, value)
    namespace.update(scale_call_model=call, scale_dispatch_waves=dispatch, scale_run_interventions=run,
                     scale_write_json=write, SCALE_INTERVENTION_RESUME_INSTALLED=state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["interventions"])
    parser.add_argument("--root", type=Path, required=True); parser.add_argument("--amendment", type=Path, required=True)
    parser.add_argument("--live", action="store_true"); args = parser.parse_args()
    state = scale_intervention_resume_install(args.root, args.amendment)
    count = [0]
    def progress(event):
        count[0] += 1
        print(json.dumps({"event": "request_terminal_or_unavailable", "completed_this_phase": count[0], **event}), flush=True)
    result = state["namespace"]["scale_run_interventions"](root=args.root, live=args.live, progress=progress)
    print(json.dumps({"phase": result["manifest"]["phase"], "amendment_sha256": state["amendment_sha256"]}), flush=True)


if __name__ == "__main__": main()
