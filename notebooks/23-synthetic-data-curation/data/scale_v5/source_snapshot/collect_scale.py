"""Explicit scale-v5 phases. Offline by default; never automatically chain phases."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    source = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare-pilot", "pilot", "prepare-main", "originals", "interventions"])
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--root", type=Path, default=source.parent / "experiment_notebooks" / "notebooks" / "23-synthetic-data-curation")
    parser.add_argument("--config", type=Path, help="Optional JSON with pilot/main size knobs; recorded immutably")
    args = parser.parse_args()
    if args.live and args.phase.startswith("prepare"):
        parser.error("Preparation never invokes a model; omit --live")
    ns = {"__name__": "scale_v5_notebook_helpers"}
    for filename in ("scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py"):
        exec(compile((source / filename).read_text(encoding="utf-8"), filename, "exec"), ns)
    ns["scale_load_cores"](core_dir=source)
    source_names = ["scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py", "collect_scale.py", *ns["SCALE_CORE_SHA256"]]
    source_hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in source_names}
    ns["SCALE_RUNTIME_SOURCE_HASHES"] = source_hashes
    requested = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
    if set(requested) - {"pilot", "main"}:
        raise ValueError("Config has only pilot/main objects")
    pilot_cfg = ns["scale_config"](requested.get("pilot"), pilot=True)
    main_cfg = ns["scale_config"](requested.get("main"))
    freeze_path = args.root / "data" / "scale_v5" / "source_freeze.json"
    freeze = {"protocol": ns["SCALE_PROTOCOL"], "source_sha256": source_hashes,
        "pilot_config": pilot_cfg, "main_config": main_cfg, "live_calls_during_preparation": 0,
        "call_boundary": "One subprocess per full gzip-cached request; no orchestration retry; CLI internal network retries uncertain"}
    if freeze_path.exists():
        if json.loads(freeze_path.read_text(encoding="utf-8")) != freeze:
            raise ValueError("Scale source/config freeze changed; no collection or replay attempted")
    elif args.phase != "prepare-pilot":
        raise RuntimeError("Prepare/freeze sources before any collection phase")
    else:
        ns["scale_write_json"](freeze_path, freeze)
    count = [0]
    def progress(event):
        count[0] += 1
        # No value/schema verdict, recovery rate, or paired advantage is monitored.
        print(json.dumps({"completed_this_phase": count[0], **event}), flush=True)
    phases = {
        "prepare-pilot": lambda: ns["scale_prepare_pilot"](pilot_cfg, root=args.root),
        "pilot": lambda: ns["scale_run_pilot"](pilot_cfg, root=args.root, live=args.live, progress=progress),
        "prepare-main": lambda: ns["scale_prepare_main"](main_cfg, root=args.root),
        "originals": lambda: ns["scale_collect_originals"](root=args.root, live=args.live, progress=progress),
        "interventions": lambda: ns["scale_run_interventions"](root=args.root, live=args.live, progress=progress),
    }
    result = phases[args.phase]()
    print(json.dumps({"phase": args.phase, "protocol": ns["SCALE_PROTOCOL"], "selected_tier": result.get("selected_tier", result.get("protocol", {}).get("selected_tier")),
        "threshold_met": result.get("threshold_met"), "metrics": result.get("metrics"), "manifest": result.get("manifest")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
