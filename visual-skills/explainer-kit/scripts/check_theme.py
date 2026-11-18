#!/usr/bin/env python3
"""Check a custom theme's colours before building with it.

A theme is a small JSON file with your own colours and fonts (format in references/themes.md). This
script checks the things that decide whether readers can use the result:

  text contrast    ink and muted text against the background and the panel (WCAG 2 contrast ratio):
                   ink >= 7 passes, >= 4.5 warns, lower fails; mut >= 4.5 passes, >= 3 warns, lower fails
  mark contrast    every data fill and accent ink against the background (non-text contrast): >= 3 passes,
                   >= 2 warns, lower fails, because a bar or dot that fades into the page is lost
  fill separation  neighbouring data fills in the order they are assigned (blue, amber, green, violet, red),
                   as seen with normal vision and simulated protan, deutan and tritan colour vision (Machado,
                   Oliveira and Fernandes 2009, full severity), distance in OKLab x 100: normal vision >= 15,
                   colour-blind >= 8 pass; 6-8 warns (use labels or shapes as well); lower fails. Pairs that
                   are not neighbours are only warned about when they nearly collide, since five colours
                   cannot all be told apart by every reader
  semantic hues    red should look red and green should look green, because the kit uses red for errors
                   and costs and green for work in progress or success; a warning if they drift far

usage:
  python check_theme.py THEME.json            check a theme file
  python check_theme.py --builtin             check the four built-in styles (for reference)
Exit code 1 if anything fails.
"""
import json
import math
import pathlib
import re
import sys

SLOTS = ["blue", "green", "amber", "violet", "red"]
ORDER = ["blue", "amber", "green", "violet", "red"]   # the order fills are assigned to categories
NEUTRALS = ["bg", "panel", "ink", "mut", "faint", "line"]

# The four built-in styles, copied from assets/kit.js, used as bases and for --builtin.
BUILTIN = {
    "chalkboard": {"dark": 1, "bg": "#1E2023", "panel": "#17191B", "ink": "#ECE7DA", "mut": "#9A9A93", "faint": "#55585E", "line": "#4A4D53",
                   "blue": "#9CC3E6", "green": "#A8DDC3", "amber": "#F2D98B", "violet": "#C3B5E8", "red": "#EBA494",
                   "fill": {"blue": "#3F82AE", "amber": "#C38719", "green": "#28AD7E", "violet": "#A070E8", "red": "#D34144"}},
    "paper": {"dark": 0, "bg": "#FBF8F1", "panel": "#F3EEE3", "ink": "#22252A", "mut": "#5F6368", "faint": "#C9C3B6", "line": "#BDB6A8",
              "blue": "#2F6DB5", "green": "#1E7F55", "amber": "#C27C12", "violet": "#7B5EA7", "red": "#C8553D",
              "fill": {"blue": "#0080D4", "amber": "#C27C12", "green": "#227D54", "violet": "#87559D", "red": "#CF2627"}},
    "editorial": {"dark": 0, "bg": "#FFFFFF", "panel": "#F5F5F2", "ink": "#1A1A1A", "mut": "#5C5C5C", "faint": "#D6D6D0", "line": "#C4C4BE",
                  "blue": "#2F6DB5", "green": "#1E7F55", "amber": "#C27C12", "violet": "#7B5EA7", "red": "#C8553D",
                  "fill": {"blue": "#0080D4", "amber": "#C27C12", "green": "#227D54", "violet": "#87559D", "red": "#CF2627"}},
    "blueprint": {"dark": 1, "bg": "#10243A", "panel": "#0C1C2E", "ink": "#E6EEF5", "mut": "#93A8BC", "faint": "#3A5672", "line": "#4A6A89",
                  "blue": "#8EC5F0", "green": "#9BE0C0", "amber": "#F5D58A", "violet": "#C9B8F2", "red": "#F2A08F",
                  "fill": {"blue": "#3F82AE", "amber": "#C38719", "green": "#28AD7E", "violet": "#A070E8", "red": "#D34144"}},
}

CVD = {
    "protan": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    "deutan": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
    "tritan": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def lin(h):
    v = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in v]


def lum(h):
    r, g, b = lin(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def oklab(rgb):
    r, g, b = (min(1.0, max(0.0, c)) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def sim(h, kind):
    c = lin(h)
    if kind == "normal":
        return c
    M = CVD[kind]
    return [sum(M[i][j] * c[j] for j in range(3)) for i in range(3)]


def dist(a, b, kind):
    A, B = oklab(sim(a, kind)), oklab(sim(b, kind))
    return 100 * math.dist(A, B)


def hue(h):
    _, a, b = oklab(lin(h))
    return math.degrees(math.atan2(b, a)) % 360


def resolve(theme):
    """Merge a theme over its base style, the same way kit.js does."""
    base_name = theme.get("base") or ("blueprint" if theme.get("dark") else "editorial")
    if base_name not in BUILTIN:
        raise SystemExit(f"base '{base_name}' is not one of {sorted(BUILTIN)}")
    st = json.loads(json.dumps(BUILTIN[base_name]))
    for k, v in theme.items():
        if k == "fill":
            st["fill"].update(v)
        else:
            st[k] = v
    if "dark" not in theme:
        st["dark"] = 1 if lum(st["bg"]) < 0.18 else 0
    return base_name, st


def check(theme, name="theme"):
    """Return (rows, worst) where rows are (level, message) and worst is PASS, WARN or FAIL."""
    rows = []
    add = lambda lvl, msg: rows.append((lvl, msg))
    bad = [k for k in NEUTRALS + SLOTS if k in theme and not HEX.match(str(theme[k]))]
    bad += [f"fill.{k}" for k, v in theme.get("fill", {}).items() if not HEX.match(str(v))]
    unknown = [k for k in theme.get("fill", {}) if k not in SLOTS]
    if bad:
        add("FAIL", f"colours must be #RRGGBB: {', '.join(bad)}")
        return rows, "FAIL"
    if unknown:
        add("FAIL", f"unknown fill slots {unknown}; the slots are {SLOTS}")
    _, st = resolve(theme)
    for key, hi, lo in (("ink", 7, 4.5), ("mut", 4.5, 3)):
        for surf in ("bg", "panel"):
            r = contrast(st[key], st[surf])
            lvl = "PASS" if r >= hi else "WARN" if r >= lo else "FAIL"
            add(lvl, f"{key} on {surf}: contrast {r:.1f} (want >= {hi})")
    for k in SLOTS:
        for label, c in ((f"fill.{k}", st["fill"][k]), (k, st[k])):
            r = contrast(c, st["bg"])
            lvl = "PASS" if r >= 3 else "WARN" if r >= 2 else "FAIL"
            if lvl != "PASS":
                add(lvl, f"{label} {c} on bg: contrast {r:.1f}; marks this faint are hard to see (want >= 3)")
    neighbours = list(zip(ORDER, ORDER[1:]))
    for kind, ok, floor in (("normal", 15, 10), ("protan", 8, 6), ("deutan", 8, 6), ("tritan", 8, 6)):
        d, a, b = min((dist(st["fill"][a], st["fill"][b], kind), a, b) for a, b in neighbours)
        lvl = "PASS" if d >= ok else "WARN" if d >= floor else "FAIL"
        add(lvl, f"closest neighbouring fills, {kind} vision: fill.{a} and fill.{b}, distance {d:.1f} (want >= {ok})")
    # Five colours cannot all be told apart by every reader. Pairs that are not neighbours in ORDER are
    # not required to pass, but a near-collision is reported so the scene can label them or avoid using both.
    for i, a in enumerate(SLOTS):
        for b in SLOTS[i + 1:]:
            if (a, b) in neighbours or (b, a) in neighbours:
                continue
            close = [(kind, dist(st["fill"][a], st["fill"][b], kind)) for kind in ("normal", "protan", "deutan", "tritan")]
            close = [(k, d) for k, d in close if d < (10 if k == "normal" else 6)]
            if close:
                who = ", ".join(f"{k} {d:.1f}" for k, d in close)
                add("WARN", f"fill.{a} and fill.{b} look alike ({who}); if a chart uses both, label them or use shape too")
    for k, (lo, hi) in (("red", (330, 60)), ("green", (110, 190))):
        h = hue(st["fill"][k])
        inside = lo <= h <= hi if lo < hi else (h >= lo or h <= hi)
        if not inside:
            add("WARN", f"fill.{k} {st['fill'][k]} does not look {k} (hue {h:.0f}); the kit uses {k} for "
                        f"{'errors and costs' if k == 'red' else 'work in progress and success'}, so readers may misread it")
    worst = "FAIL" if any(l == "FAIL" for l, _ in rows) else "WARN" if any(l == "WARN" for l, _ in rows) else "PASS"
    return rows, worst


def report(theme, name):
    rows, worst = check(theme, name)
    print(f"== {name}: {worst}")
    for lvl, msg in rows:
        if lvl != "PASS" or "--verbose" in sys.argv:
            print(f"  {lvl:4}  {msg}")
    if worst == "PASS":
        print("  all checks pass")
    return worst


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--builtin":
        worst = [report({"base": n}, n) for n in BUILTIN]
    else:
        p = pathlib.Path(sys.argv[1])
        worst = [report(json.loads(p.read_text(encoding="utf-8")), p.name)]
    sys.exit(1 if "FAIL" in worst else 0)


if __name__ == "__main__":
    main()
