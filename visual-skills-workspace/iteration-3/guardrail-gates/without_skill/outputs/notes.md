# Notes: "Starts with the right folder" is not a lock

## Message

A gate that approves a file request because the path text *starts with* the allowed folder can be fooled by paths whose spelling and destination differ. In notebook 10 it let through 5 of 14 forbidden requests, which were exactly the 5 requests built to beat a text check. The safer designs follow the path to where it really ends up, compare whole folder names and lock secret names. They let 0 of 14 through. Caveat: the requests and the safer gate were written against the same rules, so 0 is a ceiling by design. It shows which known tricks each design catches, not how often real attacks succeed.

## Form

A Khan Academy style step-through lesson in one offline HTML file (`explainer.html`, no external requests, system fonts, data embedded). Phone first: 480 px max width, 16 px gutters, sticky progress bar, large Back/Next buttons fixed at the bottom, light and dark themes. Practice questions ("Your turn") come before each reveal, and an animated folder map shows each path being walked.

`explainer.gif` (540x675, 4:5 for the LinkedIn feed, 50 frames, about 62 s, 0.64 MB) and `explainer.mp4` (600x750, H.264) were recorded from the page's `?gif=1` mode, which hides the nav bar.

## Steps

0. **Intro.** An AI helper asks, a gate decides. The shortcut: "if the path starts with the allowed folder, say yes."
1. **The rules.** The project is `/workspace/acme`: read anywhere except secret names, write only in `output/`, delete only in `tmp/` with a trusted approval, and no commands or internet. A folder map shows the delete area in green and the shortcut `tmp/shared-link` ⤳ `/srv/shared`.
2. **The starts-with gate.** Two easy cases, both judged correctly. Then a quiz: will it allow deleting `/workspace/acme/tmp-other/archive`?
3. **Five tricks**, shown as tabs: look-alike folder, climbing out with `..`, the shortcut, shortcut then up, and the secret inside. For each one: guess, see the verdict from the test data, then watch an animated walk on the map that ends red ("should be blocked").
4. **A safer gate.** Three habits plus "only 3 tools". A sandbox runs the same path through both gates, with chips for the 5 tricks and 3 legitimate requests, and an editable path box.
5. **Scoreboard.** 5 gates × 22 squares (14 forbidden, then 8 permitted). Tap a square to see the request, the verdict and where the path really leads.
6. **Reading it fairly.** The "5 of 14" is a list of tricks, not a failure rate. The perfect score comes from the design, some cases were not tested, and the page ends with the takeaway.

## Where every number comes from

All of them come from `data.json`, which `build/build.py` injects into the page at build time. Counts are computed in the page, not typed in.

| On screen | Source |
|---|---|
| 22 requests, 8 permitted, 14 forbidden | `requests.length`, and the count of `expected_allow` true and false |
| 5 gates, gate names | `gates` |
| x of 14 / x of 8 per gate (14/8, 5/8, 0/8, 0/4, 0/8) | `summary[].forbidden_allowed`, `permitted_allowed`, `*_n` |
| Each square's colour | `requests[].decisions[gate]` against `expected_allow` |
| Read only refuses 4 of 8 | `summary` for read only (8 − 4) |
| "Really leads to ..." in the tap details | `requests[].resolves_to` |
| ALLOW verdicts for the 5 tricks in step 3 | `decisions["lexical prefix"]` |
| Destinations in the walk and sandbox | computed by the page's resolver from `link_map`. Checked to match `resolves_to` (see below) |
| 110 decisions, $0, no model called, scoped = approval bound on all 22, untested cases | facts.md |
| "About 3 minutes" | my estimate of reading time, not data |

## What I checked

- **Gate logic against the data.** Playwright ran the page's own `prefixGate` and `scopedGate` on all 18 read, write and delete requests. Both gates match the recorded decisions on 17. The one exception is `untrusted_approval`: the sandbox assumes a trusted approval (and the page says so), while that request lacked one. The resolver's final paths match `resolves_to` for all 5 tricks, including `link_then_parent` → `/srv/private.txt`.
- **Phone layout.** At 390×844, no step scrolls sideways. I reviewed full-page screenshots of every step, the answered quizzes, all 5 walks, a tapped scoreboard square and the dark theme (`build/shots/`).
- **Errors and network.** No console errors. The only URL in the file is the data string `https://upload.invalid`, so nothing is loaded from the network.
- **GIF frames.** I reviewed contact sheets and fixed three problems: the walk was hidden under the header, a click scrolled the view, and the last scroll missed its target. The final frames show the path, the map and the step captions.
- **Wording.** No em dashes, no exclamation marks, and plain-language gate names, with the notebook name shown beside each.

## Files

`explainer.html`, `explainer.gif`, `explainer.mp4`, plus `build/` (template, `build.py`, `check.py`, `gif.py` and the review screenshots). To rebuild: `python build/build.py`, then `python build/gif.py`.
