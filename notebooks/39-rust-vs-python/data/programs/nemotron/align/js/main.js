"use strict";

const fs = require("fs");

const text = fs.readFileSync(process.argv[2], "utf8");
const tokens = text.split(/\s+/);
let pos = 0;

function next() { return tokens[pos++]; }
function nextInt() { return parseInt(tokens[pos++], 10); }

const alphabet = next();
const A = alphabet.length;

const charIndex = new Int32Array(26);
for (let i = 0; i < 26; i++) charIndex[i] = -1;
for (let i = 0; i < A; i++) charIndex[alphabet.charCodeAt(i) - 65] = i;

const ins = new Int32Array(A);
const del = new Int32Array(A);
for (let i = 0; i < A; i++) ins[i] = nextInt();
for (let i = 0; i < A; i++) del[i] = nextInt();
const sub = new Array(A);
for (let i = 0; i < A; i++) {
    sub[i] = new Int32Array(A);
    for (let j = 0; j < A; j++) sub[i][j] = nextInt();
}

const P = nextInt();

let prev = [];
let cur = [];
let sIdx = [];
let tIdx = [];
let insT = [];

const total = [0]; // use number directly below
let totalVal = 0;
const out = [];

for (let pair = 0; pair < P; pair++) {
    const s = next();
    const t = next();
    const n = s.length;
    const m = t.length;

    sIdx.length = n;
    for (let i = 0; i < n; i++) sIdx[i] = charIndex[s.charCodeAt(i) - 65];
    tIdx.length = m;
    insT.length = m;
    for (let j = 0; j < m; j++) { tIdx[j] = charIndex[t.charCodeAt(j) - 65]; insT[j] = ins[tIdx[j]]; }

    if (prev.length < m + 1) { prev = new Array(m + 1); cur = new Array(m + 1); }

    prev[0] = 0;
    for (let j = 1; j <= m; j++) prev[j] = prev[j - 1] + insT[j - 1];

    for (let i = 1; i <= n; i++) {
        const si = sIdx[i - 1];
        const delSi = del[si];
        const subRow = sub[si];
        cur[0] = prev[0] + delSi;
        for (let j = 1; j <= m; j++) {
            const tj = tIdx[j - 1];
            let up = prev[j] + delSi;
            let left = cur[j - 1] + insT[j - 1];
            let diag = prev[j - 1] + subRow[tj];
            let best = up < left ? up : left;
            cur[j] = diag < best ? diag : best;
        }
        const tmp = prev; prev = cur; cur = tmp;
    }

    const cost = prev[m];
    totalVal += cost;
    out.push(cost);
}
out.push("total " + totalVal);
process.stdout.write(out.join("\n") + "\n");
