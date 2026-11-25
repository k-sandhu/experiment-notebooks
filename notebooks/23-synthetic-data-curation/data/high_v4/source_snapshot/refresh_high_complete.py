"""Stage a healthy-run section-13 replacement. Never edit notebooks or READMEs."""
from pathlib import Path
import hashlib
import os


AUTHORING = Path(__file__).resolve().parent
REPO_ROOT = Path(os.environ.get("NOTEBOOK_REPO_ROOT", r"C:\Users\sandh\.codex\worktrees\synthetic-data-curation\experiment_notebooks"))
NOTEBOOK_DIRECTORY = Path("notebooks/23-synthetic-data-curation")
HIGH_COMPLETE_DEPENDENCIES = ["high_transport.py", "high_fixtures.py", "high_material_audit.py",
                              "high_experiment.py", "high_reporting.py", "high_complete_reporting.py"]


def _high_complete_namespace():
    namespace = {"__name__": "notebook_23_high_complete_builder"}
    for filename in HIGH_COMPLETE_DEPENDENCIES:
        source = (AUTHORING / filename).read_text(encoding="utf-8-sig")
        exec(compile(source, filename, "exec"), namespace)
    return namespace


def _high_complete_cell(source, kind="markdown"):
    cell = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True),
            "id": "high-complete-" + hashlib.sha256(source.encode()).hexdigest()[:14]}
    if kind == "code":
        cell.update(execution_count=None, outputs=[])
    return cell


HIGH_COMPLETE_REPLAY_CODE = '''# Presentation only: no live calls or cache replay engine.
HIGH_COMPLETE_ROOT = Path.cwd()
HIGH_COMPLETE_OFFLINE = True
if not HIGH_COMPLETE_OFFLINE:
    raise RuntimeError("This posthoc report is read-only; live collection is a separate reviewed operation.")
HIGH_COMPLETE_REPORT = high_complete_load(HIGH_COMPLETE_ROOT)
HIGH_COMPLETE_TEXT = high_complete_render(HIGH_COMPLETE_REPORT)
HIGH_COMPLETE_FIGURES = high_complete_plot_report(HIGH_COMPLETE_REPORT, root=HIGH_COMPLETE_ROOT, write=True)
print("Report state:", HIGH_COMPLETE_REPORT["state"])
print("Headline:", HIGH_COMPLETE_TEXT["headline"])
print("Examples:", HIGH_COMPLETE_TEXT["example_case_ids"])
print("Absent observed categories:", HIGH_COMPLETE_TEXT["absent_categories"])
print("Figures:", [row["path"] for row in HIGH_COMPLETE_FIGURES])
if HIGH_COMPLETE_REPORT["state"] == "complete":
    print("Paired value outcomes:", HIGH_COMPLETE_REPORT["metrics"]["paired_value_recovery"])
else:
    print("Main is incomplete. No final paired recovery or accuracy difference is claimed.")
'''


def build(root=REPO_ROOT, write=False):
    """Return narrative, report and embed cells. write=True saves new figures only."""
    root = Path(root)
    notebook_dir = root / NOTEBOOK_DIRECTORY
    namespace = _high_complete_namespace()
    report = namespace["high_complete_load"](notebook_dir)
    rendered = namespace["high_complete_render"](report)
    figures = namespace["high_complete_plot_report"](report, root=notebook_dir, write=write)
    figure_metadata = [{k: v for k, v in row.items() if k != "figure"} for row in figures]
    if not write:
        import matplotlib.pyplot as plt
        for row in figures:
            plt.close(row["figure"])
    helper = (AUTHORING / "high_complete_reporting.py").read_text(encoding="utf-8-sig")
    cells = [_high_complete_cell(rendered["markdown"]),
             _high_complete_cell("### Embedded healthy-run posthoc reporting helper\n\n"
                                 "The four frozen core helpers and existing offline high_reporting helper remain unchanged. "
                                 "This additional helper reads saved source/response artifacts only. It does not invoke the live or replay engine."),
             _high_complete_cell(helper, "code"),
             _high_complete_cell("### Rebuild healthy-run figures and tables offline\n\n"
                                 "Incomplete caches remain recorded observations. This cell never resumes a request. "
                                 "Until the final manifest exists, it draws a pending notice instead of fabricated recovery bars."),
             _high_complete_cell(HIGH_COMPLETE_REPLAY_CODE, "code")]
    return {**rendered, "report": report, "helper_source": helper, "replay_code": HIGH_COMPLETE_REPLAY_CODE,
            "cells": cells, "figures": figure_metadata, "figures_written": write,
            "notebook_written": False, "readme_written": False,
            "helper_path": AUTHORING / "high_complete_reporting.py",
            "builder_path": AUTHORING / "refresh_high_complete.py"}


def refresh(root=REPO_ROOT, write=False):
    return build(root=root, write=write)


if __name__ == "__main__":
    raise SystemExit("Import refresh_high_complete.build; it never edits notebook/README and writes figures only when write=True.")

