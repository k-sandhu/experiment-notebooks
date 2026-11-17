'use strict';

const fs = require('fs');

function readGraph(path) {
  const input = fs.readFileSync(path);
  let p = 0;

  function readInt() {
    while (input[p] <= 32) p++;
    let value = 0;
    while (input[p] > 32) {
      value = value * 10 + input[p++] - 48;
    }
    return value;
  }

  const n = readInt();
  const m = readInt();
  const q = readInt();

  const us = new Uint32Array(m);
  const vs = new Uint32Array(m);
  const ws = new Uint16Array(m);
  const offsets = new Uint32Array(n + 1);

  let edgeCount = 0;
  let maxWeight = 0;

  for (let i = 0; i < m; i++) {
    const u = readInt();
    const v = readInt();
    const w = readInt();

    if (u === v) continue;

    us[edgeCount] = u;
    vs[edgeCount] = v;
    ws[edgeCount++] = w;
    offsets[u + 1]++;
    offsets[v + 1]++;
    if (w > maxWeight) maxWeight = w;
  }

  const sources = new Uint32Array(q);
  for (let i = 0; i < q; i++) sources[i] = readInt();

  for (let i = 1; i <= n; i++) {
    offsets[i] += offsets[i - 1];
  }

  const to = new Uint32Array(edgeCount * 2);
  const weights = new Uint16Array(edgeCount * 2);
  const cursor = offsets.slice(0, n);

  for (let i = 0; i < edgeCount; i++) {
    const u = us[i];
    const v = vs[i];
    const w = ws[i];

    let j = cursor[u]++;
    to[j] = v;
    weights[j] = w;

    j = cursor[v]++;
    to[j] = u;
    weights[j] = w;
  }

  return { n, offsets, to, weights, sources, maxWeight };
}

const { n, offsets, to, weights, sources, maxWeight } =
  readGraph(process.argv[2]);

const NONE = 0xffffffff;
const useUintDistances = n * maxWeight < NONE;
const INF = useUintDistances ? NONE : Infinity;
const distances = useUintDistances
  ? new Uint32Array(n)
  : new Float64Array(n);

const next = new Uint32Array(n);
const previous = new Uint32Array(n);
const heads = new Uint32Array(1024);
const bucketBits = new Uint32Array(32);

const MAX_SAFE = Number.MAX_SAFE_INTEGER;
const cache = new Map();
const output = [];

for (let query = 0; query < sources.length; query++) {
  const source = sources[query];
  const cached = cache.get(source);

  if (cached !== undefined) {
    output.push(cached);
    continue;
  }

  distances.fill(INF);
  heads.fill(NONE);
  bucketBits.fill(0);

  distances[source] = 0;
  next[source] = NONE;
  previous[source] = NONE;
  heads[0] = source;
  bucketBits[0] = 1;

  let nonemptyWords = 1;
  let bucket = 0;
  let reachable = 0;
  let total = 0;
  let wideTotal = 0n;
  let far = 0;
  let farNode = source;

  while (nonemptyWords !== 0) {
    let u = heads[bucket];

    if (u === NONE) {
      const word = bucket >>> 5;
      let mask = bucketBits[word] & (-1 << (bucket & 31));

      if (mask !== 0) {
        bucket = (word << 5) + 31 - Math.clz32(mask & -mask);
      } else {
        let words = nonemptyWords & (-2 << word);
        if (words === 0) words = nonemptyWords;

        const nextWord = 31 - Math.clz32(words & -words);
        mask = bucketBits[nextWord];
        bucket = (nextWord << 5) + 31 - Math.clz32(mask & -mask);
      }

      u = heads[bucket];
    }

    const successor = next[u];
    heads[bucket] = successor;

    if (successor !== NONE) {
      previous[successor] = NONE;
    } else {
      const word = bucket >>> 5;
      bucketBits[word] &= ~(1 << (bucket & 31));
      if (bucketBits[word] === 0) {
        nonemptyWords &= ~(1 << word);
      }
    }

    const du = distances[u];
    reachable++;

    if (total > MAX_SAFE - du) {
      wideTotal += BigInt(total);
      total = 0;
    }
    total += du;

    if (du > far) {
      far = du;
      farNode = u;
    } else if (du === far && u < farNode) {
      farNode = u;
    }

    for (let edge = offsets[u], end = offsets[u + 1]; edge < end; edge++) {
      const v = to[edge];
      const candidate = du + weights[edge];
      const oldDistance = distances[v];

      if (candidate >= oldDistance) continue;

      if (oldDistance !== INF) {
        const oldBucket = oldDistance & 1023;
        const before = previous[v];
        const after = next[v];

        if (before === NONE) {
          heads[oldBucket] = after;
        } else {
          next[before] = after;
        }

        if (after !== NONE) previous[after] = before;

        if (heads[oldBucket] === NONE) {
          const word = oldBucket >>> 5;
          bucketBits[word] &= ~(1 << (oldBucket & 31));
          if (bucketBits[word] === 0) {
            nonemptyWords &= ~(1 << word);
          }
        }
      }

      distances[v] = candidate;

      const newBucket = candidate & 1023;
      const first = heads[newBucket];

      previous[v] = NONE;
      next[v] = first;

      if (first !== NONE) {
        previous[first] = v;
      } else {
        const word = newBucket >>> 5;
        bucketBits[word] |= 1 << (newBucket & 31);
        nonemptyWords |= 1 << word;
      }

      heads[newBucket] = v;
    }
  }

  const totalText = wideTotal === 0n
    ? String(total)
    : String(wideTotal + BigInt(total));

  const line = `${source} ${reachable} ${totalText} ${far} ${farNode}`;
  cache.set(source, line);
  output.push(line);
}

if (output.length !== 0) {
  process.stdout.write(output.join('\n') + '\n');
}
