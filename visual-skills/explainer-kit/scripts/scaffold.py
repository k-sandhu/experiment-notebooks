#!/usr/bin/env python3
"""Start a new explainer as one self-contained HTML file with explainer-kit already inlined.

The model then edits only the SCENE block at the bottom. Nothing is fetched at run time except
an optional Google Font, so the file works as a local page, a published artifact or a GIF source.

usage:
  python scaffold.py OUT.html --kind stepper|player|explorable|figure [--style chalkboard|paper|editorial|blueprint]
                     [--controls full|minimal|none] [--data DATA.json] [--theme THEME.json [--force]]
                     [--title "Short name"] [--fragment] [--viewbox 380x300]

--kind figure is one standalone view with no steps: a drawing, optional live controls and an
optional looping animation with a pause button. Use it for a figure inside an article.

--controls sets how much navigation the reader gets: full (default for stepper and player), minimal
(Back and Next, or play and scrub), none (plays by itself with only a pause button; default for figure).

--data embeds a JSON file as `const DATA = {...}` at the top of the scene, unchanged, so numbers are
never retyped by hand. Compute everything on screen from DATA.

--theme uses your own colours and fonts instead of a built-in style (format in references/themes.md).
The theme is checked first with check_theme.py; a failing theme is refused unless --force is given.

--fragment writes a widget fragment (no <html>/<head>/<body>) for chat surfaces that render
HTML snippets inline, such as a chat app's widget tool.
"""
import argparse
import json
import pathlib
import sys
for _s in (sys.stdout, sys.stderr):   # report lines contain arrows and quotes; a Windows console or pipe may not take them
    try: _s.reconfigure(errors='replace')
    except AttributeError: pass

HERE = pathlib.Path(__file__).resolve().parent
KIT = (HERE.parent / "assets" / "kit.js").read_text(encoding="utf-8")

PAGE_BG = {"chalkboard": "#141517", "paper": "#EFE9DC", "editorial": "#F2F2EE", "blueprint": "#0A1826"}
DARK = {"chalkboard": True, "paper": False, "editorial": False, "blueprint": True}

SCENES = {
    "stepper": r"""
const {P, T, F, line, rect, ellipse, arrow, curve, poly, C} = K;
// Coordinates are viewBox units. Keep text >= 14 units (about 11 px on a 360 px phone) and inside the box.
K.stepper({
  root: '#x', style: __STYLE__, viewBox: [__W__, __H__],
  title: 'One sentence that describes the whole lesson for screen readers.',
  legend: [  // one entry per colour meaning, used the same way in every step
    {key: 'you', label: 'You', color: 'amber'},
    {key: 'work', label: 'Work done', color: 'blue'},
  ],
  // The opening, for a reader who knows nothing about the subject: the everyday situation, who is in it,
  // why it matters and the question. No numbers, no product names. Shown first, as "Start here".
  intro: { title: 'What this is about', start: 'Start',
    cap: 'One concrete situation in plain words, why someone would care, and the question this answers.',
    alt: 'What the opening drawing shows.',
    draw: () =>
      P(rect(40, 90, 120, 70, 11), 'amber', 0, 600) + T(100, 130, 'A person', {h: 1, z: 20, c: 'amber', t: 300}) +
      P(line(170, 125, 220, 125, 12), 'mut', 700, 300) + P(arrow(170, 125, 220, 125, 13), 'mut', 1000, 150) +
      P(rect(230, 90, 120, 70, 14), 'blue', 1100, 600) + T(290, 130, 'The job', {h: 1, z: 20, c: 'blue', t: 1400}) +
      T(190, 230, 'The question, in plain words?', {h: 1, z: 22, t: 1900}) },
  steps: [
    { title: '1. The ordinary case', keys: ['you', 'work'],
      cap: 'One or two sentences that say what this step shows and what to watch for.',
      draw: () =>
        T(20, 40, 'Heading for this idea', {h: 1, z: 24, a: 'start'}) +
        P(rect(40, 90, 130, 70, 1), 'blue', 300, 700) +
        T(105, 130, 'A box', {h: 1, z: 18, t: 800}) +
        P(line(180, 125, 250, 125, 2), 'mut', 1100, 400) + P(arrow(180, 125, 250, 125, 3), 'mut', 1450, 150) +
        `<rect id="bar" x="40" y="200" width="300" height="14" rx="2" fill="${C.fill.blue}"/>` +
        P(rect(40, 200, 300, 14, 4), 'faint', 900, 500, 1.1),
      start(s) {                      // runtime animation, cancelled automatically when the step changes
        s.bar('#bar', 0, 0);
        s.at(1600, () => s.bar('#bar', .7, 1200));
        s.at(2900, () => s.write(345, 196, '70%', {h: 1, z: 18, a: 'end'}));
      },
      duration: 3400 },
    { title: '2. Your turn', keys: ['work'],
      cap: 'A hands-on step: say exactly what to tap and what will change.',
      draw: () => T(20, 40, 'Try it', {h: 1, z: 24, a: 'start'}) + T(190, 150, 'taps: 0', {id: 'n', h: 1, z: 30}),
      start(s) {
        let n = 0;
        s.btn('play', 'Tap me', () => { n++; s.swap('#n', 'taps: ' + n); s.float(190, 120, '+1', 'green'); }, {primary: true});
      },
      demo: async s => { for (let i = 0; i < 3; i++) { s.tap(s.act.querySelector('button')); await s.wait(700); } },
      idleDemo: 5000, demoDuration: 2600, duration: 800 },
  ],
});
""",
    "player": r"""
const {P, T, F, line, rect, ellipse, arrow, curve, poly, C, lerp, clamp} = K;
// A player redraws the whole moving layer from the time t (ms). Never keep state between frames:
// pause, scrub, replay and GIF recording all depend on frame(t) being a pure function of t.
const D = 12000;
const LANES = ['Planner', 'Helper A', 'Helper B'];
K.player({
  root: '#x', style: __STYLE__, viewBox: [__W__, __H__], duration: D,
  title: 'One sentence that describes the whole replay for screen readers.',
  legend: [{key: 'busy', label: 'Working', color: 'fill.blue'}, {key: 'wait', label: 'Waiting', color: 'fill.amber'}],
  chapters: [
    {at: 0, title: 'The setup', cap: 'What the reader is looking at, and what to watch.'},
    {at: 4000, title: 'The handoff', cap: 'The planner sends work out and waits.'},
    {at: 8000, title: 'The result', cap: 'What the timing shows, with the real number.'},
  ],
  log: [{t: 500, text: '• planner starts', c: 'violet'}, {t: 4200, text: '→ send task to Helper A', c: 'green'}],
  clock: t => (t / 1000 * 10).toFixed(0) + ' s of the real run',   // say how compressed time is
  scene: () => LANES.map((n, i) => T(16, 64 + i * 50, n, {a: 'start', z: 14, c: 'mut'}) + P(line(90, 60 + i * 50, 364, 60 + i * 50, 10 + i), 'faint', 200 * i, 600, 1)).join(''),
  frame(t, s) {
    s.dyn.innerHTML = '';                 // redraw the moving layer from scratch
    const x = v => 90 + v / D * 274;
    const bars = [[0, 0, 4000, 'fill.blue'], [0, 4000, 8000, 'fill.amber'], [1, 4200, 7600, 'fill.blue'], [2, 4300, 9000, 'fill.blue']];
    bars.forEach(([lane, a, b, c]) => { if (t <= a) return; const e = Math.min(t, b);
      s.el('rect', {x: x(a), y: 52 + lane * 50, width: Math.max(0, x(e) - x(a)), height: 16, rx: 3, fill: C.fill[c.slice(5)]}); });
    s.el('line', {x1: x(t), x2: x(t), y1: 40, y2: 200, stroke: C.ink, 'stroke-opacity': .5});
  },
});
""",
    "figure": r"""
const {P, T, F, line, rect, ellipse, arrow, curve, poly, C, scale, fmt, clamp} = K;
// A figure is one standalone view: no steps, no Next button. The drawing reveals once; controls in the
// action row (sliders, toggles) or taps on the drawing change it live. For continuous motion, add
// duration and frame(t, s) (a pure function of t, like a player): it loops, with a pause button.
function model(p) { return {share: clamp(1 - (p.conf - 50) / 62.5)}; }   // illustrative; keep the model pure so numbers and drawing agree
K.figure({
  root: '#x', style: __STYLE__, viewBox: [__W__, __H__],
  title: 'Short heading for the figure',          // leave out for a figure that sits under an article heading
  cap: 'One or two sentences: what the figure shows and what to try.',
  alt: 'What a screen reader should hear: the point of the figure, with its numbers.',
  legend: [{key: 'a', label: 'Handled automatically', color: 'fill.blue'}, {key: 'b', label: 'Sent to a person', color: 'fill.amber'}],
  actHeight: 64,
  draw: () =>
    T(20, 40, 'Share handled automatically', {h: 1, z: 20, a: 'start'}) +
    `<rect x="20" y="80" width="340" height="28" rx="3" fill="${C.fill.amber}"/>` +
    `<rect id="auto" x="20" y="80" width="340" height="28" rx="3" fill="${C.fill.blue}"/>` +
    T(20, 140, '', {id: 'v', a: 'start', z: 16}),
  start(s) {
    const show = v => { const m = model({conf: v}); s.bar('#auto', m.share, 150); s.q('#v').textContent = fmt.pct(m.share) + ' handled without a person'; };
    K.slider(s.act, {label: 'Confidence needed to skip review', min: 50, max: 99, step: 1, value: 80, fmt: v => v + '%', oninput: v => { s.touched(); show(v); }});
  },
  // duration: 6000, frame(t, s) { s.dyn.innerHTML = ''; /* draw the moving layer for time t */ },
});
""",
    "explorable": r"""
const {P, T, F, line, rect, ellipse, arrow, curve, poly, C, scale, fmt} = K;
// An explorable is a live model: every control change recomputes the model and redraws.
// Put the model in one pure function so the drawing can never disagree with the numbers.
function model(p) { const cost = p.a * p.b; return {cost}; }
K.stepper({
  root: '#x', style: __STYLE__, viewBox: [__W__, __H__],
  title: 'One sentence that describes the explorable for screen readers.',
  actHeight: 76,   // reserve room for the slider so the controls below never move
  legend: [{key: 'a', label: 'Option A', color: 'fill.blue'}, {key: 'b', label: 'Option B', color: 'fill.amber'}],
  steps: [
    { title: '1. The question', keys: ['a', 'b'], cap: 'Set up the decision the reader will explore.',
      draw: () => T(20, 40, 'What changes the answer?', {h: 1, z: 24, a: 'start'}), duration: 1200 },
    { title: '2. Try it', keys: ['a', 'b'], cap: 'Move the slider. Say what to look for and where the answer flips.',
      draw: () => T(20, 40, 'Move the price', {h: 1, z: 24, a: 'start'}) + `<rect id="b1" x="40" y="80" width="300" height="20" fill="${C.fill.blue}"/>` + T(40, 125, '', {id: 'v', a: 'start', z: 14}),
      start(s) {
        const draw = v => { const m = model({a: v, b: 2}); s.bar('#b1', m.cost / 20, 150); s.q('#v').textContent = 'cost ' + fmt.usd(m.cost); };
        K.slider(s.act, {label: 'Price', min: 0, max: 10, step: .1, value: 3, fmt: v => fmt.usd(v), oninput: v => { s.touched(); draw(v); }});
      },
      demo: async s => { const inp = s.act.querySelector('input'); for (let v = 3; v <= 9; v += .25) { inp.value = v; inp.dispatchEvent(new Event('input')); await s.wait(60); } },
      idleDemo: 5000, demoDuration: 2200, duration: 800 },
  ],
});
""",
}

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>:root{color-scheme:__SCHEME__}html,body{margin:0;background:__PAGEBG__}body{padding:16px;min-height:100vh;box-sizing:border-box}</style>
</head><body>
<div id="x"></div>
<script>
__KIT__
</script>
<script>
/* ===== SCENE: everything below is the explainer itself. Edit freely. ===== */
__SCENE__
</script>
</body></html>
"""

FRAGMENT = """<div id="x"></div>
<script>
__KIT__
</script>
<script>
__SCENE__
</script>
"""


def load_theme(path, force):
    """Read and check a theme file; return (js_literal, page_bg, dark)."""
    sys.path.insert(0, str(HERE))
    import check_theme
    theme = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    worst = check_theme.report(theme, pathlib.Path(path).name)
    if worst == "FAIL" and not force:
        sys.exit("The theme fails the check above. Fix the colours, or pass --force to build anyway and say so.")
    _, st = check_theme.resolve(theme)
    dark = bool(st["dark"])
    page_bg = theme.get("pageBg") or shade(st["bg"], -0.06 if dark else -0.04)
    return json.dumps(theme), page_bg, dark


def shade(h, amt):
    """Darken (amt < 0) or lighten a #RRGGBB colour, for the page behind the explainer card."""
    v = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    v = [round(c * (1 + amt)) if amt < 0 else round(c + (255 - c) * amt) for c in v]
    return "#" + "".join(f"{max(0, min(255, c)):02X}" for c in v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--kind", choices=sorted(SCENES), default="stepper")
    ap.add_argument("--style", choices=sorted(PAGE_BG), default="chalkboard")
    ap.add_argument("--controls", choices=["full", "minimal", "none"], help="navigation the reader gets (default: full; none for a figure)")
    ap.add_argument("--theme", help="JSON file with your own colours and fonts; overrides --style")
    ap.add_argument("--force", action="store_true", help="build with a theme that fails the check")
    ap.add_argument("--data", help="JSON file to embed unchanged as const DATA in the scene")
    ap.add_argument("--title", default="Explainer")
    ap.add_argument("--viewbox", default=None, help="drawing size in units (default 380x300; 380x170 for a figure)")
    ap.add_argument("--fragment", action="store_true")
    a = ap.parse_args()
    w, h = (int(v) for v in (a.viewbox or ("380x170" if a.kind == "figure" else "380x300")).lower().split("x"))
    if a.theme:
        style, page_bg, dark = load_theme(a.theme, a.force)
        label = f"theme={a.theme}"
    else:
        style, page_bg, dark, label = f"'{a.style}'", PAGE_BG[a.style], DARK[a.style], f"style={a.style}"
    scene = SCENES[a.kind].replace("__STYLE__", style).replace("__W__", str(w)).replace("__H__", str(h)).strip()
    if a.controls:
        scene = scene.replace("root: '#x', ", f"root: '#x', controls: '{a.controls}', ", 1)
    if a.data:
        raw = pathlib.Path(a.data).read_text(encoding="utf-8")
        data = json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        if len(data) > 400_000:
            print(f"note: {a.data} is {len(data):,} characters; embed only the fields the explainer shows")
        head, rest = scene.split("\n", 1)
        note = f"// DATA is {pathlib.Path(a.data).name}, embedded unchanged by scaffold.py --data. Show numbers computed from it."
        scene = "\n".join([head, note, f"const DATA = {data};", rest])
    tpl = FRAGMENT if a.fragment else PAGE
    html = (tpl.replace("__TITLE__", a.title).replace("__SCHEME__", "dark" if dark else "light")
               .replace("__PAGEBG__", page_bg).replace("__KIT__", KIT.strip()).replace("__SCENE__", scene))
    out = pathlib.Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists; refusing to overwrite. Delete it first or choose another name.")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes, kind={a.kind}, {label}). Edit the SCENE block at the bottom.")


if __name__ == "__main__":
    main()
