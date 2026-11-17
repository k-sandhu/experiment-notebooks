#!/usr/bin/env python3
"""Grade every run in an iteration folder: render it, then check the assertions for its case.

usage: python grade.py ITERATION_DIR [--only CASE] [--skip-render]
Writes <run>/qa/report.json (render check) and <run>/grading.json (assertions, viewer format).
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent

COMMON = [
    ("explainer.html opens without console errors or uncaught exceptions at 360 px and 560 px", "errors"),
    ("At 360 px wide the page never scrolls sideways", "overflow_x"),
    ("No visible text overlaps other text in any captured step at 360 px", "text_overlap"),
    ("No text renders smaller than 9.5 px at 360 px", "tiny_text"),
    ("No SVG text sticks out of its drawing area", "text_outside"),
    ("Navigation controls stay in the same place across steps", "controls_moved"),
    ("With reduced motion every step renders without errors or blank frames", "reduced_motion"),
]

# (assertion text, kind, pattern-or-threshold)
CASES = {
    "guardrail-gates": [
        ("The lesson has at least 4 steps the reader moves through", "steps", 4),
        ("States that the prefix-only gate let 5 of 14 forbidden requests through", "regex", r"\b5\s*(of|/|out of)\s*14\b"),
        ("States that a resolving gate let 0 of 14 forbidden requests through", "regex", r"\b0\s*(of|/|out of)\s*14\b"),
        ("The reader can do something beyond Next/Back (try a path, pick a case)", "interactive", 1),
    ],
    "handoff-timelines": [
        ("Shows the synchronous handoff's wall time of about 120 s", "regex", r"\b120(\.\d+)?\s*(s\b|sec)|\b2:00\b|\b2 min"),
        ("Shows the async spawn's wall time of about 57 s", "regex", r"\b56\.8\d*\s*s?|\b57(\.\d)?\s*(s\b|sec)"),
        ("Points out the late message that was never read", "regex", r"too late|never read|unread|arrived late|after .{0,30}(finished|done)"),
        ("The reader can pause, replay or scrub the animation", "regex_ui", r"pause|replay|scrub|restart|play"),
    ],
    "invoice-checks": [
        ("Has a control that sets the expensive model's price", "input", 1),
        ("Shows the Claude-check break-even price of about USD 0.133", "regex", r"0\.13\d*|13(\.3\d*)?\s*(¢|cents)"),
        ("Shows the repeat-check break-even price of about USD 0.0011", "regex", r"0\.0011\d*|0\.11\s*(¢|cents)|0\.1\s*(¢|cent)"),
        ("Makes concrete that the checks accepted 14 of the 72 invoices", "regex", r"\b14\s*(of|/|out of)\s*(the\s*)?72\b"),
    ],
    "sql-safety-units": [
        ("Shows Mistral Small 4 breaking the rules on 7 of 29 requests", "regex", r"\b7\s*(of|/|out of)\s*29\b"),
        ("States that 0 of 29 still allows a true rate up to about 12%", "regex", r"\b1[12](\.\d)?\s*%"),
        ("Draws the requests as individual marks (at least 300 marks for 11 x 29 requests)", "marks", 300),
        ("Names Gemma 4 31B's 3 of 29", "regex", r"\b3\s*(of|/|out of)\s*29\b"),
    ],
    "forecast-guess": [
        ("Reports the best pretrained models' relative error of about 0.86 (about 14% below repeating last week)", "regex", r"0\.86\d*|\b14\s*%"),
        ("Names the repeat-last-week baseline in words", "regex", r"last week|seasonal naive|same week"),
        ("The reader can interact beyond Next/Back (guess, toggle, scrub or pick)", "interactive", 1),
        ("Says that one example week is not the whole result (mentions the 112 origins or all series)", "regex", r"\b112\b|all (six )?series|across .{0,40}(origins|forecasts|weeks)"),
    ],
}


def render(run, page):
    qa = run / "qa"
    cmd = [sys.executable, str(HERE / "render_check.py"), str(page), "--out", str(qa), "--widths", "360,560", "--max-steps", "14"]
    subprocess.run(cmd, capture_output=True, text=True, timeout=1500)
    rp = qa / "report.json"
    return json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else None


def grade(case, run, rep, html_text):
    exp = []
    res = rep["results"] if rep else []
    runs = rep["runs"] if rep else []
    for text, check in COMMON:
        hits = [r for r in res if r["check"] == check]
        if check == "text_overlap" or check == "tiny_text":
            hits = [h for h in hits if h["detail"].startswith("360px")]
        ok = rep is not None and not hits
        exp.append({"text": text, "passed": ok, "evidence": "no findings" if ok else (hits[0]["detail"][:300] if hits else "page did not render")})
    probes = [p for r in runs if not r["rm"] for p in r["probes"]]
    alltext = " ".join(p.get("alltext", "") for p in probes)
    info = runs[0]["info"] if runs else None
    nsteps = info["count"] if info else max((len(r["probes"]) for r in runs if not r["rm"]), default=0)
    for text, kind, arg in CASES[case]:
        if kind == "steps":
            ok, ev = nsteps >= arg, f"{nsteps} steps/views detected"
        elif kind in ("regex", "regex_ui"):
            m = re.search(arg, alltext, re.I)
            if m:
                ok, ev = True, f"visible text: ...{alltext[max(0, m.start() - 60):m.end() + 40]}..."
            else:
                src = re.sub(r"<[^>]+>", " ", html_text)
                m2 = re.search(arg, src, re.I) if kind == "regex" else None
                ok = bool(m2)
                ev = f"not in captured text; in page source: ...{src[max(0, m2.start() - 60):m2.end() + 40]}..." if m2 else "not found in captured text or page source"
                if kind == "regex_ui" and not ok:
                    ui = re.search(r"<(button|input)[^>]*>([^<]*)", html_text, re.I)
                    ok = bool(re.search(r"type=.range|pause|replay|restart", html_text, re.I))
                    ev = "found a range input or pause/replay control in the page source" if ok else ev
        elif kind == "interactive":
            n = max((p.get("interactive", 0) for p in probes), default=0)
            ok, ev = n >= arg, f"max {n} interactive elements beyond navigation in a captured step"
        elif kind == "input":
            ok = bool(re.search(r"<input[^>]*type=[\"']?(range|number)|K\.slider\(|type\s*=\s*[\"']range", html_text, re.I))
            ev = "range/number input or K.slider found in page" if ok else "no price control found"
        elif kind == "marks":
            n = max((p.get("marks", 0) for p in probes), default=0)
            ok, ev = n >= arg, f"max {n} circle/rect/small-box marks in a captured step"
        exp.append({"text": text, "passed": bool(ok), "evidence": ev[:400]})
    passed = sum(e["passed"] for e in exp)
    return {"expectations": exp, "summary": {"passed": passed, "failed": len(exp) - passed, "total": len(exp), "pass_rate": round(passed / len(exp), 3)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iteration")
    ap.add_argument("--only")
    ap.add_argument("--config")
    ap.add_argument("--skip-render", action="store_true")
    a = ap.parse_args()
    it = pathlib.Path(a.iteration)
    for case_dir in sorted(p for p in it.iterdir() if p.is_dir() and p.name in CASES):
        if a.only and case_dir.name != a.only:
            continue
        for run in sorted(p for p in case_dir.iterdir() if p.is_dir() and p.name in ("with_skill", "without_skill", "old_skill")):
            if a.config and run.name != a.config:
                continue
            page = run / "outputs" / "explainer.html"
            if not page.exists():
                g = {"expectations": [{"text": "explainer.html exists", "passed": False, "evidence": "missing"}], "summary": {"passed": 0, "failed": 1, "total": 1, "pass_rate": 0}}
            else:
                rep = json.loads((run / "qa" / "report.json").read_text(encoding="utf-8")) if a.skip_render and (run / "qa" / "report.json").exists() else render(run, page)
                g = grade(case_dir.name, run, rep, page.read_text(encoding="utf-8", errors="replace"))
            (run / "grading.json").write_text(json.dumps(g, indent=1), encoding="utf-8")
            print(f"{case_dir.name:18} {run.name:14} {g['summary']['passed']}/{g['summary']['total']}")


if __name__ == "__main__":
    main()
