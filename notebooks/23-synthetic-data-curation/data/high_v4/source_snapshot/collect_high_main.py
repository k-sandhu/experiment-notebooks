"""Main-only v4e infrastructure fork. Offline replay is the default."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare-main", "originals", "interventions"])
    parser.add_argument("--live", action="store_true")
    source = Path(__file__).resolve().parent
    parser.add_argument("--root", type=Path, default=source.parent / "experiment_notebooks" / "notebooks" / "23-synthetic-data-curation")
    args = parser.parse_args()
    if args.phase == "prepare-main" and args.live:
        parser.error("Preparation never invokes a model; omit --live")
    ns = {"__name__": "high_v4e_main_helpers"}
    filenames = ("high_transport.py", "high_fixtures.py", "high_material_audit.py", "high_experiment.py", "high_parallel.py")
    for name in filenames:
        exec(compile((source / name).read_text(encoding="utf-8"), name, "exec"), ns)
    hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in filenames}
    for name, frozen_hash in ns["HIGH_PARALLEL_CORE_SOURCE_SHA256"].items():
        if hashes[name] != frozen_hash:
            raise ValueError(f"Frozen v4 core changed: {name}")
    folder = args.root / "data" / "high_v4"
    pilot_protocol = json.loads((folder / "pilot" / "protocol.json").read_text(encoding="utf-8"))
    ladder = json.loads((folder / "pilot" / "ladder.json").read_text(encoding="utf-8"))
    if pilot_protocol["protocol"] != "23-high-v4d" or ladder["protocol_hash"] != ns["high_hash"](pilot_protocol):
        raise ValueError("Main requires the completed, frozen serial v4d pilot")
    declaration_path = folder / "main_parallel_declaration.json"
    declaration = {"protocol": ns["HIGH_PROTOCOL"], "dispatch_fork": ns["HIGH_PARALLEL_VERSION"],
        "source_sha256": hashes, "pilot_ladder_hash": ns["high_hash"](ladder), "max_workers": 2,
        "wave_stop_policy": "Wait for both requests in a wave; on any transport failure stop before the next wave",
        "unchanged": ["model", "high reasoning", "source packets", "prompt construction", "eligibility", "seeds", "selection", "scoring", "paired design", "statistics"]}
    if declaration_path.exists():
        previous = json.loads(declaration_path.read_text(encoding="utf-8"))
        if {key: value for key, value in previous.items() if key != "declared_utc"} != declaration:
            raise ValueError("Frozen main infrastructure declaration changed")
    else:
        if args.phase != "prepare-main":
            raise RuntimeError("Prepare and independently audit main before collecting originals")
        ns["high_write_json"](declaration_path, {"declared_utc": datetime.now(timezone.utc).isoformat(), **declaration})
    count = [0]
    def progress(event):
        count[0] += 1
        print(json.dumps({"completed_this_phase": count[0], **event}), flush=True)
    phases = {
        "prepare-main": lambda: ns["high_prepare_main"](root=args.root),
        "originals": lambda: ns["high_collect_originals"](root=args.root, live=args.live, progress=progress),
        "interventions": lambda: ns["high_run_interventions"](root=args.root, live=args.live, progress=progress),
    }
    result = phases[args.phase]()
    print(json.dumps({"phase": args.phase, "protocol": ns["HIGH_PROTOCOL"], "max_workers": 2,
        "selected_level": result["protocol"].get("selected_level"), "metrics": result.get("metrics"),
        "n_called_or_potential_cases": len(result["cases"])}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
