'use strict';

const fs = require('fs');
const data = fs.readFileSync(process.argv[2]);

// Open addressing-free interning: JS Map keyed by the lowercased word string.
const wordMap = new Map();
const words = []; // id -> lowercased word string
let wordCount = 0;

function intern(w) {
    let id = wordMap.get(w);
    if (id === undefined) {
        id = wordCount++;
        words.push(w);
        wordMap.set(w, id);
    }
    return id;
}

// pairMap: id1 -> Map of id2 -> count
const pairMap = new Map();
let pairDistinct = 0;

function pairInc(a, b) {
    let inner = pairMap.get(a);
    if (inner === undefined) {
        inner = new Map();
        pairMap.set(a, inner);
    }
    const c = inner.get(b) | 0;
    inner.set(b, c + 1);
    if (c === 0) pairDistinct++;
}

let prevId = -1;
let wordsCount = 0;
let pairsCount = 0;
const chars = [];

function noteWord(id) {
    wordsCount++;
    if (prevId >= 0) {
        pairsCount++;
        pairInc(prevId, id);
    }
    prevId = id;
}

const n = data.length;
for (let i = 0; i < n; i++) {
    const c = data[i];
    if ((c >= 65 && c <= 90) || (c >= 97 && c <= 122)) {
        chars.push(String.fromCharCode(c | 32));
    } else {
        if (chars.length > 0) {
            noteWord(intern(chars.join('')));
            chars.length = 0;
        }
        if (c === 46 || c === 33 || c === 63) prevId = -1;
    }
}
if (chars.length > 0) noteWord(intern(chars.join('')));

const ents = [];
for (const [a, inner] of pairMap) {
    for (const [b, c] of inner) {
        ents.push([c, a, b]);
    }
}
ents.sort((x, y) => {
    if (y[0] !== x[0]) return y[0] - x[0];
    const wa = words[x[1]];
    const wb = words[y[1]];
    if (wa !== wb) return wa < wb ? -1 : 1;
    const wc = words[x[2]];
    const wd = words[y[2]];
    return wc < wd ? -1 : (wc > wd ? 1 : 0);
});

const lines = [`words ${wordsCount}`, `pairs ${pairsCount}`, `distinct ${pairDistinct}`];
const limit = Math.min(20, ents.length);
for (let i = 0; i < limit; i++) {
    const e = ents[i];
    lines.push(`${e[0]} ${words[e[1]]} ${words[e[2]]}`);
}
process.stdout.write(lines.join('\n') + '\n');
