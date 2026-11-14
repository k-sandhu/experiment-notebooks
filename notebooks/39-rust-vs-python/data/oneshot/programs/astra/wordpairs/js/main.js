'use strict';

const fs = require('fs');
const input = fs.readFileSync(process.argv[2]);
const length = input.length;

const wordStarts = [0];
const wordLengths = [0];
const wordHashes = [0];

let wordTable = new Uint32Array(1024);
let wordMask = wordTable.length - 1;
let wordLimit = Math.floor(wordTable.length * 0.7);
let vocabularySize = 0;

function growWordTable() {
    const next = new Uint32Array(wordTable.length * 2);
    const mask = next.length - 1;

    for (let id = 1; id <= vocabularySize; id++) {
        let slot = wordHashes[id] & mask;
        while (next[slot] !== 0) {
            slot = (slot + 1) & mask;
        }
        next[slot] = id;
    }

    wordTable = next;
    wordMask = mask;
    wordLimit = Math.floor(next.length * 0.7);
}

function internWord(start, size, hash) {
    hash = (hash ^ (hash >>> 16)) >>> 0;
    let slot = hash & wordMask;

    while (true) {
        const id = wordTable[slot];
        if (id === 0) break;

        if (wordHashes[id] === hash && wordLengths[id] === size) {
            const other = wordStarts[id];
            let j = 0;
            while (j < size && input[start + j] === input[other + j]) {
                j++;
            }
            if (j === size) return id;
        }

        slot = (slot + 1) & wordMask;
    }

    if (vocabularySize >= wordLimit) {
        growWordTable();
        slot = hash & wordMask;
        while (wordTable[slot] !== 0) {
            slot = (slot + 1) & wordMask;
        }
    }

    const id = ++vocabularySize;
    wordStarts.push(start);
    wordLengths.push(size);
    wordHashes.push(hash);
    wordTable[slot] = id;
    return id;
}

let pairFirst = new Uint32Array(1024);
let pairSecond = new Uint32Array(1024);
let pairCounts = new Float64Array(1024);
let pairMask = pairFirst.length - 1;
let pairLimit = Math.floor(pairFirst.length * 0.7);
let distinctPairs = 0;

function pairHash(first, second) {
    let hash = Math.imul(first, 0x9e3779b1) ^
               Math.imul(second, 0x85ebca77);
    return hash ^ (hash >>> 16);
}

function growPairTable() {
    const capacity = pairFirst.length * 2;
    const nextFirst = new Uint32Array(capacity);
    const nextSecond = new Uint32Array(capacity);
    const nextCounts = new Float64Array(capacity);
    const mask = capacity - 1;

    for (let i = 0; i < pairFirst.length; i++) {
        const first = pairFirst[i];
        if (first === 0) continue;

        const second = pairSecond[i];
        let slot = pairHash(first, second) & mask;
        while (nextFirst[slot] !== 0) {
            slot = (slot + 1) & mask;
        }

        nextFirst[slot] = first;
        nextSecond[slot] = second;
        nextCounts[slot] = pairCounts[i];
    }

    pairFirst = nextFirst;
    pairSecond = nextSecond;
    pairCounts = nextCounts;
    pairMask = mask;
    pairLimit = Math.floor(capacity * 0.7);
}

function addPair(first, second) {
    const hash = pairHash(first, second);
    let slot = hash & pairMask;

    while (pairFirst[slot] !== 0) {
        if (pairFirst[slot] === first && pairSecond[slot] === second) {
            pairCounts[slot]++;
            return;
        }
        slot = (slot + 1) & pairMask;
    }

    if (distinctPairs >= pairLimit) {
        growPairTable();
        slot = hash & pairMask;
        while (pairFirst[slot] !== 0) {
            slot = (slot + 1) & pairMask;
        }
    }

    pairFirst[slot] = first;
    pairSecond[slot] = second;
    pairCounts[slot] = 1;
    distinctPairs++;
}

let totalWords = 0;
let totalPairs = 0;
let previous = 0;
let position = 0;

while (position < length) {
    let byte = input[position];
    let lower = byte | 32;

    if (lower >= 97 && lower <= 122) {
        const start = position;
        let hash = 0x811c9dc5;

        do {
            if (byte !== lower) input[position] = lower;
            hash = Math.imul(hash ^ lower, 0x01000193);
            position++;

            if (position === length) break;
            byte = input[position];
            lower = byte | 32;
        } while (lower >= 97 && lower <= 122);

        const id = internWord(start, position - start, hash);
        totalWords++;

        if (previous !== 0) {
            addPair(previous, id);
            totalPairs++;
        }
        previous = id;

        if (position === length) break;
    }

    if (byte === 46 || byte === 33 || byte === 63) {
        previous = 0;
    }
    position++;
}

const output = [
    'words ' + totalWords,
    'pairs ' + totalPairs,
    'distinct ' + distinctPairs
];

if (distinctPairs !== 0) {
    const words = new Array(vocabularySize + 1);
    const orderedIds = new Array(vocabularySize);

    for (let id = 1; id <= vocabularySize; id++) {
        words[id] = input.toString(
            'ascii',
            wordStarts[id],
            wordStarts[id] + wordLengths[id]
        );
        orderedIds[id - 1] = id;
    }

    orderedIds.sort((a, b) => {
        const first = words[a];
        const second = words[b];
        return first < second ? -1 : first > second ? 1 : 0;
    });

    const ranks = new Uint32Array(vocabularySize + 1);
    for (let i = 0; i < orderedIds.length; i++) {
        ranks[orderedIds[i]] = i;
    }

    const topFirst = new Uint32Array(20);
    const topSecond = new Uint32Array(20);
    const topCounts = new Float64Array(20);
    let topSize = 0;

    for (let slot = 0; slot < pairFirst.length; slot++) {
        const first = pairFirst[slot];
        if (first === 0) continue;

        const count = pairCounts[slot];
        const second = pairSecond[slot];
        const firstRank = ranks[first];
        const secondRank = ranks[second];

        if (topSize === 20) {
            const lastCount = topCounts[19];
            if (count < lastCount) continue;

            if (count === lastCount) {
                const lastFirstRank = ranks[topFirst[19]];
                if (firstRank > lastFirstRank) continue;
                if (firstRank === lastFirstRank &&
                    secondRank >= ranks[topSecond[19]]) {
                    continue;
                }
            }
        }

        let index = topSize < 20 ? topSize++ : 19;

        while (index > 0) {
            const prior = index - 1;
            const priorCount = topCounts[prior];

            if (count < priorCount) break;
            if (count === priorCount) {
                const priorFirstRank = ranks[topFirst[prior]];
                if (firstRank > priorFirstRank) break;
                if (firstRank === priorFirstRank &&
                    secondRank >= ranks[topSecond[prior]]) {
                    break;
                }
            }

            topFirst[index] = topFirst[prior];
            topSecond[index] = topSecond[prior];
            topCounts[index] = priorCount;
            index--;
        }

        topFirst[index] = first;
        topSecond[index] = second;
        topCounts[index] = count;
    }

    for (let i = 0; i < topSize; i++) {
        output.push(
            topCounts[i] + ' ' +
            words[topFirst[i]] + ' ' +
            words[topSecond[i]]
        );
    }
}

process.stdout.write(output.join('\n') + '\n');
