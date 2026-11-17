---
name: explainer-kit
description: Engine, styles and quality checks for animated and interactive SVG explainers delivered as one self-contained HTML file (artifact page, claude.ai widget, or GIF/MP4). Provides a scaffold script, a small JavaScript engine (hand-drawn shapes, draw-in reveals, travelling dots, step lessons with fixed controls, a scrubbable timeline player, unit-chart motion, sliders), a render check that walks every step at phone and desktop widths and flags overlaps, moving controls and errors, and a recorder that turns the explainer into MP4 and GIF. Use it whenever you build any animated diagram, step-by-step lesson, interactive explainer or explainer GIF, together with the form skill chosen by explainer-director.
---

# Explainer kit

The kit removes the parts of building an explainer that models get wrong by hand: steps that bleed into
each other, controls that jump when a caption grows, text that shrinks below legibility on a phone,
animations that ignore reduced motion, and no way to check any of it without a human looking. You write
only the scene. The kit runs it, and its scripts look at it for you.

Files (paths relative to this skill's folder):

| File | Use |
|---|---|
| `scripts/scaffold.py` | Start a new explainer with the engine inlined. Kinds: `stepper`, `player`, `explorable`. |
| `assets/kit.js` | The engine itself (window.K). Inlined by the scaffold; read it only to debug. |
| `references/api.md` | Every function with its arguments and a short example. Read before writing the scene. |
| `references/craft.md` | Motion, layout, typography and colour rules with the reasons behind them. |
| `scripts/render_check.py` | Walk every step at 360 px and 560 px, save frames and contact sheets, report faults. |
| `scripts/record.py` | Record the explainer to MP4 and GIF, scripted demos included. |

## Workflow

1. **Storyboard first.** Use `explainer-director` if you have not decided the message, form and steps.
2. **Scaffold.**
   `python scripts/scaffold.py OUT.html --kind stepper --style chalkboard --title "Short name"`
   The file contains the engine and an example scene. Replace the example scene; keep the rest.
   For a claude.ai chat widget add `--fragment` (no html/head/body) and pass the file's text to the widget tool.
3. **Write the scene.** Read `references/api.md`, then build each storyboard step. Put data in a
   `const DATA = {...}` near the top of the scene, copied from the source files, with a comment saying
   where each value comes from. Compute every number shown on screen from DATA so text and drawing agree.
4. **Check.** `python scripts/render_check.py OUT.html` (needs Python Playwright). Fix every FAIL.
   Read every WARN and fix it unless you can say why it is harmless.
5. **Look.** Open the contact sheets it prints (`qa_<name>/sheet_w360.png` and `sheet_w560.png`) with
   your image viewer or Read tool. Check each step against its storyboard line: is the one idea visible,
   is the active thing highlighted, does the caption match what is on screen, is anything cramped? The
   script finds layout faults; only looking finds unclear explanations. Fix, re-run, look again.
6. **Record (when a GIF or video is wanted).** `python scripts/record.py OUT.html --out NAME`
   writes NAME.mp4 and NAME.gif. Steps with a `demo()` perform their taps on camera. MP4 is a third of
   the size and sharper; prefer it for LinkedIn and slides. Check one frame per step of the result.

If Playwright or ffmpeg is missing, say so and skip that step rather than claiming it passed.

## Rules the kit already enforces (do not undo them)

- Each step runs in its own generation. `s.at`, `s.loop`, `s.tween`, `s.travel` stop when the reader
  leaves the step. Never use bare `setTimeout` or `requestAnimationFrame` in a step.
- The caption area reserves the height of the longest caption, and the action row reserves 44 px
  (raise it with `actHeight` when a step holds a slider), so Back, the dots and Next never move.
- Reduced motion: reveals appear at once, travelling dots jump to the end, the player jumps chapter to
  chapter. Write steps so their final state carries the meaning without the motion.
- An idle demo stops for good as soon as the reader taps, drags or presses anything; `autoplay` stops too.
- `?step=N` opens at step N; `?record=1` autoplays every step with its demo and hides the buttons.
- `window.EXPLAINER` (and `window.EXPLAINERS` for several on one page) lets the scripts drive any
  explainer built with the kit. Keep it; it is how the checks and the recorder work.

## Rules you must follow in the scene

- **Text size.** The drawing is 380 units wide and renders about 310 px wide on a small phone, so
  1 unit is about 0.82 px. Use at least 13 units for any label (axis ticks included), 14-15 for labels a reader
  must read, 18-26 for handwritten headings. Reviewers consistently called 10-11 px chart text too small on a phone;
  if a chart cannot fit its labels at 13 units, it has too many labels: cut ticks, abbreviate, or split the chart. Body text belongs in the caption (HTML), not in the drawing.
- **Fit.** Keep every element inside the viewBox with a 12-unit margin. Long labels: shorten them, or
  move the detail to the caption. Never let text cross a line or another label; the check reports it.
- **Colour.** Use the style's named colours (`'blue'`, `'green'`, `'amber'`, `'violet'`, `'red'` for
  ink; `'fill.blue'` etc. for data fills; `'ink'`, `'mut'`, `'faint'` for neutrals). One colour, one
  meaning, kept across steps and listed in the legend. Never rely on colour alone: label or shape too.
- **Seeds.** Give each hand-drawn shape its own seed number so its wobble stays fixed; reuse a seed only
  to redraw the same shape.
- **Order of reveal.** Stagger with the `t` delay so the drawing appears in reading order: frame, then
  labels, then connectors, then the thing that moves. 2-4 seconds of reveal per step is plenty.
- **Durations.** Give each step a `duration` (ms until its animation settles). Recording, checks and
  autoplay use it. Add `demo()` to every hands-on step so passive readers and GIFs still see the
  interaction, and `idleDemo` (about 5000 ms) so it runs if the reader does nothing.

## Styles

| Style | Look | Use for |
|---|---|---|
| `chalkboard` (default) | Charcoal board, warm off-white ink, pastel accents, Caveat handwriting, rough lines | Lessons, concepts, social GIFs |
| `paper` | Warm paper, dark ink, Kalam handwriting, lighter wobble | Friendly explainers on light pages |
| `editorial` | White, crisp lines, serif headings, no wobble | Data stories next to an article or README |
| `blueprint` | Navy grid, mono labels, crisp lines | Systems, pipelines, agent harnesses |

The data fills of each style were checked for colour-blind separation against its background with a
palette validator (adjacent pairs ΔE ≥ 8 under protan, deutan and tritan simulation). The pastel ink
colours were not: they are for lines and text with labels, not for telling categories apart in a chart.
Details and reasons are in `references/craft.md`.

## Delivering

- **Artifact or page:** the scaffolded HTML is complete. Give it a `<title>` of two to four words.
- **claude.ai widget:** scaffold with `--fragment`; the widget host supplies fonts and sizing.
- **GIF/MP4:** run `record.py`. Keep each under about 10 MB; split long lessons into one GIF per step
  (`?step=N` plus `--seconds`) if needed.
- Tell the user what was checked (render check result, which widths, whether you looked at every
  step) and what was not.
