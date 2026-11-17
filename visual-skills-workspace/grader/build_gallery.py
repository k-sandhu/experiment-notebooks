#!/usr/bin/env python3
"""Build the gallery page: every test case with its two explainers side by side, live, plus scores.

usage: python build_gallery.py ITERATION_DIR OUT_DIR
Writes OUT_DIR/index.html and OUT_DIR/runs/<case>/{with,without}.html (copies of the explainers).
"""
import html
import json
import pathlib
import shutil
import sys

it = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2])
# PREV: earlier iteration folders, oldest first, separated by commas ("-" for none)
prevs = [pathlib.Path(p).resolve() for p in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[3] != "-" else []
showcase = pathlib.Path(sys.argv[4]).resolve() if len(sys.argv) > 4 else None
rnum = lambda p: int(p.name.split("-")[-1])
ROUND = rnum(it)
pkeys = {p: json.loads((p / "blind_key.json").read_text(encoding="utf-8")) if (p / "blind_key.json").exists() else {} for p in prevs}
prev = prevs[-1] if prevs else None
cases = json.loads((it.parent.parent / "visual-skills" / "evals" / "cases.json").read_text(encoding="utf-8"))
key = json.loads((it / "blind_key.json").read_text(encoding="utf-8")) if (it / "blind_key.json").exists() else {}

TITLES = {
    "guardrail-gates": ("Why a path check can be fooled", "Notebook 10 · a lesson for non-engineers"),
    "handoff-timelines": ("Who waited for whom", "Notebook 07 · replay of recorded agent runs"),
    "invoice-checks": ("When checking a cheap model pays off", "Econ 21 · an interactive for finance managers"),
    "sql-safety-units": ("Zero out of 29 is not proof", "Notebook 05 · a LinkedIn visual"),
    "forecast-guess": ("Beat “repeat last week”", "Notebook 16 · something engaging on forecasting"),
}
CRIT = ["message", "accuracy", "engagement", "craft", "fit"]
esc = html.escape


def load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


rows, sections = [], []
tot = {"with_skill": [0, 0], "without_skill": [0, 0]}
wins = {"with_skill": 0, "without_skill": 0, "tie": 0}
pwin_tot = {p: {"with_skill": 0, "without_skill": 0, "tie": 0} for p in prevs}
PICK = {'with_skill': 'With skills', 'without_skill': 'Without', 'tie': 'Tie', None: '–'}
for case in TITLES:
    if not (it / case).exists():
        continue
    (out / "runs" / case).mkdir(parents=True, exist_ok=True)
    g, t = {}, {}
    for cfg, short in (("with_skill", "with"), ("without_skill", "without")):
        page = it / case / cfg / "outputs" / "explainer.html"
        if page.exists():
            shutil.copy(page, out / "runs" / case / f"{short}.html")
        g[cfg] = load(it / case / cfg / "grading.json")
        t[cfg] = load(it / case / cfg / "timing.json")
        if g[cfg]:
            tot[cfg][0] += g[cfg]["summary"]["passed"]
            tot[cfg][1] += g[cfg]["summary"]["total"]
    v = load(it / "blind" / case / "verdict.json")
    k = key.get(case, {})
    label = {k.get("A"): "A", k.get("B"): "B"}
    vs = {}
    winner = None
    if v:
        for cfg in ("with_skill", "without_skill"):
            sc = v["scores"].get(label.get(cfg), {})
            vs[cfg] = sum(sc.get(c, 0) for c in CRIT)
        w = v.get("winner", "tie")
        winner = "tie" if w == "tie" else k.get(w)
        wins[winner or "tie"] += 1
    title, sub = TITLES[case]
    pwins, older = [], []
    for p in prevs:
        pv = load(p / "blind" / case / "verdict.json")
        pwin = None
        if pv:
            pw_ = pv.get("winner", "tie"); pwin = "tie" if pw_ == "tie" else pkeys[p].get(case, {}).get(pw_)
            pwin_tot[p][pwin or "tie"] += 1
        pwins.append(pwin)
        r = p / case / "with_skill" / "outputs" / "explainer.html"
        if r.exists():
            shutil.copy(r, out / "runs" / case / f"with_r{rnum(p)}.html")
            older.append(rnum(p))

    def checks(cfg):
        gg = g.get(cfg)
        if not gg:
            return "<p class='muted'>Not graded.</p>"
        items = "".join(f"<li class='{'ok' if e['passed'] else 'no'}'><span aria-hidden='true'>{'✓' if e['passed'] else '✗'}</span> {esc(e['text'])}"
                        + ("" if e["passed"] else f"<small>{esc(e['evidence'][:160])}</small>") + "</li>" for e in gg["expectations"])
        return f"<details><summary>{gg['summary']['passed']} of {gg['summary']['total']} automatic checks passed</summary><ul class='checks'>{items}</ul></details>"

    def review(cfg):
        if not v:
            return ""
        sc = v["scores"].get(label.get(cfg), {})
        cells = "".join(f"<span><b>{sc.get(c, '–')}</b>{c}</span>" for c in CRIT)
        defects = v.get("defects", {}).get(label.get(cfg), [])
        d = "".join(f"<li>{esc(x)}</li>" for x in defects[:3])
        return f"<div class='scores' aria-label='Blind review scores out of 5'>{cells}</div>" + (f"<ul class='defects'>{d}</ul>" if d else "")

    def mins(cfg):
        return f"{t[cfg]['total_duration_seconds'] / 60:.0f} min" if t.get(cfg) else "–"

    def col(cfg, short, name):
        badge = "<span class='win'>Reviewer's pick</span>" if winner == cfg else ""
        return f"""<div class="run">
  <div class="run-head"><h3>{name}</h3>{badge}<span class="muted">{mins(cfg)} to build</span></div>
  <div class="frame"><iframe src="runs/{case}/{short}.html" title="{esc(title)}, {name.lower()}" loading="lazy"></iframe></div>
  <div class="opens"><button type="button" class="open" data-src="runs/{case}/{short}.html" data-title="{esc(title)}, {name.lower()}">Open full size</button>{''.join(f'<button type="button" class="open" data-src="runs/{case}/with_r{n}.html" data-title="{esc(title)}, round {n} version with the skills">Round {n} version</button>' for n in older) if short == 'with' else ''}</div>
  {review(cfg)}
  {checks(cfg)}
</div>"""

    reason = f"<p class='reason'><b>Reviewer:</b> {esc(v['reason'])}</p>" if v else ""
    sections.append(f"""<section class="case" id="{case}">
  <p class="eyebrow">{esc(sub)}</p>
  <h2>{esc(title)}</h2>
  <blockquote>{esc(cases[case]['prompt'])}</blockquote>
  {reason}
  <div class="pair">{col('with_skill', 'with', 'With the skills')}{col('without_skill', 'without', 'Without the skills')}</div>
</section>""")
    gw, gwo = g.get("with_skill"), g.get("without_skill")
    rows.append(f"<tr><td><a href='#{case}'>{esc(title)}</a></td>"
                f"<td class='num'>{gw['summary']['passed'] if gw else '–'}/{gw['summary']['total'] if gw else '–'}</td>"
                f"<td class='num'>{gwo['summary']['passed'] if gwo else '–'}/{gwo['summary']['total'] if gwo else '–'}</td>"
                f"<td class='num'>{vs.get('with_skill', '–')}</td><td class='num'>{vs.get('without_skill', '–')}</td>"
                + "".join(f"<td>{PICK[x]}</td>" for x in pwins)
                + f"<td>{PICK[winner]}</td></tr>")

SKILLS = [
    ("explainer-director", "Finds the one message, picks the form, writes a storyboard with one idea per step."),
    ("explainer-kit", "Engine, four styles, scaffold, render check at phone and desktop widths, GIF/MP4 recorder."),
    ("stepper-lesson", "Khan Academy style lesson: Next, short captions, one or two steps the reader plays."),
    ("system-replay", "Recorded runs replayed on a timeline you can pause and scrub, or a designed walkthrough."),
    ("explorable-model", "A live model the reader steers with a slider; the break-even point is marked."),
    ("unit-story", "Every item is a dot; dots regroup by outcome; small samples show their uncertainty."),
    ("predict-reveal", "The reader commits a guess, then the real data animates in against it."),
]
skills_html = "".join(f"<li><code>{n}</code><span>{esc(d)}</span></li>" for n, d in SKILLS)
pw = lambda c: f"{tot[c][0]}/{tot[c][1]}"

SHOW = [
    ("31-self-repairing-scrapers", "Scrapers that repair themselves", "Notebook 31", "Replay"),
    ("27-adaptive-knowledge-rollouts", "When to stop repeating a task", "Notebook 27", "Explorable"),
    ("33-judge-exam", "Which models make reliable judges", "Notebook 33", "Every item a dot"),
    ("41-direct-weight-mlps", "A classifier written as plain numbers", "Notebook 41", "Guess, then reveal"),
    ("28-monitor-removal-honesty", "Does an agent admit removing its monitor?", "Notebook 28", "Lesson"),
    ("29-theory-of-mind", "Who saw the change?", "Notebook 29", "Lesson with predictions"),
    ("12-tax-research-harnesses", "Do extra steps fix tax workpapers?", "Notebook 12", "Harness walkthrough"),
    ("08-lab-requisition-extraction", "Reading paper lab orders", "Notebook 08", "Every item a dot"),
]
show_html = ""
if showcase:
    cards = []
    for nb, ttl, src, form in SHOW:
        d = showcase / nb
        if not (d / "explainer.html").exists():
            continue
        (out / "runs" / "showcase" / nb).mkdir(parents=True, exist_ok=True)
        shutil.copy(d / "explainer.html", out / "runs" / "showcase" / nb / "index.html")
        img = ""
        if (d / "card.png").exists():
            shutil.copy(d / "card.png", out / "runs" / "showcase" / nb / "card.png")
            img = f"<img src='runs/showcase/{nb}/card.png' alt='{esc(ttl)}: a frame from the explainer' loading='lazy'>"
        cards.append(f"<button type='button' class='card open' data-src='runs/showcase/{nb}/index.html' data-title='{esc(ttl)}'>{img}<span class='eyebrow'>{esc(src)} · {esc(form)}</span><b>{esc(ttl)}</b><span class='muted'>Open</span></button>")
    if cards:
        show_html = f"""<section aria-labelledby="more"><h2 id="more">More experiments</h2>
<p class="muted" style="max-width:72ch;margin-bottom:16px">Eight more notebooks, each built once with the revised skills from the notebook's README and data, with no human edits. Tap a card to open it full size.</p>
<div class="cards">{''.join(cards)}</div></section>
"""

viewer_js = r"""<script>
(function () {
  const v = document.getElementById('viewer'), fr = document.getElementById('viewer-frame'), t = document.getElementById('viewer-title'), x = document.getElementById('viewer-close');
  let back = null;
  function open(src, title, from) { back = from; t.textContent = title; fr.src = src; v.hidden = false; document.body.style.overflow = 'hidden'; x.focus(); }
  function close() { v.hidden = true; fr.src = 'about:blank'; document.body.style.overflow = ''; if (back) back.focus(); }
  document.addEventListener('click', e => { const b = e.target.closest('button.open'); if (b) open(b.dataset.src, b.dataset.title, b); });
  x.addEventListener('click', close);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !v.hidden) close(); });
})();
</script>"""
page = f"""<title>Explainer Skills Lab</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Caveat:wght@600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap">
<style>
/* Layout: one reading column for the story, widening to a two-up comparison for each test case. */
:root {{
  --bg: #F6F5F1; --panel: #FFFFFF; --ink: #1D2125; --muted: #5E646B; --line: #DAD8D0;
  --accent: #6A4FC2; --good: #1E7F55; --bad: #B4472F; --chalk: #1E2023;
  --hand: 'Caveat', cursive; --sans: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; --mono: 'JetBrains Mono', ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #15171A; --panel: #1E2124; --ink: #ECE9E1; --muted: #A2A69F; --line: #34383D; --accent: #B9A5F0; --good: #67C79A; --bad: #EE8E78; --chalk: #0F1012; color-scheme: dark }} }}
:root[data-theme="dark"] {{ --bg: #15171A; --panel: #1E2124; --ink: #ECE9E1; --muted: #A2A69F; --line: #34383D; --accent: #B9A5F0; --good: #67C79A; --bad: #EE8E78; --chalk: #0F1012; color-scheme: dark }}
body {{ background: var(--bg); color: var(--ink); font: 15px/1.6 var(--sans); padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 28px 64px }}
main {{ max-width: 1120px; margin: 0 auto; display: grid; gap: 56px }}
main > * {{ min-width: 0 }}
.intro {{ max-width: 68ch; display: grid; gap: 12px }}
h1 {{ font: 600 clamp(40px, 7vw, 64px)/1 var(--hand); margin: 0; text-wrap: balance }}
h2 {{ font: 600 clamp(30px, 4.5vw, 40px)/1.05 var(--hand); margin: 0 0 8px; text-wrap: balance }}
h3 {{ font: 600 15px/1.3 var(--sans); margin: 0 }}
p {{ margin: 0 }}
.muted, small {{ color: var(--muted) }}
.eyebrow {{ font: 500 12px/1.3 var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px }}
code {{ font: 500 13px var(--mono) }}
.skills {{ list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 330px), 1fr)); gap: 2px 28px }}
.skills li {{ display: grid; gap: 2px; padding: 10px 0; border-top: 1px solid var(--line) }}
.skills code {{ color: var(--accent) }}
.tbl {{ overflow-x: auto }}
table {{ border-collapse: collapse; width: 100%; min-width: 560px; font-size: 14px }}
th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top }}
th {{ font-weight: 600; font-size: 12.5px; color: var(--muted) }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums }}
tfoot td {{ font-weight: 600 }}
a {{ color: var(--accent) }}
blockquote {{ margin: 8px 0 12px; padding: 10px 14px; border-left: 3px solid var(--line); color: var(--muted); max-width: 80ch }}
.reason {{ max-width: 80ch; margin-bottom: 16px }}
.pair {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr)); gap: 24px }}
.run {{ display: grid; gap: 10px; min-width: 0; align-content: start }}
.run-head {{ display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap }}
.win {{ font-size: 12px; font-weight: 600; color: var(--good); border: 1px solid currentColor; border-radius: 999px; padding: 1px 8px }}
.frame {{ background: var(--chalk); border-radius: 14px; overflow: hidden; border: 1px solid var(--line) }}
iframe {{ display: block; width: 100%; height: 820px; border: 0; background: #fff }}
.opens {{ display: flex; gap: 8px; flex-wrap: wrap }}
button.open {{ font: 500 13px var(--sans); color: var(--accent); background: none; border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; cursor: pointer }}
button.open:hover {{ border-color: var(--accent) }}
.card.open {{ font: inherit; text-align: left; padding: 10px 10px 12px; cursor: pointer; color: var(--ink) }}
.viewer {{ position: fixed; inset: 0; z-index: 50; background: var(--bg); display: grid; grid-template-rows: auto 1fr; padding: calc(env(safe-area-inset-top, 0px) + 10px) max(12px, env(safe-area-inset-right, 0px)) calc(env(safe-area-inset-bottom, 0px) + 10px) max(12px, env(safe-area-inset-left, 0px)); gap: 8px }}
.viewer[hidden] {{ display: none }}
.viewer-bar {{ display: flex; align-items: center; gap: 12px; justify-content: space-between; max-width: 620px; width: 100%; margin: 0 auto }}
.viewer-bar b {{ font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0 }}
.viewer-bar button {{ font: 600 14px var(--sans); background: var(--panel); color: var(--ink); border: 1px solid var(--line); border-radius: 8px; padding: 8px 14px; cursor: pointer }}
.viewer iframe {{ width: 100%; max-width: 620px; height: 100%; margin: 0 auto; border-radius: 14px; border: 1px solid var(--line) }}
.scores {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; font-size: 11.5px; color: var(--muted); text-align: center }}
.scores span {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 6px 2px }}
.scores b {{ display: block; font-size: 18px; color: var(--ink); font-variant-numeric: tabular-nums }}
.defects {{ margin: 0; padding-left: 18px; font-size: 13px; color: var(--muted) }}
details {{ font-size: 13.5px }}
summary {{ cursor: pointer; color: var(--ink) }}
.checks {{ list-style: none; padding: 0; margin: 8px 0 0; display: grid; gap: 4px }}
.checks .ok span {{ color: var(--good) }} .checks .no span {{ color: var(--bad) }}
.checks small {{ display: block; margin-left: 18px }}
.note {{ max-width: 72ch; display: grid; gap: 10px }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 18px }}
.card {{ display: grid; gap: 6px; align-content: start; text-decoration: none; color: var(--ink); background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 10px 10px 12px }}
.card:hover {{ border-color: var(--accent) }}
.card img {{ width: 100%; aspect-ratio: 3 / 4; object-fit: cover; object-position: top; border-radius: 8px; background: var(--chalk) }}
.card .eyebrow {{ margin: 4px 0 0 }}
:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px }}
</style>
<main>
<header class="intro">
  <p class="eyebrow">Experiment notebooks · visual explainer skills</p>
  <h1>Explainer Skills Lab</h1>
  <p>Seven agent skills for turning a finding, a process or a dataset into an animated, interactive explainer that a newcomer can follow on a phone. They grew out of the chalkboard animations of an agentic finance harness and a lesson on deep work versus parallel agents.</p>
  <p>To test them, the same model built five explainers from this repository's experiment data with the skills and without them, and a separate model compared each pair blind. After each round, the reviews' complaints went into the skills and the five were rebuilt, always against the same versions made without the skills. Round 3 and the no-skills versions are live below, side by side, with the round-1 and round-2 versions one click away. Eight more notebooks built with the skills follow.</p>
</header>

<section aria-labelledby="sk"><h2 id="sk">The skills</h2><ul class="skills">{skills_html}</ul></section>

<section aria-labelledby="res"><h2 id="res">Results</h2>
<div class="tbl"><table>
<thead><tr><th>Test case</th><th class="num">Checks, with (round {ROUND})</th><th class="num">Checks, without</th><th class="num">Review score, with</th><th class="num">Review score, without</th>{''.join(f'<th>Pick, round {rnum(p)}</th>' for p in prevs)}<th>Pick, round {ROUND}</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
<tfoot><tr><td>All five</td><td class="num">{pw('with_skill')}</td><td class="num">{pw('without_skill')}</td><td></td><td></td>{''.join(f"<td>With {pwin_tot[p]['with_skill']}, without {pwin_tot[p]['without_skill']}</td>" for p in prevs)}<td>With {wins['with_skill']}, without {wins['without_skill']}{f", tie {wins['tie']}" if wins['tie'] else ''}</td></tr></tfoot>
</table></div>
<p class="muted" style="margin-top:10px;max-width:80ch">Automatic checks render each page at 360 px and 560 px and look for errors, sideways scrolling, overlapping or tiny text, controls that move, and the case's key numbers on screen. The review score is the sum of five 1-to-5 ratings (message, accuracy, engagement, craft, fit) from a separate model that saw both versions unlabelled and used them in a browser.</p>
</section>

{''.join(sections)}

{show_html}<section class="note" aria-labelledby="chg"><h2 id="chg">What three rounds of reviews taught</h2>
<p>Across three rounds the version with the skills won 8 of the 15 blind comparisons (3, 2, then 3 of 5). Its summed review score was higher in every round: 110 to 105, 109 to 103, then 112 to 100 out of 125. The skills made layout reliable: 54 of 55 automatic checks passed in each round with them, against 48 of 55 without. The replay and the forecast won all three rounds; the guardrail lesson and the SQL card lost all three.</p>
<p>The round-2 changes, tested in round 3:</p>
<ul>
<li>Outcome in the reader's units. Worked: the invoice explorable now gives a monthly bill at a volume the reader picks, and it won back the case (24 to 19).</li>
<li>Text size, legends, no internal names. Worked: no tiny-text failures with the skills in any case, and the reviewers no longer flagged run names.</li>
<li>End with the test's limits. Followed, but the SQL case still lost by one point. The reviewer preferred the other version's fixed-size card for a LinkedIn post and its note that the models still answered ordinary questions, which shows the clean scores were not refusals.</li>
<li>Question steps mark the reader's answer. Only half followed: the guardrail lesson now waits for the guess, but its feedback reads the same whatever the reader picks, and it packs four tricks into one auto-playing step where the other version gives each trick its own guess.</li>
</ul>
</section>

<section class="note" aria-labelledby="lim"><h2 id="lim">How far to trust this</h2>
<p>Each case was built once per condition in each round, and all three rounds reused the same no-skills versions, so the 8-of-15 result could easily swing either way with more runs. The reviewer is also a model, and it scored the same no-skills page differently from round to round (the invoice page got 21, 21, then 19), so differences of one or two points are noise. Read the comparison as a map of what the skills change, not a measurement of how much.</p>
<p>The skill files contain no data or wording from the five test notebooks, so the runs with skills could not copy an answer. The pages here are copies of each run's output, unedited.</p>
</section>
</main>
<div class="viewer" id="viewer" hidden role="dialog" aria-modal="true" aria-labelledby="viewer-title">
  <div class="viewer-bar"><b id="viewer-title"></b><button type="button" id="viewer-close">Close</button></div>
  <iframe id="viewer-frame" title="Explainer, full size"></iframe>
</div>
{viewer_js}
"""
out.mkdir(parents=True, exist_ok=True)
(out / "index.html").write_text(page, encoding="utf-8")
print(f"wrote {out / 'index.html'}; checks with {pw('with_skill')}, without {pw('without_skill')}; wins {wins}")
