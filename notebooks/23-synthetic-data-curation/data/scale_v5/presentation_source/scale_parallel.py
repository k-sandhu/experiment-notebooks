"""Bounded waves for scale v5. Never retry or dispatch beyond a failed wave."""
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


SCALE_DISPATCH_VERSION = "23-scale-four-worker-waves-v1"


class SCALE_InfrastructureStop(RuntimeError):
    pass


def scale_dispatch_waves(jobs, invoke, directory, max_workers=4, progress=None):
    if type(max_workers) is not int or not 1 <= max_workers <= 4:
        raise ValueError("One to four workers are allowed")
    jobs = list(jobs)
    lock = threading.Lock()
    def run(job):
        try:
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
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for start in range(0, len(jobs), max_workers):
            wave = jobs[start:start + max_workers]
            futures = [executor.submit(run, job) for job in wave]
            results = [future.result() for future in futures]
            failed = [result for result in results if result["exception"] or result["row"]["transport_error"]]
            if failed:
                scale_write_json(Path(directory) / "infrastructure_stop.json", {
                    "protocol": SCALE_PROTOCOL, "dispatch_version": SCALE_DISPATCH_VERSION, "phase_complete": False,
                    "max_workers": max_workers, "wave_index": start // max_workers,
                    "jobs_submitted_this_dispatch": start + len(wave), "jobs_in_failed_wave": len(wave),
                    "completed_prior_wave_request_keys": [row["request_key"] for row in ledger],
                    "remaining_jobs_not_dispatched": len(jobs) - start - len(wave), "wave_results": results,
                    "resolution": "All current-wave tasks settled. Full written raw caches are retained. No next wave or orchestration retry occurs; review infrastructure explicitly."})
                raise SCALE_InfrastructureStop(f"Scale infrastructure stop in wave {start // max_workers}; "
                    f"{len(failed)} failures; {len(jobs) - start - len(wave)} jobs not dispatched")
            rows.extend(result["row"] for result in results)
            ledger.extend(result["ledger"] for result in results)
    return rows, ledger
