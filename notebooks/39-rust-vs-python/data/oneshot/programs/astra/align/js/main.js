'use strict';

const fs = require('fs');
const tokens = fs.readFileSync(process.argv[2], 'utf8').trim().split(/\s+/);
let pos = 0;

const alphabet = tokens[pos++];
const size = alphabet.length;
const letterIndex = new Uint8Array(91);

for (let i = 0; i < size; i++) {
  letterIndex[alphabet.charCodeAt(i)] = i;
}

const insertions = new Uint16Array(size);
const deletions = new Uint16Array(size);

for (let i = 0; i < size; i++) insertions[i] = Number(tokens[pos++]);
for (let i = 0; i < size; i++) deletions[i] = Number(tokens[pos++]);

const substitutions = new Array(size);
const transposed = new Array(size);

for (let i = 0; i < size; i++) {
  substitutions[i] = new Uint16Array(size);
  transposed[i] = new Uint16Array(size);
}

for (let i = 0; i < size; i++) {
  for (let j = 0; j < size; j++) {
    const cost = Number(tokens[pos++]);
    substitutions[i][j] = cost;
    transposed[j][i] = cost;
  }
}

function alignmentCost(source, target, ins, del, sub) {
  const n = source.length;
  const m = target.length;

  const dp = new Float64Array(m + 1);
  const targetLetters = new Uint8Array(m + 1);
  const targetInsertions = new Uint16Array(m + 1);
  const prepared = new Array(size);

  let boundary = 0;
  for (let j = 1; j <= m; j++) {
    const letter = letterIndex[target.charCodeAt(j - 1)];
    targetLetters[j] = letter;
    const cost = ins[letter];
    targetInsertions[j] = cost;
    boundary += cost;
    dp[j] = boundary;
  }

  for (let i = 0; i < n; i++) {
    const letter = letterIndex[source.charCodeAt(i)];
    const deletion = del[letter];

    let replacements = prepared[letter];
    if (replacements === undefined) {
      replacements = new Uint16Array(m + 1);
      const substitutionRow = sub[letter];
      for (let j = 1; j <= m; j++) {
        replacements[j] = substitutionRow[targetLetters[j]];
      }
      prepared[letter] = replacements;
    }

    let diagonal = dp[0];
    let left = diagonal + deletion;
    dp[0] = left;

    for (let j = 1; j <= m; j++) {
      const above = dp[j];
      let best = above + deletion;

      const insertion = left + targetInsertions[j];
      if (insertion < best) best = insertion;

      const replacement = diagonal + replacements[j];
      if (replacement < best) best = replacement;

      dp[j] = best;
      diagonal = above;
      left = best;
    }
  }

  return dp[m];
}

const pairs = Number(tokens[pos++]);
const output = new Array(pairs + 1);
let total = 0n;

for (let p = 0; p < pairs; p++) {
  const source = tokens[pos++];
  const target = tokens[pos++];

  let cost;
  if (source === target) {
    cost = 0;
  } else if (target.length <= source.length) {
    cost = alignmentCost(source, target, insertions, deletions, substitutions);
  } else {
    cost = alignmentCost(target, source, deletions, insertions, transposed);
  }

  output[p] = String(cost);
  total += BigInt(cost);
}

output[pairs] = 'total ' + total.toString();
process.stdout.write(output.join('\n') + '\n');
