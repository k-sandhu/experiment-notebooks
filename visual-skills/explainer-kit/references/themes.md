# Custom themes

A theme replaces the colours and fonts of a built-in style with the user's own, for an explainer that
has to carry a brand: a company post, a product page, a client report. It is a small JSON file. Pass it
to the scaffold instead of a style name:

```
python scripts/scaffold.py OUT.html --kind stepper --theme brand.json --title "Short name"
```

The scaffold checks the theme first (`scripts/check_theme.py`), prints the report, and refuses a theme that
fails unless you add `--force`. If you force it, tell the user which check failed and what that costs
their readers.

## How a theme works

A theme starts from a built-in style (its `base`) and overrides only the keys it gives. Anything left out
keeps the base's value. When there is no `base`, the theme starts from `editorial` on a light background or
`blueprint` (without its grid) on a dark one, so a theme of just colours gets crisp lines and plain
headings.

The colour slots keep their names whatever colours they hold. A scene asks for `'blue'` or `'fill.amber'`,
and the theme decides what that looks like. So the same scene code works with every style and theme, and
switching theme never means editing the scene.

## Slots

| Key | What it is | Notes |
|---|---|---|
| `base` | Built-in style to start from | `chalkboard`, `paper`, `editorial`, `blueprint`. Optional. |
| `dark` | 1 for a dark background, 0 for light | Optional; worked out from `bg` when left out. |
| `bg` | Background of the explainer card | |
| `panel` | Background of boxes inside the card (log, panels) | Close to `bg`. |
| `pageBg` | Page around the card | Optional; a shade of `bg` when left out. |
| `ink` | Main text and strokes | Needs contrast of 7 or more against `bg`. |
| `mut` | Secondary text: captions of axes, counters, legend | Needs 4.5 or more against `bg`. |
| `faint` | Context lines, dimmed elements | |
| `line` | Borders of buttons and panels | |
| `blue`, `amber`, `green`, `violet`, `red` | Ink colours for strokes and coloured text | Used for lines and labels, so they need contrast against `bg`. |
| `fill.blue` ... `fill.red` | Data colours for bars, dots and areas | Checked for colour-blind separation. |
| `hand` | Font family for headings and hand-written labels | CSS font-family, e.g. `"'Space Grotesk', sans-serif"`. |
| `handSize` | Size factor for `hand` text | 1 = as written; script fonts often need 1.1, mono 0.8. |
| `sans` | Font family for captions, buttons and body labels | Optional; system sans-serif when left out. |
| `font` | Google Fonts stylesheet URL (or a list of URLs) that loads `hand` and `sans` | Leave out for fonts the reader already has. |
| `rough` | Hand-drawn wobble, 0 to 1 | 0 = straight lines, 1 = chalkboard. |
| `texture` | 1 adds the chalk speckle | Only suits dark backgrounds. |
| `grid` | 1 adds a blueprint grid | |

### What the colour slots mean

The kit uses each slot for one kind of thing, so a reader can learn a colour once and keep it:

| Slot | Default meaning |
|---|---|
| `amber` | The human, the person doing the task |
| `violet` | The model or the agent |
| `green` | A tool call, work in progress, or success |
| `blue` | Data, a result |
| `red` | An error or a cost |

When mapping brand colours, put the brand's main colour in the slot whose meaning fits the story (often
`blue` for data). Keep `red` reddish and `green` greenish: readers read red as bad and green as good, and the
check warns when they drift. A story can change the meanings, as long as the legend says so.

Data fills are assigned in the order blue, amber, green, violet, red, and the check requires each
neighbour in that order to be distinct for colour-blind readers. Order the brand's data colours so the two
that look most alike are not neighbours.

## Example

A light brand with a teal main colour, Space Grotesk headings and Inter text. This theme passes every
check except one warning (green and red are close for deuteranopes, as they are in most palettes):

```json
{
  "name": "Harbor",
  "bg": "#FFFFFF", "panel": "#F2F6F7", "ink": "#13232E", "mut": "#4E5D66", "faint": "#D3DCE0", "line": "#B9C6CC",
  "blue": "#0F6E8C", "amber": "#B86E00", "green": "#2E7D4F", "violet": "#6C4AB6", "red": "#C2364A",
  "fill": {"blue": "#0F6E8C", "amber": "#B87400", "green": "#2A9468", "violet": "#7A55C7", "red": "#D1495B"},
  "hand": "'Space Grotesk', system-ui, sans-serif", "handSize": 0.95,
  "font": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;600&display=swap",
  "sans": "'Inter', system-ui, sans-serif",
  "rough": 0
}
```

A dark variant needs only `"dark": 1` and dark `bg`, `panel`, light `ink` and `mut`; lighter fills read
better on dark backgrounds.

## The check

```
python scripts/check_theme.py brand.json        # PASS, WARN or FAIL, with the reason for each
python scripts/check_theme.py --builtin         # the same checks on the four built-in styles
```

| Check | Pass | Warn | Fail |
|---|---|---|---|
| `ink` on `bg` and `panel` (contrast ratio) | 7 or more | 4.5 to 7 | under 4.5 |
| `mut` on `bg` and `panel` | 4.5 or more | 3 to 4.5 | under 3 |
| Each fill and accent ink on `bg` | 3 or more | 2 to 3 | under 2 |
| Neighbouring fills, normal vision (OKLab distance x 100) | 15 or more | 10 to 15 | under 10 |
| Neighbouring fills, protan, deutan, tritan simulation | 8 or more | 6 to 8 | under 6 |
| Non-neighbouring fills that nearly collide | | listed | |
| `red` and `green` still look red and green | | listed | |

Contrast is the WCAG 2 ratio. Colour-blind vision is simulated with the Machado, Oliveira and Fernandes
(2009) matrices at full severity. When the user's brand colours fail, show them the failing pair and
suggest the nearest shade that passes (darker or lighter, same hue), rather than silently changing their
colours.
