#!/usr/bin/env python3
"""Record an explainer to MP4 and GIF, cropped to the explainer, at 2x pixel density.

For explainer-kit pages the page is opened with ?record=1: every step plays in order, steps with a
demo() perform their scripted taps (a ripple marks each tap), the Back/Next/Replay buttons are hidden
and the step dots stay visible. Other pages are recorded for --seconds, optionally clicking a Next
button every --click-next seconds.

usage: python record.py PAGE.html [--out OUT_BASENAME] [--width 380] [--scale 2] [--fps 30]
                        [--gif-fps 12] [--gif-width 480] [--seconds 60] [--click-next 0] [--no-gif]
Writes OUT.mp4 (small, sharp, best for LinkedIn and slides) and OUT.gif (plays anywhere).
Needs ffmpeg on PATH.
"""
import argparse
import base64
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from browser import launch  # noqa: E402
for _s in (sys.stdout, sys.stderr):   # report lines contain arrows and quotes; a Windows console or pipe may not take them
    try: _s.reconfigure(errors='replace')
    except AttributeError: pass

NEXT_JS = r"""() => { const re = /^(next|continue|›|»|→|>)\b|\bnext\b/i;
  const b = [...document.querySelectorAll('button, [role=button]')].find(e => re.test((e.getAttribute('aria-label') || '') + ' ' + (e.textContent || '').trim()) && e.offsetParent !== null);
  if (b) b.click(); return !!b; }"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("--out", default=None)
    ap.add_argument("--width", type=int, default=380, help="CSS width of the viewport")
    ap.add_argument("--scale", type=float, default=2)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--gif-fps", type=int, default=12)
    ap.add_argument("--gif-width", type=int, default=480)
    ap.add_argument("--seconds", type=float, default=240, help="hard limit")
    ap.add_argument("--click-next", type=float, default=0, help="non-kit pages: click Next every N seconds")
    ap.add_argument("--no-gif", action="store_true")
    ap.add_argument("--gif-max-mb", type=float, default=9.5, help="shrink the GIF until it is under this size")
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    page_path = pathlib.Path(a.page).resolve()
    out = pathlib.Path(a.out) if a.out else page_path.with_suffix("")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="kxrec_"))
    frames = []
    with sync_playwright() as pw:
        br = launch(pw)
        # Screencast frames arrive at CSS-pixel size, so render at 2x by zooming the page instead.
        ctx = br.new_context(viewport={"width": int(a.width * a.scale), "height": 2200}, device_scale_factor=1)
        page = ctx.new_page()
        page.add_init_script(f"document.addEventListener('DOMContentLoaded', () => document.documentElement.style.zoom = '{a.scale}')")
        page.goto(page_path.as_uri() + "?record=1")
        page.wait_for_load_state("networkidle", timeout=15000)
        kit = page.evaluate("() => !!window.EXPLAINER")
        if kit:
            page.evaluate("() => window.EXPLAINER.ready")
        page.evaluate("() => { const e = (window.EXPLAINER && window.EXPLAINER.root) || document.body; e.setAttribute('data-kx-rec', ''); }")
        box = page.locator("[data-kx-rec]").bounding_box()      # viewport pixels, zoom included
        vh = int(box["y"] + box["height"] + 20)
        page.set_viewport_size({"width": int(a.width * a.scale), "height": vh})
        box = page.locator("[data-kx-rec]").bounding_box()
        box = {"x": box["x"], "y": box["y"], "w": box["width"], "h": box["height"]}
        cdp = ctx.new_cdp_session(page)

        def on_frame(ev):
            frames.append((ev["metadata"]["timestamp"], ev["data"]))
            try:
                cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
            except Exception:
                pass

        cdp.on("Page.screencastFrame", on_frame)
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "everyNthFrame": 1,
                                          "maxWidth": int(a.width * a.scale), "maxHeight": vh})
        t0 = time.time()
        last_click = t0
        while time.time() - t0 < a.seconds:
            page.wait_for_timeout(250)
            if kit and page.evaluate("() => !!window.EXPLAINER.done"):
                page.wait_for_timeout(1200)
                break
            if not kit and a.click_next and time.time() - last_click > a.click_next:
                last_click = time.time()
                if not page.evaluate(NEXT_JS):
                    break
        cdp.send("Page.stopScreencast")
        br.close()
    if len(frames) < 2:
        sys.exit("no frames captured")
    frames.sort()
    lines = []
    for k, (ts, data) in enumerate(frames):
        p = tmp / f"f{k:05d}.jpg"
        p.write_bytes(base64.b64decode(data))
        dur = (frames[k + 1][0] - ts) if k + 1 < len(frames) else 1.0
        lines += [f"file '{p.as_posix()}'", f"duration {max(dur, 0.001):.4f}"]
    lines.append(f"file '{(tmp / f'f{len(frames) - 1:05d}.jpg').as_posix()}'")
    (tmp / "list.txt").write_text("\n".join(lines), encoding="utf-8")
    from PIL import Image
    with Image.open(tmp / "f00000.jpg") as im0:
        s = im0.width / int(a.width * a.scale)   # frame pixels per viewport pixel (1 unless the browser downscaled)
    cx, cy = int(box["x"] * s) // 2 * 2, int(box["y"] * s) // 2 * 2
    with Image.open(tmp / "f00000.jpg") as im0:
        fw, fh = im0.size
    cw, ch = min(int(box["w"] * s), fw - cx) // 2 * 2, min(int(box["h"] * s), fh - cy) // 2 * 2
    crop = f"crop={cw}:{ch}:{cx}:{cy}"
    mp4 = out.with_suffix(".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"),
                    "-vf", f"{crop},fps={a.fps},format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "slow",
                    "-movflags", "+faststart", str(mp4)], check=True)
    print(f"wrote {mp4} ({mp4.stat().st_size / 1e6:.1f} MB)")
    if not a.no_gif:
        gif = out.with_suffix(".gif")
        vf = (f"fps={a.gif_fps},scale={a.gif_width}:-1:flags=lanczos,split[x][y];"
              f"[x]palettegen=max_colors=96:stats_mode=diff[p];[y][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf", vf, str(gif)], check=True)
        # LinkedIn and most chat apps choke on GIFs over ~10 MB: step down frame rate and width until it fits
        for fps, width in ((10, a.gif_width), (8, int(a.gif_width * .85)), (6, int(a.gif_width * .75))):
            if gif.stat().st_size <= a.gif_max_mb * 1e6:
                break
            vf = (f"fps={fps},scale={width}:-1:flags=lanczos,split[x][y];"
                  f"[x]palettegen=max_colors=64:stats_mode=diff[p];[y][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf", vf, str(gif)], check=True)
        print(f"wrote {gif} ({gif.stat().st_size / 1e6:.1f} MB)" + ("" if gif.stat().st_size <= a.gif_max_mb * 1e6 else " - still large; record single steps with ?step=N"))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
