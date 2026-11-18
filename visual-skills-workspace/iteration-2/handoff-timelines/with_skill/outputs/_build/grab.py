"""Seek the player to given animation times (ms) and screenshot the explainer at one width."""
import sys, pathlib
sys.path.insert(0, r'C:/Users/sandh/OneDrive/Projects/experiment_notebooks/.claude/worktrees/visual-skills/visual-skills/explainer-kit/scripts')
from browser import launch
from playwright.sync_api import sync_playwright
page_path = pathlib.Path(sys.argv[1]).resolve(); width = int(sys.argv[2]); times = [int(x) for x in sys.argv[3].split(',')]; out = pathlib.Path(sys.argv[4]); out.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = launch(p); pg = b.new_page(viewport={'width': width, 'height': 1000}, device_scale_factor=2)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(page_path.as_uri() + '?static=1'); pg.wait_for_timeout(1500)
    for t in times:
        pg.evaluate(f'window.EXPLAINER.pause(); window.EXPLAINER.seek({t})'); pg.wait_for_timeout(150)
        pg.locator('#x').screenshot(path=str(out / f'w{width}_t{t:06d}.png'))
    print('errors', errs, 'duration', pg.evaluate('document.querySelector(".kx-scrub input").max'))
    b.close()
