"""Launch a headless Chromium with Playwright, falling back to any browser already on the machine.

Playwright pins one browser build per release. When that build is missing, this tries other
Playwright Chromium builds, then installed Chrome or Edge, before giving up with a clear message.
Nothing is downloaded.
"""
import glob
import os
import pathlib


def _candidates():
    roots = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright"),
             os.path.expanduser("~/.cache/ms-playwright"), os.path.expanduser("~/Library/Caches/ms-playwright")]
    pats = ["chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell*", "chromium-*/chrome-*/chrome.exe",
            "chromium-*/chrome-linux*/chrome", "chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium"]
    found = []
    for r in filter(None, roots):
        for p in pats:
            found += sorted(glob.glob(os.path.join(r, p)), reverse=True)
    return [f for f in found if pathlib.Path(f).is_file() and not f.endswith((".pak", ".dll"))]


def launch(pw, **kw):
    errors = []
    try:
        return pw.chromium.launch(**kw)
    except Exception as e:  # missing pinned build
        errors.append(str(e).splitlines()[0])
    for exe in _candidates():
        try:
            return pw.chromium.launch(executable_path=exe, **kw)
        except Exception as e:
            errors.append(f"{exe}: {str(e).splitlines()[0]}")
    for ch in ("chrome", "msedge"):
        try:
            return pw.chromium.launch(channel=ch, **kw)
        except Exception as e:
            errors.append(f"channel {ch}: {str(e).splitlines()[0]}")
    raise RuntimeError("No usable Chromium found. Run `python -m playwright install chromium`.\n" + "\n".join(errors[:5]))
