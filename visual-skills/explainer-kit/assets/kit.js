/* explainer-kit v1. A small engine for animated, stepwise SVG explainers. No dependencies.
   Exposes window.K. Read explainer-kit/SKILL.md for the API and the rules it encodes.
   Every animation is tied to a "generation": moving to another step cancels all timers,
   loops and tweens of the old step, so steps can never bleed into each other. */
(function () {
'use strict';
const NS = 'http://www.w3.org/2000/svg';
const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
const QS = new URLSearchParams(location.search);
const REC = QS.has('record');
const f = n => (+n).toFixed(1);
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const lerp = (a, b, k) => a + (b - a) * k;
const ease = { inOut: k => k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2, out: k => 1 - Math.pow(1 - k, 3), linear: k => k };
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
function rng(seed) { let a = seed >>> 0; return () => { a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

/* ---------- styles: one object per look. ink colours draw lines and text; fill colours encode data
   (fills were checked for colour-blind separation against their background). */
const STYLES = {
  chalkboard: { dark: 1, bg: '#1E2023', panel: '#17191B', ink: '#ECE7DA', mut: '#9A9A93', faint: '#55585E', line: '#4A4D53',
    blue: '#9CC3E6', green: '#A8DDC3', amber: '#F2D98B', violet: '#C3B5E8', red: '#EBA494',
    fill: { blue: '#4A8FDB', amber: '#BF8420', green: '#2FA876', violet: '#A070E8', red: '#E8604F' },
    rough: 1, texture: 1, hand: "'Caveat', cursive", handSize: 1.12, font: 'https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&display=swap' },
  paper: { dark: 0, bg: '#FBF8F1', panel: '#F3EEE3', ink: '#22252A', mut: '#5F6368', faint: '#C9C3B6', line: '#BDB6A8',
    blue: '#2F6DB5', green: '#1E7F55', amber: '#C27C12', violet: '#7B5EA7', red: '#C8553D',
    fill: { blue: '#2F6DB5', amber: '#C27C12', green: '#1E7F55', violet: '#7B5EA7', red: '#C8553D' },
    rough: .7, texture: 0, hand: "'Kalam', cursive", handSize: 1, font: 'https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap' },
  editorial: { dark: 0, bg: '#FFFFFF', panel: '#F5F5F2', ink: '#1A1A1A', mut: '#5C5C5C', faint: '#D6D6D0', line: '#C4C4BE',
    blue: '#2F6DB5', green: '#1E7F55', amber: '#C27C12', violet: '#7B5EA7', red: '#C8553D',
    fill: { blue: '#2F6DB5', amber: '#C27C12', green: '#1E7F55', violet: '#7B5EA7', red: '#C8553D' },
    rough: 0, texture: 0, hand: "'Source Serif 4', Georgia, serif", handSize: .9, font: 'https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&display=swap' },
  blueprint: { dark: 1, bg: '#10243A', panel: '#0C1C2E', ink: '#E6EEF5', mut: '#93A8BC', faint: '#3A5672', line: '#4A6A89',
    blue: '#8EC5F0', green: '#9BE0C0', amber: '#F5D58A', violet: '#C9B8F2', red: '#F2A08F',
    fill: { blue: '#4A8FDB', amber: '#BF8420', green: '#2FA876', violet: '#A070E8', red: '#E8604F' },
    rough: 0, texture: 0, grid: 1, hand: "'IBM Plex Mono', ui-monospace, monospace", handSize: .78, font: 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&display=swap' },
};
let ST = STYLES.chalkboard, ROUGH = 1;
const C = {};                                   // active colours, e.g. K.C.ink, K.C.fill.blue
function col(c) { if (!c) return C.ink; if (c[0] === '#' || c.startsWith('rgb') || c === 'none' || c === 'transparent') return c; if (c.startsWith('fill.')) return C.fill[c.slice(5)] || c; return C[c] || c; }
/* A theme is an object instead of a style name: your own colours and fonts merged over a built-in base
   (references/themes.md). Slot names stay the same, so scene code works with any theme. */
function resolveStyle(name) {
  if (name && typeof name === 'object') {
    const t = name, lum = h => { const v = [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4); return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; };
    const dark = 'dark' in t ? !!t.dark : (t.bg ? lum(t.bg) < .18 : false);
    const base = t.base in STYLES ? t.base : dark ? 'blueprint' : 'editorial';
    const st = { ...STYLES[base], ...t, fill: { ...STYLES[base].fill, ...(t.fill || {}) }, dark: dark ? 1 : 0 };
    if (!t.base && !('grid' in t)) st.grid = 0;
    if (t.hand && !('font' in t)) st.font = null;           // a theme font that is installed locally, or a system font
    return [st, base];
  }
  return name in STYLES ? [STYLES[name], name] : [STYLES.chalkboard, 'chalkboard'];
}
function useStyle(name, root) {
  let base; [ST, base] = resolveStyle(name); ROUGH = ST.rough || 0;
  Object.keys(C).forEach(k => delete C[k]); Object.assign(C, ST, { fill: { ...ST.fill } });
  injectCSS();
  [].concat(ST.font || []).forEach(u => { if (!document.querySelector(`link[href="${u}"]`)) { const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = u; document.head.appendChild(l); } });
  if (root) {
    const v = { bg: ST.bg, panel: ST.panel, ink: ST.ink, mut: ST.mut, faint: ST.faint, line: ST.line, blue: ST.blue, green: ST.green, amber: ST.amber, violet: ST.violet, red: ST.red, hand: ST.hand };
    for (const k in v) root.style.setProperty('--k-' + k, v[k]);
    if (ST.sans) root.style.setProperty('--font-sans', ST.sans);
    root.classList.add('kx', 'kx-' + base);
    if (ST.texture) { const r = rng(9); let s = ''; for (let i = 0; i < 140; i++) s += `<circle cx='${(r() * 240).toFixed(1)}' cy='${(r() * 240).toFixed(1)}' r='${(.4 + r() * .8).toFixed(2)}' fill='%23ffffff' fill-opacity='${(.02 + r() * .045).toFixed(3)}'/>`; root.style.backgroundImage = `url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>${s}</svg>")`; }
    if (ST.grid) root.style.backgroundImage = `linear-gradient(${ST.faint}55 1px,transparent 1px),linear-gradient(90deg,${ST.faint}55 1px,transparent 1px)`, root.style.backgroundSize = '20px 20px';
  }
  return ST;
}
function fontsReady(ms = 1500) { const fams = [ST.hand, ST.sans].filter(Boolean).map(h => h.split(',')[0]); return Promise.race([document.fonts ? document.fonts.ready.then(() => Promise.all(fams.map(f => document.fonts.load(`20px ${f}`)))) : Promise.resolve(), new Promise(r => setTimeout(r, ms))]).catch(() => {}); }

/* ---------- hand-drawn geometry. Each shape takes a seed so its wobble is identical on every frame. */
const J = (r, a) => (r() - .5) * 2 * a * ROUGH;
function line(x1, y1, x2, y2, seed = 1, bow = 1.6) { const r = rng(seed); return `M${f(x1 + J(r, .5))} ${f(y1 + J(r, .5))} Q${f((x1 + x2) / 2 + J(r, bow))} ${f((y1 + y2) / 2 + J(r, bow))} ${f(x2)} ${f(y2)}`; }
function rect(x, y, w, h, seed = 1) {
  if (!ROUGH) return `M${f(x)} ${f(y)}H${f(x + w)}V${f(y + h)}H${f(x)}Z`;
  const r = rng(seed), p = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]].map(q => [q[0] + J(r, 1.3), q[1] + J(r, 1.3)]);
  let d = `M${f(p[0][0])} ${f(p[0][1])}`;
  for (let i = 0; i < 4; i++) { const A = p[i], B = p[(i + 1) % 4]; d += ` Q${f((A[0] + B[0]) / 2 + J(r, 1.5))} ${f((A[1] + B[1]) / 2 + J(r, 1.5))} ${f(B[0])} ${f(B[1])}`; }
  return d + ` L${f(p[0][0] + (p[1][0] - p[0][0]) * .08)} ${f(p[0][1] + J(r, 1))}`;
}
function ellipse(cx, cy, rx, ry = rx, seed = 1) { const r = rng(seed); return `M${f(cx - rx)} ${f(cy)} A${f(rx)} ${f(ry + J(r, .6))} 0 1 0 ${f(cx + rx)} ${f(cy + J(r, .6))} A${f(rx)} ${f(ry + J(r, .6))} 0 1 0 ${f(cx - rx + 1.5 * ROUGH)} ${f(cy + .6 * ROUGH)}`; }
function arrow(fx, fy, x, y, seed = 1, L = 8) { const a = Math.atan2(y - fy, x - fx), r = rng(seed), k = .5 + J(r, .06); return `M${f(x - L * Math.cos(a - k))} ${f(y - L * Math.sin(a - k))} L${f(x)} ${f(y)} L${f(x - L * Math.cos(a + k))} ${f(y - L * Math.sin(a + k))}`; }
function poly(pts, seed = 1) { const r = rng(seed); return 'M' + pts.map((p, i) => `${f(p[0] + (i ? J(r, .6) : 0))} ${f(p[1] + (i ? J(r, .6) : 0))}`).join(' L'); }
function curve(x1, y1, x2, y2, bend = .3) { const mx = (x1 + x2) / 2, my = (y1 + y2) / 2, dx = x2 - x1, dy = y2 - y1; return `M${f(x1)} ${f(y1)} Q${f(mx - dy * bend)} ${f(my + dx * bend)} ${f(x2)} ${f(y2)}`; }

/* ---------- markup builders. Elements carry data-k (draw|fade), data-t (delay ms) and data-d (duration ms);
   the engine reveals them in that order when a step opens, and shows them at once with reduced motion. */
function P(d, c, t = 0, du = 600, w = 1.5, extra = '') { return `<path d="${d}" fill="none" stroke="${col(c)}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round" data-k="draw" data-t="${t}" data-d="${du}" ${extra}/>`; }
function T(x, y, s, o = {}) {
  const fam = o.h ? 'var(--k-hand)' : o.m ? 'var(--font-mono, ui-monospace, Menlo, monospace)' : 'var(--font-sans, system-ui, -apple-system, Segoe UI, Roboto, sans-serif)';
  const z = (o.z || 12) * (o.h ? ST.handSize : 1);
  return `<text${o.id ? ` id="${o.id}"` : ''} x="${x}" y="${y}" text-anchor="${o.a || 'middle'}" font-size="${f(z)}"${o.w ? ` font-weight="${o.w}"` : ''} fill="${col(o.c)}" style="font-family:${fam};font-variant-numeric:tabular-nums" data-k="fade" data-t="${o.t || 0}" data-d="${o.d || 450}"${o.extra ? ' ' + o.extra : ''}>${o.raw ? s : esc(s)}</text>`;
}
function F(shape, c, t = 0, o = {}) { return `<path d="${shape}" fill="${col(c)}" fill-opacity="${o.op == null ? .85 : o.op}" stroke="none" data-k="fade" data-t="${t}" data-d="${o.d || 450}"${o.id ? ` id="${o.id}"` : ''}/>`; }
function reveal(svg) {
  const els = [...svg.querySelectorAll('[data-k]')];
  if (RM) { els.forEach(e => { e.style.opacity = 1; e.style.strokeDashoffset = 0; }); return 0; }
  let end = 0;
  els.forEach(e => { e.style.transition = 'none'; const t = +e.dataset.t, d = +e.dataset.d; end = Math.max(end, t + d); if (e.dataset.k === 'draw') { const L = e.getTotalLength() + 1; e.style.strokeDasharray = L + ' ' + L; e.style.strokeDashoffset = L; } else e.style.opacity = 0; });
  svg.getBoundingClientRect();
  requestAnimationFrame(() => requestAnimationFrame(() => els.forEach(e => { const t = e.dataset.t, d = e.dataset.d; if (e.dataset.k === 'draw') { e.style.transition = `stroke-dashoffset ${d}ms cubic-bezier(.45,0,.55,1) ${t}ms`; e.style.strokeDashoffset = 0; } else { e.style.transition = `opacity ${d}ms ease ${t}ms`; e.style.opacity = 1; } })));
  return end;
}
function finish(svg) { svg.querySelectorAll('[data-k]').forEach(e => { e.style.transition = 'none'; e.style.strokeDashoffset = 0; e.style.opacity = 1; }); }

/* ---------- small DOM helpers */
function mk(tag, attrs = {}, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
const ICON = {
  left: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  right: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  play: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>',
  pause: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor"/></svg>',
  replay: '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.6-5.9M4 4v4h4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  check: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M5 12l5 5 9-10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  restart: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M9 14L4 9l5-5M4 9h11a5 5 0 0 1 0 10h-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
};
let cssDone = false;
function injectCSS() {
  if (cssDone) return; cssDone = true;
  const s = document.createElement('style');
  s.textContent = `.kx{background-color:var(--k-bg);color:var(--k-ink);border-radius:16px;padding:14px 10px 12px;font-family:var(--font-sans,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif);max-width:560px;margin:0 auto;position:relative;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
.kx *{box-sizing:border-box}.kx svg.kx-stage{display:block;width:100%;height:auto;overflow:visible;transition:opacity .22s ease}
.kx-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px;margin:0 6px;min-height:28px}
.kx-title{font-family:var(--k-hand);font-size:23px;line-height:1.15}.kx-blueprint .kx-title,.kx-editorial .kx-title{font-size:19px}
.kx-count{font-size:11px;color:var(--k-mut);white-space:nowrap;font-variant-numeric:tabular-nums}
.kx-cap{font-size:13.5px;line-height:1.55;margin:6px 8px 8px;color:var(--k-ink)}
.kx-act{display:flex;justify-content:center;align-items:center;gap:8px;min-height:44px;flex-wrap:wrap;margin:0 4px 4px}
.kx-legend{display:flex;flex-wrap:wrap;align-content:flex-start;gap:4px 12px;font-size:12px;color:var(--k-mut);margin:6px 8px 8px;min-height:40px}.kx-legend>span{transition:opacity .4s}
.kx-sw{display:inline-block;width:12px;height:4px;border-radius:2px;vertical-align:middle;margin-right:5px}
.kx-nav{display:flex;align-items:center;gap:8px}.kx button.kx-next{min-width:112px}.kx-act .kx-ctl{flex:1 1 100%}
@media (max-width:480px){.kx{padding:12px 8px 10px}.kx button.kx-next{min-width:96px;padding:0 8px}.kx button.kx-dot{padding:10px 3px}.kx-nav{gap:6px}}
.kx button{background:transparent;border:1px solid var(--k-line);color:var(--k-ink);border-radius:8px;padding:0 12px;font:inherit;font-size:13px;min-height:40px;min-width:40px;display:inline-flex;align-items:center;justify-content:center;gap:5px;cursor:pointer}
.kx button:hover{border-color:var(--k-mut)}.kx button:focus-visible,.kx [role=button]:focus-visible{outline:2px solid var(--k-violet);outline-offset:2px}
.kx button.pri{border-color:var(--k-violet);color:var(--k-violet)}.kx button[aria-pressed=true]{background:color-mix(in srgb,var(--k-violet) 18%,transparent)}
.kx-dots{display:flex;flex:1;justify-content:center;flex-wrap:nowrap;min-width:0}
.kx button.kx-dot{padding:10px 5px;border:0;min-height:0;min-width:0;background:none}
.kx-dot i{width:8px;height:8px;border-radius:50%;border:1px solid var(--k-mut);display:inline-block}.kx-dot[aria-current=step] i{background:var(--k-ink);border-color:var(--k-ink)}
.kx-log{font-family:var(--font-mono,ui-monospace,Menlo,monospace);font-size:11px;line-height:17px;height:92px;overflow:hidden;background:var(--k-panel);border:1px solid var(--k-line);border-radius:8px;padding:6px 8px;margin:8px 4px 0;display:flex;flex-direction:column;justify-content:flex-end;white-space:pre-wrap}
.kx-scrub{display:flex;align-items:center;gap:8px;margin:6px 4px}.kx-scrub input{flex:1}
.kx-time{font-size:11px;color:var(--k-mut);min-width:64px;text-align:right;font-variant-numeric:tabular-nums}
.kx input[type=range]{accent-color:var(--k-violet);height:32px;width:100%;margin:0}
.kx-ctl{display:grid;grid-template-columns:1fr auto;gap:2px 10px;align-items:center;font-size:12.5px;margin:4px 8px}.kx-ctl output{font-variant-numeric:tabular-nums;color:var(--k-ink);font-weight:600}.kx-ctl input{grid-column:1/3}
.kx .pulse{animation:kxpl 1.2s ease-in-out 1 forwards}@keyframes kxpl{0%,100%{opacity:0}50%{opacity:.85}}
.kx-ripple{position:absolute;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;border:2px solid var(--k-ink);pointer-events:none;animation:kxrp .6s ease-out forwards}@keyframes kxrp{from{transform:scale(.3);opacity:.9}to{transform:scale(1.4);opacity:0}}
.kx-recording .kx-nav button:not(.kx-dot),.kx-recording .kx-scrub button{visibility:hidden}
.kx .sr-only,.sr-only{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media (prefers-reduced-motion:reduce){.kx *{transition:none!important;animation:none!important}}`;
  document.head.appendChild(s);
}

/* ---------- step context: everything a step needs, bound to its generation */
function makeCtx(eng, svg, i) {
  const g = eng.gen, alive = () => g === eng.gen, dyn = svg.querySelector('.kx-dyn');
  const q = s => svg.querySelector(s);
  const pick = e => typeof e === 'string' ? q(e) : e;
  const s = {
    i, svg, dyn, q, alive, C, RM, root: eng.root, act: eng.act,
    at(ms, fn) { const id = setTimeout(() => { if (alive()) fn(); }, ms); eng.timers.push(id); return id; },
    wait(ms) { return new Promise(r => s.at(ms, () => { if (!(eng.inDemo && eng.touched)) r(); })); },   // an idle demo stops for good once the reader acts
    loop(delay, fn) { s.at(delay, () => { let last = performance.now(); const t0 = last, st = {}; const k = n => { if (!alive()) return; st.dt = Math.min(.05, Math.max(0, (n - last) / 1000)); last = n; st.e = n - t0; if (fn(st) !== false) requestAnimationFrame(k); }; requestAnimationFrame(k); }); },
    tween(du, fn, o = {}) { const ez = ease[o.ease || 'inOut']; return new Promise(res => s.at(o.delay || 0, () => { if (RM || du <= 0) { fn(1); res(); return; } const t0 = performance.now(); const k = n => { if (!alive()) return; const p = clamp((n - t0) / du); fn(ez(p)); if (p < 1) requestAnimationFrame(k); else res(); }; requestAnimationFrame(k); })); },
    el(tag, attrs, parent) { return mk(tag, attrs, parent || dyn); },
    drawIn(e, du = 500, delay = 0) { e = pick(e); if (!e || RM) return; const L = e.getTotalLength() + 1; e.style.transition = 'none'; e.style.strokeDasharray = L + ' ' + L; e.style.strokeDashoffset = L; e.getBoundingClientRect(); e.style.transition = `stroke-dashoffset ${du}ms cubic-bezier(.45,0,.55,1) ${delay}ms`; e.style.strokeDashoffset = 0; },
    fadeIn(e, du = 400, delay = 0) { e = pick(e); if (!e) return; e.style.transition = 'none'; e.style.opacity = 0; e.getBoundingClientRect(); e.style.transition = `opacity ${du}ms ease ${delay}ms`; e.style.opacity = 1; },
    fadeOut(e, du = 400, remove = true) { e = pick(e); if (!e) return; e.style.transition = `opacity ${du}ms`; e.style.opacity = 0; if (remove) setTimeout(() => e.remove(), du + 50); },
    travel(path, du = 600, c = 'ink', o = {}) {   // a dot that moves along a path element or a list of points
      let p = pick(path), temp = false;
      if (Array.isArray(path)) { p = mk('path', { d: 'M' + path.map(q => q.join(' ')).join(' L'), fill: 'none', stroke: col(c), 'stroke-width': 1.6, 'stroke-opacity': o.trail === false ? 0 : .5, 'stroke-linecap': 'round' }, dyn); temp = true; if (o.trail !== false) s.drawIn(p, du); }
      const d = mk('circle', { r: o.r || 3.6, fill: col(c) }, dyn), L = p.getTotalLength();
      const done = () => { s.fadeOut(d, 300); if (temp && !o.keep) setTimeout(() => s.fadeOut(p, 450), 200); };
      if (RM) { const e = p.getPointAtLength(L); d.setAttribute('cx', e.x); d.setAttribute('cy', e.y); done(); return Promise.resolve(); }
      return s.tween(du, k => { const e = p.getPointAtLength(k * L); d.setAttribute('cx', f(e.x)); d.setAttribute('cy', f(e.y)); }, { delay: o.delay || 0 }).then(done);
    },
    ring(x, y, w, h, c = 'ink', o = {}) { const p = mk('path', { d: rect(x, y, w, h, Math.round(x * 7 + y)), fill: 'none', stroke: col(c), 'stroke-width': o.w || 2.4, 'stroke-linecap': 'round', class: 'pulse' }, dyn); p.style.opacity = 0; setTimeout(() => p.remove(), 1400); return p; },
    write(x, y, text, o = {}) { const w = document.createElementNS(NS, 'g'); w.innerHTML = T(x, y, text, o); const t = w.firstChild; dyn.appendChild(t); t.removeAttribute('data-k'); s.fadeIn(t, o.d || 450, o.t || 0); return t; },
    float(x, y, text, c = 'ink', z = 16) { const t = s.write(x, y, text, { h: 1, z, c }); if (!RM) { t.style.transition = 'transform 1.1s ease-out, opacity 1.1s ease-out'; requestAnimationFrame(() => requestAnimationFrame(() => { t.style.transform = 'translateY(-18px)'; t.style.opacity = 0; })); } setTimeout(() => t.remove(), 1200); },
    swap(e, text, c) { e = pick(e); if (!e) return; e.style.transition = 'opacity .15s'; e.style.opacity = 0; s.at(160, () => { e.textContent = text; if (c) e.setAttribute('fill', col(c)); e.style.opacity = 1; }); },
    count(e, to, o = {}) { e = pick(e); if (!e) return; const from = o.from != null ? o.from : (+e.dataset.v || 0), fmt = o.fmt || (v => Math.round(v).toLocaleString()); e.dataset.v = to; return s.tween(o.du || 900, k => { e.textContent = (o.pre || '') + fmt(lerp(from, to, k)) + (o.post || ''); }, { delay: o.delay || 0 }); },
    bar(e, frac, du = 600, axis = 'x') { e = pick(e); if (!e) return; e.style.transformBox = 'fill-box'; e.style.transformOrigin = axis === 'x' ? '0 50%' : '50% 100%'; e.style.transition = RM ? 'none' : `transform ${du}ms cubic-bezier(.45,0,.55,1)`; e.style.transform = axis === 'x' ? `scaleX(${clamp(frac).toFixed(4)})` : `scaleY(${clamp(frac).toFixed(4)})`; },
    btn(icon, label, fn, o = {}) { const b = document.createElement('button'); if (o.primary) b.className = 'pri'; b.innerHTML = (ICON[icon] || '') + esc(label); b.type = 'button'; b.onclick = e => { if (e.isTrusted) s.touched(); fn(b); }; eng.act.appendChild(b); return b; },
    on(e, fn, label) { e = pick(e); e.setAttribute('role', 'button'); e.setAttribute('tabindex', '0'); if (label) e.setAttribute('aria-label', label); e.style.cursor = 'pointer'; const h = ev => { if (ev.isTrusted) s.touched(); fn(ev); }; e.addEventListener('click', h); e.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); h(ev); } }); return e; },
    point(ev) { const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY; const m = svg.getScreenCTM(); return m ? pt.matrixTransform(m.inverse()) : { x: 0, y: 0 }; },
    drag(e, o) { e = pick(e); e.style.touchAction = 'none'; e.style.cursor = 'grab'; let on = false; e.addEventListener('pointerdown', ev => { on = true; e.setPointerCapture(ev.pointerId); s.touched(); o.move && o.move(s.point(ev), ev); }); e.addEventListener('pointermove', ev => { if (on && alive()) o.move && o.move(s.point(ev), ev); }); const up = ev => { if (!on) return; on = false; o.end && o.end(s.point(ev), ev); }; e.addEventListener('pointerup', up); e.addEventListener('pointercancel', up); return e; },
    cap(text) { eng.cap.textContent = text; },
    touched() { eng.touched = true; if (eng.stopAuto && !REC) eng.stopAuto(); },   // a reader who acts takes over from autoplay
    tap(e) { e = pick(e); if (!e || !alive() || (eng.inDemo && eng.touched)) return; const r = e.getBoundingClientRect(), R = eng.root.getBoundingClientRect(), d = document.createElement('div'); d.className = 'kx-ripple'; d.style.left = (r.left + r.width / 2 - R.left) + 'px'; d.style.top = (r.top + r.height / 2 - R.top) + 'px'; eng.root.appendChild(d); setTimeout(() => d.remove(), 650); e.dispatchEvent(new MouseEvent('click', { bubbles: true })); },
    /* unit charts: one circle per item, keyed, so items keep their identity when they move */
    units(items, o = {}) { const gU = mk('g', { class: 'kx-units' }, o.parent || dyn); s._units = items.map((it, j) => { const c = mk('circle', { cx: o.x0 || 0, cy: o.y0 || 0, r: o.r || 4, fill: col(o.fill || 'fill.blue') }, gU); c.style.transition = 'fill .5s, opacity .5s'; return { it, c, x: o.x0 || 0, y: o.y0 || 0, r: o.r || 4, j }; }); return s._units; },
    arrange(layout, o = {}) { const U = s._units || [], du = o.du || 900, stg = o.stagger == null ? 4 : o.stagger, ez = ease[o.ease || 'inOut'];
      const tg = U.map((u, j) => { const L = layout(u.it, j) || {}; if (L.fill) u.c.style.fill = col(L.fill); if (L.opacity != null) u.c.style.opacity = L.opacity; return { x0: u.x, y0: u.y, r0: u.r, x: L.x == null ? u.x : L.x, y: L.y == null ? u.y : L.y, r: L.r == null ? u.r : L.r, dl: (L.order == null ? j : L.order) * stg }; });
      const tot = du + Math.max(0, ...tg.map(t => t.dl));
      return s.tween(tot, k => { const ms = k * tot; U.forEach((u, j) => { const t = tg[j], p = ez(clamp((ms - t.dl) / du)); u.x = lerp(t.x0, t.x, p); u.y = lerp(t.y0, t.y, p); u.r = lerp(t.r0, t.r, p); u.c.setAttribute('cx', f(u.x)); u.c.setAttribute('cy', f(u.y)); u.c.setAttribute('r', f(u.r)); }); }, { ease: 'linear', delay: o.delay || 0 }); },
  };
  return s;
}

/* ---------- stepper: a lesson that moves one idea at a time, with fixed controls */
const ALL = (window.EXPLAINERS = window.EXPLAINERS || []);
function frame(root, o, kind) {
  root = typeof root === 'string' ? document.querySelector(root) : root;
  useStyle(o.style || 'chalkboard', root);
  const [W, H] = o.viewBox || [380, 300];
  const legend = (o.legend || []).map(l => `<span data-l="${l.key}"><span class="kx-sw" style="background:${col(l.color)}"></span>${esc(l.label)}</span>`).join('');
  root.innerHTML = `<h2 class="sr-only">${esc(o.title || '')}</h2><div class="kx-head"><span class="kx-title"></span><span class="kx-count"></span></div>
<svg class="kx-stage" viewBox="0 0 ${W} ${H}" role="img"></svg><p class="kx-cap" aria-live="polite"></p>${kind === 'player' && o.log ? '<div class="kx-log" aria-hidden="true"></div>' : ''}
${kind === 'player' ? '<div class="kx-scrub"><button class="kx-pp" type="button"></button><input type="range" min="0" step="1" aria-label="Scrub the timeline"><span class="kx-time"></span></div>' : '<div class="kx-act"></div>'}
${legend ? `<div class="kx-legend">${legend}</div>` : ''}<div class="kx-nav"><button class="kx-back" type="button" aria-label="Previous">${ICON.left}</button><div class="kx-dots"></div>${kind === 'stepper' ? `<button class="kx-replay" type="button" aria-label="Replay this step" title="Replay this step">${ICON.replay}</button>` : ''}<button class="kx-next" type="button"></button></div>`;
  if (REC) root.classList.add('kx-recording');
  const $ = s => root.querySelector(s);
  return { root, W, H, svg: $('.kx-stage'), cap: $('.kx-cap'), act: $('.kx-act'), title: $('.kx-title'), count: $('.kx-count'), dots: $('.kx-dots'), next: $('.kx-next'), back: $('.kx-back'), replay: $('.kx-replay'), log: $('.kx-log'), $ };
}
function fixCaptionHeight(fr, texts) {   // reserve the tallest caption so nothing below it ever moves
  const m = fr.cap.cloneNode(); m.style.cssText = `position:absolute;visibility:hidden;left:-9999px;top:0;min-height:0;width:${fr.cap.clientWidth}px`; m.removeAttribute('aria-live'); fr.cap.parentNode.appendChild(m);
  let h = 0; texts.forEach(t => { m.textContent = t; h = Math.max(h, m.offsetHeight); }); m.remove(); fr.cap.style.minHeight = h + 'px';
}
function stepper(o) {
  const fr = frame(o.root, o, 'stepper'), S = o.steps;
  if (o.actHeight) fr.act.style.minHeight = o.actHeight + 'px';
  const eng = { gen: 0, timers: [], root: fr.root, act: fr.act, cap: fr.cap, touched: false };
  let cur = 0, first = true, auto = null, ends = [];
  eng.stopAuto = () => { auto = null; };
  S.forEach((st, i) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'kx-dot'; b.setAttribute('aria-label', 'Go to step ' + (i + 1)); b.innerHTML = '<i></i>'; b.onclick = () => go(i); fr.dots.appendChild(b); });
  const capTexts = S.map(st => st.cap || '').concat(o.extraCaptions || []);
  fixCaptionHeight(fr, capTexts); addEventListener('resize', () => fixCaptionHeight(fr, capTexts));
  const fixNext = () => {   // size Next to its widest label, so 'Start over' never pushes the other controls
    const keep = fr.next.innerHTML; fr.next.style.minWidth = ''; let w = 0;
    for (const h of [ICON.restart + 'Start over', 'Next' + ICON.right]) { fr.next.innerHTML = h; w = Math.max(w, fr.next.getBoundingClientRect().width); }
    fr.next.innerHTML = keep; fr.next.style.minWidth = Math.ceil(w) + 'px'; };
  fontsReady().then(() => { fixCaptionHeight(fr, capTexts); fixNext(); });   // a web font can wrap and size text differently once it loads
  addEventListener('resize', fixNext);
  function build(i) {
    cur = i; eng.touched = false; const st = S[i], s = {};
    fr.svg.innerHTML = (typeof st.draw === 'function' ? st.draw(K) : st.draw || '') + '<g class="kx-dyn"></g>';
    fr.act.innerHTML = ''; fr.title.textContent = st.title || ''; fr.count.textContent = `Step ${i + 1} of ${S.length}`;
    fr.svg.setAttribute('aria-label', (st.title || '') + '. ' + (st.alt || st.cap || ''));
    [...fr.dots.children].forEach((d, j) => j === i ? d.setAttribute('aria-current', 'step') : d.removeAttribute('aria-current'));
    fr.root.querySelectorAll('[data-l]').forEach(e => e.style.display = !st.keys || st.keys.includes(e.dataset.l) ? '' : 'none');   // only this step's colours
    fr.next.innerHTML = i === S.length - 1 ? ICON.restart + 'Start over' : 'Next' + ICON.right;
    fr.cap.style.transition = 'none'; fr.cap.style.opacity = 0; fr.cap.textContent = st.cap || '';
    const revealEnd = reveal(fr.svg);
    const ctx = makeCtx(eng, fr.svg, i);
    ctx.at(st.capDelay == null ? 300 : st.capDelay, () => { fr.cap.style.transition = 'opacity .6s'; fr.cap.style.opacity = 1; });
    if (st.start) st.start(ctx);
    eng.inDemo = false;
    if (st.demo && st.idleDemo && !REC && !st.ask) ctx.at(st.idleDemo, () => { if (!eng.touched) { eng.inDemo = true; Promise.resolve(st.demo(ctx)).finally(() => { eng.inDemo = false; }); } });
    ends[i] = st.duration || revealEnd + 600;
    eng.ctx = ctx;
  }
  function go(i, keepAuto) {
    if (!keepAuto) auto = null;
    eng.gen++; eng.timers.forEach(clearTimeout); eng.timers = [];
    i = Math.max(0, Math.min(S.length - 1, i));
    const g = eng.gen;
    if (first || RM) { first = false; build(i); fr.svg.style.opacity = 1; }
    else { fr.svg.style.opacity = 0; setTimeout(() => { if (g === eng.gen) { build(i); fr.svg.style.opacity = 1; } }, 230); }
  }
  fr.back.onclick = () => go(cur - 1);
  fr.next.onclick = () => go(cur < S.length - 1 ? cur + 1 : 0);
  fr.replay.onclick = () => go(cur);
  document.addEventListener('keydown', e => { if (e.target.closest && e.target.closest('[role=button],input,button,textarea,select')) return; if (ALL.length > 1 && !fr.root.contains(document.activeElement)) return; if (e.key === 'ArrowRight') go(cur + 1); if (e.key === 'ArrowLeft') go(cur - 1); });
  const api = {
    kind: 'stepper', root: fr.root, get count() { return S.length; }, get current() { return cur; },
    go: i => go(i), duration: i => S[i].duration || ends[i] || 4000, hasDemo: i => !!S[i].demo,
    demo: i => { const c = eng.ctx; return c && c.i === i && S[i].demo ? Promise.resolve(S[i].demo(c)) : Promise.resolve(); },
    demoDuration: i => S[i].demoDuration || 0,
    async autoplay(hold = o.hold || 2200) { const me = auto = {}; for (let i = 0; i < S.length; i++) { if (auto !== me) return; go(i, true); await sleep(260 + api.duration(i)); if (auto !== me) return; if (S[i].demo) { await Promise.race([api.demo(i), sleep(S[i].demoDuration || 12000)]); await sleep(S[i].demoDuration ? 0 : 600); } await sleep(hold); } },
  };
  let resolveReady; api.ready = new Promise(r => resolveReady = r);
  ALL.push(api); window.EXPLAINER = window.EXPLAINER || api;
  fontsReady().then(() => { go(+(QS.get('step') || 1) - 1); resolveReady(); if (REC && ALL[0] === api) api.autoplay().then(() => { api.done = true; });
    else if (o.autoplay && !RM && !QS.has('step') && !QS.has('static')) { const run = () => api.autoplay().then(() => { if (o.autoplay === 'loop' && auto) run(); }); run(); } });
  return api;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ---------- player: a scrubbable timeline. frame(t, s) must draw the scene for time t from scratch,
   so pause, scrub, replay and recording all work for free. Chapters label stretches of the timeline. */
function player(o) {
  const fr = frame(o.root, o, 'player'), eng = { gen: 0, timers: [], root: fr.root, act: null, cap: fr.cap, touched: false };
  const CH = o.chapters || [{ at: 0, title: o.title || '', cap: '' }], D = o.duration;
  const range = fr.$('.kx-scrub input'), pp = fr.$('.kx-pp'), tm = fr.$('.kx-time');
  range.max = D; let t = 0, playing = false, last = 0, chap = -1, speed = o.speed || 1;
  fr.svg.innerHTML = (typeof o.scene === 'function' ? o.scene(K) : o.scene || '') + '<g class="kx-dyn"></g>';
  const ctx = makeCtx(eng, fr.svg, 0); reveal(fr.svg);
  CH.forEach((c, i) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'kx-dot'; b.setAttribute('aria-label', 'Go to ' + (c.title || 'part ' + (i + 1))); b.innerHTML = '<i></i>'; b.onclick = () => { seek(c.at); play(); }; fr.dots.appendChild(b); });
  fixCaptionHeight(fr, CH.map(c => c.cap || '')); fontsReady().then(() => fixCaptionHeight(fr, CH.map(c => c.cap || '')));
  const chapterAt = x => { let k = 0; CH.forEach((c, i) => { if (x >= c.at) k = i; }); return k; };
  function setChapter(k) { if (k === chap) return; chap = k; const c = CH[k]; fr.title.textContent = c.title || ''; fr.count.textContent = `Part ${k + 1} of ${CH.length}`; fr.cap.textContent = c.cap || ''; fr.svg.setAttribute('aria-label', (c.title || '') + '. ' + (c.alt || c.cap || '')); [...fr.dots.children].forEach((d, j) => j === k ? d.setAttribute('aria-current', 'step') : d.removeAttribute('aria-current')); fr.root.querySelectorAll('[data-l]').forEach(e => e.style.display = !c.keys || c.keys.includes(e.dataset.l) ? '' : 'none'); }
  function logTo(x) { if (!fr.log || !o.log) return; const L = o.log.filter(e => e.t <= x).slice(-6), key = L.map(e => e.t + e.text).join('|'); if (key === fr.log.dataset.k) return; fr.log.dataset.k = key; fr.log.innerHTML = L.map(e => `<div style="color:${col(e.c || 'mut')}">${esc(e.text)}</div>`).join(''); }
  function draw() { range.value = t; tm.textContent = o.clock ? o.clock(t) : (t / 1000).toFixed(1) + ' s'; setChapter(chapterAt(t)); logTo(t); o.frame(t, ctx); }
  function seek(x) { t = clamp(x, 0, D); draw(); }
  function tick(n) { if (!playing) return; const dt = Math.min(64, n - last); last = n; t += dt * speed; if (t >= D) { t = D; playing = false; updPP(); } draw(); if (playing) requestAnimationFrame(tick); }
  function play() { if (t >= D) t = 0; if (RM) { seek(end(chapterAt(t)) - 1); return; } playing = true; last = performance.now(); updPP(); requestAnimationFrame(tick); }  // reduced motion: jump to the end state of the chapter instead of animating
  function pause() { playing = false; updPP(); }
  function updPP() { pp.innerHTML = playing ? ICON.pause + 'Pause' : t >= D ? ICON.replay + 'Replay' : ICON.play + 'Play'; pp.setAttribute('aria-label', playing ? 'Pause' : 'Play'); }
  pp.onclick = () => playing ? pause() : play();
  range.oninput = () => { pause(); seek(+range.value); };
  fr.back.onclick = () => { seek(CH[Math.max(0, chapterAt(t) - (t - CH[chapterAt(t)].at < 600 ? 1 : 0))].at); };
  fr.next.innerHTML = 'Next' + ICON.right; fr.next.onclick = () => { const k = chapterAt(t); seek(k < CH.length - 1 ? CH[k + 1].at : 0); play(); };
  const end = i => i < CH.length - 1 ? CH[i + 1].at : D;
  const api = { kind: 'player', root: fr.root, get count() { return CH.length; }, get current() { return chapterAt(t); }, go: i => { seek(CH[i].at); play(); }, duration: i => (end(i) - CH[i].at) / speed, hasDemo: () => false, demo: () => Promise.resolve(), seek, play, pause, get time() { return t; },
    async autoplay() { seek(0); play(); while (t < D) await sleep(200); await sleep(o.hold || 2000); } };
  let resolveReady; api.ready = new Promise(r => resolveReady = r);
  ALL.push(api); window.EXPLAINER = window.EXPLAINER || api;
  fontsReady().then(() => { const k = +(QS.get('step') || 1) - 1; seek(CH[Math.min(k, CH.length - 1)].at); updPP(); if (o.autoplay !== false && !QS.has('static')) play(); resolveReady(); if (REC && ALL[0] === api) api.autoplay().then(() => { api.done = true; }); });
  return api;
}

/* ---------- controls for explorables */
let uid = 0;
function slider(parent, o) {
  parent = typeof parent === 'string' ? document.querySelector(parent) : parent; const id = 'kx' + (++uid);
  const w = document.createElement('div'); w.className = 'kx-ctl';
  w.innerHTML = `<label for="${id}">${esc(o.label)}</label><output for="${id}"></output><input id="${id}" type="range" min="${o.min}" max="${o.max}" step="${o.step || 'any'}" value="${o.value}">`;
  parent.appendChild(w); const inp = w.querySelector('input'), out = w.querySelector('output'), fmt = o.fmt || (v => v);
  const upd = () => { out.textContent = fmt(+inp.value); o.oninput && o.oninput(+inp.value); };
  inp.addEventListener('input', upd); upd();
  return { el: w, input: inp, get value() { return +inp.value; }, set(v) { inp.value = v; upd(); } };
}
function toggle(parent, o) {
  parent = typeof parent === 'string' ? document.querySelector(parent) : parent;
  const b = document.createElement('button'); b.type = 'button'; b.setAttribute('aria-pressed', o.value ? 'true' : 'false'); b.innerHTML = esc(o.label); parent.appendChild(b);
  b.onclick = () => { const v = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', v); o.onchange && o.onchange(v); };
  return b;
}

/* ---------- layout and number helpers */
const grid = (j, o) => ({ x: (o.x0 || 0) + (j % o.cols) * (o.gap || 10), y: (o.y0 || 0) + Math.floor(j / o.cols) * (o.gapY || o.gap || 10) });
function scale(d0, d1, r0, r1) { const s = v => r0 + (v - d0) / (d1 - d0 || 1) * (r1 - r0); s.invert = p => d0 + (p - r0) / (r1 - r0 || 1) * (d1 - d0); return s; }
const fmt = {
  int: v => Math.round(v).toLocaleString('en-US'),
  pct: (v, d = 0) => (v * 100).toFixed(d) + '%',
  usd: (v, d = 2) => (v < 0 ? '−' : '') + '$' + Math.abs(v).toFixed(d),
  sec: v => v < 60 ? v.toFixed(0) + ' s' : Math.floor(v / 60) + ' min ' + Math.round(v % 60) + ' s',
};
/* Wilson score interval for k successes in n trials (95% by default). Use it whenever a small sample is shown as a rate. */
function wilson(k, n, z = 1.96) { if (!n) return [0, 1]; const p = k / n, d = 1 + z * z / n, c = p + z * z / (2 * n), m = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [Math.max(0, (c - m) / d), Math.min(1, (c + m) / d)]; }

const K = { version: '1.1', NS, RM, C, STYLES, useStyle, resolveStyle, rng, ease, clamp, lerp, f, esc, col, line, rect, ellipse, arrow, poly, curve, P, T, F, reveal, finish, mk, ICON, stepper, player, slider, toggle, grid, scale, fmt, wilson, sleep };
window.K = K;
})();
