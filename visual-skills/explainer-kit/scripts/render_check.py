#!/usr/bin/env python3
"""Look at an explainer the way a reader would, and report what a reader would notice.

Opens the page in headless Chromium at phone and desktop widths, walks every step (or chapter),
saves frames at several moments of each step, builds one contact sheet per width, and checks:

  errors          console errors or uncaught exceptions                                   FAIL
  blank           a final frame that is (almost) one flat colour                           FAIL
  overflow_x      the page scrolls sideways                                                FAIL
  text_outside    SVG text that sticks out of its drawing                                  FAIL
  controls_moved  a navigation button changes position between steps                       FAIL
  text_overlap    two visible pieces of text cover each other                              WARN
  tiny_text       text rendered smaller than 10.5 px                                         WARN
  height_changed  the explainer changes height between steps (the page jumps)              WARN
  caption_overflow a caption taller than the space reserved for it                         WARN
  reduced_motion  errors or blank frames when the reader asks for reduced motion           FAIL

Works best with explainer-kit pages (window.EXPLAINER). Other pages are stepped by clicking a
button labelled Next (or similar); if there is none, frames are taken over time.

usage: python render_check.py PAGE.html [--out DIR] [--widths 360,560] [--samples .2,.6,1]
                              [--max-steps 20] [--no-rm] [--index 0] [--wait-ms 4000]
Then LOOK at the contact sheets. The checks catch layout faults, not unclear explanations.
"""
import argparse
import json
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from browser import launch  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageStat
except ImportError:  # contact sheets are optional
    Image = None

PROBE = r"""
(idx) => {
  const ex = (window.EXPLAINERS && window.EXPLAINERS[idx]) || window.EXPLAINER || null;
  const root = (ex && ex.root) || document.body;
  const visible = el => { for (let e = el; e && e.nodeType === 1; e = e.parentNode) { const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return false;
      if (e.classList && e.classList.contains('sr-only')) return false; } return true; };
  const items = [];
  root.querySelectorAll('svg text').forEach(t => {
    const s = (t.textContent || '').trim(); if (!s || !visible(t)) return;
    const r = t.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return;
    const svg = t.ownerSVGElement, m = svg && svg.getScreenCTM(), sc = m ? Math.hypot(m.a, m.b) : 1;
    const sr = svg.getBoundingClientRect();
    items.push({kind: 'svg', s: s.slice(0, 48), r: [r.left, r.top, r.right, r.bottom], px: parseFloat(getComputedStyle(t).fontSize) * sc,
                out: r.left < sr.left - 2 || r.right > sr.right + 2 || r.top < sr.top - 2 || r.bottom > sr.bottom + 2});
  });
  const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let nid = 0;
  for (let n = tw.nextNode(); n; n = tw.nextNode()) {
    const p = n.parentElement; if (!p || p.closest('svg') || p.closest('script,style') || !n.textContent.trim() || !visible(p)) continue;
    const rg = document.createRange(); rg.selectNodeContents(n); nid++;
    for (const r of rg.getClientRects()) { if (r.width < 1 || r.height < 1) continue;   // one box per line, so wrapped text is not a false overlap
      items.push({kind: 'html', id: nid, s: n.textContent.trim().slice(0, 48), r: [r.left, r.top, r.right, r.bottom], px: parseFloat(getComputedStyle(p).fontSize), out: false}); }
  }
  const overlaps = [];
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    if (items[i].id && items[i].id === items[j].id) continue;
    const a = items[i].r, b = items[j].r, w = Math.min(a[2], b[2]) - Math.max(a[0], b[0]), h = Math.min(a[3], b[3]) - Math.max(a[1], b[1]);
    if (w <= 1 || h <= 1) continue;
    const area = w * h, small = Math.min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]));
    if (area > 0.2 * small) overlaps.push([items[i].s, items[j].s, Math.round(100 * area / small)]);
  }
  const seen = {};
  const btns = [...root.querySelectorAll('button')].filter(b => visible(b) || getComputedStyle(b).visibility === 'hidden').map(b => {
    const r = b.getBoundingClientRect(); const base = (b.className && typeof b.className === 'string' ? b.className.split(' ')[0] : '') || b.getAttribute('aria-label') || b.textContent.trim().slice(0, 20);
    seen[base] = (seen[base] || 0) + 1; const key = base + '#' + seen[base];
    return {key, x: Math.round(r.left), y: Math.round(r.top), nav: !!b.closest('.kx-nav, nav, [class*=nav], [class*=controls]')}; });
  const cap = root.querySelector('.kx-cap');
  const rr = root.getBoundingClientRect();
  return {
    texts: items.length, overlaps: overlaps.slice(0, 12), nOverlaps: overlaps.length,
    tiny: items.filter(t => t.px < 10.5).map(t => [t.s, Math.round(t.px * 10) / 10]).slice(0, 8), nTiny: items.filter(t => t.px < 10.5).length,
    outside: items.filter(t => t.out).map(t => t.s).slice(0, 8),
    overflowX: document.documentElement.scrollWidth > innerWidth + 1, scrollW: document.documentElement.scrollWidth,
    height: Math.round(rr.height), buttons: btns,
    capOverflow: cap ? cap.scrollHeight > cap.clientHeight + 1 && cap.clientHeight > 0 && getComputedStyle(cap).minHeight !== '0px' && cap.scrollHeight > parseFloat(getComputedStyle(cap).minHeight) + 1 : false,
  };
}
"""

INFO = r"""
(idx) => { const ex = (window.EXPLAINERS && window.EXPLAINERS[idx]) || window.EXPLAINER || null;
  if (!ex) return null; const n = ex.count; const d = []; for (let i = 0; i < n; i++) d.push(ex.duration(i));
  const demo = []; for (let i = 0; i < n; i++) demo.push(ex.hasDemo(i)); return {kind: ex.kind, count: n, durations: d, demo}; }
"""

NEXT_JS = r"""
() => { const re = /^(next|continue|forward|start|begin|›|»|→|>)\b|\bnext\b/i;
  const b = document.querySelector('#next:not([disabled]), button.next:not([disabled])') || [...document.querySelectorAll('button, [role=button], a')].find(e => re.test((e.getAttribute('aria-label') || '') + ' ' + (e.textContent || '').trim()) && e.offsetParent !== null);
  if (!b) return false; b.click(); return true; }
"""


def flat(img_path):
    if Image is None:
        return False
    im = Image.open(img_path).convert("L")
    st = ImageStat.Stat(im)
    return st.stddev[0] < 3.0


def sheet(frames, out_path, cols):
    if Image is None or not frames:
        return
    ims = [Image.open(p).convert("RGB") for p, _ in frames]
    tw = 300
    th = max(int(im.height * tw / im.width) for im in ims)
    rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 26) + 8), (245, 245, 245))
    d = ImageDraw.Draw(S)
    for k, (im, (_, label)) in enumerate(zip(ims, frames)):
        r, c = divmod(k, cols)
        x, y = 8 + c * (tw + 8), 8 + r * (th + 26)
        S.paste(im.resize((tw, int(im.height * tw / im.width))), (x, y + 18))
        d.text((x, y + 2), label, fill=(40, 40, 40))
    S.save(out_path)


def run_width(pw, url, width, a, out, rm=False):
    br = launch(pw)
    ctx = br.new_context(viewport={"width": width, "height": 1000}, device_scale_factor=2, reduced_motion="reduce" if rm else "no-preference")
    page = ctx.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text[:200]) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)[:200]))
    page.goto(url)
    page.wait_for_load_state("networkidle", timeout=15000)
    has = page.evaluate("() => !!(window.EXPLAINER || (window.EXPLAINERS && window.EXPLAINERS.length))")
    if has:
        page.evaluate(f"() => ((window.EXPLAINERS && window.EXPLAINERS[{a.index}]) || window.EXPLAINER).ready")
    info = page.evaluate(INFO, a.index) if has else None
    tag = f"w{width}{'_rm' if rm else ''}"
    target = page.locator(".kx").nth(a.index) if has and page.locator(".kx").count() > a.index else page.locator("body")
    frames, probes = [], []
    samples = [1.0] if rm else a.samples

    def shoot(label, fname):
        p = out / fname
        try:
            target.screenshot(path=str(p))
        except Exception:
            page.screenshot(path=str(p), full_page=True)
        frames.append((p, label))
        return p

    if info:
        n = min(info["count"], a.max_steps)
        for i in range(n):
            page.evaluate(f"() => ((window.EXPLAINERS && window.EXPLAINERS[{a.index}]) || window.EXPLAINER).go({i})")
            dur = max(400, min(info["durations"][i], 20000))
            t0 = time.time()
            last = None
            for s in samples:
                wait = 0.26 + (dur / 1000) * s + (0.5 if s >= 1 else 0)
                dt = wait - (time.time() - t0)
                if dt > 0:
                    page.wait_for_timeout(dt * 1000)
                last = shoot(f"step {i + 1} @{int(s * 100)}%", f"{tag}_s{i + 1:02d}_{int(s * 100):03d}.png")
            pr = page.evaluate(PROBE, a.index)
            pr["step"] = i + 1
            pr["blank"] = flat(last)
            probes.append(pr)
            if info["demo"][i] and not rm:
                page.evaluate(f"() => ((window.EXPLAINERS && window.EXPLAINERS[{a.index}]) || window.EXPLAINER).demo({i})")
                page.wait_for_timeout(3500)
                shoot(f"step {i + 1} demo", f"{tag}_s{i + 1:02d}_demo.png")
    else:
        i = 0
        while i < a.max_steps:
            page.wait_for_timeout(a.wait_ms)
            last = shoot(f"view {i + 1}", f"{tag}_v{i + 1:02d}.png")
            pr = page.evaluate(PROBE, a.index)
            pr["step"] = i + 1
            pr["blank"] = flat(last)
            probes.append(pr)
            i += 1
            if not page.evaluate(NEXT_JS):
                break
    br.close()
    cols = len(samples) + (1 if info and any(info["demo"]) and not rm else 0) if info else 4
    sheet(frames, out / f"sheet_{tag}.png", max(1, cols))
    return {"width": width, "rm": rm, "info": info, "errors": errors, "probes": probes, "frames": len(frames), "sheet": str(out / f"sheet_{tag}.png")}


def judge(runs):
    res = []

    def add(level, check, msg):
        res.append((level, check, msg))

    for r in runs:
        w = f"{r['width']}px{' reduced-motion' if r['rm'] else ''}"
        if r["errors"]:
            add("FAIL", "reduced_motion" if r["rm"] else "errors", f"{w}: {len(r['errors'])} error(s), first: {r['errors'][0]}")
        for p in r["probes"]:
            if p["blank"]:
                add("FAIL", "reduced_motion" if r["rm"] else "blank", f"{w} step {p['step']}: final frame is blank")
        if r["rm"]:
            continue
        for p in r["probes"]:
            st = f"{w} step {p['step']}"
            if p["overflowX"]:
                add("FAIL", "overflow_x", f"{st}: page is {p['scrollW']}px wide")
            if p["outside"]:
                add("FAIL", "text_outside", f"{st}: {p['outside'][:4]}")
            if p["nOverlaps"]:
                add("WARN", "text_overlap", f"{st}: {p['nOverlaps']} pair(s), e.g. {p['overlaps'][:3]}")
            if p["nTiny"]:
                add("WARN", "tiny_text", f"{st}: {p['nTiny']} label(s) under 10.5px, e.g. {p['tiny'][:3]}")
            if p["capOverflow"]:
                add("WARN", "caption_overflow", f"{st}: caption taller than its reserved space")
        hs = [p["height"] for p in r["probes"]]
        if hs and max(hs) - min(hs) > 4:
            add("WARN", "height_changed", f"{w}: explainer height ranges {min(hs)}-{max(hs)}px across steps")
        pos = {}
        for p in r["probes"]:
            for b in p["buttons"]:
                if b["nav"]:
                    pos.setdefault(b["key"], []).append((b["x"], b["y"]))
        moved = [k for k, v in pos.items() if len(v) > 1 and (max(x for x, _ in v) - min(x for x, _ in v) > 2 or max(y for _, y in v) - min(y for _, y in v) > 2)]
        if moved:
            add("FAIL", "controls_moved", f"{w}: {moved[:4]} change position between steps")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("--out", default=None)
    ap.add_argument("--widths", default="360,560")
    ap.add_argument("--samples", default=".2,.6,1")
    ap.add_argument("--max-steps", type=int, default=20)
    ap.add_argument("--index", type=int, default=0, help="which explainer on the page, if there are several")
    ap.add_argument("--wait-ms", type=int, default=4000, help="time per view for pages without explainer-kit")
    ap.add_argument("--no-rm", action="store_true", help="skip the reduced-motion pass")
    a = ap.parse_args()
    a.samples = [float(s) for s in a.samples.split(",")]
    page = pathlib.Path(a.page).resolve()
    out = pathlib.Path(a.out) if a.out else page.parent / f"qa_{page.stem}"
    out.mkdir(parents=True, exist_ok=True)
    url = page.as_uri()
    runs = []
    with sync_playwright() as pw:
        for w in [int(x) for x in a.widths.split(",")]:
            runs.append(run_width(pw, url, w, a, out))
        if not a.no_rm:
            runs.append(run_width(pw, url, int(a.widths.split(",")[0]), a, out, rm=True))
    res = judge(runs)
    info = runs[0]["info"]
    summary = {"page": str(page), "explainer": info, "results": [{"level": l, "check": c, "detail": m} for l, c, m in res],
               "sheets": [r["sheet"] for r in runs], "runs": runs}
    (out / "report.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    kind = f"{info['kind']} with {info['count']} steps" if info else "page without explainer-kit (stepped by its Next button, if any)"
    print(f"render_check: {page.name}: {kind}")
    fails = [r for r in res if r[0] == "FAIL"]
    for lvl in ("FAIL", "WARN"):
        for l, c, m in res:
            if l == lvl:
                print(f"  {l:4} {c:16} {m}")
    if not res:
        print("  PASS all checks")
    print(f"  contact sheets: {', '.join(summary['sheets'])}")
    print(f"  report: {out / 'report.json'}")
    print("  Now open the contact sheets and look: checks find layout faults, not unclear explanations.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
