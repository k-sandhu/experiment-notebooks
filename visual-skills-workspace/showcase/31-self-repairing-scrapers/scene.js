/* ===== SCENE: everything below is the explainer itself. Edit freely. ===== */
const {P, T, F, line, rect, ellipse, arrow, curve, poly, C} = K;

/* ---------- DATA. Source: notebooks/31-self-repairing-scrapers (README.md and data/). See notes.md.
   Grid codes per source-week, derived from data/attempts.jsonl (last attempt of each source-week):
   C = accepted and correct with no writer call, R = accepted and correct after a repair that week,
   F = not accepted (flagged for a person), X = accepted but wrong (nobody noticed).
   Column order = README section 1 table order. */
const SRC = ['bok','kso','krs','ksc','asc','mer','nca','hfb','gbs','lhr','cvp','pgc','bra','ohb','keb','pkb','fmf','oce','poa','adv'];
const REDESIGNED = ['kso','krs','ksc','hfb','lhr','cvp'];                     // README section 1, redesign column
const GRID = {
  haiku:      ['CCCCCCCRCCCCCCCCCCCC','CCCCCCCCCCCCCCCCCCCC','CRRCCCCRCRCCCCCCCCCC','CCCCCCCCCCCCCCCCCCCC'],  // Haiku 5.5, rules only
  granRules:  ['RXFRXFCFRRCRCFCXXXXF','CXFCXFCFCCCCCFCXXXFF','CRFRXFCFCRXCCFCXXXFF','CCXCXFCRCCXCCFCXXXFF'],  // Granite 4.2 8B, rules only
  granReview: ['FRFFFFCFRRCRCFCFFXFF','RCFRRFCFCCCCCFCRFRRF','CFFRCFCFCRRCCFCCRCCF','CRFCCFCRCCCCCFCCCCCF'],  // Granite 4.2 8B, rules + review
};
const COST = {            // US dollars, README sections 5 and 7 (Haiku weekly: $0.21 / $0.00 / $0.07 / $0.00)
  haikuW1first: 0.19,     // data/attempts.jsonl: week-1 write cost before the Harrow & Finch repair = $0.193
  hfbRepair: 0.013,       // README section 3: "cost $0.013"
  haikuW1: 0.21, haikuTotal: 0.28, sonnetTotal: 1.76,
  granRules: 0.06, granReview: 4.87,
};
const PLANTED = [         // README section 6, planted-error table: [label, cases, rules flagged, review flagged]
  ['Date taken from the next row', 20, 0, 20],
  ['Day and month swapped', 20, 14, 20],
  ['Body: first paragraph only', 20, 1, 20],
  ['Body: links and footer added', 20, 6, 20],
  ['Author missing on every record', 15, 15, 15],
  ['Title cut to five words', 20, 0, 20],
  ['Three oldest releases missing', 20, 12, 20],
  ['No change (control)', 20, 0, 0],
];
const METHODS = [         // README section 7: [label, release-weeks right of 593, four-week cost, kind]
  ['Haiku programs, rules only', 593, 0.28, 'prog'],
  ['Sonnet programs, rules only', 593, 1.76, 'prog'],
  ['Sonnet reads every page', 593, 4.25, 'read'],
  ['Haiku programs, rules + review', 593, 5.31, 'prog'],
  ['Sonnet programs, rules + review', 593, 7.03, 'prog'],
  ['Granite reads every page', 572, 0.06, 'read'],
  ['Haiku reads every page', 560, 0.23, 'read'],
  ['Granite programs, rules + review', 404, 4.87, 'prog'],
  ['Granite programs, rules only', 294, 0.06, 'prog'],
];
const count = (rows, code) => rows.join('').split('').filter(c => code.includes(c)).length;
const wk4ok = rows => count([rows[3]], 'CR');

/* ---------- layout */
const MONO = 'var(--font-mono, ui-monospace, Menlo, monospace)';
const BX = {             // system boxes: x, y, w, h
  pages: [12, 12, 60, 42], prog: [88, 12, 64, 42], rules: [168, 12, 58, 42],
  review: [242, 12, 58, 42], track: [316, 12, 52, 42], writer: [88, 84, 64, 40],
};
const X0 = 50, CW = 15.9, CELLW = 13.5, Y0 = 168, RH = 21, CELLH = 17;
const cx = j => X0 + j * CW, cy = w => Y0 + w * RH;
const FILL = {C: 'fill.green', R: 'fill.blue', F: 'fill.amber', X: 'fill.red'};
const GLYPH = {C: '', R: 'R', F: 'F', X: '✗', P: '!'};
const usd = v => '$' + v.toFixed(2);

// a box: plain (shown at once) or drawn in with a delay
function box(id, color, labels, o = {}) {
  const [x, y, w, h] = BX[id], seed = {pages: 11, prog: 12, rules: 13, review: 14, track: 15, writer: 16}[id];
  const dash = o.dashed ? ' stroke-dasharray="4 4"' : '';
  const outline = o.anim ? P(rect(x, y, w, h, seed), color, o.t || 0, 600, 1.6, dash)
    : `<path d="${rect(x, y, w, h, seed)}" fill="none" stroke="${K.col(color)}" stroke-width="1.6"${dash}/>`;
  let txt = '';
  labels.forEach((l, i) => { txt += T(x + w / 2, y + (labels.length === 1 ? h / 2 + 5 : 19 + i * 15), l.s,
    {h: l.h, z: l.z || 13, c: l.c || color, t: (o.t || 0) + 200, id: l.id}); });
  return `<g id="g_${id}" style="transition:opacity .45s;opacity:${o.op == null ? 1 : o.op}">${outline}${txt}</g>`;
}
function conn(x1, y1, x2, y2, color, seed, o = {}) {
  const d = line(x1, y1, x2, y2, seed, .6), a = arrow(x1, y1, x2, y2, seed + 1, 6);
  if (o.anim) return P(d, color, o.t || 0, 300, 1.4) + P(a, color, (o.t || 0) + 280, 120, 1.4);
  return `<path d="${d} ${a}" fill="none" stroke="${K.col(color)}" stroke-width="1.4" stroke-linecap="round"/>`;
}

// the whole system diagram; o.writer = model name; o.review = 'off' | 'on'; o.dim = ids to dim; o.anim = draw in
function system(o = {}) {
  const dim = id => (o.dim || []).includes(id) ? .28 : 1, an = !!o.anim, t0 = an ? 0 : 0;
  const revOn = o.review === 'on';
  let m = '';
  m += box('pages', 'ink', [{s: 'Pages', h: 1, z: 15}, {s: '20 sites', z: 12, c: 'mut'}], {anim: an, t: t0, op: dim('pages')});
  m += box('prog', 'ink', [{s: 'Program', h: 1, z: 15}, {s: 'runs free', z: 12, c: 'mut'}], {anim: an, t: t0 + 250, op: dim('prog')});
  m += box('rules', 'ink', [{s: 'Rules', h: 1, z: 15}, {s: 'free', z: 12, c: 'mut'}], {anim: an, t: t0 + 500, op: dim('rules')});
  m += box('review', revOn ? 'violet' : 'mut', [{s: 'Review', h: 1, z: 15, id: 'revLab'}, {s: revOn ? 'Opus 5.5' : 'off', z: 12, c: revOn ? 'violet' : 'mut', id: 'revSub'}],
    {anim: an, t: t0 + 750, dashed: !revOn, op: o.review === 'hide' ? .28 : dim('review')});
  m += box('track', 'ink', [{s: 'Tracker', h: 1, z: 14}], {anim: an, t: t0 + 1000, op: dim('track')});
  m += box('writer', 'violet', [{s: 'Writer', h: 1, z: 15}, {s: o.writer || 'Haiku 5.5', z: 12, id: 'wName'}], {anim: an, t: t0 + 1250, op: dim('writer')});
  const c = an ? 1400 : 0;
  m += `<g id="g_conn" style="transition:opacity .45s">` +
    conn(72, 33, 87, 33, 'mut', 21, {anim: an, t: c}) + conn(152, 33, 167, 33, 'mut', 23, {anim: an, t: c + 100}) +
    conn(226, 33, 241, 33, 'mut', 25, {anim: an, t: c + 200}) + conn(300, 33, 315, 33, 'mut', 27, {anim: an, t: c + 300}) + `</g>`;
  // writer -> program (writes), rules -> writer (report on a failed check)
  m += `<g id="g_writes" style="transition:opacity .45s;opacity:${dim('writer')}">` + conn(120, 83, 120, 56, 'violet', 31, {anim: an, t: c + 400}) +
    T(126, 74, 'writes', {z: 12, c: 'violet', a: 'start', t: c + 500}) + `</g>`;
  const rp = `M197 55 L197 104 L154 104`;
  m += `<g id="g_report" style="transition:opacity .45s;opacity:${dim('report')}">` +
    (an ? P(rp, 'red', c + 600, 500, 1.4, 'stroke-dasharray="3 3"') : `<path d="${rp}" fill="none" stroke="${C.red}" stroke-width="1.4" stroke-dasharray="3 3"/>`) +
    (an ? P(arrow(197, 104, 154, 104, 33, 6), 'red', c + 1050, 120, 1.4) : `<path d="${arrow(197, 104, 154, 104, 33, 6)}" fill="none" stroke="${C.red}" stroke-width="1.4"/>`) +
    T(202, 76, 'failed?', {z: 12, c: 'red', a: 'start', t: c + 700}) + T(202, 90, 'report', {z: 12, c: 'red', a: 'start', t: c + 750}) + `</g>`;
  return m;
}
// paths the travelling dots follow
const PATH = {
  pagesToProg: [[72, 33], [88, 33]], progToRules: [[152, 33], [168, 33]],
  rulesToTrack: [[226, 33], [316, 33]], rulesToReview: [[226, 33], [242, 33]], reviewToTrack: [[300, 33], [316, 33]],
  writerToProg: [[120, 84], [120, 54]], report: [[197, 54], [197, 104], [152, 104]],
};

function spend(v, label) {
  return `<g id="g_spend">` + T(250, 96, label || 'Model spend', {z: 12, c: 'mut', a: 'start'}) +
    T(250, 120, usd(v), {id: 'spend', z: 22, w: 600, a: 'start', extra: `data-v="${v}"`}) + `</g>`;
}

// the 20 x 4 grid; rows: 4 strings with '.' for weeks not yet run
function grid(rows, o = {}) {
  let m = T(12, 148, o.cond || 'Claude Haiku 5.5 writes, rules check', {z: 12, c: 'mut', a: 'start', id: 'cond'});
  const showRe = o.redesign;
  m += T(368, 148, '▲ redesigned in week 3', {z: 12, c: 'mut', a: 'end', id: 'reLab', extra: `style="opacity:${showRe ? 1 : 0};transition:opacity .4s"`});
  SRC.forEach((s, j) => {
    if (!REDESIGNED.includes(s)) return;
    const x = cx(j) + CELLW / 2;
    m += `<path class="re" d="M${x - 4} 163 L${x + 4} 163 L${x} 156 Z" fill="${C.mut}" style="opacity:${showRe ? 1 : 0};transition:opacity .4s"/>`;
  });
  for (let w = 0; w < 4; w++) {
    m += T(14, cy(w) + 13, 'Wk ' + (w + 1), {z: 12, c: 'mut', a: 'start'});
    for (let j = 0; j < 20; j++) m += cell(w, j, rows[w][j]);
  }
  return m;
}
function cellAttrs(code) {
  if (code === '.' || !code) return {fill: 'none', stroke: C.faint, txt: '', tc: C.bg};
  if (code === 'P') return {fill: 'none', stroke: C.red, txt: '!', tc: C.red};
  return {fill: K.col(FILL[code]), stroke: 'none', txt: GLYPH[code], tc: C.bg};
}
function cell(w, j, code) {
  const a = cellAttrs(code), x = cx(j), y = cy(w);
  return `<g id="c${w}_${j}"><rect x="${x}" y="${y}" width="${CELLW}" height="${CELLH}" rx="2.5" fill="${a.fill}" stroke="${a.stroke}" stroke-width="1.2" style="transition:fill .35s,stroke .35s"/>` +
    `<text x="${x + CELLW / 2}" y="${y + 12.5}" text-anchor="middle" font-size="12" font-weight="700" fill="${a.tc}" style="font-family:var(--font-sans, system-ui, sans-serif)">${a.txt}</text></g>`;
}
function setCell(s, w, j, code) {
  const g = s.q(`#c${w}_${j}`); if (!g) return;
  const a = cellAttrs(code), r = g.querySelector('rect'), t = g.querySelector('text');
  r.setAttribute('fill', a.fill); r.setAttribute('stroke', a.stroke); t.textContent = a.txt; t.setAttribute('fill', a.tc);
}
const ring = (s, w, j, c) => s.ring(cx(j) - 2, cy(w) - 2, CELLW + 4, CELLH + 4, c);

// the event log panel: a fixed box with up to 6 lines; addLog writes into it
const LOG_Y = 280, LOG_H = 144;
function logPanel(head) {
  return `<rect x="12" y="${LOG_Y}" width="356" height="${LOG_H}" rx="7" fill="${C.panel}" stroke="${C.line}"/>` +
    T(22, LOG_Y + 18, head || 'event log of the recorded run', {m: 1, z: 12, c: 'faint', a: 'start'}) +
    `<g id="log"></g>`;
}
function makeLog(s) {
  const lines = [], g = s.q('#log');
  return (text, c = 'ink') => {
    lines.push([text, c]); if (lines.length > 6) lines.shift();
    g.innerHTML = lines.map((l, i) => `<text x="22" y="${LOG_Y + 42 + i * 19}" font-size="12" fill="${K.col(l[1])}" style="font-family:${MONO}">${K.esc(l[0])}</text>`).join('');
    const last = g.lastChild; s.fadeIn(last, 300);
  };
}
const summary = (text, c) => T(190, 266, text, {id: 'sum', z: 13, c: c || 'ink', w: 600});
const rowsUpTo = (rows, n, extra) => rows.map((r, w) => w < n ? r : (extra && extra[w]) || '....................');

/* ---------- steps */
K.stepper({
  root: '#x', style: 'chalkboard', viewBox: [380, 432],
  title: 'A replay of a recorded experiment: a language model writes 20 web scrapers, free automatic rules catch the breaks after six site redesigns, one repair each fixes them, and a paid model review only matters when the writer model is weak.',
  legend: [
    {key: 'ok', label: 'Correct, no model call', color: 'fill.green'},
    {key: 'rep', label: 'Correct after a repair', color: 'fill.blue'},
    {key: 'flag', label: 'Flagged for a person', color: 'fill.amber'},
    {key: 'bad', label: 'Wrong, nobody noticed', color: 'fill.red'},
    {key: 'model', label: 'Model call (costs money)', color: 'violet'},
  ],
  extraCaptions: [
    'With the Opus review, only 1 wrong source-week slips through and 16 of 20 sources are right by week 4. The reviews raise four weeks of spend from $0.06 to $4.87.',
  ],
  steps: [
    { title: '1. Watching 20 news pages', keys: ['model'],
      cap: 'Every Monday a program visits 20 news pages and copies each new release into a tracker. A model writes the program; checks that never see the right answer decide whether to keep it.',
      draw: () => system({anim: true, review: 'off'}) + spend(0) + grid(rowsUpTo(GRID.haiku, 0)) + logPanel(),
      start(s) {
        const log = makeLog(s);
        s.at(2200, () => log('• 20 made-up organisations, 1 news page each'));
        s.at(2700, () => log('• 4 weekly runs, 5 to 26 October 2026'));
        s.at(3200, () => log('• fields: headline, date, author, text'));
        s.at(3700, () => log('• the right answers are hidden from every check', 'mut'));
      },
      duration: 4300 },

    { title: '2. Week 1: write once', keys: ['ok', 'model'],
      cap: 'Claude Haiku 5.5 sees one listing page and one sample release per site and writes 20 programs. 19 pass every rule and are fully correct. One does not.',
      draw: () => system({review: 'off', dim: ['report']}) + spend(0) + grid(rowsUpTo(GRID.haiku, 0)) + logPanel(),
      start(s) {
        const log = makeLog(s);
        log('→ Haiku writes 20 programs, one per site', 'violet');
        s.travel(PATH.writerToProg, 600, 'violet', {delay: 300});
        s.count('#spend', COST.haikuW1first, {from: 0, du: 2200, delay: 400, fmt: usd});
        for (let j = 0; j < 20; j++) s.at(900 + j * 110, () => {
          if (SRC[j] === 'hfb') { setCell(s, 0, j, 'P'); ring(s, 0, j, 'red'); } else setCell(s, 0, j, 'C');
        });
        s.at(1200, () => s.travel([...PATH.progToRules, ...PATH.rulesToTrack.slice(1)], 900, 'green'));
        s.at(3300, () => log('✓ 19 pass every rule: all 19 fully correct', 'green'));
        s.at(3900, () => log('✗ Harrow & Finch Bank fails the date rule', 'red'));
      },
      duration: 4600 },

    { title: '3. Check, report, repair', keys: ['rep', 'model'],
      cap: 'Harrow & Finch sends dates in milliseconds. The program read them as seconds and returned no date. The free date rule caught it, the report went back, and one repair fixed it.',
      draw: () => system({review: 'off', dim: ['pages', 'track']}) + spend(COST.haikuW1first) +
        grid(rowsUpTo(GRID.haiku, 0, ['CCCCCCCPCCCCCCCCCCCC'])) + logPanel(),
      start(s) {
        const log = makeLog(s), j = SRC.indexOf('hfb');
        ring(s, 0, j, 'red');
        log('← 6 records: headlines, authors, text ok', 'ink');
        s.at(500, () => log('  published_at 1790602200000 -> date: None', 'mut'));
        s.at(900, () => s.travel(PATH.progToRules, 500, 'ink'));
        s.at(1500, () => { s.ring(168, 12, 58, 42, 'red'); log('✗ rule: date must be "YYYY-MM-DD", got None', 'red'); });
        s.at(2300, () => { s.travel(PATH.report, 800, 'red'); log('→ report: error, 15 requests, 2 records', 'red'); });
        s.at(3300, () => { s.ring(88, 84, 64, 40, 'violet'); log('→ Haiku repairs: big numbers / 1000', 'violet');
          s.count('#spend', COST.haikuW1, {from: COST.haikuW1first, du: 700, fmt: usd}); });
        s.at(3900, () => s.travel(PATH.writerToProg, 500, 'violet'));
        s.at(4500, () => s.travel([...PATH.progToRules, ...PATH.rulesToTrack.slice(1)], 900, 'blue'));
        s.at(5400, () => { setCell(s, 0, j, 'R'); ring(s, 0, j, 'blue'); log('✓ date 2026-09-28: 24 of 24 fields right', 'blue'); });
      },
      duration: 6000 },

    { title: '4. Week 2: reuse for free', keys: ['ok'],
      cap: 'In week 2 the stored programs run again on 1 to 3 new releases per site. No site changed, every rule passes, so no model is called: 20 of 20 correct for $0.00.',
      draw: () => system({review: 'off', dim: ['writer', 'report']}) + spend(COST.haikuW1) + grid(rowsUpTo(GRID.haiku, 1)) + logPanel(),
      start(s) {
        const log = makeLog(s);
        log('→ same 20 programs, this week\'s pages', 'ink');
        s.travel([...PATH.pagesToProg, ...PATH.progToRules.slice(0), ...PATH.rulesToTrack.slice(1)], 1500, 'green', {delay: 300});
        for (let j = 0; j < 20; j++) s.at(700 + j * 70, () => setCell(s, 1, j, GRID.haiku[1][j]));
        s.at(2300, () => log('✓ 20 of 20 pass every rule', 'green'));
        s.at(2800, () => log('✓ 20 of 20 fully correct, no model call', 'green'));
        s.at(3300, () => log('  spend this week: $0.00', 'mut'));
      },
      duration: 3800 },

    { title: '5. Week 3: six redesigns', keys: ['ok', 'rep', 'model'],
      cap: 'Six sites are redesigned. Four redesigns break the program and a free rule flags every break; one repair each fixes them. Week 4 runs free. Sonnet 5.5 did the same for $1.76.',
      draw: () => system({review: 'off'}) + spend(COST.haikuW1) + grid(rowsUpTo(GRID.haiku, 2), {redesign: true}) + logPanel() +
        `<text id="sum" x="190" y="266" text-anchor="middle" font-size="13" font-weight="600" fill="${C.ink}"></text>`,
      start(s) {
        const log = makeLog(s), H = GRID.haiku[2];
        const breaks = [ // README section 5 and data/attempts.jsonl static_problems, week 3
          ['kso', '✗ Statistics Office: 0 records'],
          ['krs', '✗ Revenue Service: 5 records vs 8 last week'],
          ['hfb', '✗ Harrow & Finch: 0 records (410 Gone)'],
          ['lhr', '✗ Lumen Home: author "Words by Daren Pell"'],
        ];
        for (let j = 0; j < 20; j++) s.at(300 + j * 60, () => setCell(s, 2, j, H[j] === 'R' ? 'P' : 'C'));
        breaks.forEach(([id, txt], i) => s.at(1700 + i * 650, () => { const j = SRC.indexOf(id); ring(s, 2, j, 'red'); log(txt, 'red'); }));
        s.at(4400, () => s.travel(PATH.report, 600, 'red'));
        s.at(5000, () => { s.travel(PATH.writerToProg, 500, 'violet'); s.count('#spend', COST.haikuTotal, {from: COST.haikuW1, du: 800, fmt: usd}); });
        s.at(5600, () => { breaks.forEach(([id]) => setCell(s, 2, SRC.indexOf(id), 'R')); log('→ 4 repairs, +$0.07: all 4 now correct', 'blue'); });
        s.at(6200, () => log('✓ Securities Comm., Corvel: still correct', 'green'));
        for (let j = 0; j < 20; j++) s.at(6900 + j * 45, () => setCell(s, 3, j, GRID.haiku[3][j]));
        s.at(7900, () => { log('✓ week 4: 20 of 20, no model call', 'green');
          s.q('#sum').textContent = `${count(GRID.haiku, 'CR')} of 80 source-weeks correct for ${usd(COST.haikuTotal)}`; s.fadeIn('#sum', 400); });
      },
      duration: 8600 },

    { title: '6. A weak writer', keys: ['ok', 'rep', 'flag', 'bad', 'model'],
      cap: 'Granite 4.2 8B, a small open model, writes weaker programs. With rules only, 22 source-weeks of wrong records slip through (red ✗). Tap to add the Opus review of 2 sampled records.',
      draw: () => system({review: 'off', writer: 'Granite 8B'}) + spend(COST.granRules, 'Spend, 4 weeks') +
        grid(GRID.haiku, {cond: 'Granite 4.2 8B writes, rules check', redesign: true}) +
        `<rect x="12" y="${LOG_Y}" width="356" height="${LOG_H}" rx="7" fill="${C.panel}" stroke="${C.line}"/>` +
        T(30, LOG_Y + 34, 'Wrong, nobody noticed', {z: 13, c: 'ink', a: 'start'}) +
        T(350, LOG_Y + 36, String(count(GRID.granRules, 'X')), {id: 'stBad', z: 24, w: 700, c: 'red', a: 'end', extra: `data-v="${count(GRID.granRules, 'X')}"`}) +
        T(30, LOG_Y + 52, 'source-weeks out of 80', {z: 12, c: 'mut', a: 'start'}) +
        T(30, LOG_Y + 82, 'Sources correct in week 4', {z: 13, c: 'ink', a: 'start'}) +
        T(350, LOG_Y + 84, wk4ok(GRID.granRules) + ' of 20', {id: 'stOk', z: 24, w: 700, c: 'green', a: 'end'}) +
        T(30, LOG_Y + 112, 'Flagged for a person, 4 weeks', {z: 13, c: 'ink', a: 'start'}) +
        T(350, LOG_Y + 114, String(count(GRID.granRules, 'F')), {id: 'stFlag', z: 24, w: 700, c: 'amber', a: 'end', extra: `data-v="${count(GRID.granRules, 'F')}"`}) +
        T(30, LOG_Y + 132, 'source-weeks out of 80', {z: 12, c: 'mut', a: 'start'}),
      start(s) {
        let on = false;
        const order = [...Array(80).keys()];
        for (let k = 0; k < 80; k++) { const w = Math.floor(k / 20), j = k % 20; s.at(200 + k * 18, () => setCell(s, w, j, GRID.granRules[w][j])); }
        const apply = () => {
          const G = on ? GRID.granReview : GRID.granRules;
          order.forEach(k => { const w = Math.floor(k / 20), j = k % 20; s.at(k * 12, () => setCell(s, w, j, G[w][j])); });
          const rv = s.q('#g_review path'); rv.setAttribute('stroke', on ? C.violet : C.mut); rv.setAttribute('stroke-dasharray', on ? '' : '4 4');
          s.swap('#revSub', on ? 'Opus 5.5' : 'off', on ? 'violet' : 'mut'); s.q('#revLab').setAttribute('fill', on ? C.violet : C.mut);
          s.swap('#cond', on ? 'Granite 4.2 8B writes, rules + review' : 'Granite 4.2 8B writes, rules check');
          s.count('#stBad', count(G, 'X'), {du: 800});
          s.count('#stFlag', count(G, 'F'), {du: 800});
          s.swap('#stOk', wk4ok(G) + ' of 20');
          s.count('#spend', on ? COST.granReview : COST.granRules, {du: 900, fmt: usd});
          if (on) { s.ring(242, 12, 58, 42, 'violet'); s.travel([...PATH.rulesToReview, ...PATH.reviewToTrack.slice(0)], 800, 'violet'); }
          s.cap(on ? 'With the Opus review, only 1 wrong source-week slips through and 16 of 20 sources are right by week 4. The reviews raise four weeks of spend from $0.06 to $4.87.'
                   : 'Granite 4.2 8B, a small open model, writes weaker programs. With rules only, 22 source-weeks of wrong records slip through (red ✗). Tap to add the Opus review of 2 sampled records.');
        };
        const b = s.btn('check', 'Add the Opus review', () => { on = !on; b.setAttribute('aria-pressed', on); b.lastChild.textContent = on ? 'Remove the review' : 'Add the Opus review'; apply(); }, {primary: true});
        b.setAttribute('aria-pressed', 'false');
      },
      demo: async s => { s.tap(s.act.querySelector('button')); await s.wait(2600); },
      idleDemo: 5500, demoDuration: 2800, duration: 1800 },

    { title: '7. Which check catches what', keys: ['model'],
      cap: 'Errors were planted in correct output. The free rules flagged 48 of 135, mostly loud ones. The Opus review flagged all 135. Neither raised an alarm on 20 unchanged controls.',
      draw: () => {
        const tot = PLANTED.slice(0, 7), nR = tot.reduce((a, r) => a + r[2], 0), nV = tot.reduce((a, r) => a + r[3], 0), nC = tot.reduce((a, r) => a + r[1], 0);
        let m = T(12, 22, `${nC} planted errors, 20 unchanged controls`, {z: 14, a: 'start', w: 600}) +
          T(12, 42, `Rules flagged ${nR}`, {z: 13, c: 'ink', a: 'start'}) + T(130, 42, `Review flagged ${nV}`, {z: 13, c: 'violet', a: 'start'});
        PLANTED.forEach((r, i) => {
          const y = 58 + i * 46, ctl = i === 7, BW = 220 / r[1];
          m += T(12, y + 12, r[0], {z: 13, a: 'start', c: ctl ? 'mut' : 'ink', t: 200 + i * 120});
          m += T(12, y + 27, 'rules', {z: 12, c: 'mut', a: 'start', t: 200 + i * 120}) + T(12, y + 41, 'review', {z: 12, c: 'violet', a: 'start', t: 200 + i * 120});
          m += `<rect x="70" y="${y + 18}" width="220" height="10" rx="2" fill="${C.faint}" opacity=".35"/>`;
          m += `<rect x="70" y="${y + 32}" width="220" height="10" rx="2" fill="${C.faint}" opacity=".35"/>`;
          m += `<rect class="pb" x="70" y="${y + 18}" width="${Math.max(0, r[2] * BW)}" height="10" rx="2" fill="${C.ink}" style="transform-box:fill-box;transform-origin:0 50%;transform:scaleX(0)"/>`;
          m += `<rect class="pb" x="70" y="${y + 32}" width="${Math.max(0, r[3] * BW)}" height="10" rx="2" fill="${C.fill.violet}" style="transform-box:fill-box;transform-origin:0 50%;transform:scaleX(0)"/>`;
          const lab = ctl ? ['0 false alarms', '0 false alarms'] : [`${r[2]} of ${r[1]}`, `${r[3]} of ${r[1]}`];
          m += T(296, y + 27, lab[0], {z: 12, a: 'start', c: 'ink', t: 900 + i * 150}) + T(296, y + 41, lab[1], {z: 12, a: 'start', c: 'violet', t: 900 + i * 150});
        });
        return m;
      },
      start(s) { [...s.svg.querySelectorAll('.pb')].forEach((b, k) => s.at(300 + Math.floor(k / 2) * 150, () => s.bar(b, 1, 700))); },
      duration: 2600 },

    { title: '8. Or read every page?', keys: [],
      cap: 'Haiku’s programs with free rules were right in all 593 release-weeks for $0.28. Sonnet reading every page was also always right, for $4.25. Real pages are often 10 to 50 times larger.',
      draw: () => {
        let m = T(12, 20, 'Share of 593 release-weeks right', {z: 13, a: 'start', w: 600}) + T(368, 20, '4-week cost', {z: 13, a: 'end', w: 600});
        METHODS.forEach((r, i) => {
          const y = 34 + i * 43, frac = r[1] / 593, pct = r[1] === 593 ? '100%' : (100 * frac).toFixed(1) + '%';
          m += T(12, y + 13, r[0], {z: 13, a: 'start', c: 'ink', t: 150 + i * 100});
          m += T(368, y + 13, usd(r[2]), {z: 13, a: 'end', w: 600, c: 'ink', t: 150 + i * 100});
          m += `<rect x="12" y="${y + 20}" width="290" height="11" rx="2" fill="${C.faint}" opacity=".35"/>`;
          m += `<rect class="mb" x="12" y="${y + 20}" width="${290 * frac}" height="11" rx="2" fill="${C.fill.green}" style="transform-box:fill-box;transform-origin:0 50%;transform:scaleX(0)"/>`;
          m += T(310, y + 30, pct, {z: 12, a: 'start', c: 'ink', t: 900 + i * 100});
        });
        m += T(12, 428, 'Bars: share right. Costs: model calls, list prices.', {z: 12, a: 'start', c: 'mut', t: 1600});
        return m;
      },
      start(s) {
        [...s.svg.querySelectorAll('.mb')].forEach((b, k) => s.bar(b, 1, 700 + k * 60));
        s.at(1900, () => s.ring(8, 30, 364, 40, 'green'));
      },
      duration: 2800 },

    { title: '9. What to do', keys: ['model'],
      cap: 'Let a capable model write the scrapers, run the free rules on every run, and pay for a model review only where the rules are blind: new or repaired programs and weak writers.',
      draw: () => {
        let m = system({review: 'on', dim: []}) + spend(COST.haikuTotal, 'Haiku, 4 weeks');
        const items = [
          ['1', 'Let a capable model write', 'the programs. Haiku was enough.', 'violet'],
          ['2', 'Run the free rules on every run;', 'a failed rule triggers a repair.', 'ink'],
          ['3', 'Pay for the review only on new or', 'repaired programs and weak writers.', 'violet'],
        ];
        items.forEach((it, i) => {
          const y = 158 + i * 54, t = 400 + i * 900;
          m += T(22, y + 4, it[0], {h: 1, z: 22, c: it[3], t});
          m += T(40, y, it[1], {z: 13, a: 'start', t: t + 100}) + T(40, y + 18, it[2], {z: 13, a: 'start', t: t + 200});
        });
        m += `<rect x="12" y="330" width="356" height="92" rx="7" fill="${C.panel}" stroke="${C.line}"/>` +
          T(24, 352, 'Caveat', {h: 1, z: 18, c: 'amber', a: 'start', t: 3200}) +
          T(24, 374, '20 made-up, small, tidy sites, one trap each.', {z: 12.5, a: 'start', t: 3300}) +
          T(24, 392, 'Real sites will make errors nobody planned for,', {z: 12.5, a: 'start', t: 3400}) +
          T(24, 410, 'and the rules flagged only 48 of 135 planted ones.', {z: 12.5, a: 'start', t: 3500});
        return m;
      },
      start(s) {
        s.at(500, () => s.ring(88, 84, 64, 40, 'violet'));
        s.at(1400, () => s.ring(168, 12, 58, 42, 'ink'));
        s.at(2300, () => s.ring(242, 12, 58, 42, 'violet'));
      },
      duration: 4100 },
  ],
});
