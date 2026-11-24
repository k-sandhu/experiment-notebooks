# Guardrail gates lesson: notes

## Message

A file gate that only checks how a path's text starts was fooled by 5 of 14 forbidden requests in
notebook 10. All 5 were requests written to beat a text check. Gates that first work out where the
path really leads let 0 of 14 through and still allowed all 8 permitted jobs.

- Reader: non-engineers on a phone or in a LinkedIn feed.
- Misconception: "If the address starts with the right folder, the file is inside that folder."
- Form: `stepper-lesson` (Khan Academy style). It has two steps the reader plays (tap a request card)
  and one dot-chart evidence step borrowed from `unit-story`. Built with `explainer-kit` in the
  chalkboard style. The drawing is 380 x 380, so it reads on a phone and records square.

## Steps

1. **Meet the gate.** The cast: an AI agent, the request `delete /workspace/acme/tmp/stale.txt`, the
   prefix gate, and a folder map. The map shows the project (tmp/ with stale.txt and shared-link,
   output/, tmp-other/, .env) and the area outside it (/srv with private.txt and shared/archive). A
   dashed arrow marks the link from shared-link to /srv/shared. The rule: deletes only inside tmp/.
2. **Checking the start.** The prefix gate highlights `/workspace/acme/tmp` in the text and allows
   it. A dot walks to stale.txt, and the verdict is right. This is the ordinary case.
3. **Your turn: fool it** (hands-on). Six cards: Climb out (traversal), Look-alike (prefix_sibling),
   Shortcut link (linked_target), Link then up (link_then_parent), Secret file (secret) and Honest
   detour (normalized_temp, a permitted request). Tapping a card shows the path with the gate's
   matched prefix, the prefix gate's verdict, a dot walking the real route with ".." and "link"
   labels, a "really goes to" line, and a caption explaining the trick. A counter tracks how often
   the prefix gate was fooled. The demo taps 3 cards.
4. **Follow the path first.** The scoped gate appears next to the prefix gate. On the traversal
   request it walks the path (the "walking:" line changes from /workspace/acme/tmp to /workspace/acme,
   /workspace, / and then /srv/shared/archive), so it blocks. The prefix gate allows the request.
   The caption gives the scoped gate's three habits.
5. **Your turn: both gates** (hands-on). Same cards, and now both gates judge each one. The honest
   detour shows that the scoped gate does not refuse every "..". The demo taps the last 3 cards.
6. **All 22 requests, 5 gates.** One dot per request in each gate's row: 14 forbidden and 8
   permitted. A filled dot means the gate allowed the request and a hollow ring means it blocked it.
   Colours: red is forbidden but let in, blue is blocked rightly, green is allowed rightly, and amber
   is a permitted job blocked. A note says scoped and approval-bound made the same decisions on all
   22 requests.
7. **What to ask of a gate.** "Check where it leads, not how it is spelled." The three rules come
   with the headline numbers and the read-only tradeoff. The caption gives the main caveat.

## Where every number comes from

All data are inlined as `DATA` in the scene and copied by script from
`evals/guardrail-gates/files/data.json`, which comes from notebook 10's cases.json,
gate_decisions.csv and summary.csv. The page computes every number on screen from DATA.

| On screen | Value | Source |
|---|---|---|
| 22 requests, 14 forbidden, 8 permitted | counts of `requests` by `expected_allow` | data.json `requests`; matches `summary[].forbidden_n/permitted_n` |
| Per gate "X of 14 forbidden in · Y of 8 jobs done" (14/8, 5/8, 0/8, 0/4, 0/8) | `summary` rows | data.json `summary` (summary.csv). The page recounts them from the 110 per-request `decisions` and logs a console error on any mismatch; none occurred |
| "the 5 path tricks" | forbidden requests with `decisions['lexical prefix'] = true` | data.json; listed in facts.md (README section 8) |
| Each dot's fill and ring | `decisions[gate]` and `expected_allow` for that request | data.json |
| Verdicts in steps 2-5 (ALLOWS/BLOCKS, right/wrong) | `decisions['lexical prefix']`, `decisions['scoped capabilities']` against `expected_allow` | data.json |
| Paths as written | `target` | data.json |
| "really goes to" destinations | `resolves_to` | data.json (README section 8 table). For normalized_temp, facts.md says it is the same file as remove_temp: /workspace/acme/tmp/stale.txt |
| Intermediate "walking:" locations (/workspace/acme, /workspace, /, /srv/shared, /srv) | derived by applying each ".." or link in order | the link map `tmp/shared-link -> /srv/shared` (data.json `link_map`). link_then_parent follows facts.md: the link is entered first, then ".." |
| Prefix gate's highlighted prefix per operation | read `/workspace/acme`, write `/workspace/acme/output`, delete `/workspace/acme/tmp` | facts.md, README section 2 |
| Scoped gate habits, protected names (.env, .ssh, credentials, payroll) | text | facts.md, README section 2 |
| "Scoped and approval-bound decided all 22 alike" | checked in code (`SAME_SC_AB`) | data.json decisions; facts.md, README section 5 |
| "read-only blocked 4 of 8 jobs" | 8 − 4 permitted allowed | data.json `summary` |
| Caveat in step 7 | text | facts.md caveats (ceiling by design, 22 hand-written requests) |

The folder map is a teaching drawing of the paths in the data. The positions of the boxes carry no
data. The broker demo and container probes from notebook 10 are not shown; they are a separate
demonstration and fall outside this message.

## What I checked

- `render_check.py` walked all 7 steps at 360 px and 560 px, and at 360 px with reduced motion. It
  checks for errors, blank frames, sideways scroll, text outside the drawing, controls moving,
  overlapping text, tiny text, height changes and caption overflow. The final run reported
  **PASS all checks**, with no console errors, so the DATA recount matched summary.csv.
- I looked at the contact sheets and the individual frames at both widths for steps 2, 3 (demo), 4,
  5 (demo), 6 and 7. Fixes from that review:
  - Walked routes now turn into dotted footsteps. As solid lines they read as extra folder walls.
  - The fooled counter was shortened so it fits the phone width.
  - The step 5 counter now says "so far". It counts only the cards tapped, so a "2 of 5" could
    mislead.
- I recorded the lesson with `record.py` to `guardrail-gates.mp4` and `guardrail-gates.gif`: about
  64 s, all 7 steps, with the scripted taps in steps 3 and 5. I made a 1-frame-per-6-s contact sheet
  of the video and checked each step's state and caption. One sampled frame fell on the 230 ms fade
  between steps, which is expected.
- Not checked: playing it on a real phone, and screen-reader output beyond the kit's aria labels.
  The GIF is about 7 MB, under LinkedIn's limits. The MP4 is smaller and sharper. For a shorter
  LinkedIn loop, record one step with `?step=N` and `--seconds`; steps 4 and 6 work best on their
  own.

## Files

- `explainer.html`: the lesson, one self-contained file (the engine is inlined; only the Caveat font
  is loaded from Google Fonts, with a cursive fallback offline).
- `guardrail-gates.mp4`, `guardrail-gates.gif`: recordings of the whole lesson.
- `qa_explainer/`: render-check frames, contact sheets and report.json, plus `rec/` frames from the
  recording.
