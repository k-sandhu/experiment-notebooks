---
name: explainer-kit
description: Engine, styles (four built-in looks or a custom theme with the user's own brand colours and fonts) and quality checks for animated and interactive SVG explainers delivered as one self-contained HTML file (artifact page, claude.ai widget, or GIF/MP4). Provides a scaffold script, a small JavaScript engine (hand-drawn shapes, draw-in reveals, travelling dots, step lessons with fixed controls, a scrubbable timeline player, standalone one-view figures, unit-chart motion, sliders), a render check that walks every step at phone and desktop widths and flags overlaps, moving controls and errors, and a recorder that turns the explainer into MP4 and GIF. Use it whenever you build any animated diagram, step-by-step lesson, interactive explainer or explainer GIF, together with the form skill chosen by explainer-director.
---

# Explainer kit

The kit removes the parts of building an explainer that models get wrong by hand: steps that bleed into
each other, controls that jump when a caption grows, text that shrinks below legibility on a phone,
animations that ignore reduced motion, and no way to check any of it without a human looking. You write
only the scene. The kit runs it, and its scripts look at it for you.

Files (paths relative to this skill's folder):

| File | Use |
|---|---|
| `scripts/scaffold.py` | Start a new explainer with the engine inlined. Kinds: `stepper`, `player`, `explorable`, `figure`. |
| `scripts/check_theme.py` | Check a custom theme's colours (contrast, colour-blind separation) before building with it. |
| `references/themes.md` | Custom themes: your own colours and fonts in a JSON file. Read when the user names a brand, colours or fonts. |
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
   For the user's own colours and fonts, write a theme file and pass `--theme THEME.json` instead of
   `--style` (see `references/themes.md`); the scaffold checks the theme first and refuses one that fails.
   When the data is in a JSON file, add `--data FILE.json`: the scaffold embeds it unchanged as
   `const DATA`, so no number is retyped by hand.
   For one figure with no steps (inside an article, a README, a doc), use `--kind figure`: no Next or Back,
   optional live controls and an optional looping animation with a Pause button. `--controls
   full|minimal|none` sets how much navigation a stepper or player shows: `minimal` keeps only Back and
   Next (or play and scrub), `none` plays and loops by itself with only a Pause button.
3. **Write the scene.** Read `references/api.md`, then build each storyboard step. Use the embedded
   `DATA`, or put a `const DATA = {...}` near the top of the scene, copied from the source files, with a
   comment saying where each value comes from. Compute every number shown on screen from DATA, in code,
   so text and drawing agree and nothing is rounded twice.
4. **Check.** `python scripts/render_check.py OUT.html` (needs Python Playwright). Fix every FAIL.
   Read every WARN and fix it unless you can say why it is harmless. Besides layout it measures text
   contrast from the pixels, finds blank bands and clipped text, and uses every slider, option and
   tappable mark on each step, checking the layout in each state and whether text still names an old
   value. Each check in it comes from a fault that reviewers marked down in tested explainers.
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
- Anything that moves by itself for more than a few seconds has a Pause button: `controls: 'none'` keeps
  one, and a figure with `frame()` gets one. Under reduced motion a stepper or player with `controls: 'none'`
  shows Back and Next (or the scrub bar) instead, and a figure shows one still frame.
- `?step=N` opens at step N; `?record=1` autoplays every step with its demo and hides the buttons.
- `window.EXPLAINER` (and `window.EXPLAINERS` for several on one page) lets the scripts drive any
  explainer built with the kit. Keep it; it is how the checks and the recorder work.

## Rules you must follow in the scene

- **Text size.** The drawing is 380 units wide and renders about 310 px wide on a small phone, so
  1 unit is about 0.82 px. Use at least 14 units for any label (axis ticks included; about 11.5 px on
  screen), 15-16 for labels a reader must read, 18-26 for handwritten headings. Reviewers marked down
  10-12 px chart text in every round; if a chart cannot fit its labels at 14 units, it has too many labels:
  cut ticks, abbreviate, or split the chart. Body text belongs in the caption (HTML), not in the drawing.
- **Contrast.** Text must stay readable when dimmed: dim shapes to 30% if you like, but never take text
  below 50% opacity on the built-in styles, and never put grey text on a mid-tone fill. The check measures
  contrast from the screenshot and warns under 3:1.
- **Crowded charts on a phone.** At about 310 px, three overlapping lines are a tangle. Show the stretch
  that matters (zoom the axis to the forecast week, not three weeks), put at most three series in one
  chart, label lines at their ends instead of in a legend, and give a comparison its own step when it
  needs more. Reviewers flagged overlapping lines in three rounds running.
- **No empty bands.** A step whose drawing fills only half the frame leaves a hole above the controls.
  Size the viewBox height to the busiest step, and give quiet steps a larger drawing, not more space.
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

In every style, each pair of the five data fills stays apart for readers with each common kind of colour
blindness: at least 8 apart (OKLab x 100) under simulated protan, deutan and tritan vision and at least 15
with normal vision, and each fill has contrast of at least 3 against its background
(`python scripts/check_theme.py --builtin` prints the numbers). Earlier versions of the kit met this only
for neighbouring fills; blue and violet looked alike to red-green colour-blind readers until the fills were
re-tuned. Still label marks rather than rely on colour alone. The pastel ink colours were not checked as
data colours: they are for lines and text with labels. Details and reasons are in `references/craft.md`.

### Custom themes

When the user gives brand colours or fonts, put them in a theme file instead of picking a built-in style.
A theme overrides any slot of a base style and keeps the slot names, so every scene works with any
theme. The format, an example and what each slot means are in `references/themes.md`. Run
`python scripts/check_theme.py THEME.json` and fix every FAIL before building; tell the user about any WARN
you leave, such as two brand colours that colour-blind readers cannot tell apart.

## Delivering

- **Artifact or page:** the scaffolded HTML is complete. Give it a `<title>` of two to four words.
- **claude.ai widget:** scaffold with `--fragment`; the widget host supplies fonts and sizing.
- **GIF/MP4:** run `record.py`. Keep each under about 10 MB; split long lessons into one GIF per step
  (`?step=N` plus `--seconds`) if needed.
- Tell the user what was checked (render check result, which widths, whether you looked at every
  step) and what was not.
