"use strict";

// Log scan: status-class counts and latency percentiles of the busiest path templates (see SPEC.md).
//
// The file is streamed in 1 MiB chunks with fs.readSync. Each line is checked by a hand-written matcher
// that accepts exactly the language of the SPEC regex, working on the bytes of the chunk. Path templates
// are interned in a Map keyed by string. Only the ten busiest templates have their latencies sorted.
// Latencies are kept as numbers, which are exact up to 2^53 tenths of a millisecond.

const fs = require("fs");

const CHUNK_SIZE = 1 << 20;
const TOP_N = 10;

const CH_DASH = 45; // -
const CH_SLASH = 47; // /
const CH_0 = 48; // 0
const CH_QUESTION = 63; // ?
const CH_B = 66; // B
const CH_A = 65; // A
const CH_Z = 90; // Z
const CH_QUOTE = 34; // "
const CH_SPACE = 32;
const CH_DOT = 46; // .
const CH_NEWLINE = 10;
const CH_UNDERSCORE = 95; // _
const CH_D = 100; // d, a digit position in the timestamp pattern
const CH_M = 109; // m
const CH_S = 115; // s
const CH_LOWER_A = 97; // a
const CH_LOWER_Z = 122; // z

// Characters allowed in the path group: [A-Za-z0-9_/-], indexed by byte value.
const PATH_CHAR = new Uint8Array(256);
for (let c = 0; c < 256; c++) {
  const ok =
    (c >= CH_LOWER_A && c <= CH_LOWER_Z) ||
    (c >= CH_A && c <= CH_Z) ||
    (c >= CH_0 && c <= CH_0 + 9) ||
    c === CH_UNDERSCORE ||
    c === CH_SLASH ||
    c === CH_DASH;
  PATH_CHAR[c] = ok ? 1 : 0;
}

const TIMESTAMP = Buffer.from("dddd-dd-ddTdd:dd:dd.dddZ", "latin1");
const METHOD_GET = Buffer.from("GET ", "latin1");
const METHOD_POST = Buffer.from("POST ", "latin1");
const METHOD_PUT = Buffer.from("PUT ", "latin1");
const METHOD_DELETE = Buffer.from("DELETE ", "latin1");
const METHOD_PATCH = Buffer.from("PATCH ", "latin1");

let total = 0;
let malformed = 0;
const statusCount = new Array(10).fill(0);
const templates = new Map(); // template string -> { name, count, latencies }

// Results of parseLine for the line that matched. Path offsets are indices into the chunk.
let lineStatus = 0;
let lineTenths = 0;
let linePathStart = 0;
let linePathEnd = 0;

// Scratch buffer for the template of the current line.
let tmpl = Buffer.allocUnsafe(1024);
let tmplLen = 0;

function isDigit(c) {
  return c >= CH_0 && c <= CH_0 + 9;
}

function isLower(c) {
  return c >= CH_LOWER_A && c <= CH_LOWER_Z;
}

// True if b[q, e) starts with lit.
function matchAt(b, q, e, lit) {
  if (e - q < lit.length) return false;
  for (let i = 0; i < lit.length; i++) {
    if (b[q + i] !== lit[i]) return false;
  }
  return true;
}

// Matches one line b[p, e) (without its '\n') against the SPEC regex. Returns false if malformed.
function parseLine(b, p, e) {
  if (e - p < 25) return false;
  for (let i = 0; i < 24; i++) {
    const c = TIMESTAMP[i];
    if (c === CH_D ? !isDigit(b[p + i]) : b[p + i] !== c) return false;
  }
  if (b[p + 24] !== CH_SPACE) return false;

  // Host: [a-z]+-\d+ followed by a space.
  let q = p + 25;
  let s = q;
  while (q < e && isLower(b[q])) q++;
  if (q === s || q === e || b[q] !== CH_DASH) return false;
  q++;
  s = q;
  while (q < e && isDigit(b[q])) q++;
  if (q === s || q === e || b[q] !== CH_SPACE) return false;
  q++;

  // Method, then a space.
  if (matchAt(b, q, e, METHOD_GET)) q += 4;
  else if (matchAt(b, q, e, METHOD_POST)) q += 5;
  else if (matchAt(b, q, e, METHOD_PUT)) q += 4;
  else if (matchAt(b, q, e, METHOD_DELETE)) q += 7;
  else if (matchAt(b, q, e, METHOD_PATCH)) q += 6;
  else return false;

  // Path: '/' and path characters, then an optional query running to the next space.
  if (q === e || b[q] !== CH_SLASH) return false;
  linePathStart = q;
  q++;
  while (q < e && PATH_CHAR[b[q]] === 1) q++;
  linePathEnd = q;
  if (q < e && b[q] === CH_QUESTION) {
    while (q < e && b[q] !== CH_SPACE) q++;
  }
  if (q === e || b[q] !== CH_SPACE) return false;
  q++;

  // Status: three digits, then a space.
  if (e - q < 4 || !isDigit(b[q]) || !isDigit(b[q + 1]) || !isDigit(b[q + 2]) || b[q + 3] !== CH_SPACE) {
    return false;
  }
  lineStatus = b[q] - CH_0;
  q += 4;

  // Size: \d+B followed by a space.
  s = q;
  while (q < e && isDigit(b[q])) q++;
  if (q === s || q === e || b[q] !== CH_B) return false;
  q++;
  if (q === e || b[q] !== CH_SPACE) return false;
  q++;

  // Latency: \d+ '.' \d 'ms' followed by a space, kept in tenths of a millisecond.
  s = q;
  let whole = 0;
  while (q < e && isDigit(b[q])) {
    whole = whole * 10 + (b[q] - CH_0);
    q++;
  }
  if (q === s || q === e || b[q] !== CH_DOT) return false;
  q++;
  if (q === e || !isDigit(b[q])) return false;
  const frac = b[q] - CH_0;
  q++;
  if (e - q < 3 || b[q] !== CH_M || b[q + 1] !== CH_S || b[q + 2] !== CH_SPACE) return false;
  q += 3;
  lineTenths = whole * 10 + frac;

  // User agent: "[^"]*" which must end the line.
  if (e - q < 2 || b[q] !== CH_QUOTE || b[e - 1] !== CH_QUOTE) return false;
  for (let u = q + 1; u < e - 1; u++) {
    if (b[u] === CH_QUOTE) return false;
  }
  return true;
}

// Path template: each non-empty all-digit segment becomes {id}. Writes into tmpl.
function buildTemplate(b, start, end) {
  const len = end - start;
  if (tmpl.length < 4 * len + 4) tmpl = Buffer.allocUnsafe(4 * len + 4);
  const out = tmpl;
  let n = 0;
  let s = start;
  for (;;) {
    let e = s;
    let digits = true;
    while (e < end && b[e] !== CH_SLASH) {
      if (!isDigit(b[e])) digits = false;
      e++;
    }
    if (e > s && digits) {
      out[n++] = 123; // {
      out[n++] = 105; // i
      out[n++] = 100; // d
      out[n++] = 125; // }
    } else {
      for (let i = s; i < e; i++) out[n++] = b[i];
    }
    if (e === end) break;
    out[n++] = CH_SLASH;
    s = e + 1;
  }
  tmplLen = n;
}

function addLine(b, p, e) {
  total++;
  if (!parseLine(b, p, e)) {
    malformed++;
    return;
  }
  statusCount[lineStatus]++;
  buildTemplate(b, linePathStart, linePathEnd);
  const key = tmpl.toString("latin1", 0, tmplLen);
  let t = templates.get(key);
  if (t === undefined) {
    t = { name: key, count: 0, latencies: [] };
    templates.set(key, t);
  }
  t.count++;
  t.latencies.push(lineTenths);
}

// Orders templates by count descending, then name ascending (names are ASCII, so this is byte order).
function better(a, b) {
  if (a.count !== b.count) return a.count > b.count;
  return a.name < b.name;
}

function formatTenths(t) {
  return `${Math.floor(t / 10)}.${t % 10}`;
}

function report() {
  const out = [`lines ${total}`, `malformed ${malformed}`];
  for (let c = 0; c < 10; c++) {
    if (statusCount[c] !== 0) out.push(`status ${c}xx ${statusCount[c]}`);
  }

  // Keep the TOP_N busiest templates, best first, by insertion into a small sorted array.
  const top = [];
  for (const t of templates.values()) {
    if (top.length === TOP_N) {
      if (!better(t, top[TOP_N - 1])) continue;
      top[TOP_N - 1] = t;
    } else {
      top.push(t);
    }
    for (let k = top.length - 1; k > 0 && better(top[k], top[k - 1]); k--) {
      const x = top[k];
      top[k] = top[k - 1];
      top[k - 1] = x;
    }
  }

  for (const t of top) {
    const lat = Float64Array.from(t.latencies).sort(); // typed-array sort is numeric
    const n = lat.length;
    const p50 = lat[Math.floor((50 * n + 99) / 100) - 1];
    const p95 = lat[Math.floor((95 * n + 99) / 100) - 1];
    const max = lat[n - 1];
    out.push(`path ${t.name} ${t.count} ${formatTenths(p50)} ${formatTenths(p95)} ${formatTenths(max)}`);
  }
  return out.join("\n") + "\n";
}

function main() {
  const inputPath = process.argv[2];
  if (!inputPath) {
    console.error("usage: node main.js INPUT_PATH");
    process.exitCode = 2;
    return;
  }

  const fd = fs.openSync(inputPath, "r");
  let buf = Buffer.allocUnsafe(CHUNK_SIZE);
  let start = 0; // first byte of the unprocessed data
  let end = 0; // one past the last byte read
  let eof = false;
  try {
    for (;;) {
      // indexOf may find a newline in stale bytes past `end`; such a match is not a line here.
      const nl = buf.indexOf(CH_NEWLINE, start);
      if (nl >= 0 && nl < end) {
        addLine(buf, start, nl);
        start = nl + 1;
        continue;
      }
      if (eof) {
        if (start < end) addLine(buf, start, end); // last line without '\n'
        break;
      }
      // No complete line in the buffer: move the partial line to the front and read more.
      if (start > 0) {
        buf.copy(buf, 0, start, end);
        end -= start;
        start = 0;
      }
      if (end === buf.length) {
        // one line longer than the buffer
        const grown = Buffer.allocUnsafe(buf.length * 2);
        buf.copy(grown, 0, 0, end);
        buf = grown;
      }
      const n = fs.readSync(fd, buf, end, buf.length - end, null);
      if (n === 0) eof = true;
      else end += n;
    }
  } finally {
    fs.closeSync(fd);
  }

  process.stdout.write(report());
}

main();
