"use strict";

const fs = require("fs");

function main() {
  const buf = fs.readFileSync(process.argv[2]);
  const rd = buf.length;
  let p = 0;

  function nextInt() {
    while (p < rd && (buf[p] < 48 || buf[p] > 57)) p++;
    let v = 0;
    while (p < rd && buf[p] >= 48 && buf[p] <= 57) {
      v = v * 10 + (buf[p] - 48);
      p++;
    }
    return v;
  }

  const H = nextInt();
  const W = nextInt();
  const S = nextInt();
  const n = H * W;

  let cur = new Int32Array(n);
  let nxt = new Int32Array(n);
  const wall = new Uint8Array(n);
  const openList = new Int32Array(n);
  let m = 0;

  while (p < rd && buf[p] !== 10) p++;
  if (p < rd) p++;

  for (let r = 0; r < H; r++) {
    for (let c = 0; c < W; c++) {
      const ch = buf[p++];
      const i = r * W + c;
      if (ch === 35) {
        // '#'
        wall[i] = 1;
      } else if (ch >= 49 && ch <= 57) {
        cur[i] = (ch - 48) * 1000;
      } else {
        openList[m++] = i;
      }
    }
    while (p < rd && buf[p] !== 10) p++;
    if (p < rd) p++;
  }

  nxt.set(cur); // sources keep their fixed value in the swap buffer

  const iup = new Int32Array(n);
  const idown = new Int32Array(n);
  const ileft = new Int32Array(n);
  const iright = new Int32Array(n);
  for (let k = 0; k < m; k++) {
    const i = openList[k];
    const r = (i / W) | 0, c = i % W;
    iup[i] = r > 0 && !wall[i - W] ? i - W : i;
    idown[i] = r + 1 < H && !wall[i + W] ? i + W : i;
    ileft[i] = c > 0 && !wall[i - 1] ? i - 1 : i;
    iright[i] = c + 1 < W && !wall[i + 1] ? i + 1 : i;
  }

  for (let s = 0; s < S; s++) {
    for (let k = 0; k < m; k++) {
      const i = openList[k];
      const v = cur[i];
      nxt[i] = (4 * v + cur[iup[i]] + cur[idown[i]] + cur[ileft[i]] + cur[iright[i]]) >> 3;
    }
    let t = cur;
    cur = nxt;
    nxt = t;
  }

  let sum = 0, chk = 0, mx = -1, mi = 0;
  for (let k = 0; k < m; k++) {
    const i = openList[k];
    const v = cur[i];
    sum += v;
    chk += v * (i + 1);
    if (v > mx) { mx = v; mi = i; }
  }

  process.stdout.write(
    `sum ${sum}\nmax ${mx} ${(mi / W) | 0} ${mi % W}\nchecksum ${chk}\n`
  );
}

main();
