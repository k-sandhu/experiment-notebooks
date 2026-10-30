"""Explicit v4 phases. Offline replay is the default; no phase auto-chains."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare-pilot", "pilot", "prepare-main", "originals", "interventions"])
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent / "experiment_notebooks" / "notebooks" / "23-synthetic-data-curation")
    args = parser.parse_args()
    if args.live and args.phase.startswith("prepare"):
        parser.error("Preparation never invokes a model; omit --live")
    namespace = {"__name__": "high_notebook_helpers"}
    source = Path(__file__).resolve().parent
    for filename in ("high_transport.py", "high_fixtures.py", "high_material_audit.py", "high_experiment.py"):
        exec(compile((source / filename).read_text(encoding="utf-8"), filename, "exec"), namespace)
    count = [0]
    def progress(event):
        count[0] += 1
        print(json.dumps({"completed_this_phase": count[0], **event}), flush=True)
    dispatch = {
        "prepare-pilot": lambda: namespace["high_prepare_pilot"](root=args.root),
        "pilot": lambda: namespace["high_run_pilot"](root=args.root, live=args.live, progress=progress),
        "prepare-main": lambda: namespace["high_prepare_main"](root=args.root),
        "originals": lambda: namespace["high_collect_originals"](root=args.root, live=args.live, progress=progress),
        "interventions": lambda: namespace["high_run_interventions"](root=args.root, live=args.live, progress=progress),
    }
    result = dispatch[args.phase]()
    output = {"phase": args.phase, "root": str(args.root), "live": args.live,
        "selected_level": result.get("selected_level", result.get("protocol", {}).get("selected_level")),
        "threshold_met": result.get("threshold_met"), "metrics": result.get("metrics"),
        "n_potential_cases": len(result.get("cases", []))}
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
