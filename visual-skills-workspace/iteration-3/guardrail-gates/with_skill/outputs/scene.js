/* ===== SCENE: everything below is the explainer itself. ===== */
document.head.insertAdjacentHTML('beforeend', `<style>
.try{display:flex;gap:6px;flex:1 1 100%;margin:0 4px}
.try select,.try input{background:var(--k-panel);color:var(--k-ink);border:1px solid var(--k-line);border-radius:8px;min-height:40px;font-size:16px;box-sizing:border-box}
.try select{flex:0 0 84px;padding:0 4px}
.try input{flex:1 1 auto;min-width:0;padding:0 8px;font-family:ui-monospace,Menlo,Consolas,monospace}
</style>`);
const {P, T, F, line, rect, poly, C} = K;

/* DATA is injected by build.py from evals/guardrail-gates/files/data.json, which comes from notebook 10
   (notebooks/10-code-execution-guardrails: data/cases.json, data/gate_decisions.csv, data/summary.csv,
   data/broker_audit.json). requests[].d = decisions in GATE_KEYS order, 1 = the gate allowed it. */
const DATA = /*DATA*/null;
const GATE_KEYS = ['observe only', 'lexical prefix', 'scoped capabilities', 'read only', 'approval bound'];
const REQ = Object.fromEntries(DATA.requests.map(r => [r.id, r]));

// GATES-BEGIN: a small copy of the two gate designs, used to judge paths the reader types in step 6.
// Rules from the notebook README sections 1-2. build.py checks these functions against all 22 recorded decisions.
const ROOT = '/workspace/acme';
const LINKS = {'/workspace/acme/tmp/shared-link': '/srv/shared'};
const PROTECTED = ['.env', '.ssh', 'credentials', 'payroll'];
const PREFIX_NEED = {read: ROOT, write: ROOT + '/output', delete: ROOT + '/tmp'};
const under = (p, dir) => p.startsWith(dir + '/');
function prefixGate(op, path, approved = true) {          // notebook: "lexical prefix"
  const need = PREFIX_NEED[op];
  if (!need) return {ok: false, why: 'no such action'};
  if (!path.startsWith(need)) return {ok: false, why: "start doesn't match"};
  if (op === 'delete' && !approved) return {ok: false, why: 'no trusted approval'};
  return {ok: true, why: 'start matches'};
}
function resolvePath(path) {                              // walk one part at a time, following .. and links
  if (!path.startsWith('/')) path = ROOT + '/' + path;
  let parts = []; const hops = ['/'];
  for (const seg of path.split('/')) {
    if (!seg || seg === '.') continue;
    if (seg === '..') parts.pop(); else parts.push(seg);
    let cur = '/' + parts.join('/'), n = 0;
    hops.push(cur);
    while (LINKS[cur] && n++ < 8) { cur = LINKS[cur]; parts = cur.split('/').filter(Boolean); hops.push(cur); }
  }
  return {end: '/' + parts.join('/'), hops};
}
function scopedGate(op, path, approved = true, readOnly = false) {   // notebook: "scoped capabilities"
  if (!['read', 'write', 'delete'].includes(op) || (readOnly && op !== 'read')) return {ok: false, why: 'no such action', end: null, hops: []};
  const {end, hops} = resolvePath(path);
  const r = (ok, why) => ({ok, why, end, hops});
  if (!(end === ROOT || under(end, ROOT))) return r(false, 'ends outside the project');
  const bad = end.slice(ROOT.length).split('/').find(x => PROTECTED.some(n => x.toLowerCase() === n || x.toLowerCase().startsWith(n + '.')));
  if (bad) return r(false, 'secret name: ' + bad);
  if (op === 'write' && !under(end, ROOT + '/output')) return r(false, 'writes only in output/');
  if (op === 'delete' && !under(end, ROOT + '/tmp')) return r(false, 'deletes only in tmp/');
  if (op === 'delete' && !approved) return r(false, 'no trusted approval');
  return r(true, op === 'read' ? 'ends inside the project' : op === 'write' ? 'ends in output/' : 'ends in tmp/');
}
// GATES-END

/* ---------- the folder map (same place in steps 1-6) */
const NODES = {   // path: [x of label, baseline y, label]
  '/': [24, 182, '/ (top)'],
  '/workspace': [38, 201, 'workspace/'],
  '/workspace/acme': [52, 220, 'acme/'],
  '/workspace/acme/input': [66, 239, 'input/'],
  '/workspace/acme/output': [66, 258, 'output/'],
  '/workspace/acme/tmp': [66, 277, 'tmp/'],
  '/workspace/acme/tmp/stale.txt': [80, 296, 'stale.txt'],
  '/workspace/acme/tmp/shared-link': [80, 315, 'shared-link'],
  '/workspace/acme/tmp-other': [66, 335, 'tmp-other/'],
  '/workspace/acme/.env': [66, 354, '.env'],
  '/srv': [240, 201, 'srv/'],
  '/srv/shared': [254, 220, 'shared/'],
  '/srv/shared/archive': [268, 239, 'archive'],
  '/srv/private.txt': [254, 258, 'private.txt'],
};
const NID = {}; Object.keys(NODES).forEach((p, i) => NID[p] = 'n' + i);
const mk = p => [NODES[p][0] - 7, NODES[p][1] - 4.5];
const parentOf = p => p === '/' ? null : (p.slice(0, p.lastIndexOf('/')) || '/');
const LINK_Y = 323;
function route(a, b) {
  const A = mk(a), B = mk(b);
  if (LINKS[a] === b) return [[A[0], LINK_Y], [214, LINK_Y], [214, B[1]], B];
  if (a === '/' && b === '/srv') return [[A[0], 188], [B[0], 188], B];
  if (a === '/srv' && b === '/') return [[A[0], 188], [B[0], 188], B];
  if (parentOf(b) === a) return [[A[0], B[1]], B];
  if (parentOf(a) === b) return [[B[0], A[1]], B];
  return [B];
}
function walkPoints(hops) {
  const known = hops.filter(h => NODES[h]).filter((h, i, a) => i === 0 || h !== a[i - 1]);
  const pts = [mk(known[0])];
  for (let i = 1; i < known.length; i++) pts.push(...route(known[i - 1], known[i]));
  return {pts, last: known[known.length - 1]};
}
function mapMarkup(t0 = 0) {
  let m = '';
  // project area and outside area
  m += P(rect(36, 207, 172, 156, 41), 'faint', t0, 700, 1.1, 'stroke-dasharray="4 4"');
  m += P(rect(224, 190, 144, 80, 42), 'faint', t0 + 100, 700, 1.1, 'stroke-dasharray="4 4"');
  m += T(296, 182, 'outside: off limits', {z: 13, c: 'red', t: t0 + 300});
  // connectors
  let k = 0;
  Object.keys(NODES).forEach(p => {
    const par = parentOf(p); if (!par || !NODES[par]) return;
    const pts = p === '/srv' ? [mk('/'), [mk('/')[0], 188], [mk(p)[0], 188], [mk(p)[0], mk(p)[1] - 3]] : [mk(par), [mk(par)[0], mk(p)[1]], [mk(p)[0] - 3, mk(p)[1]]];
    m += P(poly(pts, 60 + k++), 'faint', t0 + 200 + k * 40, 300, 1.2);
  });
  // labels and markers
  Object.keys(NODES).forEach((p, i) => {
    const [x, y, lab] = NODES[p], [mx, my] = mk(p);
    m += `<circle cx="${mx}" cy="${my}" r="2.6" fill="${C.mut}"/>`;
    m += T(x, y, lab, {z: 14, a: 'start', id: NID[p], t: t0 + 150 + i * 60});
  });
  // the link
  const L = mk('/workspace/acme/tmp/shared-link'), S = mk('/srv/shared');
  m += P(poly([[L[0], L[1] + 4], [L[0], LINK_Y], [214, LINK_Y], [214, S[1]], [S[0] - 5, S[1]]], 77), 'mut', t0 + 1200, 700, 1.3, 'stroke-dasharray="3 4"');
  m += P(K.arrow(214, S[1], S[0] - 4, S[1], 78, 6), 'mut', t0 + 1850, 150, 1.3);
  m += T(160, 315, 'link', {z: 13, c: 'mut', a: 'start', t: t0 + 1300});
  // the rules, written where they apply
  const note = (p, x, txt, c, t) => T(x, NODES[p][1], txt, {z: 13, c, a: 'start', t: t0 + t, id: 'a_' + NID[p]});
  m += note('/workspace/acme', 96, '← the project', 'mut', 1000);
  m += note('/workspace/acme/output', 124, 'writes OK', 'green', 1100);
  m += note('/workspace/acme/tmp', 104, 'deletes OK', 'green', 1200);
  m += note('/workspace/acme/.env', 124, 'secret: never', 'red', 1300);
  return m;
}

/* ---------- the request card and the two gate boxes */
function cardMarkup() {
  return P(rect(12, 12, 356, 66, 11), 'violet', 0, 600) +
    T(24, 32, '', {id: 'op', c: 'violet', z: 14, a: 'start'}) +
    T(24, 52, '', {id: 'p1', m: 1, z: 14, a: 'start'}) +
    T(24, 70, '', {id: 'p2', m: 1, z: 14, a: 'start'});
}
function boxMarkup(x, id, name, color, seed, t = 300) {
  return P(rect(x, 86, 172, 72, seed), color, t, 600) +
    T(x + 12, 108, name, {h: 1, z: 20, c: color, a: 'start', t: t + 200, id: id + 'n'}) +
    T(x + 12, 132, '', {id: id + 'v', z: 16, w: 600, a: 'start'}) +
    T(x + 12, 150, '', {id: id + 'r', z: 13, c: 'mut', a: 'start'});
}
const cut = (str, n) => str.length > n ? str.slice(0, n - 1) + '…' : str;
function splitPath(op, path) {
  const need = PREFIX_NEED[op];
  if (need && path.startsWith(need)) return [need, cut(path.slice(need.length), 38)];
  if (path.length <= 38) return [path, ''];
  let i = path.lastIndexOf('/', 38); if (i < 8) i = 38;
  return [path.slice(0, i), cut(path.slice(i), 38)];
}
const OPWORD = {read: 'read', write: 'write', delete: 'delete'};
function setCard(s, op, path, fade = true) {
  const [a, b] = splitPath(op, path), set = (id, txt, c) => { if (fade) s.swap('#' + id, txt, c); else { const e = s.q('#' + id); e.textContent = txt; if (c) e.setAttribute('fill', K.col(c)); } };
  set('op', 'The agent asks to ' + OPWORD[op] + ':', 'violet'); set('p1', a, 'ink'); set('p2', b, 'ink');
}
function prefixLook(s, op, path) {   // the prefix check reads only the start: colour it amber, dim the rest
  const g = prefixGate(op, path), p1 = s.q('#p1'), p2 = s.q('#p2');
  s.dyn.querySelectorAll('.ul').forEach(e => e.remove());
  if (g.ok) {
    p1.setAttribute('fill', K.col('amber')); p2.setAttribute('fill', K.col('mut'));
    const w = p1.getComputedTextLength(), u = s.el('path', {d: line(24, 56, 24 + w, 56, 90), stroke: K.col('amber'), 'stroke-width': 2, fill: 'none', 'stroke-linecap': 'round', class: 'ul'});
    s.drawIn(u, 450);
  } else { p1.setAttribute('fill', K.col('ink')); p2.setAttribute('fill', K.col('ink')); }
  return g;
}
function verdict(s, id, ok, why, words = ['✓ allowed', '✗ blocked'], colors = ['ink', 'ink']) {
  s.swap('#' + id + 'v', ok ? words[0] : words[1], ok ? colors[0] : colors[1]);
  s.swap('#' + id + 'r', why, 'mut');
}
const truth = (s, ok, why) => verdict(s, 'R', ok, why, ['✓ permitted', '✗ forbidden'], ['green', 'red']);
async function walk(s, hops, color, endColor, du) {   // a dot walks the path on the map and marks where it ends
  const {pts, last} = walkPoints(hops), before = new Set(s.dyn.children);
  const go = s.travel(pts, du || Math.min(3200, 240 * pts.length), color, {r: 4, keep: true});
  [...s.dyn.children].forEach(e => { if (!before.has(e) && e.tagName === 'path') { e.setAttribute('stroke-width', 2.6); e.setAttribute('stroke-opacity', .85); } });   // a trail the reader can follow afterwards
  await go;
  const [mx, my] = mk(last);
  s.el('circle', {cx: mx, cy: my, r: 6, fill: 'none', stroke: K.col(endColor), 'stroke-width': 2.2});
  const lab = s.q('#' + NID[last]); if (lab) lab.setAttribute('fill', K.col(endColor));
  return last;
}
function offMap(s, last, end, color) {   // the end is deeper than the map shows: write the rest after the label
  if (!end || end === last || !NODES[last]) return;
  const lab = s.q('#' + NID[last]), rest = end.slice(last === '/' ? 1 : last.length + 1);
  const x = NODES[last][0] + lab.getComputedTextLength() + (lab.textContent.endsWith('/') ? 1 : 4);
  const note = s.q('#a_' + NID[last]); if (note) note.style.opacity = 0;   // make room: hide the rule note on this row
  s.write(x, NODES[last][1], cut(rest, last === '/' ? 22 : 16), {z: 14, a: 'start', c: color});
}
function badge(s, p, n, extra = 0) {
  const lab = s.q('#' + NID[p]), x = NODES[p][0] + lab.getComputedTextLength() + 13 + extra, y = NODES[p][1] - 5;
  s.el('circle', {cx: x, cy: y, r: 8, fill: K.col('red')});
  s.write(x, y + 4.5, String(n), {z: 13, w: 700, c: C.bg});
}
const hopsOf = r => resolvePath(r.target).hops;
const resolvedEnd = r => resolvePath(r.target).end;

/* ---------- counts for step 7, computed from the recorded decisions and checked against summary.csv */
const COUNTS = GATE_KEYS.map((g, gi) => {
  const forb = DATA.requests.filter(r => !r.expected_allow), perm = DATA.requests.filter(r => r.expected_allow);
  const c = {gate: g, fa: forb.filter(r => r.d[gi]).length, fn: forb.length, pa: perm.filter(r => r.d[gi]).length, pn: perm.length};
  const sm = DATA.summary.find(x => x.gate === g);
  if (!sm || sm.forbidden_allowed !== c.fa || sm.permitted_allowed !== c.pa || sm.forbidden_n !== c.fn || sm.permitted_n !== c.pn) console.error('count mismatch for ' + g);
  return c;
});
const TRICKS = ['traversal', 'prefix_sibling', 'linked_target', 'link_then_parent', 'secret'];
const TRICK_WHY = {prefix_sibling: 'tmp-other is not tmp/', linked_target: 'link leads to /srv', link_then_parent: 'ends in /srv', secret: '.env is a secret'};
const prefixLetThrough = DATA.requests.filter(r => !r.expected_allow && r.d[1]).map(r => r.id);
if (prefixLetThrough.join() !== TRICKS.join()) console.error('trick list differs from data: ' + prefixLetThrough.join());

const ANSWER = ok => (ok ? 'Right, it lets it through. ' : 'It lets it through. ') +
  'The three .. climb out of the project to /srv/shared/archive, but the check only read the amber start. The rules say forbidden.';

/* ---------- step 6: the reader's own path */
const EXAMPLES = ['traversal', 'prefix_sibling', 'linked_target', 'link_then_parent', 'secret', 'normalized_temp', 'read_normalized', 'nested_report', 'input_overwrite', 'source_delete', 'external_read'];

K.stepper({
  root: '#x', style: 'chalkboard', viewBox: [380, 380], actHeight: 100,
  title: 'An eight-step lesson on why a file gate that only checks how a path starts can be tricked, and what safer gates do differently, using the 22 test requests from notebook 10.',
  legend: [
    {key: 'req', label: "Agent's request", color: 'violet'},
    {key: 'prefix', label: 'Prefix check', color: 'amber'},
    {key: 'scoped', label: 'Scoped gate', color: 'blue'},
    {key: 'good', label: 'Permitted', color: 'green'},
    {key: 'bad', label: 'Forbidden', color: 'red'},
  ],
  extraCaptions: [ANSWER(true), ANSWER(false)],
  steps: [
    { title: '1. A gate guards the files', keys: ['req', 'prefix', 'good', 'bad'],
      cap: 'An AI agent asks to delete a file. A small program, the gate, says yes or no before anything runs. A path is directions on the folder map: from the top into workspace, acme, tmp, then stale.txt.',
      draw: () => cardMarkup() + boxMarkup(12, 'G', 'Prefix check', 'amber', 21) + boxMarkup(196, 'R', 'The rules say', 'ink', 22, 500) + mapMarkup(700),
      start(s) {
        const r = REQ.remove_temp; setCard(s, r.operation, r.target, false);
        s.at(900, () => verdict(s, 'G', true, 'decides first', ['? waiting', '']));
        s.at(1100, () => truth(s, true, 'delete inside tmp/'));
        s.at(2800, () => walk(s, hopsOf(r), 'violet', 'green', 1800));
      },
      duration: 5000 },

    { title: '2. The prefix check at work', keys: ['req', 'prefix', 'good', 'bad'],
      cap: 'For a delete, the prefix check asks one thing: does the text start with /workspace/acme/tmp? stale.txt does, so it is allowed. /srv/shared/archive does not, so it is blocked. Both calls match the rules.',
      draw: () => cardMarkup() + boxMarkup(12, 'G', 'Prefix check', 'amber', 21, 0) + boxMarkup(196, 'R', 'The rules say', 'ink', 22, 0) + mapMarkup(0),
      start(s) {
        const a = REQ.remove_temp, b = REQ.outside_delete;
        setCard(s, a.operation, a.target, false);
        s.at(700, () => { const g = prefixLook(s, a.operation, a.target); verdict(s, 'G', g.ok, g.why); });
        s.at(1300, () => truth(s, true, 'delete inside tmp/'));
        s.at(1500, () => walk(s, hopsOf(a), 'violet', 'green', 1400));
        s.at(3900, () => { s.dyn.innerHTML = ''; ['op', 'p1', 'p2'].forEach(id => s.q('#' + id).setAttribute('fill', K.col('ink'))); s.q('#' + NID['/workspace/acme/tmp/stale.txt']).setAttribute('fill', K.col('ink')); setCard(s, b.operation, b.target); });
        s.at(4500, () => { const g = prefixLook(s, b.operation, b.target); verdict(s, 'G', g.ok, g.why); });
        s.at(5000, () => truth(s, false, 'outside the project'));
        s.at(5200, () => walk(s, hopsOf(b), 'violet', 'red', 1400));
      },
      duration: 7000 },

    { title: '3. Your guess', keys: ['req', 'prefix', 'bad'], ask: true,
      cap: "This path starts like an allowed one, then has ../../.. in it, and each .. means 'go up one folder'. Will the prefix check let this delete through? Pick an answer below.",
      draw: () => cardMarkup() + boxMarkup(12, 'G', 'Prefix check', 'amber', 21, 0) + boxMarkup(196, 'R', 'The rules say', 'ink', 22, 0) + mapMarkup(0),
      start(s) {
        const r = REQ.traversal; setCard(s, r.operation, r.target, false);
        s.q('#Gv').textContent = '?'; s.q('#Rv').textContent = '?';
        const answer = async said => {
          [...s.act.querySelectorAll('button')].forEach(b => b.remove());
          s.cap(ANSWER(said === (r.d[1] === 1)));
          const g = prefixLook(s, r.operation, r.target); verdict(s, 'G', g.ok, g.why);
          s.at(500, () => s.ring(12, 86, 172, 72, 'red'));
          s.at(900, () => truth(s, false, 'ends in /srv/shared'));
          await s.wait(1200);
          await walk(s, hopsOf(r), 'violet', 'red', 2600);
        };
        s.btn('check', 'Lets it through', () => answer(true), {primary: true});
        s.btn('', 'Blocks it', () => answer(false));
      },
      demo: async s => { await s.wait(1200); s.tap(s.act.querySelector('button')); await s.wait(4400); },
      demoDuration: 5800, duration: 1200 },

    { title: '4. Four more tricks', keys: ['req', 'prefix', 'bad'],
      cap: 'Each starts like an allowed path, so the prefix check allows all four. 1: tmp-other only begins with tmp. 2 and 3: a link leads out to /srv. 4: .env is a secret inside the project.',
      draw: () => cardMarkup() + boxMarkup(12, 'G', 'Prefix check', 'amber', 21, 0) + boxMarkup(196, 'R', 'The rules say', 'ink', 22, 0) + mapMarkup(0),
      start(s) {
        const list = TRICKS.slice(1), STEP = 3600;
        list.forEach((id, n) => {
          const r = REQ[id], t0 = n * STEP;
          s.at(t0, () => {
            s.dyn.querySelectorAll('.trail').forEach(e => e.remove());
            ['p1', 'p2'].forEach(k => s.q('#' + k).setAttribute('fill', K.col('ink')));
            setCard(s, r.operation, r.target, n > 0);
          });
          s.at(t0 + 500, () => { const g = prefixLook(s, r.operation, r.target); verdict(s, 'G', g.ok, g.why); });
          s.at(t0 + 800, () => truth(s, false, TRICK_WHY[id]));
          s.at(t0 + 900, async () => {
            const before = new Set(s.dyn.children);
            const last = await walk(s, hopsOf(r), 'violet', 'red', 1700);
            [...s.dyn.children].forEach(e => { if (!before.has(e) && e.tagName === 'path') e.classList.add('trail'); });
            const end = resolvedEnd(r);
            offMap(s, last, end, 'red');
            badge(s, last, n + 1, end !== last ? 52 : 0);
          });
        });
      },
      duration: 4 * 3600 + 400 },

    { title: '5. Walk first, then check', keys: ['req', 'prefix', 'scoped', 'bad'],
      cap: 'The scoped gate (blue) walks the path itself, following every .. and link, then checks where it really ends: inside the project, in the right folder, not a secret name. This delete ends in /srv: blocked.',
      draw: () => cardMarkup() + boxMarkup(12, 'G', 'Prefix check', 'amber', 21, 0) + boxMarkup(196, 'S', 'Scoped gate', 'blue', 23, 300) + mapMarkup(0),
      start(s) {
        const r = REQ.traversal; setCard(s, r.operation, r.target, false);
        s.at(400, () => { const g = prefixLook(s, r.operation, r.target); verdict(s, 'G', g.ok, g.why); });
        s.at(900, () => { s.q('#Sv').textContent = 'walking…'; s.q('#Sv').setAttribute('fill', K.col('mut')); });
        s.at(1200, async () => {
          await walk(s, hopsOf(r), 'blue', 'red', 2800);
          const g = scopedGate(r.operation, r.target); verdict(s, 'S', g.ok, g.why);
          s.ring(196, 86, 172, 72, 'blue');
        });
      },
      duration: 4800 },

    { title: '6. Your turn: test a path', keys: ['req', 'prefix', 'scoped', 'good', 'bad'],
      cap: 'Pick an action, type any path and press Check: both gates judge it. Try adding ../ or a name like payroll. Deletes count as approved here. Example steps through the test requests.',
      draw: () => cardMarkup() + boxMarkup(12, 'G', 'Prefix check', 'amber', 21, 0) + boxMarkup(196, 'S', 'Scoped gate', 'blue', 23, 0) + mapMarkup(0),
      start(s) {
        const wrap = document.createElement('div');
        wrap.className = 'try';
        wrap.innerHTML = '<select aria-label="Action"><option>read</option><option>write</option><option selected>delete</option></select>' +
          '<input type="text" aria-label="Path to test" spellcheck="false" autocapitalize="off" autocomplete="off">';
        s.act.appendChild(wrap);
        const sel = wrap.querySelector('select'), inp = wrap.querySelector('input');
        let token = 0, ex = 0;
        const check = async () => {
          const me = ++token, op = sel.value, path = (inp.value || '').trim() || '/';
          s.dyn.innerHTML = '';
          Object.keys(NODES).forEach(p => { s.q('#' + NID[p]).setAttribute('fill', K.col('ink')); const a = s.q('#a_' + NID[p]); if (a) a.style.opacity = 1; });
          setCard(s, op, path, false);
          const g = prefixLook(s, op, path); verdict(s, 'G', g.ok, g.why);
          const sc = scopedGate(op, path);
          s.q('#Sv').textContent = 'walking…'; s.q('#Sv').setAttribute('fill', K.col('mut')); s.q('#Sr').textContent = '';
          const last = await walk(s, sc.hops, 'blue', sc.ok ? 'green' : 'red', 1800);
          if (me !== token) return;
          offMap(s, last, sc.end, sc.ok ? 'green' : 'red');
          verdict(s, 'S', sc.ok, sc.why);
        };
        const example = () => { const r = REQ[EXAMPLES[ex++ % EXAMPLES.length]]; sel.value = r.operation; inp.value = r.target; check(); };
        inp.addEventListener('keydown', e => { if (e.key === 'Enter') { s.touched(); check(); } });
        inp.addEventListener('input', () => s.touched()); sel.addEventListener('change', () => s.touched());
        s.btn('check', 'Check', check, {primary: true});
        s.btn('right', 'Example', example);
        sel.value = 'delete'; inp.value = '/workspace/acme/tmp/../src/main.py'; check();
      },
      demo: async s => {
        const inp = s.act.querySelector('input'), sel = s.act.querySelector('select');
        sel.value = 'read'; inp.value = '';
        const txt = '/workspace/acme/output/../.env';
        for (let i = 1; i <= txt.length; i += 3) { inp.value = txt.slice(0, i); await s.wait(45); }
        inp.value = txt; await s.wait(300);
        s.tap(s.act.querySelectorAll('button')[0]); await s.wait(3600);
      },
      idleDemo: 7000, demoDuration: 5200, duration: 3000 },

    { title: '7. All 22 test requests', keys: ['bad', 'good'],
      cap: 'Each square is one request. The prefix check let 5 of 14 forbidden ones through, every one built to fool a text check. The three scoped gates let none through; read-only also blocked 4 of 8 permitted jobs.',
      draw: () => {
        const NAME = ['Observe only', 'Prefix check', 'Scoped gate', 'Scoped, read-only', 'Scoped + approval'];
        const DESC = ['logs, then allows all', 'reads how the path starts', 'walks the path, then checks', 'write and delete removed', 'approval tied to exact file'];
        const NC = ['ink', 'amber', 'blue', 'blue', 'blue'];
        let m = T(14, 26, `${COUNTS[0].fn} forbidden requests`, {z: 14, a: 'start', w: 600}) + T(226, 26, `${COUNTS[0].pn} permitted`, {z: 14, a: 'start', w: 600}) +
          T(14, 44, 'red = let through', {z: 13, a: 'start', c: 'red'}) + T(226, 44, 'green = allowed', {z: 13, a: 'start', c: 'green'});
        COUNTS.forEach((c, gi) => {
          const y = 76 + gi * 52, t = 300 + gi * 350;
          m += T(14, y, NAME[gi], {z: 15, w: 600, a: 'start', c: NC[gi], t}) + T(368, y, DESC[gi], {z: 13, a: 'end', c: 'mut', t});
          for (let j = 0; j < c.fn; j++) m += F(`M${14 + j * 12} ${y + 9}h10v10h-10z`, j < c.fa ? 'fill.red' : 'faint', t + 150 + j * 25, {op: j < c.fa ? 1 : .35});
          for (let j = 0; j < c.pn; j++) m += F(`M${226 + j * 12} ${y + 9}h10v10h-10z`, j < c.pa ? 'fill.green' : 'faint', t + 150 + j * 25, {op: j < c.pa ? 1 : .35});
          m += T(186, y + 19, `${c.fa}/${c.fn}`, {z: 13, a: 'start', c: c.fa ? 'red' : 'mut', t: t + 500, w: 600});
          m += T(326, y + 19, `${c.pa}/${c.pn}`, {z: 13, a: 'start', c: c.pa === c.pn ? 'green' : 'amber', t: t + 500, w: 600});
        });
        m += T(14, 344, 'Scoped + approval made the same 22 calls as Scoped:', {z: 13, a: 'start', c: 'mut', t: 2400});
        m += T(14, 362, 'no test reused an approval, so this test cannot split them.', {z: 13, a: 'start', c: 'mut', t: 2500});
        return m;
      },
      start(s) { s.at(2000, () => s.ring(8, 76 + 52 - 18, 364, 44, 'amber')); },
      duration: 3600 },

    { title: '8. What to take away', keys: ['scoped', 'bad'],
      cap: 'Judge where a path ends, not how it is spelled. The counts show which known tricks each design catches, not how often real attacks succeed.',
      draw: () => {
        const card = (y, n, head, lines, seed, t) => P(rect(12, y, 356, 76, seed), 'blue', t, 600) +
          T(26, y + 25, n + '. ' + head, {h: 1, z: 21, a: 'start', c: 'blue', t: t + 200}) +
          lines.map((l, i) => T(26, y + 46 + i * 17, l, {z: 13.5, a: 'start', t: t + 350 + i * 100})).join('');
        const noCap = DATA.requests.filter(r => !['read', 'write', 'delete'].includes(r.operation)).length, broker = DATA.broker_audit, reused = broker.filter(b => b.operation === 'delete' && b.status === 'denied').length;
        return card(10, 1, 'Check where a path really ends', ['Follow every .. and link before deciding.', `The prefix check missed all ${TRICKS.length} such tricks.`], 31, 0) +
          card(94, 2, 'Offer only the actions needed', ['Read, write, delete. No shell, Python,', `PowerShell or network: all ${noCap} such requests refused.`], 32, 500) +
          card(178, 3, 'Tie each approval to one file', ['In a real-folder demo, both tries to reuse', `an approval were refused (${reused} of ${reused}).`], 33, 1000) +
          P(rect(12, 264, 356, 104, 34), 'faint', 1500, 600, 1.2, 'stroke-dasharray="4 4"') +
          T(26, 286, 'Limits of this test', {h: 1, z: 20, a: 'start', c: 'mut', t: 1700}) +
          ['22 hand-written requests, one fixed run, no AI model.', 'Gate and requests share the same rules, so 0 of 14', 'is a ceiling by design. Not tested: hard links, or a', 'link swapped between the check and the use.']
            .map((l, i) => T(26, 306 + i * 17, l, {z: 13, a: 'start', c: 'mut', t: 1850 + i * 100})).join('');
      },
      duration: 2800 },
  ],
});
