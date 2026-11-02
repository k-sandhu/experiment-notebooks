"""Stage a v5 section body. No notebook/README edits and no live execution."""
from pathlib import Path
import hashlib
import os

AUTHORING=Path(__file__).resolve().parent
_PORTABLE_NOTEBOOK_ROOT=AUTHORING.parents[2]
_DEFAULT_ROOT=(_PORTABLE_NOTEBOOK_ROOT if (_PORTABLE_NOTEBOOK_ROOT/"data"/"scale_v5"/"main"/"protocol.json").is_file()
               else Path(r"C:\Users\sandh\.codex\worktrees\synthetic-data-curation\experiment_notebooks"))
REPO_ROOT=Path(os.environ.get("NOTEBOOK_REPO_ROOT",str(_DEFAULT_ROOT)))
NOTEBOOK_DIRECTORY=Path("notebooks/23-synthetic-data-curation")

SCALE_REPORT_REPLAY_CODE='# Posthoc reading only. No engine-phase replay and no model calls.\nSCALE_REPORT_OFFLINE = True\nif not SCALE_REPORT_OFFLINE:\n    raise RuntimeError("Live collection is a separate preregistered operation.")\nSCALE_REPORT = scale_report_load(Path.cwd())\nSCALE_REPORT_TEXT = scale_report_render(SCALE_REPORT)\nSCALE_REPORT_ANALYSIS_PATH = scale_report_save_analysis(SCALE_REPORT, root=Path.cwd())\nSCALE_REPORT_FIGURES = scale_report_figures(SCALE_REPORT, root=Path.cwd(), write=True)\nprint("State:", SCALE_REPORT_TEXT["state"])\nprint("Headline:", SCALE_REPORT_TEXT["headline"])\nprint("Pending reason:", SCALE_REPORT_TEXT["pending_reason"])\nprint("Worked case IDs:", SCALE_REPORT_TEXT["example_case_ids"])\nprint("Missing-outcome analysis:", SCALE_REPORT_ANALYSIS_PATH)\nprint("New figures:", [r["path"] for r in SCALE_REPORT_FIGURES])\n'


def scale_report_namespace(notebook_root):
    snapshot=Path(notebook_root)/"data"/"scale_v5"/"source_snapshot"
    namespace={"__name__":"notebook23_scale_posthoc"}
    # Frozen snapshot first. These definitions do not make calls or replay phases.
    for name in ("scale_transport.py", "scale_fixtures.py", "scale_parallel.py", "scale_experiment.py"):
        source=(snapshot/name).read_text(encoding="utf-8-sig")
        exec(compile(source,name,"exec"),namespace)
    embedded={name:(snapshot/name).read_text(encoding="utf-8-sig") for name in namespace["SCALE_CORE_SHA256"]}
    namespace["scale_load_cores"](core_sources=embedded)
    helper=(AUTHORING/"scale_missing_outcomes_003.py").read_text(encoding="utf-8-sig")+"\n\n"+(AUTHORING/"scale_reporting.py").read_text(encoding="utf-8-sig")
    exec(compile(helper,"scale_reporting.py","exec"),namespace)
    return namespace,helper


def build(root=REPO_ROOT,write=False):
    root=Path(root)
    notebook_root=root if (root/"data"/"scale_v5").is_dir() else root/NOTEBOOK_DIRECTORY
    namespace,helper=scale_report_namespace(notebook_root)
    report=namespace["scale_report_load"](notebook_root)
    rendered=namespace["scale_report_render"](report)
    analysis_path=namespace["scale_report_save_analysis"](report, root=notebook_root) if write else None
    figures=namespace["scale_report_figures"](report,root=notebook_root,write=True) if write and report["state"]=="complete" else rendered["figures"]
    def cell(source,kind):
        item={"cell_type":kind,"metadata":{},"source":source.splitlines(keepends=True),
              "id":"scale-posthoc-"+hashlib.sha256(source.encode()).hexdigest()[:14]}
        if kind=="code":item.update(execution_count=None,outputs=[])
        return item
    return {**rendered,"report":report,"helper_source":helper,"replay_code":SCALE_REPORT_REPLAY_CODE,
            "figures":figures,"notebook_root":str(notebook_root),"analysis_path":analysis_path,
            "cells":[cell(rendered["markdown"],"markdown"),cell(helper,"code"),cell(SCALE_REPORT_REPLAY_CODE,"code")]}


if __name__=="__main__":
    result=build()
    print(result["state"])
    print(result["headline"])
    print(result["pending_reason"])
