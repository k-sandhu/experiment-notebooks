'use strict';

// Summarise a web server access log (see SPEC.md).
// Node 22, built-in modules only. Single pass over the input: validate every
// line against the grammar, count status classes, group latency tenths by
// path template, then report the top 10.

const fs = require('fs');

const data = fs.readFileSync(process.argv[2]);
const n = data.length;

class Stats {
  constructor() {
    this.count = 0;
    this.lat = [];
  }
}

// Open-addressing-free aggregation: Map keyed by interned template strings.
// (JS has no transparent lookup over raw buffers, so the template string is
// built once per valid line and used for the Map hit/insert.)
const map = new Map();

let nLines = 0;
let nMalformed = 0;
const statusCount = new Uint32Array(10);

function isDig(c) {
  return c >= 48 && c <= 57;
}

function pathChar(c) {
  return (c >= 65 && c <= 90) || (c >= 97 && c <= 122) || isDig(c) ||
    c === 0x5f || c === 0x2f || c === 0x2d; // _ / -
}

// Validates one line (bytes [start, end), newline excluded) against the
// SPEC.md grammar. Fills res and returns true on success.
function parseLine(start, end, res) {
  if (end - start < 49) return false; // shortest possible well-formed line

  // timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<sp>
  if (data[start + 4] !== 0x2d || data[start + 7] !== 0x2d ||
      data[start + 10] !== 0x54 || data[start + 13] !== 0x3a ||
      data[start + 16] !== 0x3a || data[start + 19] !== 0x2e ||
      data[start + 23] !== 0x5a || data[start + 24] !== 0x20)
    return false;
  for (const off of [0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22]) {
    if (!isDig(data[start + off])) return false;
  }

  // host: [a-z]+-\d+<sp>
  let h = start + 25;
  if (h >= end || data[h] < 0x61 || data[h] > 0x7a) return false;
  do { ++h; } while (h < end && data[h] >= 0x61 && data[h] <= 0x7a);
  if (h >= end || data[h] !== 0x2d) return false;
  ++h;
  if (h >= end || !isDig(data[h])) return false;
  do { ++h; } while (h < end && isDig(data[h]));
  if (h >= end || data[h] !== 0x20) return false;
  ++h; // method

  let mlen = 0;
  const rem = end - h;
  if (rem >= 3 && data[h] === 0x47 && data[h + 1] === 0x45 && data[h + 2] === 0x54) mlen = 3; // GET
  else if (rem >= 3 && data[h] === 0x50 && data[h + 1] === 0x55 && data[h + 2] === 0x54) mlen = 3; // PUT
  else if (rem >= 4 && data[h] === 0x50 && data[h + 1] === 0x4f && data[h + 2] === 0x53 && data[h + 3] === 0x54) mlen = 4; // POST
  else if (rem >= 6 && data[h] === 0x44 && data[h + 1] === 0x45 && data[h + 2] === 0x4c && data[h + 3] === 0x45 && data[h + 4] === 0x54 && data[h + 5] === 0x45) mlen = 6; // DELETE
  else if (rem >= 5 && data[h] === 0x50 && data[h + 1] === 0x41 && data[h + 2] === 0x54 && data[h + 3] === 0x43 && data[h + 4] === 0x48) mlen = 5; // PATCH
  if (mlen === 0) return false;
  h += mlen;
  if (h >= end || data[h] !== 0x20) return false;
  ++h;

  // path: /[A-Za-z0-9_/-]* then optional \?[^ ]* then <sp>
  if (h >= end || data[h] !== 0x2f) return false;
  const pathStart = h;
  ++h;
  while (h < end) {
    const c = data[h];
    if (c === 0x20 || c === 0x3f) break; // space or ?
    if (!pathChar(c)) return false;
    ++h;
  }
  const pathEnd = h;
  if (h < end && data[h] === 0x3f) { // ?
    ++h;
    while (h < end && data[h] !== 0x20) ++h;
  }
  if (h >= end || data[h] !== 0x20) return false;
  ++h;

  // status: \d{3}<sp>
  if (end - h < 3 || !isDig(data[h]) || !isDig(data[h + 1]) || !isDig(data[h + 2])) return false;
  res[0] = data[h] - 48;
  h += 3;
  if (h >= end || data[h] !== 0x20) return false;
  ++h;

  // size: \d+B<sp>
  if (h >= end || !isDig(data[h])) return false;
  do { ++h; } while (h < end && isDig(data[h]));
  if (h >= end || data[h] !== 0x42) return false; // B
  ++h;
  if (h >= end || data[h] !== 0x20) return false;
  ++h;

  // latency: \d+.\dms "<ua>"<end>
  let lat = 0;
  if (h >= end || !isDig(data[h])) return false;
  do { lat = lat * 10 + (data[h] - 48); ++h; } while (h < end && isDig(data[h]));
  if (h >= end || data[h] !== 0x2e) return false;
  ++h;
  if (h >= end || !isDig(data[h])) return false;
  lat = lat * 10 + (data[h] - 48);
  ++h;
  if (end - h < 4 || data[h] !== 0x6d || data[h + 1] !== 0x73 || data[h + 2] !== 0x20 || data[h + 3] !== 0x22) return false;
  h += 4;
  while (h < end && data[h] !== 0x22) ++h;
  if (h >= end || data[h] !== 0x22) return false;
  ++h;
  if (h !== end) return false;

  res[1] = lat;
  res[2] = pathStart;
  res[3] = pathEnd;
  return true;
}

// Build path template from bytes [pathStart, pathEnd): split on '/',
// replace all-digit non-empty segments with {id}, rejoin with '/' (slashes
// between segments are preserved, including a trailing one).
function template(pathStart, pathEnd) {
  let out = '/';
  let segStart = pathStart + 1;
  let i = segStart;
  while (true) {
    if (i === pathEnd || data[i] === 0x2f) {
      const seglen = i - segStart;
      if (seglen > 0) {
        let allDig = true;
        for (let j = segStart; j < i; j++) {
          if (!isDig(data[j])) { allDig = false; break; }
        }
        out += allDig ? '{id}' : data.toString('ascii', segStart, i);
      }
      if (i < pathEnd) out += '/';
      segStart = i + 1;
    }
    if (i === pathEnd) break;
    ++i;
  }
  return out;
}

const res = new Int32Array(4);
let p = 0;
while (p < n) {
  ++nLines;
  const lineStart = p;
  let e = p;
  while (e < n && data[e] !== 0x0a) ++e; // newline
  if (parseLine(lineStart, e, res)) {
    statusCount[res[0]]++;
    const tmpl = template(res[2], res[3]);
    const st = map.get(tmpl);
    if (st === undefined) {
      const ns = new Stats();
      ns.count = 1;
      ns.lat.push(res[1]);
      map.set(tmpl, ns);
    } else {
      st.count++;
      st.lat.push(res[1]);
    }
  } else {
    nMalformed++;
  }
  p = e + 1;
}

const items = [];
map.forEach((st, name) => items.push({ name, st }));
items.sort((a, b) => {
  if (b.st.count !== a.st.count) return b.st.count - a.st.count;
  return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; // byte order
});

const out = [];
out.push('lines ' + nLines);
out.push('malformed ' + nMalformed);
for (let c = 0; c < 10; c++) {
  if (statusCount[c] !== 0) {
    out.push('status ' + String.fromCharCode(0x30 + c) + 'xx ' + statusCount[c]);
  }
}
const top = items.length < 10 ? items.length : 10;
for (let i = 0; i < top; i++) {
  const st = items[i].st;
  const lat = st.lat.slice(0).sort((a, b) => a - b);
  const nn = lat.length;
  const kth = (pct) => lat[((pct * nn + 99) / 100 | 0) - 1];
  const fmt = (t) => Math.floor(t / 10) + '.' + (t % 10);
  out.push('path ' + items[i].name + ' ' + st.count +
    ' ' + fmt(kth(50)) + ' ' + fmt(kth(95)) + ' ' + fmt(lat[nn - 1]));
}

process.stdout.write(out.join('\n') + '\n');
