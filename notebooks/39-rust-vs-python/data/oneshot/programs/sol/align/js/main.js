'use strict';

const fs = require('fs');
const input = fs.readFileSync(process.argv[2]);
let pos = 0;

while (input[pos] > 32) pos++;
const A = pos;

const letterId = new Uint8Array(256);
for (let i = 0; i < A; i++) {
  letterId[input[i]] = i;
}

function nextInt() {
  while (input[pos] <= 32) pos++;
  let value = 0;
  let c;
  while ((c = input[pos]) >= 48 && c <= 57) {
    value = value * 10 + c - 48;
    pos++;
  }
  return value;
}

const insertion = new Uint16Array(A);
const deletion = new Uint16Array(A);

for (let i = 0; i < A; i++) insertion[i] = nextInt();
for (let i = 0; i < A; i++) deletion[i] = nextInt();

const substitution = new Array(A);
const transposed = new Array(A);
for (let i = 0; i < A; i++) {
  substitution[i] = new Uint16Array(A);
  transposed[i] = new Uint16Array(A);
}

for (let i = 0; i < A; i++) {
  for (let j = 0; j < A; j++) {
    const cost = nextInt();
    substitution[i][j] = cost;
    transposed[j][i] = cost;
  }
}

const P = nextInt();
const output = new Array(P + 1);
let total = 0n;

for (let pair = 0; pair < P; pair++) {
  while (input[pos] <= 32) pos++;
  const sStart = pos;
  while (input[pos] > 32) pos++;
  const sLength = pos - sStart;

  while (input[pos] <= 32) pos++;
  const tStart = pos;
  while (input[pos] > 32) pos++;
  const tLength = pos - tStart;

  if (sLength === tLength) {
    let k = 0;
    while (k < sLength && input[sStart + k] === input[tStart + k]) k++;
    if (k === sLength) {
      output[pair] = '0';
      continue;
    }
  }

  let rowStart, columnStart, n, m, del, ins, sub;
  if (tLength <= sLength) {
    rowStart = sStart;
    columnStart = tStart;
    n = sLength;
    m = tLength;
    del = deletion;
    ins = insertion;
    sub = substitution;
  } else {
    rowStart = tStart;
    columnStart = sStart;
    n = tLength;
    m = sLength;
    del = insertion;
    ins = deletion;
    sub = transposed;
  }

  const columns = new Uint8Array(m);
  const insertCosts = new Uint16Array(m);
  const dp = new Float64Array(m + 1);

  let initial = 0;
  for (let j = 0; j < m; j++) {
    const id = letterId[input[columnStart + j]];
    columns[j] = id;
    const cost = ins[id];
    insertCosts[j] = cost;
    initial += cost;
    dp[j + 1] = initial;
  }

  const cachedRows = new Array(A);

  for (let i = 0; i < n; i++) {
    const id = letterId[input[rowStart + i]];
    const deleteCost = del[id];

    let costs = cachedRows[id];
    if (costs === undefined) {
      costs = new Uint16Array(m);
      const subRow = sub[id];
      for (let j = 0; j < m; j++) {
        costs[j] = subRow[columns[j]];
      }
      cachedRows[id] = costs;
    }

    let diagonal = dp[0];
    let left = diagonal + deleteCost;
    dp[0] = left;

    for (let j = 0; j < m; j++) {
      const above = dp[j + 1];

      let best = diagonal + costs[j];
      const remove = above + deleteCost;
      if (remove < best) best = remove;

      const insert = left + insertCosts[j];
      if (insert < best) best = insert;

      dp[j + 1] = best;
      left = best;
      diagonal = above;
    }
  }

  const result = dp[m];
  output[pair] = String(result);
  total += BigInt(result);
}

output[P] = 'total ' + total.toString();
process.stdout.write(output.join('\n') + '\n');
