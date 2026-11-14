// Word pairs benchmark - JavaScript on Node 22, built-in modules only.
// Single pass: lowercase words in place, intern them to ids, emit packed
// (prevId, curId) pairs within sentences, sort the packed pairs (ids stay
// below ~2^26 for the benchmark scale, so id1*(V+1)+id2 is an exact
// double), count runs, keep the top 20 by (count desc, word1 asc, word2 asc).
'use strict';

const fs = require('fs');

const data = fs.readFileSync(process.argv[2]);
const n = data.length;

const wordIds = new Map();
const words = [];
const w1Arr = [];
const w2Arr = [];

let prevId = -1;
let havePrev = false;
let wordTotal = 0;
let pairTotal = 0;

let i = 0;
while (i < n) {
    // skip to the next word; sentence enders reset the previous word
    while (i < n) {
        const c = data[i];
        if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122)) break;
        if (c === 46 || c === 33 || c === 63) havePrev = false;
        i++;
    }
    if (i >= n) break;

    // scan the word, lowercasing in place
    const start = i;
    while (i < n) {
        let c = data[i];
        if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122)) {
            data[i] = c | 0x20;
            i++;
        } else {
            break;
        }
    }
    const word = data.toString('ascii', start, i);
    let id = wordIds.get(word);
    if (id === undefined) {
        id = words.length;
        words.push(word);
        wordIds.set(word, id);
    }

    wordTotal++;
    if (havePrev) {
        w1Arr.push(prevId);
        w2Arr.push(id);
        pairTotal++;
    }
    prevId = id;
    havePrev = true;
}

// Pack pairs as exact doubles: id1*(V+1)+id2 < 2^53 for any realistic input.
const v = words.length;
const mul = v + 1;
const pairCount = pairTotal;
const keys = new Float64Array(pairCount);
for (let t = 0; t < pairCount; t++) {
    keys[t] = w1Arr[t] * mul + w2Arr[t];
}
// release the parallel arrays before sorting
w1Arr.length = 0;
w2Arr.length = 0;

// numeric sort (default for TypedArray.sort with no comparator)
keys.sort();

const bestCount = new Array(20);
const bestW1 = new Array(20);
const bestW2 = new Array(20);
let bestn = 0;

function better(c1, a1, b1, c2, a2, b2) {
    // is (c1,a1,b1) better than (c2,a2,b2)? count desc, then words asc
    if (c1 !== c2) return c1 > c2;
    if (words[a1] !== words[a2]) return words[a1] < words[a2];
    return words[b1] < words[b2];
}

function consider(count, w1, w2) {
    if (bestn < 20) {
        let pos = bestn;
        while (pos > 0 && better(count, w1, w2, bestCount[pos - 1], bestW1[pos - 1], bestW2[pos - 1])) {
            bestCount[pos] = bestCount[pos - 1];
            bestW1[pos] = bestW1[pos - 1];
            bestW2[pos] = bestW2[pos - 1];
            pos--;
        }
        bestCount[pos] = count;
        bestW1[pos] = w1;
        bestW2[pos] = w2;
        bestn++;
    } else if (better(count, w1, w2, bestCount[19], bestW1[19], bestW2[19])) {
        const c = count;
        const a = w1;
        const b = w2;
        let pos = 19;
        while (pos > 0 && better(c, a, b, bestCount[pos - 1], bestW1[pos - 1], bestW2[pos - 1])) {
            bestCount[pos] = bestCount[pos - 1];
            bestW1[pos] = bestW1[pos - 1];
            bestW2[pos] = bestW2[pos - 1];
            pos--;
        }
        bestCount[pos] = c;
        bestW1[pos] = a;
        bestW2[pos] = b;
    }
}

let t = 0;
let distinct = 0;
while (t < pairCount) {
    const k = keys[t];
    let u = t + 1;
    while (u < pairCount && keys[u] === k) u++;
    const count = u - t;
    const w1 = (k / mul) | 0;
    const w2 = (k - w1 * mul) | 0;
    consider(count, w1, w2);
    distinct++;
    t = u;
}

const lines = [];
lines.push('words ' + wordTotal);
lines.push('pairs ' + pairTotal);
lines.push('distinct ' + distinct);
for (let k = 0; k < bestn; k++) {
    lines.push(bestCount[k] + ' ' + words[bestW1[k]] + ' ' + words[bestW2[k]]);
}
process.stdout.write(lines.join('\n') + '\n');
