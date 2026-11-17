# Path gate lesson: notes

## Message

A gate that only checks how a path's text starts can be tricked: in notebook 10's 22 hand-written
requests it let 5 of 14 forbidden requests through (every one of the five built to beat a text check),
while the safer designs, which first work out where the path really ends and then compare whole folder
names and secret names, let 0 of 14 through and still allowed all 8 permitted requests (the read-only
variant allowed 4 of 8).

- Reader: non-engineers, on a phone, giving a lesson about two minutes.
- Misconception it targets: "if the path starts with my project folder, it is inside my project."
- Form: `stepper-lesson` (Khan Academy style, reader-paced, Next button), chalkboard style, built with
  `explainer-kit`. Two hands-on steps (a four-question allow/block quiz and a type-your-own-path
  playground). A GIF/MP4 is recorded from the same file with `?record=1`, which plays every step and
  runs the demos (the quiz demo answers one question wrongly so the "Not quite" reply is on camera).

## Storyboard (as built)

1. **Meet the parts** (cast). The map of the disk: `/workspace/acme` (the project, blue) with input/,
   src/, output/, tmp/ (holding stale.txt, cache/ and the shortcut shared-link), tmp-other/ and .env;
   `/srv` (outside, red) with shared/archive and private.txt. A dashed amber arrow shows that
   tmp/shared-link leads to /srv/shared. The gate box states the rules. One ordinary request
   (delete tmp/stale.txt) travels to the gate, is allowed, and a dot walks to stale.txt.
2. **A gate that reads the start** (mechanism). Prefix gate. The matched letters of
   /workspace/acme/tmp/stale.txt turn green, allowed, dot walks to the file. Then /srv/shared/archive:
   no match, blocked.
3. **Your turn: allow or block?** (hands-on, `ask: true`). Four questions, one per trick, each with its
   own Right / Not quite reply: traversal (`..` climbs out), prefix_sibling (tmp-other begins with the
   letters tmp), linked_target (shortcut to /srv/shared), secret (.env). After the pick: the green
   matched letters, the prefix gate's "allowed" stamp, and a dot that walks the path part by part
   (the active part is underlined in the request) to where it really ends, ringed in red. Final caption
   names the fifth trick (link_then_parent, ending at /srv/private.txt).
4. **A gate that follows the path** (mechanism). Safer gate: follow every `..` and shortcut first, then
   check whole folder names and secret names. Traversal ends at /srv/shared/archive: blocked.
   normalized_temp (`tmp/cache/../stale.txt`) also has `..` but ends in tmp/: allowed (so "refuse every
   `..`" is not the fix).
5. **Try your own path** (hands-on). Text box, action menu, Check and Test request (cycles through all
   22 study requests and shows the study's right answer). Both gates judge with a one-line reason; the
   dot walks the real path on the map. Demo tries tmp-other/archive, the shortcut-then-`..` read, and
   output/../.env.
6. **All 22 requests, five gates** (evidence). One dot per request per gate (110 dots), red ring =
   forbidden, blue ring = permitted, filled = let through. Counts per gate. The five tricks sit first
   in each red row; the prefix row's five filled dots are ringed. Note that the safer gate and the
   exact-approvals gate made identical decisions on all 22.
7. **What to take away** (takeaway). Three things a safer gate does, then "What this test cannot tell
   you": 22 hand-written requests run once, no real attacker or live disk in the main test, untested
   cases (shortcut swapped between check and delete, hardlinks, sandbox escape). Caption names the
   ceiling: the 0 comes from requests written against the same rules.

Legend (one colour, one meaning): amber = agent request and the walking dot; blue = inside the project
/ permitted; red = outside / forbidden; green = letters the prefix test matched (and the "allowed"
stamp); violet = gate and its "blocked" stamp. Every stamp also carries a word and ✓ or ✗, and the
scoreboard uses filled versus ring, so colour is never the only cue.

## Where every number on screen comes from

All values come from the two input files (`evals/guardrail-gates/files/data.json` and `facts.md`,
which cite notebooks/10-code-execution-guardrails). They are copied into `const DATA` at the top of
the scene with a source comment.

| On screen | Value | Source |
|---|---|---|
| 22 requests, 14 forbidden, 8 permitted | counted from `DATA.requests` (`ok` = `expected_allow`) | data.json `requests` |
| Prefix gate 5/14 forbidden, 8/8 permitted | counted from per-request decisions, then checked against `DATA.summary` (console error on mismatch; none) | data.json `requests[].decisions`, `summary` (summary.csv) |
| Log only 14/14, 8/8; Safer gate 0/14, 8/8; read-only 0/14, 4/8; exact approvals 0/14, 8/8 | same | same |
| "Safer gate and exact approvals made identical decisions on all 22" | decisions columns are equal | facts.md headline note, README section 5 |
| The four quiz paths and where they lead | `target`, `resolves_to` | data.json; facts.md table (README section 8) |
| "A fifth did too ... /srv/private.txt" | link_then_parent `resolves_to` | data.json |
| tmp/shared-link leads to /srv/shared | `link_map` | data.json, README section 1 |
| Prefix rules (/workspace/acme for reads, /workspace/acme/tmp for deletes, /output for writes) | | facts.md "The five gates" |
| Secret names .env, .ssh, credentials, payroll | | facts.md "Scoped capabilities" |
| Untested cases (link swapped between check and use, hardlinks, sandbox escape) | | facts.md caveats |

Gate names on screen are the reader's words, mapped as: Log only (no check) = observe only; Prefix
gate = lexical prefix; Safer gate = scoped capabilities; Safer gate, read-only = read only; Safer gate
+ exact approvals = approval bound.

The playground (step 5) re-implements the prefix and safer gates in JavaScript from the plain-word
rules so a reader can type any path. A self-test runs on load: on all 22 study requests both functions
return exactly the recorded decisions (`window.GATE_MISMATCHES` is empty). For typed paths, deletes are
assumed to carry a trusted approval (the study's approval list is not modelled); the Test request
button passes the study's approval status, so untrusted_approval is blocked by both, as recorded.
Approval fingerprints (the difference between "Safer gate" and "exact approvals") are not shown in the
playground because no study request exercises them.

Not used on screen: the broker demo (7 real-folder requests) and container probes; they answer a
different question than the path trick.

## What I checked

- `render_check.py` at 360 px and 560 px plus a reduced-motion pass: **PASS all checks** (no console
  errors, no text outside the drawing, no text overlaps, no text under 10.5 px, controls fixed, height
  constant). Earlier runs failed `controls_moved`; I fixed the causes: two step titles that wrapped to two
  lines, a legend that grew to three rows, and the step 5 controls wrapping to three rows. Frames and
  contact sheets are in `qa/`.
- I looked at the 360 px frames of every step against the storyboard. I fixed file names that ran past
  their folder boxes (orders.json, summary.txt, main.py), the quiz question overlapping the gate rules
  in the final frame, and a path wrap that started a line with "/".
- Gate logic: `window.GATE_MISMATCHES` is empty, so the JavaScript prefix and safer gates reproduce the
  recorded `lexical prefix` and `scoped capabilities` decisions on all 22 requests. Scoreboard counts are
  computed from per-request decisions and match `summary.csv` for all five gates (checked in code).
- Playground, driven with Playwright at 360 px. `/workspace/acme/tmp2/x` delete: prefix allows, safer
  blocks ("outside tmp/"). `output/report.md` write: both allow. The shortcut-then-`..` read: prefix
  allows, safer blocks ("ends at /srv/private.txt"). `/home/user/.ssh/id_rsa`: both block.
  `rm -rf /` as "run a program": both block. Cycling Test request through all 22 gave no errors.
- Wording against the data, focusing on totality words. "all four" in step 3 is right (P = 1 for all
  four). "all five path tricks" in step 6 is right (exactly the five forbidden requests with P = 1).
  "The safer designs let 0 through" covers scoped, read-only and approval-bound (all 0/14). "identical
  decisions on all 22" holds (S and A columns are equal).
- Every caption is 220 characters or less (longest 212).
- Not checked: real phones (only headless Chromium at phone width), screen readers, and a fresh
  "Not quite" pass by hand on every quiz question (the recorded demo shows one).

## Recording

`record.py` plays the page with `?record=1`: each step runs, the quiz demo answers (one wrong on
purpose) and the playground demo tries three paths. Outputs: `path-gate-lesson.mp4` (4.7 MB, 114 s; sharper and
smaller, better for LinkedIn) and `path-gate-lesson.gif` (7.6 MB). I checked sampled frames at 20, 45,
75 and 100 s: quiz question, quiz reveal with the link walk, safer-gate walk and playground verdicts all
render with the controls hidden. The recording runs about two minutes, which
is long for a feed. For a post, trim to steps 2-3 (the prefix gate and one trick) or record a single
step with `?step=N` and `--seconds`.
