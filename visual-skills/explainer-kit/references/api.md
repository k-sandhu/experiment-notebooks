# explainer-kit API

Everything hangs off `window.K`. Coordinates are viewBox units (default 380 x 300). Times are milliseconds.
Colours are names from the active style (`'ink'`, `'mut'`, `'faint'`, `'blue'`, `'green'`, `'amber'`,
`'violet'`, `'red'`, data fills `'fill.blue'` ... `'fill.red'`) or any CSS colour. `K.C` holds the active
values, e.g. `K.C.fill.green`, for use inside template strings.

Contents: 1 Engines (stepper, player) · 2 Drawing (shapes, markup builders) · 3 Step context `s`
(motion, text, interaction, units) · 4 Controls (slider, toggle) · 5 Helpers · 6 Patterns

## 1. Engines

### K.stepper(options) → api
A lesson of steps with Back, step dots, Replay and Next. Options:

| Option | Meaning |
|---|---|
| `root` | Selector or element to build into (e.g. `'#x'`). |
| `style` | `'chalkboard'` (default), `'paper'`, `'editorial'`, `'blueprint'`, or a theme object with your own colours and fonts (`references/themes.md`; `scaffold.py --theme` writes it in for you). |
| `viewBox` | `[w, h]`, default `[380, 300]`. Keep 380 wide for phones and GIFs; height 260-440. |
| `title` | One sentence describing the whole explainer, read by screen readers. |
| `legend` | `[{key, label, color}]`. Steps list the keys they use; others dim to 30%. |
| `steps` | Array of step objects (below). |
| `actHeight` | Reserved height in px of the action row (default 44). Use 76 for a slider, more for two. |
| `hold` | Pause after each step in autoplay/recording (default 2200). |
| `autoplay` | `true` plays every step once on load; `'loop'` repeats. A reader who taps anything takes over. Use for feed posts and GIF-like cards. |
| `extraCaptions` | Captions you will set at run time with `s.cap()`, so their height is reserved. |

Step object:

| Field | Meaning |
|---|---|
| `title` | Handwritten heading above the drawing, e.g. `'2. Switching was expensive'`. |
| `cap` | Caption under the drawing, 1-2 sentences, <= 220 characters. |
| `keys` | Legend keys this step uses. |
| `draw(K)` | Returns SVG markup (string) for the static scene. Elements made with `P`, `T`, `F` reveal in order of their `t` delay. |
| `start(s)` | Runs after the scene is drawn. Animate and wire interactions here with the step context `s`. |
| `duration` | ms until the step's animation settles. Used by autoplay, recording and the render check. |
| `capDelay` | ms before the caption fades in (default 300). |
| `demo(s)` | Optional async function that performs the step's interaction (taps, drags, slider moves) for passive viewers and recordings. Use `s.tap(el)` and `await s.wait(ms)`. |
| `ask` | `true` for a step that asks the reader a question. Its demo then runs only in recordings and autoplay, never on an idle timer, and the step waits for the reader's answer. |
| `idleDemo` | ms of no interaction after which `demo` runs by itself (about 5000). |
| `demoDuration` | ms the demo takes (recording waits this long). |
| `alt` | Text alternative for the drawing if the caption is not enough. |

The returned api (also `window.EXPLAINER`): `go(i)`, `count`, `current`, `duration(i)`, `demo(i)`, `autoplay()`, `ready` (Promise).

### K.player(options) → api
A scrubbable timeline: Play/Pause, a scrub bar, a time readout, chapter dots and an optional event log.
Use it for replays of recorded runs and anything where the reader should be able to stop time.

| Option | Meaning |
|---|---|
| `root`, `style`, `viewBox`, `title`, `legend` | As for the stepper. |
| `duration` | Total timeline length in ms of animation time. |
| `scene(K)` | Static markup drawn once (lanes, boxes, axes, labels). |
| `frame(t, s)` | Draws the moving layer for time `t`. Must be a pure function of `t`: clear `s.dyn` and redraw, never accumulate state. |
| `chapters` | `[{at, title, cap, keys}]`: stretches of the timeline with their own heading and caption. |
| `log` | Optional `[{t, text, c}]` events; the last 6 with `t <= now` show in a terminal-like panel. Start text with `→` call, `←` result, `✗` error, `✓` done, `•` note. |
| `clock(t)` | Optional readout text, e.g. `t => (t / 1000 * 10).toFixed(0) + ' s of the real run'`. |
| `speed` | Playback speed multiplier (default 1). |
| `autoplay` | Start playing on load (default true). |

api: `go(i)` (jump to chapter i and play), `seek(t)`, `play()`, `pause()`, `time`, `count`, `duration(i)`.

## 2. Drawing

Shape functions return SVG path data. The `seed` fixes the hand-drawn wobble (styles with `rough: 0` draw straight).

| Function | Draws |
|---|---|
| `K.line(x1, y1, x2, y2, seed, bow=1.6)` | Slightly bowed line. |
| `K.rect(x, y, w, h, seed)` | Hand-drawn box with an overshoot at the start corner. |
| `K.ellipse(cx, cy, rx, ry, seed)` | Hand-drawn ellipse or circle. |
| `K.arrow(fromX, fromY, x, y, seed, len=8)` | Arrowhead at (x, y) pointing away from (fromX, fromY). Pair with a line. |
| `K.poly([[x,y],...], seed)` | Polyline through points. |
| `K.curve(x1, y1, x2, y2, bend=.3)` | Smooth connector with a bend (positive bends left). |

Markup builders return strings to concatenate in `draw()` or `scene()`:

| Builder | Makes |
|---|---|
| `K.P(d, color, t=0, dur=600, width=1.5, extra='')` | A stroked path that draws itself in, starting at `t`. |
| `K.T(x, y, text, o)` | Text that fades in. `o`: `h` handwriting, `m` mono, `z` size (units), `a` anchor (`'start'`, `'middle'`, `'end'`), `c` colour, `t` delay, `w` weight, `id`, `raw` (text is markup, e.g. `<tspan>`). |
| `K.F(d, color, t=0, o)` | A filled shape that fades in. `o.op` opacity (default .85), `o.id`. |

Plain SVG elements in the markup are shown at once. Give elements an `id` to animate them in `start()`.
A bar that will grow: `<rect id="b" ... style="transform-box:fill-box;transform-origin:0 50%;transform:scaleX(0)"/>`, then `s.bar('#b', .6)`.

## 3. Step context `s`

Passed to `start(s)`, `demo(s)` and `frame(t, s)`. Everything on it stops when the step changes.

Timing:
- `s.at(ms, fn)` run later. `await s.wait(ms)` inside async code.
- `s.loop(delay, st => {...})` per-frame loop; `st.dt` seconds since last frame, `st.e` ms since start. Return `false` to stop.
- `s.tween(dur, k => {...}, {delay, ease})` calls with k from 0 to 1; returns a Promise. Eases: `'inOut'` (default), `'out'`, `'linear'`.

Motion and emphasis:
- `s.drawIn(el, dur=500, delay=0)` draw a path in. `s.fadeIn(el, dur, delay)`, `s.fadeOut(el, dur, remove=true)`.
- `s.travel(pathElOrPoints, dur=600, color='ink', {r, delay, trail, keep})` dot travelling along a path element or `[[x,y],...]`; returns a Promise. Use for data, calls and messages moving between parts.
- `s.ring(x, y, w, h, color)` a pulse outline around a region (draws attention, then fades).
- `s.bar(elOrSel, frac, dur=600, axis='x')` grow or shrink a bar (`axis 'y'` grows upward).
- `s.count(elOrSel, to, {from, du, fmt, pre, post, delay})` count a number up or down in a text element.
- `s.swap(elOrSel, text, color)` quick fade-swap of a text's content.

Text and elements:
- `s.write(x, y, text, o)` add text (same options as `K.T`) to the dynamic layer, fading in.
- `s.float(x, y, text, color, size)` text that rises and fades (+1, "still working").
- `s.el(tag, attrs, parent=s.dyn)` create an SVG element. `s.q(selector)` find inside the drawing. `s.dyn` is the layer for moving things.
- `s.cap(text)` replace the caption (list such texts in `extraCaptions`).

Interaction:
- `s.btn(icon, label, fn, {primary})` add a button to the action row under the caption. Icons: `left`, `right`, `play`, `pause`, `replay`, `check`, `restart`, or `''`.
- `s.on(elOrSel, fn, ariaLabel)` make an SVG element tappable and keyboard-operable (Enter/Space). Give it a transparent `<rect>` hit area of at least 36 x 36 units.
- `s.drag(elOrSel, {move(p, ev), end(p, ev)})` pointer drag in viewBox coordinates (`p.x`, `p.y`).
- `s.point(event)` convert a pointer event to viewBox coordinates.
- `s.tap(elOrSel)` (for demos) show a ripple at the element and click it.
- `s.touched()` mark that the reader interacted (cancels the idle demo; buttons and `s.on` call it for you).
- `s.act` the action-row element (place sliders here), `s.root` the explainer element.

Units (one mark per item; marks keep identity when they move):
- `s.units(items, {r=4, fill, x0, y0, parent})` create one circle per item. Returns `[{it, c, x, y, r}]`.
- `s.arrange(layout, {du=900, stagger=4, ease, delay})` move every unit to `layout(item, index)` → `{x, y, r, fill, opacity, order}`; `order` sets who moves first. Returns a Promise.

## 4. Controls for explorables

- `K.slider(parent, {label, min, max, step, value, fmt, oninput})` → `{el, input, value, set(v)}`. A labelled range input with a live value readout; `oninput(v)` runs at once and on every change.
- `K.toggle(parent, {label, value, onchange})` → button with `aria-pressed`.

Place them in `s.act` and set `actHeight` on the stepper so the controls below never move.

## 5. Helpers

- `K.scale(d0, d1, r0, r1)` linear scale; `.invert(p)` goes back.
- `K.grid(j, {cols, x0, y0, gap, gapY})` → `{x, y}` for the j-th cell of a grid (for unit charts).
- `K.wilson(k, n)` → `[low, high]` 95% interval for k successes in n trials. Use it whenever a small sample is shown as a rate.
- `K.fmt.int(v)`, `K.fmt.pct(v, d)`, `K.fmt.usd(v, d)`, `K.fmt.sec(v)`.
- `K.rng(seed)` seeded random numbers (use for any simulation so replays match).
- `K.clamp`, `K.lerp`, `K.ease`, `K.esc` (escape text for markup), `K.col(name)` (colour lookup).

## 6. Patterns

Highlight one part and dim the rest:
```js
const focus = ids => ['a','b','c'].forEach(id => s.q('#' + id).style.opacity = !ids || ids.includes(id) ? 1 : .28);
// give the groups class-free ids and style="transition:opacity .45s" in draw()
```

A call that goes out and comes back with a result card:
```js
await s.travel([[190,170],[190,228]], 400, 'green');      // request
s.ring(96, 224, 188, 52, 'ink');                            // the router reacts
await s.travel([[190,228],[190,170]], 400, 'blue');         // data returns
s.swap('#status', '← 412 rows', 'blue');
```

A frame function for a replay of recorded spans (pure in t):
```js
frame(t, s) {
  s.dyn.innerHTML = '';
  const now = t / SPEED;                                  // seconds of the real run
  RUN.spans.forEach(sp => { if (sp.start >= now) return;
    const x0 = X(sp.start), x1 = X(Math.min(now, sp.end));
    s.el('rect', {x: x0, y: LANE[sp.agent] - 7, width: Math.max(.5, x1 - x0), height: 14, rx: 3, fill: K.col(KIND[sp.kind])}); });
  s.el('line', {x1: X(now), x2: X(now), y1: 40, y2: 260, stroke: K.C.ink, 'stroke-opacity': .5});
}
```

A hands-on step that demonstrates itself:
```js
{ title: '2. Your turn', cap: 'Tap a ticket to route it through both queues.',
  start(s) { ITEMS.forEach((it, i) => s.on('#req' + i, () => judge(s, i), 'Send ' + it.label)); },
  demo: async s => { for (const i of [0, 3]) { s.tap('#req' + i); await s.wait(1800); } },
  idleDemo: 5000, demoDuration: 3800, duration: 1500 }
```

Units regrouped by outcome, keeping identity:
```js
const U = s.units(ITEMS, {r: 4.2, fill: 'faint'});
await s.arrange((it, j) => ({...K.grid(j, {cols: 20, x0: 22, y0: 80, gap: 11.5}), fill: it.failed ? 'fill.red' : 'fill.blue'}), {stagger: 6});
```
