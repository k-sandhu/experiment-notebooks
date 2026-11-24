/* ===== SCENE: replay of three recorded runs from notebook 07 (subagent handoff harness). =====
   DATA (above) is copied unchanged from data.json by _build/make_data.py:
   runs.<level>.spans = [agent, kind, label, start s, end s]; events = [t s, kind, from, to];
   comparison = data/comparison.csv rows. Every number on screen is computed from DATA below. */
const {C, clamp} = K;
K.useStyle('blueprint');            // fill K.C before the colour constants below read it
const R1 = DATA.runs.L1_sync_handoff, R2 = DATA.runs.L2_async_spawn, R3 = DATA.runs.L3_progress_and_redirect, R0 = DATA.runs.L0_single_agent;
const AG = ['main', 'city_researcher#2', 'city_researcher#3', 'city_researcher#4'];
const LANE_NAME = ['planner', 'Lisbon', 'Rome', 'Prague'];
const sum = a => a.reduce((x, y) => x + y, 0);
const f1 = v => v.toFixed(1);
// planner ledger: own model time, own searches, waiting (seconds), from spans on agent "main"
function ledger(run, now = 1e9) {
  const o = {llm: 0, tool: 0, blocked: 0};
  run.spans.forEach(([a, k, , s0, s1]) => { if (a === 'main' && s0 < now) o[k] += Math.min(now, s1) - s0; });
  return o;
}
const L1 = ledger(R1), L2 = ledger(R2);
const ev = (run, kind, to) => run.events.find(e => e[1] === kind && (!to || e[3] === to || e[2] === to));
const blocks1 = R1.spans.filter(s => s[0] === 'main' && s[1] === 'blocked');      // 3 waits
const flights1 = R1.spans.find(s => s[0] === 'main' && s[2] === 'search_flights')[3];
const flights2 = R2.spans.find(s => s[0] === 'main' && s[2] === 'search_flights')[3];
const res2 = R2.events.filter(e => e[1] === 'result').map(e => e[0]);
const spawn2 = R2.events.filter(e => e[1] === 'spawn').map(e => e[0]);
const waitAll2 = R2.spans.filter(s => s[0] === 'main' && s[2] === 'search_flights').pop()[4];   // 43.94: last flight search ends, then wait_all (no blocked span recorded)
const P3 = 'city_researcher#4';
const fail3 = R3.spans.find(s => s[0] === P3 && s[2] === 'search_hotels');                         // failed search (HTTP 503 per README)
const backup3 = R3.spans.find(s => s[0] === P3 && s[2] === 'search_hotels_backup');
const alert3 = ev(R3, 'alert')[0], instr3 = ev(R3, 'instruction')[0], final3 = R3.events.find(e => e[1] === 'result' && e[2] === P3)[0];
const lastCall3 = R3.spans.filter(s => s[0] === P3 && s[1] === 'llm' && s[3] < instr3).pop();      // 46.86-53.70, started before the instruction
const CMP = DATA.comparison;
const W0 = R0.wall_s, W1 = R1.wall_s, W2 = R2.wall_s, W3 = R3.wall_s;
const others = CMP.filter(c => /^[2346] /.test(c.level)).map(c => c.wall_s);
const helperBusy = run => AG.slice(1).map(a => sum(run.spans.filter(s => s[0] === a).map(s => s[4] - s[3])));

// ---------- timeline: segments of animation time, each showing one view over a stretch of real time
const SEG = [];
let A = 0;
function seg(view, r0, r1, speed, hold, chapter) {
  const dur = r1 > r0 ? (r1 - r0) / speed * 1000 : 0;
  SEG.push({view, r0, r1, a0: A, dur, hold, speed, chapter}); A += dur + hold;
}
seg('cmp', 0, 0, 1, 5200, 0);
seg('cmp', 0, 16.5, 4.5, 1600, 1);
seg('cmp', 16.5, 44.2, 5, 1800, 2);
seg('cmp', 44.2, W2, 4.5, 4200, 3);
seg('cmp', W2, flights1, 5, 2200, 4);
seg('cmp', flights1, W1, 5, 6500, 5);
seg('l3', 0, 41, 6.5, 2200, 6);
seg('l3', 41, W3, 4, 6500, 7);
seg('all', 0, 0, 1, 10000, 8);
const D = A;
function at(t) {                       // animation ms -> {seg, now (real s), moving}
  let g = SEG[0];
  SEG.forEach(x => { if (t >= x.a0) g = x; });
  const k = g.dur ? clamp((t - g.a0) / g.dur) : 1;
  return {g, now: g.r0 + (g.r1 - g.r0) * k, moving: g.dur > 0 && t < g.a0 + g.dur, local: t - g.a0};
}
function anim(view, tr) {              // real time in a view -> animation ms (first segment that covers it)
  const g = SEG.find(x => x.view === view && tr >= x.r0 && tr <= x.r1 && x.dur > 0) || SEG.find(x => x.view === view);
  return g.a0 + (g.dur ? (tr - g.r0) / (g.r1 - g.r0) * g.dur : 0);
}
const chapAt = i => SEG.find(x => x.chapter === i).a0;

// ---------- layout
const X0 = 74, X1 = 366, TMAX = 125;
const X = v => X0 + v / TMAX * (X1 - X0);
const BLOCK = [{run: R1, name: 'Sync handoff', y: 20}, {run: R2, name: 'Async spawn', y: 116}];
const laneY = (by, i) => by + 16 + i * 18;
const AX_Y = 200;
const KIND = {llm: C.fill.violet, tool: C.fill.green};
const HALO = `paint-order:stroke;stroke:${C.bg};stroke-width:3px;stroke-linejoin:round`;
const txt = (x, y, s, o = {}) => `<text x="${x.toFixed(1)}" y="${y}" font-size="${o.z || 12}" text-anchor="${o.a || 'start'}" fill="${o.c || C.ink}"${o.w ? ` font-weight="${o.w}"` : ''} style="font-variant-numeric:tabular-nums;${o.halo ? HALO : ''}">${K.esc(s)}</text>`;
const rect = (x, y, w, h, fill, extra = '') => `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${Math.max(0, w).toFixed(1)}" height="${h}" rx="2" fill="${fill}" ${extra}/>`;
const WAITFILL = 'url(#hatch)', WAITSTROKE = `stroke="${C.fill.amber}" stroke-width="1"`;
const vline = (x, y1, y2, c, w = 1, extra = '') => `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${y1}" y2="${y2}" stroke="${c}" stroke-width="${w}" ${extra}/>`;
const arrowHead = (x, y, dir, c) => `<path d="M${(x - 3.5).toFixed(1)} ${y - dir * 5} L${x.toFixed(1)} ${y} L${(x + 3.5).toFixed(1)} ${y - dir * 5}" fill="none" stroke="${c}" stroke-width="1.4"/>`;

function axis(scale, ticks, y, unit) {
  let m = `<line x1="${X0}" x2="${X1}" y1="${y}" y2="${y}" stroke="${C.line}"/>`;
  ticks.forEach((v, i) => { const x = scale(v); m += vline(x, y, y + 4, C.line) + txt(i === ticks.length - 1 ? x + 6 : x, y + 15, v + (i === ticks.length - 1 ? unit : ''), {a: i === ticks.length - 1 ? 'end' : 'middle', c: C.mut}); });
  return m;
}
function lanes(run, by, names, scale, now, lo = 0, hi = 1e9, laneYf = i => laneY(by, i), h = 12) {
  let m = '';
  names.forEach((n, i) => {
    if (!n) return;
    const y = laneYf(i);
    m += txt(12, y + 4, n, {c: i === 0 ? C.ink : C.mut});
    m += `<line x1="${X0}" x2="${X1}" y1="${y}" y2="${y}" stroke="${C.faint}" stroke-dasharray="2 3"/>`;
  });
  run.spans.forEach(([a, k, , s0, s1]) => {
    const i = AG.indexOf(a); if (i < 0 || !names[i] || s0 >= now || s1 <= lo || s0 >= hi) return;
    const a0 = Math.max(s0, lo), a1 = Math.min(s1, now, hi), y = laneYf(i);
    if (k === 'blocked') {
      if (a1 - a0 <= 0) return;
      m += rect(scale(a0), y - h / 2, scale(a1) - scale(a0), h, WAITFILL, WAITSTROKE);
    } else m += rect(scale(a0), y - h / 2 + 1, Math.max(.8, scale(a1) - scale(a0) - .6), h - 2, KIND[k]);
  });
  return m;
}
function messages(run, laneYf, scale, now, lo = 0, hi = 1e9, skipKinds = []) {
  let m = '';
  run.events.forEach(([t, k, from, to]) => {
    if (t > now || t < lo || t > hi || skipKinds.includes(k)) return;
    const i0 = AG.indexOf(from), i1 = AG.indexOf(to); if (i0 < 0 || i1 < 0) return;
    const x = scale(t), y0 = laneYf(i0), y1 = laneYf(i1), dir = y1 > y0 ? 1 : -1;
    const c = k === 'spawn' || k === 'instruction' ? C.ink : C.blue;
    m += vline(x, y0, y1 - dir * 6, c, 1.3) + arrowHead(x, y1 - dir * 6, dir, c);
    const age = now - t;
    if (age < 3) m += `<circle cx="${x.toFixed(1)}" cy="${y1}" r="${(5 + age * 3).toFixed(1)}" fill="none" stroke="${c}" stroke-opacity="${(1 - age / 3).toFixed(2)}"/>`;
  });
  return m;
}
function nowLine(x, y1, y2) { return vline(x, y1, y2, C.ink, 1, 'stroke-opacity=".55"'); }

// ---------- views
function viewCompare(now, t) {
  let m = '';
  const showRef = t >= chapAt(4);
  BLOCK.forEach(b => {
    m += txt(12, b.y, b.name, {z: 13, w: 600});
    m += lanes(b.run, b.y, LANE_NAME, X, now);
    m += messages(b.run, i => laneY(b.y, i), X, now);
    // wait labels on the planner lane
    b.run.spans.forEach(([a, k, , s0, s1]) => {
      if (a !== 'main' || k !== 'blocked' || s0 >= now) return;
      const e = Math.min(now, s1), w = X(e) - X(s0);
      if (w > 30) m += txt((X(s0) + X(e)) / 2, laneY(b.y, 0) + 4, f1(e - s0) + ' s', {a: 'middle', halo: 1});
    });
    if (now >= b.run.wall_s) {
      m += vline(X(b.run.wall_s), laneY(b.y, 0) - 8, laneY(b.y, 3) + 8, C.green, 1.5);
      m += txt(X1, b.y, '✓ done at ' + f1(b.run.wall_s) + ' s', {a: 'end', c: C.green, w: 600});
    }
  });
  if (showRef) {
    const x = X(W0);
    m += vline(x, 26, AX_Y, C.mut, 1, 'stroke-dasharray="4 3"');
    m += txt(x, AX_Y + 28, 'dashed: one agent alone, ' + f1(W0) + ' s', {a: x > 250 ? 'end' : 'middle', c: C.mut});
  }
  m += axis(X, [0, 20, 40, 60, 80, 100, 120], AX_Y, ' s');
  m += nowLine(X(Math.min(now, TMAX)), 24, AX_Y);
  // planner time ledger: model calls + own searches + waiting = elapsed planner time
  [[R1, 'Sync'], [R2, 'Async']].forEach(([run, nm], j) => {
    const y = 248 + j * 28, e = Math.min(now, run.wall_s), L = ledger(run, e);
    let x = X0;
    const done = now >= run.wall_s;
    const seg = (v, fill, extra) => { const w = X(v) - X(0); m += rect(x, y + 4, w, 10, fill, extra); x += w; };
    seg(L.llm, C.fill.violet); seg(L.tool, C.fill.green); seg(L.blocked, WAITFILL, WAITSTROKE);
    m += txt(12, y, `${nm} planner: ${f1(e)} s ${done ? 'total' : 'so far'}, ${f1(L.blocked)} s waiting` + (done ? ` (${Math.round(L.blocked / e * 100)}%)` : ''), {c: L.blocked > 0 ? C.amber : C.ink});
  });
  return m;
}
const ZLO = 38, ZHI = 56;
const ZX = v => X0 + (v - ZLO) / (ZHI - ZLO) * (X1 - X0);
function viewL3(now) {
  let m = txt(12, 20, 'Progress + redirect run', {z: 13, w: 600});
  m += lanes(R3, 20, LANE_NAME, X, now);
  m += messages(R3, i => laneY(20, i), X, now, 0, 1e9, ['instruction']);
  if (now >= fail3[4]) m += txt(X(fail3[4]), 108, '✗ search failed (503)', {a: 'middle', c: C.red});
  if (now >= W3) {
    m += vline(X(W3), laneY(20, 0) - 8, laneY(20, 3) + 8, C.green, 1.5);
    m += txt(X1, 20, '✓ done at ' + f1(W3) + ' s', {a: 'end', c: C.green, w: 600});
  }
  m += nowLine(X(Math.min(now, TMAX)), 24, 98);
  // zoom frame on the top lanes and the inset
  const zy0 = 124, zy1 = 228;
  m += `<rect x="${X(ZLO).toFixed(1)}" y="26" width="${(X(ZHI) - X(ZLO)).toFixed(1)}" height="72" fill="none" stroke="${C.mut}" stroke-dasharray="3 3"/>`;
  m += `<path d="M${X(ZLO).toFixed(1)} 98 L${X0} ${zy0} M${X(ZHI).toFixed(1)} 98 L${X1} ${zy0}" stroke="${C.faint}" fill="none"/>`;
  m += `<rect x="${X0 - 2}" y="${zy0}" width="${X1 - X0 + 4}" height="${zy1 - zy0}" rx="4" fill="${C.panel}" fill-opacity=".6" stroke="${C.line}"/>`;
  m += txt(X0 + 4, zy0 + 13, `zoom: ${ZLO}-${ZHI} s`, {c: C.mut});
  const ZY = i => i === 0 ? 156 : i === 3 ? 192 : null;
  m += lanes(R3, 0, ['planner', null, null, 'Prague'], ZX, now, ZLO, ZHI, ZY, 16);
  // messages in the zoom: alert (Prague -> planner, blue) and the late instruction (planner -> Prague, red)
  if (now >= alert3) {
    const x = ZX(alert3); m += vline(x, 183, 171, C.blue, 1.4) + arrowHead(x, 165, -1, C.blue) + vline(x, 171, 165, C.blue, 1.4);
    m += txt(x + 6, 178, 'alert: search down', {c: C.blue, halo: 1});
  }
  if (now >= lastCall3[3]) {
    const x0 = ZX(lastCall3[3]), x1 = ZX(Math.min(lastCall3[4], ZHI));
    m += `<path d="M${x0.toFixed(1)} 204 v4 H${x1.toFixed(1)} v-4" fill="none" stroke="${C.violet}"/>`;
    m += txt(x1, 222, 'last model call began ' + f1(lastCall3[3]) + ' s', {a: 'end', c: C.violet, halo: 1});
  }
  if (now >= instr3) {
    const x = ZX(instr3), ok = now - instr3;
    m += vline(x, 165, 183, C.red, 1.6) + arrowHead(x, 183, 1, C.red);
    m += txt(x, 142, 'instruction sent ' + f1(instr3) + ' s', {a: 'middle', c: C.red, halo: 1});
    if (now >= final3) m += txt(x + 6, 178, '✗ never read', {c: C.red, w: 600, halo: 1});
    if (ok < 3) m += `<circle cx="${x.toFixed(1)}" cy="183" r="${(5 + ok * 3).toFixed(1)}" fill="none" stroke="${C.red}" stroke-opacity="${(1 - ok / 3).toFixed(2)}"/>`;
  }
  m += axis(ZX, [38, 42, 46, 50, 54], 242, ' s');
  if (now >= ZLO && now <= ZHI) m += nowLine(ZX(now), zy0 + 18, zy1 - 2);
  if (now >= final3) m += txt(12, 274, `Prague answered at ${f1(final3)} s from its backup search.`, {c: C.ink});
  if (now >= W3 - 0.01) m += txt(12, 290, 'Nothing told the planner. The answer was still correct.', {c: C.mut});
  return m;
}
function viewAll(local) {
  const k = clamp(local / 1800), ease = 1 - Math.pow(1 - k, 3);
  let m = txt(12, 20, 'Finish time of all 7 recorded runs', {z: 13, w: 600});
  const short = {0: 'single', 1: 'sync', 2: 'async', 3: 'report', 4: 'ask', 5: 'race*', 6: 'nested'};
  m += vline(X(W0), 30, 194, C.mut, 1, 'stroke-dasharray="4 3"');
  CMP.forEach((c, i) => {
    const y = 40 + i * 22, lv = +c.level[0], hi = lv === 1 || lv === 2 || lv === 3;
    m += txt(12, y + 4, lv + ' ' + short[lv], {c: hi ? C.ink : C.mut, w: hi ? 600 : 400});
    const own = (c.wall_s - c.blocked_s) * ease, wait = c.blocked_s * ease;
    m += rect(X0, y - 6, X(own) - X0, 12, C.mut, 'fill-opacity=".55"');
    if (wait > 0) m += rect(X(own), y - 6, X(own + wait) - X(own), 12, WAITFILL, WAITSTROKE);
    const xe = X(c.wall_s * ease), lab = f1(c.wall_s) + ' s' + (c.blocked_s > 0 ? `, waited ${f1(c.blocked_s)} s` : '');
    if (k >= 1) m += xe + 4 + lab.length * 6.4 > X1 ? txt(xe - 4, y + 4, lab, {a: 'end', halo: 1}) : txt(xe + 4, y + 4, lab, {c: C.ink, halo: 1});
  });
  m += axis(X, [0, 20, 40, 60, 80, 100, 120], 196, ' s');
  const n = CMP.length, ok = CMP.filter(c => c.correct === 'True').length;
  m += txt(12, 236, 'Grey: planner working. Hatched: waiting. Dashed: 1 agent.', {c: C.mut});
  m += txt(12, 254, `${ok} of ${n} answers correct, so correctness can't rank them.`, {c: C.ink});
  m += txt(12, 272, 'One recorded run each: a few seconds may not repeat.', {c: C.ink});
  m += txt(12, 290, '*Level 5 searched flights only; not comparable on time.', {c: C.mut});
  return m;
}

// ---------- event log (animation-time stamps computed from the recorded event times)
const LOG = [];
const lg = (view, t, text, c) => LOG.push({t: Math.round(anim(view, t)), text: (view === 'all' ? '' : f1(t).padStart(5) + 's ') + text, c});
const city = {'city_researcher#2': 'Lisbon', 'city_researcher#3': 'Rome', 'city_researcher#4': 'Prague'};
lg('cmp', 0, 'both planners start thinking', 'mut');
R1.events.forEach(([t, k, fr, to]) => k === 'spawn' ? lg('cmp', t, `sync → ${city[to]} handed off; planner waits`, 'amber') : lg('cmp', t, `sync ← ${city[fr]} answer`, 'blue'));
R2.events.forEach(([t, k, fr, to]) => k === 'spawn' ? lg('cmp', t, `async → ${city[to]} helper started`, 'ink') : lg('cmp', t, `async ← ${city[fr]} answer, planner busy`, 'blue'));
lg('cmp', flights2, 'async • planner searches flights', 'green');
lg('cmp', waitAll2, 'async • wait_all: all 3 already in', 'green');
lg('cmp', W2, `async ✓ done at ${f1(W2)} s`, 'green');
lg('cmp', flights1, 'sync • planner starts flights', 'green');
lg('cmp', W1, `sync ✓ done at ${f1(W1)} s`, 'green');
LOG.sort((a, b) => a.t - b.t);
LOG.push({t: chapAt(6), text: '• replay of the level 3 run', c: 'mut'});
R3.events.forEach(([t, k, fr, to]) => {
  if (k === 'spawn') lg('l3', t, `→ ${city[to]} helper started`, 'ink');
  else if (k === 'progress') lg('l3', t, `← ${city[fr]} progress report`, 'blue');
  else if (k === 'result') lg('l3', t, `← ${city[fr]} answer`, 'blue');
  else if (k === 'alert') lg('l3', t, `← Prague alert: search failed`, 'blue');
  else if (k === 'instruction') lg('l3', t, `→ planner to Prague: use backup`, 'red');
});
lg('l3', fail3[4], '✗ Prague hotel search: HTTP 503', 'red');
lg('l3', backup3[3], '• Prague tries backup search', 'green');
lg('l3', lastCall3[3], '• Prague last model call starts', 'violet');
lg('l3', final3 + 0.01, '✗ instruction never read', 'red');
lg('l3', W3, `✓ done at ${f1(W3)} s`, 'green');
LOG.push({t: chapAt(8) + 10, text: '• all 7 runs from comparison.csv', c: 'mut'});
LOG.sort((a, b) => a.t - b.t);

// ---------- chapters
const pct1 = Math.round(L1.blocked / W1 * 100);
const hb1 = helperBusy(R1), hb2 = helperBusy(R2);
const CH = [
  {title: 'Same trip, two ways', keys: ['model', 'search', 'wait', 'msg'],
   cap: 'Two recorded runs. A planner model gives each city\'s hotel and weather research to a helper model, then searches flights itself. Top: hand off and wait. Bottom: start all three, keep working.'},
  {title: 'Hand off, then wait', keys: ['model', 'search', 'wait', 'msg'],
   cap: `Sync hands Lisbon over at ${f1(R1.events[0][0])} s and sits idle (hatched) until it answers. Async spends one model call per helper and has all three running by ${f1(spawn2[2])} s.`},
  {title: 'Work while they work', keys: ['model', 'search', 'wait', 'msg'],
   cap: `Async searches flights from ${f1(flights2)} s while its helpers answer at ${res2.map(f1).join(', ')} s. Sync gets Lisbon's answer at ${f1(blocks1[0][4])} s, hands Rome over and waits again.`},
  {title: `Async done at ${f1(W2)} s`, keys: ['model', 'search', 'wait', 'msg'],
   cap: `When async asked for all answers at ${f1(waitAll2)} s, they were already in, so its planner never waited. It finished at ${f1(W2)} s. Sync is still waiting for Rome.`},
  {title: 'A third wait', keys: ['model', 'search', 'wait', 'msg'],
   cap: `Sync waits ${f1(blocks1[2][4] - blocks1[2][3])} s more for Prague. By ${f1(W0)} s (dashed line) one agent doing every search itself had already finished. Sync starts its flights at ${f1(flights1)} s.`},
  {title: `Sync done at ${f1(W1)} s`, keys: ['model', 'search', 'wait', 'msg'],
   cap: `Finish time = planner's model calls + its searches + its waiting. Sync waited ${f1(L1.blocked)} s (${pct1}%), async 0 s. Helpers worked about ${Math.floor(Math.min(...hb1, ...hb2))}-${Math.round(Math.max(...hb1, ...hb2))} s each in both runs.`},
  {title: 'Helpers report back', keys: ['model', 'search', 'msg', 'lost'],
   cap: `A third run: helpers send progress reports. Prague's hotel search fails at ${f1(fail3[4])} s; its helper switches to a backup search and alerts the planner at ${f1(alert3)} s.`},
  {title: 'A reply too late', keys: ['model', 'search', 'msg', 'lost'],
   cap: `The planner replies at ${f1(instr3)} s, but the helper's last model call began at ${f1(lastCall3[3])} s, so it never read the instruction. It was the only unread message in all 7 runs.`},
  {title: 'Keep planners busy', keys: ['wait'],
   cap: `Only sync handoff was slower than one agent (${f1(W0)} s); levels 2, 3, 4 and 6 took ${Math.round(Math.min(...others))}-${Math.round(Math.max(...others))} s. Helpers save time only when the planner keeps working instead of waiting.`},
].map((c, i) => ({...c, at: chapAt(i)}));

const isSecond = t => at(t).moving;
K.player({
  root: '#x', style: 'blueprint', viewBox: [380, 300], duration: D,
  title: 'Replay of recorded runs from notebook 07: a planner agent that hands work to helpers one at a time and waits took 120.2 s; one that starts all helpers and keeps working took 56.8 s; in a third run one late instruction was never read.',
  legend: [
    {key: 'model', label: 'model call', color: 'fill.violet'},
    {key: 'search', label: 'search', color: 'fill.green'},
    {key: 'wait', label: 'planner waiting', color: 'fill.amber'},
    {key: 'msg', label: 'message', color: 'blue'},
    {key: 'lost', label: 'unread message', color: 'red'},
  ],
  chapters: CH,
  log: LOG,
  clock: t => { const p = at(t), g = p.g;
    if (g.view === 'all') return 'all 7 runs';
    const run = g.view === 'cmp' ? 'sync + async' : 'level 3';
    return `${run} · ${f1(p.now)} s` + (p.moving ? ` · 1 s = ${g.speed} s` : ' · paused'); },
  scene: () => `<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="${C.fill.amber}" fill-opacity=".35"/><line x1="0" y1="0" x2="0" y2="5" stroke="${C.fill.amber}" stroke-width="2.2"/></pattern></defs>`,
  frame(t, s) {
    const p = at(t);
    s.dyn.innerHTML = p.g.view === 'cmp' ? viewCompare(p.now, t) : p.g.view === 'l3' ? viewL3(p.now) : viewAll(p.local);
  },
});
