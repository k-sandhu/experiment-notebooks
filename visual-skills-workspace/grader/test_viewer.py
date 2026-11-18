import sys, pathlib
sys.path.insert(0, 'grader')
from playwright.sync_api import sync_playwright
from browser import launch
S = sys.argv[1]
url = pathlib.Path('gallery/index.html').resolve().as_uri()
with sync_playwright() as pw:
    b = launch(pw); p = b.new_page(viewport={'width': 390, 'height': 860}); errs = []
    p.on('pageerror', lambda e: errs.append(str(e)))
    p.goto(url); p.wait_for_timeout(1500)
    p.locator('.card.open').nth(3).click(); p.wait_for_timeout(3500)
    fr = p.frame_locator('#viewer-frame')
    print('viewer open:', p.is_visible('#viewer'), '| title:', p.inner_text('#viewer-title'), '| explainer steps:', fr.locator('.kx-dot').count())
    p.screenshot(path=f"{S}/viewer.png")
    p.click('#viewer-close'); p.wait_for_timeout(300); print('closed:', not p.is_visible('#viewer'))
    p.locator('button.open', has_text='Round 3 version').first.click(); p.wait_for_timeout(2500)
    print('round-1 opens:', p.frame_locator('#viewer-frame').locator('.kx-dot').count() > 0, '| errors:', errs, '| width:', p.evaluate('document.documentElement.scrollWidth'))
    b.close()
