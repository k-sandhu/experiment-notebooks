'use strict';

const fs = require('fs');

function main() {
  const input = fs.readFileSync(process.argv[2]);
  const size = input.length;

  let wordTable = new Uint32Array(2048);
  let wordMask = 2047;
  let wordLimit = Math.floor(2048 * 0.7);

  let wordStarts = new Uint32Array(1024);
  let wordLengths = new Uint32Array(1024);
  let wordHashes = new Uint32Array(1024);
  let vocabularySize = 0;

  let pairCapacity = 65536;
  let pairTable = new Uint32Array(pairCapacity * 3);
  let pairMask = pairCapacity - 1;
  let pairLimit = Math.floor(pairCapacity * 0.7);

  let totalWords = 0;
  let totalPairs = 0;
  let distinctPairs = 0;
  let previous = 0;

  function growWordStorage() {
    const capacity = wordStarts.length * 2;

    const starts = new Uint32Array(capacity);
    const lengths = new Uint32Array(capacity);
    const hashes = new Uint32Array(capacity);

    starts.set(wordStarts);
    lengths.set(wordLengths);
    hashes.set(wordHashes);

    wordStarts = starts;
    wordLengths = lengths;
    wordHashes = hashes;
  }

  function growWordTable() {
    const capacity = wordTable.length * 2;
    const table = new Uint32Array(capacity);
    const mask = capacity - 1;

    for (let id = 1; id <= vocabularySize; id++) {
      let slot = wordHashes[id] & mask;
      while (table[slot] !== 0) {
        slot = (slot + 1) & mask;
      }
      table[slot] = id;
    }

    wordTable = table;
    wordMask = mask;
    wordLimit = Math.floor(capacity * 0.7);
  }

  function growPairTable() {
    const old = pairTable;
    const capacity = pairCapacity * 2;
    const table = new Uint32Array(capacity * 3);
    const mask = capacity - 1;
    const length = table.length;

    for (let i = 0; i < old.length; i += 3) {
      const first = old[i];
      if (first === 0) continue;

      const second = old[i + 1];
      let hash =
        Math.imul(first, 0x9e3779b1) ^
        Math.imul(second, 0x85ebca77);
      hash ^= hash >>> 16;
      hash = Math.imul(hash, 0xc2b2ae3d);
      hash ^= hash >>> 16;

      let slot = (hash & mask) * 3;
      while (table[slot] !== 0) {
        slot += 3;
        if (slot === length) slot = 0;
      }

      table[slot] = first;
      table[slot + 1] = second;
      table[slot + 2] = old[i + 2];
    }

    pairTable = table;
    pairCapacity = capacity;
    pairMask = mask;
    pairLimit = Math.floor(capacity * 0.7);
  }

  let position = 0;

  while (position < size) {
    let character = input[position] | 32;

    if (character < 97 || character > 122) {
      if (character === 46 || character === 33 || character === 63) {
        previous = 0;
      }
      position++;
      continue;
    }

    const start = position;
    let hash = 0x811c9dc5;

    do {
      input[position] = character;
      hash = Math.imul(hash ^ character, 0x01000193);
      position++;

      if (position === size) break;
      character = input[position] | 32;
    } while (character >= 97 && character <= 122);

    hash >>>= 0;
    const length = position - start;

    let slot = hash & wordMask;
    let id;

    for (;;) {
      id = wordTable[slot];

      if (id === 0) {
        id = ++vocabularySize;

        if (id === wordStarts.length) {
          growWordStorage();
        }

        wordStarts[id] = start;
        wordLengths[id] = length;
        wordHashes[id] = hash;
        wordTable[slot] = id;

        if (vocabularySize > wordLimit) {
          growWordTable();
        }
        break;
      }

      if (wordHashes[id] === hash && wordLengths[id] === length) {
        const otherStart = wordStarts[id];
        let offset = 0;

        while (
          offset < length &&
          input[start + offset] === input[otherStart + offset]
        ) {
          offset++;
        }

        if (offset === length) break;
      }

      slot = (slot + 1) & wordMask;
    }

    totalWords++;

    if (previous !== 0) {
      totalPairs++;

      let pairHash =
        Math.imul(previous, 0x9e3779b1) ^
        Math.imul(id, 0x85ebca77);
      pairHash ^= pairHash >>> 16;
      pairHash = Math.imul(pairHash, 0xc2b2ae3d);
      pairHash ^= pairHash >>> 16;

      const table = pairTable;
      let pairSlot = (pairHash & pairMask) * 3;

      for (;;) {
        const first = table[pairSlot];

        if (first === 0) {
          table[pairSlot] = previous;
          table[pairSlot + 1] = id;
          table[pairSlot + 2] = 1;
          distinctPairs++;

          if (distinctPairs > pairLimit) {
            growPairTable();
          }
          break;
        }

        if (first === previous && table[pairSlot + 1] === id) {
          table[pairSlot + 2]++;
          break;
        }

        pairSlot += 3;
        if (pairSlot === table.length) pairSlot = 0;
      }
    }

    previous = id;
  }

  const output = [
    'words ' + totalWords,
    'pairs ' + totalPairs,
    'distinct ' + distinctPairs
  ];

  if (distinctPairs === 0) {
    process.stdout.write(output.join('\n') + '\n');
    return;
  }

  const words = new Array(vocabularySize + 1);
  const orderedIds = new Array(vocabularySize);

  for (let id = 1; id <= vocabularySize; id++) {
    words[id] = input.toString(
      'latin1',
      wordStarts[id],
      wordStarts[id] + wordLengths[id]
    );
    orderedIds[id - 1] = id;
  }

  orderedIds.sort((a, b) => {
    if (words[a] < words[b]) return -1;
    if (words[a] > words[b]) return 1;
    return 0;
  });

  const ranks = new Uint32Array(vocabularySize + 1);
  for (let i = 0; i < vocabularySize; i++) {
    ranks[orderedIds[i]] = i;
  }

  const top = [];

  function better(count, firstRank, secondRank, other) {
    return (
      count > other.count ||
      (count === other.count &&
        (firstRank < other.firstRank ||
          (firstRank === other.firstRank &&
            secondRank < other.secondRank)))
    );
  }

  for (let i = 0; i < pairTable.length; i += 3) {
    const count = pairTable[i + 2];
    if (count === 0) continue;

    if (top.length === 20 && count < top[19].count) continue;

    const first = pairTable[i];
    const second = pairTable[i + 1];
    const firstRank = ranks[first];
    const secondRank = ranks[second];

    if (
      top.length === 20 &&
      !better(count, firstRank, secondRank, top[19])
    ) {
      continue;
    }

    let index = top.length;
    if (index === 20) index = 19;

    while (
      index > 0 &&
      better(count, firstRank, secondRank, top[index - 1])
    ) {
      top[index] = top[index - 1];
      index--;
    }

    top[index] = { count, first, second, firstRank, secondRank };
  }

  for (const entry of top) {
    output.push(
      entry.count + ' ' + words[entry.first] + ' ' + words[entry.second]
    );
  }

  process.stdout.write(output.join('\n') + '\n');
}

main();
