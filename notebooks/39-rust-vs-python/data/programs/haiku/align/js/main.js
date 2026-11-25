"use strict";

// Weighted alignment cost (see SPEC.md).
//
// The input file is read as one Buffer and parsed in place; tokens are ranges of that buffer.
// The DP keeps one row of costs, updated in place, with the diagonal and left values held in
// locals. Scratch arrays are reused across pairs and only grow.
//
// Costs are at most (n + m) * 1000, and n + m is at most the file length. When that bound fits
// in int32 (any input of about 2 MB or less), the row uses Int32Array and the minimum is
// branch-free; this is about twice as fast in V8. Larger inputs use Float64Array, which is exact
// up to 2^53, with ordinary comparisons.

const fs = require("fs");

const data = fs.readFileSync(process.argv[2]);
const useInt32 = (data.length + 2) * 1000 < 2 ** 31;
let pos = 0;
let tokStart = 0;
let tokEnd = 0;

// Skips whitespace; sets tokStart and tokEnd to the next token's range.
function nextToken() {
  let p = pos;
  while (p < data.length && data[p] <= 32) p++;
  tokStart = p;
  while (p < data.length && data[p] > 32) p++;
  tokEnd = p;
  pos = p;
}

function nextNumber() {
  nextToken();
  let v = 0;
  for (let k = tokStart; k < tokEnd; k++) v = v * 10 + (data[k] - 48);
  return v;
}

// Cost of the pair: s[1..n] are rows (deletions), t[1..m] are columns (insertions).
// tIns[j] = ins[t[j]]. row must hold m + 1 values.
function alignCostInt32(s, n, t, m, tIns, del, sub, a, row) {
  row[0] = 0;
  for (let j = 1; j <= m; j++) row[j] = row[j - 1] + tIns[j];

  for (let i = 1; i <= n; i++) {
    const si = s[i];
    const d = del[si];
    const base = si * a;

    let diag = row[0];
    row[0] += d;
    let left = row[0];
    for (let j = 1; j <= m; j++) {
      const up = row[j];
      const fromUp = up + d;
      const fromDiag = diag + sub[base + t[j]];
      // Branch-free min(fromUp, fromDiag); valid because the differences fit in int32.
      let diff = fromUp - fromDiag;
      const low = fromDiag + (diff & (diff >> 31));
      // left is the only term that depends on the previous cell, so it goes last.
      const fromLeft = left + tIns[j];
      diff = low - fromLeft;
      const v = fromLeft + (diff & (diff >> 31));
      row[j] = v;
      left = v;
      diag = up;
    }
  }
  return row[m];
}

function alignCostWide(s, n, t, m, tIns, del, sub, a, row) {
  row[0] = 0;
  for (let j = 1; j <= m; j++) row[j] = row[j - 1] + tIns[j];

  for (let i = 1; i <= n; i++) {
    const si = s[i];
    const d = del[si];
    const base = si * a;

    let diag = row[0];
    row[0] += d;
    let left = row[0];
    for (let j = 1; j <= m; j++) {
      const up = row[j];
      const fromUp = up + d;
      const fromDiag = diag + sub[base + t[j]];
      let v = fromUp < fromDiag ? fromUp : fromDiag;
      const fromLeft = left + tIns[j];
      v = v < fromLeft ? v : fromLeft;
      row[j] = v;
      left = v;
      diag = up;
    }
  }
  return row[m];
}

function main() {
  if (process.argv.length < 3) {
    process.stderr.write("usage: node main.js INPUT_PATH\n");
    process.exitCode = 1;
    return;
  }

  const Num = useInt32 ? Int32Array : Float64Array;
  const alignCost = useInt32 ? alignCostInt32 : alignCostWide;

  nextToken();
  const a = tokEnd - tokStart;
  const code = new Int32Array(256);
  for (let i = 0; i < a; i++) code[data[tokStart + i]] = i;

  const ins = new Num(a);
  const del = new Num(a);
  const sub = new Num(a * a);
  for (let i = 0; i < a; i++) ins[i] = nextNumber();
  for (let i = 0; i < a; i++) del[i] = nextNumber();
  for (let i = 0; i < a * a; i++) sub[i] = nextNumber();

  const pairs = nextNumber();

  let s = new Int32Array(1);
  let t = new Int32Array(1);
  let tIns = new Num(1);
  let row = new Num(1);
  const lines = [];
  let total = 0;

  for (let p = 0; p < pairs; p++) {
    nextToken();
    const sStart = tokStart;
    const n = tokEnd - sStart;
    nextToken();
    const tStart = tokStart;
    const m = tokEnd - tStart;

    if (s.length < n + 1) s = new Int32Array(n + 1);
    if (t.length < m + 1) {
      t = new Int32Array(m + 1);
      tIns = new Num(m + 1);
      row = new Num(m + 1);
    }
    for (let i = 1; i <= n; i++) s[i] = code[data[sStart + i - 1]];
    for (let j = 1; j <= m; j++) {
      t[j] = code[data[tStart + j - 1]];
      tIns[j] = ins[t[j]];
    }

    const cost = alignCost(s, n, t, m, tIns, del, sub, a, row);
    total += cost;
    lines.push(String(cost));
  }

  lines.push(`total ${total}`);
  process.stdout.write(lines.join("\n") + "\n");
}

main();
