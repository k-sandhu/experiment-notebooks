import sys, pathlib, json
sys.path.insert(0, 'grader')
from playwright.sync_api import sync_playwright
from browser import launch
url = pathlib.Path('gallery/index.html').resolve().as_uri()
S = sys.argv[1]
with sync_playwright() as pw:
    b = launch(pw); p = b.new_page(viewport={'width': 390, 'height': 900}); errs = []; p.on('pageerror', lambda e: errs.append(str(e)))
    p.goto(url); p.wait_for_timeout(2500); print('width', p.evaluate("document.documentElement.scrollWidth"), 'errors', errs)
    p.locator('#more').scroll_into_view_if_needed(); p.wait_for_timeout(1500); p.screenshot(path=f"{S}/gal_more.png")
    b.close()
files = sorted(f.relative_to('gallery').as_posix() for f in pathlib.Path('gallery').rglob('*') if f.is_file() and f.relative_to('gallery').as_posix() != 'index.html')
print(json.dumps({f: f for f in files}))
