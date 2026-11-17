'use strict';

const fs = require('fs');

function readGraph(path) {
  const input = fs.readFileSync(path);
  let position = 0;

  function nextInt() {
    while (input[position] <= 32) position++;
    let value = 0;
    while (input[position] > 32) {
      value = value * 10 + input[position++] - 48;
    }
    return value;
  }

  const n = nextInt();
  const m = nextInt();
  const q = nextInt();

  const from = new Uint32Array(m);
  const to = new Uint32Array(m);
  const weights = new Uint16Array(m);
  const offsets = new Uint32Array(n + 1);
  let edgeCount = 0;

  for (let i = 0; i < m; i++) {
    const u = nextInt();
    const v = nextInt();
    const w = nextInt();

    if (u === v) continue;

    from[edgeCount] = u;
    to[edgeCount] = v;
    weights[edgeCount] = w;
    offsets[u + 1]++;
    offsets[v + 1]++;
    edgeCount++;
  }

  const sources = new Uint32Array(q);
  for (let i = 0; i < q; i++) sources[i] = nextInt();

  for (let i = 1; i <= n; i++) {
    offsets[i] += offsets[i - 1];
  }

  const cursor = offsets.slice(0, n);
  const neighbors = new Uint32Array(edgeCount * 2);
  const lengths = new Uint16Array(edgeCount * 2);

  for (let i = 0; i < edgeCount; i++) {
    const u = from[i];
    const v = to[i];
    const w = weights[i];

    let index = cursor[u]++;
    neighbors[index] = v;
    lengths[index] = w;

    index = cursor[v]++;
    neighbors[index] = u;
    lengths[index] = w;
  }

  return { n, offsets, neighbors, lengths, sources };
}

const { n, offsets, neighbors, lengths, sources } =
  readGraph(process.argv[2]);

const distances = new Float64Array(n);
const next = new Int32Array(n);
const previous = new Int32Array(n);
const heads = new Int32Array(1024);
const occupied = new Uint32Array(32);

function solve(source) {
  distances.fill(Infinity);
  heads.fill(-1);
  occupied.fill(0);

  distances[source] = 0;
  next[source] = -1;
  previous[source] = -1;
  heads[0] = source;
  occupied[0] = 1;

  let occupiedGroups = 1;
  let bucket = 0;
  let queued = 1;

  let reachable = 0;
  let total = 0;
  let largeTotal = 0n;
  let farthest = 0;
  let farthestNode = source;

  // Pending distances span at most 1000, so 1024 cyclic buckets suffice.
  while (queued !== 0) {
    let u = heads[bucket];

    if (u === -1) {
      let group = bucket >>> 5;
      let bits = occupied[group] & (-1 << (bucket & 31));

      if (bits === 0) {
        const laterGroups = group === 31
          ? 0
          : occupiedGroups & (-1 << (group + 1));

        const groups = laterGroups !== 0 ? laterGroups : occupiedGroups;
        group = 31 - Math.clz32(groups & -groups);
        bits = occupied[group];
      }

      bucket = (group << 5) + 31 - Math.clz32(bits & -bits);
      u = heads[bucket];
    }

    const following = next[u];
    heads[bucket] = following;

    if (following !== -1) {
      previous[following] = -1;
    } else {
      const group = bucket >>> 5;
      occupied[group] &= ~(1 << (bucket & 31));
      if (occupied[group] === 0) {
        occupiedGroups &= ~(1 << group);
      }
    }

    queued--;

    const distance = distances[u];
    reachable++;
    total += distance;

    // Flush before Number accumulation can lose integer precision.
    if (total >= 4503599627370496) {
      largeTotal += BigInt(total);
      total = 0;
    }

    if (
      distance > farthest ||
      (distance === farthest && u < farthestNode)
    ) {
      farthest = distance;
      farthestNode = u;
    }

    const end = offsets[u + 1];
    for (let edge = offsets[u]; edge < end; edge++) {
      const v = neighbors[edge];
      const candidate = distance + lengths[edge];
      const oldDistance = distances[v];

      if (candidate >= oldDistance) continue;

      if (oldDistance !== Infinity) {
        const oldBucket = oldDistance & 1023;
        const before = previous[v];
        const after = next[v];

        if (before === -1) {
          heads[oldBucket] = after;
        } else {
          next[before] = after;
        }

        if (after !== -1) previous[after] = before;

        if (heads[oldBucket] === -1) {
          const group = oldBucket >>> 5;
          occupied[group] &= ~(1 << (oldBucket & 31));
          if (occupied[group] === 0) {
            occupiedGroups &= ~(1 << group);
          }
        }
      } else {
        queued++;
      }

      distances[v] = candidate;

      const newBucket = candidate & 1023;
      const first = heads[newBucket];

      previous[v] = -1;
      next[v] = first;

      if (first !== -1) {
        previous[first] = v;
      } else {
        const group = newBucket >>> 5;
        occupied[group] |= 1 << (newBucket & 31);
        occupiedGroups |= 1 << group;
      }

      heads[newBucket] = v;
    }
  }

  const exactTotal = largeTotal + BigInt(total);
  return `${source} ${reachable} ${exactTotal} ${farthest} ${farthestNode}`;
}

const cache = new Map();
const output = new Array(sources.length);

for (let i = 0; i < sources.length; i++) {
  const source = sources[i];
  let line = cache.get(source);

  if (line === undefined) {
    line = solve(source);
    cache.set(source, line);
  }

  output[i] = line;
}

if (output.length !== 0) {
  process.stdout.write(output.join('\n') + '\n');
}
