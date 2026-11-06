"use strict";

const fs = require("fs");

function main() {
  const buf = fs.readFileSync(process.argv[2]);
  const len = buf.length;
  let pos = 0;

  const isWs = (b) => b === 32 || b === 10 || b === 13 || b === 9 || b === 11 || b === 12;

  function token() {
    while (pos < len && isWs(buf[pos])) pos++;
    const start = pos;
    while (pos < len && !isWs(buf[pos])) pos++;
    return [start, pos];
  }

  function nextInt() {
    while (pos < len && isWs(buf[pos])) pos++;
    let v = 0;
    while (pos < len && !isWs(buf[pos])) {
      v = v * 10 + (buf[pos] - 48);
      pos++;
    }
    return v;
  }

  // Alphabet token
  let tok = token();
  const a = tok[1] - tok[0];
  const charId = new Int16Array(128).fill(-1);
  for (let i = 0; i < a; i++) charId[buf[tok[0] + i]] = i;

  const ins = new Int32Array(a);
  const del = new Int32Array(a);
  const sub = new Int32Array(a * a);
  for (let i = 0; i < a; i++) ins[i] = nextInt();
  for (let i = 0; i < a; i++) del[i] = nextInt();
  for (let i = 0; i < a * a; i++) sub[i] = nextInt();
  const p = nextInt();

  const sIds = new Int32Array(1100);
  const tIds = new Int32Array(1100);
  const rowA = new Int32Array(1101);
  const rowB = new Int32Array(1101);
  const outParts = new Array(p + 1);
  let total = 0;

  let curIdx = 0;
  const rows = [rowA, rowB];

  const solve = (n, m) => {
    // rows, tIds, ins, del, sub, a are captured from the enclosing scope
    let prev = rows[curIdx];
    let cur = rows[1 - curIdx];
    prev[0] = 0;
    for (let j = 1; j <= m; j++) prev[j] = prev[j - 1] + ins[tIds[j - 1]];
    for (let i = 0; i < n; i++) {
      const si = sIds[i];
      const dc = del[si];
      const subBase = si * a;
      let left = prev[0] + dc;
      cur[0] = left;
      let diag = prev[0];
      for (let j = 1; j <= m; j++) {
        const tj = tIds[j - 1];
        let best = prev[j] + dc;
        const l = left + ins[tj];
        const d = diag + sub[subBase + tj];
        if (l < best) best = l;
        if (d < best) best = d;
        cur[j] = best;
        left = best;
        diag = prev[j];
      }
      const tmp = prev;
      prev = cur;
      cur = tmp;
    }
    return prev[m];
  };

  for (let q = 0; q < p; q++) {
    tok = token();
    const n = tok[1] - tok[0];
    for (let i = 0; i < n; i++) sIds[i] = charId[buf[tok[0] + i]];
    tok = token();
    const m = tok[1] - tok[0];
    for (let j = 0; j < m; j++) tIds[j] = charId[buf[tok[0] + j]];
    const cost = solve(n, m);
    total += cost;
    outParts[q] = cost;
  }
  outParts[p] = "total " + total;
  process.stdout.write(outParts.join("\n") + "\n");
}

main();
