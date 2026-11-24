"""Infrastructure-only v4e fork: bounded two-request waves, unchanged core scoring.

Load after the frozen high_* core in a main-only namespace. Replay the completed
serial v4d pilot in its own namespace. This helper never calls a model on import.
"""
import copy
import threading
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


HIGH_PARALLEL_VERSION = "23-high-v4e-two-worker-wave-v1"
HIGH_PARALLEL_CORE_SOURCE_SHA256 = {'high_transport.py': '3b324623231fd381cc1843f8bebe62974f8151576ff08898fe16a70bf03dc717', 'high_fixtures.py': 'ff9479d80c93327d3cf0f4f854b1da89e5bd8d8b0db48707509f9cfe77e15547', 'high_material_audit.py': 'cb8d8d6242936886b4f8ff865d7375d02a79d9562d29fc601650da9c6d584bb0', 'high_experiment.py': '639a0cc8191573a4115e53eff17132f480e1bde1c7b8a93c7af473678be8795f'}
HIGH_PARALLEL_CORE_CONFIG = high_config
HIGH_PARALLEL_CORE_RUN_JOBS = high_run_jobs
HIGH_PARALLEL_CORE_PROFILE = high_profile_protocol
HIGH_PROTOCOL = "23-high-v4e"
HIGH_MAIN_CONFIG = {**HIGH_MAIN_CONFIG, "protocol": HIGH_PROTOCOL, "max_workers": 2}
HIGH_FULL_CONFIG = HIGH_MAIN_CONFIG


def high_config(config=None, pilot=False):
    """Retain every core bound, changing only the main dispatch worker bound."""
    if pilot:
        raise ValueError("The parallel infrastructure fork is main-only; replay the frozen serial pilot separately")
    cfg = {**HIGH_MAIN_CONFIG, **copy.deepcopy(config or {})}
    workers = cfg["max_workers"]
    if type(workers) is not int or workers not in (1, 2):
        raise ValueError("V4e permits one or two workers only")
    checked = HIGH_PARALLEL_CORE_CONFIG({**cfg, "max_workers": 1}, pilot=False)
    return {**checked, "max_workers": workers}


def high_profile_protocol(config, phase, **extra):
    """Replace infrastructure metadata only; the scientific protocol is inherited."""
    result = HIGH_PARALLEL_CORE_PROFILE(config, phase, **extra)
    result["infrastructure_stop_policy"] = (
        f"At most {config['max_workers']} requests in each wave. Wait for every request in the current wave. "
        "If any transport failure or dispatch exception occurs, preserve all current-wave caches and diagnostics, "
        "stop the incomplete phase, and dispatch no next wave. Cached failures never requery.")
    result["protocol_dispatch_fork"] = {"version": HIGH_PARALLEL_VERSION,
        "core_source_sha256": dict(HIGH_PARALLEL_CORE_SOURCE_SHA256),
        "actual_max_workers": config["max_workers"], "maximum_wave_size": config["max_workers"],
        "unchanged": ["model", "high reasoning", "one case per request", "source packets", "prompt construction",
            "seeds", "failure eligibility", "expansion and selection", "paired interventions", "scoring", "statistics"],
        "pilot": "Completed serial 23-high-v4d calibration remains frozen; no pilot requests are dispatched by this helper"}
    return result


def high_parallel_run_one(job, directory, config, live=False, progress=None):
    """Use the exact frozen singleton transform, isolating only its stop report.

    A function-local globals copy redirects the core's operational stop JSON to a
    request-specific filename. The cache directory, requests, response parsing,
    verification, row fields, and ledger construction are the frozen core's code.
    This avoids racing on infrastructure_stop.json when both wave jobs fail.
    """
    request_key = None
    captured = []
    try:
        request_key = high_request_key(high_job_request(job))
        namespace = dict(HIGH_PARALLEL_CORE_RUN_JOBS.__globals__)
        original_writer = namespace["high_write_json"]
        def isolated_writer(path, value):
            path = Path(path)
            if path.name == "infrastructure_stop.json":
                captured.append(copy.deepcopy(value))
                path = path.with_name(f"infrastructure_stop_single_{request_key}.json")
            original_writer(path, value)
        namespace["high_write_json"] = isolated_writer
        singleton = types.FunctionType(HIGH_PARALLEL_CORE_RUN_JOBS.__code__, namespace,
            name="high_parallel_frozen_singleton", argdefs=HIGH_PARALLEL_CORE_RUN_JOBS.__defaults__,
            closure=HIGH_PARALLEL_CORE_RUN_JOBS.__closure__)
        rows, ledger = singleton([job], directory, {**config, "max_workers": 1}, live, progress)
        return {"request_key": request_key, "row": rows[0], "ledger": ledger[0], "exception": None}
    except Exception as exc:
        stop = captured[-1] if captured else {}
        return {"request_key": request_key, "row": stop.get("candidate"),
            "ledger": stop.get("request_ledger_entry"),
            "case_id": job["case"]["case_id"], "arm": job["arm"],
            "exception": {"type": type(exc).__name__, "message": str(exc)}}


def high_run_jobs(jobs, directory, config, live=False, progress=None):
    """Dispatch one bounded wave at a time; preserve deterministic result order."""
    cfg = high_config(config)
    jobs = list(jobs)
    if len(jobs) > cfg["max_physical_cli_requests"]:
        raise RuntimeError("Declared physical CLI request cap would be exceeded")
    rows, ledger = [], []
    lock = threading.Lock()
    def safe_progress(event):
        if progress:
            with lock:
                progress(event)
    with ThreadPoolExecutor(max_workers=cfg["max_workers"]) as executor:
        for start in range(0, len(jobs), cfg["max_workers"]):
            wave = jobs[start:start + cfg["max_workers"]]
            futures = [executor.submit(high_parallel_run_one, job, directory, cfg, live, safe_progress) for job in wave]
            # All futures settle before checking the gate or dispatching another wave.
            results = [future.result() for future in futures]
            failed = [result for result in results if result["exception"] or
                (result["row"] is not None and result["row"]["transport_error"])]
            if failed:
                high_write_json(Path(directory) / "infrastructure_stop_parallel.json", {
                    "protocol": HIGH_PROTOCOL, "dispatch_fork": HIGH_PARALLEL_VERSION, "phase_complete": False,
                    "actual_max_workers": cfg["max_workers"], "wave_index": start // cfg["max_workers"],
                    "jobs_in_failed_wave": len(wave), "jobs_submitted_this_dispatch": start + len(wave),
                    "completed_prior_wave_request_keys": [entry["request_key"] for entry in ledger],
                    "remaining_jobs_not_dispatched": len(jobs) - start - len(wave),
                    "failed_request_keys": [result["request_key"] for result in failed], "wave_results": results,
                    "resolution": "Review service availability explicitly. Both current-wave raw caches are retained when written. No next wave or orchestration retry occurs."})
                raise RuntimeError(f"V4e infrastructure stop after wave {start // cfg['max_workers']}: "
                    f"{len(failed)} failed request(s); {len(jobs) - start - len(wave)} jobs not dispatched")
            rows.extend(result["row"] for result in results)
            ledger.extend(result["ledger"] for result in results)
    return rows, ledger
