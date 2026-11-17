'use strict';

const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');

function buildModule() {
  function unsignedLEB(value) {
    const bytes = [];
    do {
      let byte = value & 127;
      value = Math.floor(value / 128);
      if (value !== 0) byte |= 128;
      bytes.push(byte);
    } while (value !== 0);
    return bytes;
  }

  function signedLEB(value) {
    const bytes = [];
    for (;;) {
      let byte = Number(value & 127n);
      value >>= 7n;
      const done =
        (value === 0n && (byte & 64) === 0) ||
        (value === -1n && (byte & 64) !== 0);
      if (!done) byte |= 128;
      bytes.push(byte);
      if (done) return bytes;
    }
  }

  function section(id, bytes) {
    return [id, ...unsignedLEB(bytes.length), ...bytes];
  }

  function name(value) {
    const bytes = Array.from(Buffer.from(value));
    return [...unsignedLEB(bytes.length), ...bytes];
  }

  // Parameters: seed, first walker, exclusive last walker, steps, bound.
  // i64 locals:
  // 5 walker, 6 state, 7 mixed value, 8 x, 9 y, 10 steps remaining,
  // 11 spread, 12 bumps, 13 returns, 14 best walker, 15 best distance,
  // 16 temporary coordinate/distance, 17 twice the bound.
  // i32 local 18: axis.
  const body = [2, 13, 0x7e, 1, 0x7f];

  const op = (...bytes) => body.push(...bytes);
  const get = index => op(0x20, index);
  const set = index => op(0x21, index);
  const tee = index => op(0x22, index);
  const constant = value => {
    op(0x42, ...signedLEB(BigInt.asIntN(64, BigInt(value))));
  };

  get(1);
  set(5);
  constant(-1);
  set(14);
  constant(-1);
  set(15);
  get(4);
  get(4);
  op(0x7c);
  set(17);

  op(0x02, 0x40); // Walker exit block.
  op(0x03, 0x40); // Walker loop.

  get(5);
  get(2);
  op(0x5a);       // i64.ge_u
  op(0x0d, 1);

  get(0);
  get(5);
  op(0x7c);
  set(6);

  constant(0);
  set(8);
  constant(0);
  set(9);
  get(3);
  set(10);

  op(0x03, 0x40); // Step loop; L is positive.

  get(6);
  constant(0x9e3779b97f4a7c15n);
  op(0x7c);
  tee(6);

  get(6);
  constant(30);
  op(0x88, 0x85); // shr_u, xor
  constant(0xbf58476d1ce4e5b9n);
  op(0x7e);
  tee(7);

  get(7);
  constant(27);
  op(0x88, 0x85);
  constant(0x94d049bb133111ebn);
  op(0x7e);
  set(7);

  // The final xor with z >> 31 cannot change the top two bits.
  // Select the active coordinate using bit 63.
  get(9);
  get(8);
  get(7);
  constant(63);
  op(0x88, 0xa7);
  tee(18);
  op(0x1b);

  // Add +1 or -1 according to bit 62.
  constant(1);
  get(7);
  constant(61);
  op(0x88);
  constant(2);
  op(0x83, 0x7d, 0x7c);
  set(16);

  // An unsigned interval test handles both boundaries.
  get(16);
  get(4);
  op(0x7c);
  get(17);
  op(0x56); // i64.gt_u

  op(0x04, 0x40);
  get(12);
  constant(1);
  op(0x7c);
  set(12);
  op(0x05);

  get(8);
  get(16);
  get(18);
  op(0x1b);
  set(8);

  get(16);
  get(9);
  get(18);
  op(0x1b);
  set(9);

  get(13);
  get(8);
  get(9);
  op(0x84, 0x50, 0xad, 0x7c);
  set(13);

  op(0x0b);

  get(10);
  constant(1);
  op(0x7d);
  tee(10);
  op(0x50, 0x45);
  op(0x0d, 0);
  op(0x0b); // End step loop.

  get(11);
  get(8);
  get(8);
  op(0x7e);
  get(9);
  get(9);
  op(0x7e, 0x7c, 0x7c);
  set(11);

  // abs(x)
  get(8);
  constant(0);
  get(8);
  op(0x7d);
  get(8);
  constant(0);
  op(0x59, 0x1b);

  // abs(y)
  get(9);
  constant(0);
  get(9);
  op(0x7d);
  get(9);
  constant(0);
  op(0x59, 0x1b);

  op(0x7c);
  set(16);

  get(16);
  get(15);
  op(0x55);
  op(0x04, 0x40);
  get(16);
  set(15);
  get(5);
  set(14);
  op(0x0b);

  get(5);
  constant(1);
  op(0x7c);
  set(5);
  op(0x0c, 0);

  op(0x0b, 0x0b);

  for (let i = 0; i < 5; i++) {
    op(0x41, ...signedLEB(BigInt(i * 8)));
    get(11 + i);
    op(0x37, 3, 0);
  }
  op(0x0b);

  const bytes = [
    0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
    ...section(1, [1, 0x60, 5, 0x7e, 0x7e, 0x7e, 0x7e, 0x7e, 0]),
    ...section(3, [1, 0]),
    ...section(5, [1, 0, 1]),
    ...section(7, [
      2,
      ...name('run'), 0, 0,
      ...name('memory'), 2, 0
    ]),
    ...section(10, [1, ...unsignedLEB(body.length), ...body])
  ];

  return new WebAssembly.Module(Uint8Array.from(bytes));
}

function simulate(module, seed, first, last, steps, bound) {
  const instance = new WebAssembly.Instance(module);
  instance.exports.run(seed, first, last, steps, bound);

  const view = new DataView(instance.exports.memory.buffer);
  return [
    view.getBigInt64(0, true),
    view.getBigInt64(8, true),
    view.getBigInt64(16, true),
    view.getBigInt64(24, true),
    view.getBigInt64(32, true)
  ];
}

function printResult(result) {
  process.stdout.write(
    `spread ${result[0]}\n` +
    `bumps ${result[1]}\n` +
    `returns ${result[2]}\n` +
    `farthest ${result[3]} ${result[4]}\n`
  );
}

if (!isMainThread) {
  const { module, seed, first, last, steps, bound } = workerData;
  parentPort.postMessage(simulate(module, seed, first, last, steps, bound));
} else {
  const input = require('fs')
    .readFileSync(process.argv[2], 'utf8')
    .trim()
    .split(/\s+/);

  const walkers = BigInt(input[0]);
  const steps = BigInt(input[1]);
  const inputBound = BigInt(input[2]);
  const seed = BigInt(input[3]);
  const bound = inputBound < steps ? inputBound : steps;
  const workers = Number(process.argv[3]);
  const module = buildModule();

  if (workers === 1) {
    printResult(simulate(module, seed, 0n, walkers, steps, bound));
  } else {
    const count = BigInt(workers);
    const result = [0n, 0n, 0n, -1n, -1n];
    let remaining = workers;

    for (let i = 0; i < workers; i++) {
      const first = walkers * BigInt(i) / count;
      const last = walkers * BigInt(i + 1) / count;

      const worker = new Worker(__filename, {
        workerData: { module, seed, first, last, steps, bound }
      });

      worker.on('message', partial => {
        result[0] += partial[0];
        result[1] += partial[1];
        result[2] += partial[2];

        if (
          partial[4] > result[4] ||
          (partial[4] === result[4] && partial[3] < result[3])
        ) {
          result[3] = partial[3];
          result[4] = partial[4];
        }

        if (--remaining === 0) printResult(result);
      });
    }
  }
}
