#!/usr/bin/env python3
"""Copy each case's two runs into blind A/B folders for a side-by-side review.

Only what a reader would see goes in: the HTML page and the contact sheets. notes.md is left out,
and the mapping from A/B to configuration is written to a separate key file the reviewer never sees.
usage: python blind_prep.py ITERATION_DIR
"""
import json
import pathlib
import shutil
import sys

it = pathlib.Path(sys.argv[1])
blind = it / "blind"
blind.mkdir(exist_ok=True)
key = {}
flip = {"guardrail-gates": False, "handoff-timelines": True, "invoice-checks": False, "sql-safety-units": True, "forecast-guess": False}
for case, swap in flip.items():
    order = ["without_skill", "with_skill"] if swap else ["with_skill", "without_skill"]
    key[case] = {"A": order[0], "B": order[1]}
    for label, cfg in zip("AB", order):
        src = it / case / cfg
        dst = blind / case / label
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        page = src / "outputs" / "explainer.html"
        if page.exists():
            shutil.copy(page, dst / "explainer.html")
        for sheet in (src / "qa").glob("sheet_w*.png"):
            if "_rm" not in sheet.name:
                shutil.copy(sheet, dst / sheet.name)
        # copy each run's phone contact sheet into its outputs so the eval viewer shows it as an image
        s360 = src / "qa" / "sheet_w360.png"
        if s360.exists():
            shutil.copy(s360, src / "outputs" / "contact_sheet_360px.png")
(it / "blind_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
print(json.dumps(key, indent=1))
