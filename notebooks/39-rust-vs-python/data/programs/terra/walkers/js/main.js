const fs = require('node:fs');
const { Worker, isMainThread, workerData } = require('node:worker_threads');
if (isMainThread) {
  const [n, steps, b, seed] = fs.readFileSync(process.argv[2], 'utf8').trim().split(/\s+/).map(BigInt);
  const count = Number(process.argv[3]);
  const jobs = [];
  for (let i = 0; i < count; i++) {
    const w = BigInt(count), k = BigInt(i), rem = n % w;
    const start = n / w * k + (k < rem ? k : rem);
    const next = k + 1n;
    const end = n / w * next + (next < rem ? next : rem);
    jobs.push(new Promise((resolve, reject) => {
      const worker = new Worker(__filename, {workerData: {start, end, steps, b, seed}});
      worker.on('message', resolve); worker.on('error', reject);
      worker.on('exit', code => { if (code !== 0) reject(new Error(`worker exited ${code}`)); });
    }));
  }
  Promise.all(jobs).then(results => {
    let spread=0n, bumps=0n, returns=0n, id=0n, distance=-1n;
    for (const a of results) {
      spread+=a.spread; bumps+=a.bumps; returns+=a.returns;
      if (a.distance>distance || (a.distance===distance && a.id<id)) {distance=a.distance; id=a.id;}
    }
    process.stdout.write(`spread ${spread}\nbumps ${bumps}\nreturns ${returns}\nfarthest ${id} ${distance}\n`);
  }).catch(e => { console.error(e); process.exitCode=1; });
} else {
  const { start, end, steps, b, seed } = workerData;
  let spread=0n, bumps=0n, returns=0n, id=0n, distance=-1n;
  // High word of an unsigned 32 by 32 multiplication, computed exactly in doubles.
  function high(a, b) {
    const a0=a&65535, a1=a>>>16, b0=b&65535, b1=b>>>16;
    return (a1*b1 + Math.floor((a1*b0+a0*b1+Math.floor(a0*b0/65536))/65536)) >>> 0;
  }
  const mask=(1n<<64n)-1n;
  const limit=BigInt(Number.MAX_SAFE_INTEGER);
  if (steps <= limit) {
    const count=Number(steps), bound=Number(b<steps?b:steps);
    for (let j=start;j<end;j++) {
      let state=(seed+j)&mask, lo=Number(state&0xffffffffn)>>>0, hi=Number(state>>32n)>>>0;
      let x=0,y=0,bu=0,re=0;
      for (let s=0;s<count;s++) {
        let next=(lo+0x7f4a7c15)>>>0; hi=(hi+0x9e3779b9+(next<lo?1:0))>>>0; lo=next;
        let zl=(lo ^ (lo>>>30) ^ (hi<<2))>>>0, zh=(hi ^ (hi>>>30))>>>0;
        let h=(high(zl,0x1ce4e5b9)+Math.imul(zh,0x1ce4e5b9)+Math.imul(zl,0xbf58476d))>>>0;
        zl=Math.imul(zl,0x1ce4e5b9)>>>0; zh=h;
        let l=(zl ^ (zl>>>27) ^ (zh<<5))>>>0; h=(zh ^ (zh>>>27))>>>0;
        zh=(high(l,0x133111eb)+Math.imul(h,0x133111eb)+Math.imul(l,0x94d049bb))>>>0;
        switch(zh>>>30) {
          case 0: if(x<bound) x++; else {bu++;continue;} break;
          case 1: if(x>-bound) x--; else {bu++;continue;} break;
          case 2: if(y<bound) y++; else {bu++;continue;} break;
          default: if(y>-bound) y--; else {bu++;continue;}
        }
        if(x===0 && y===0) re++;
      }
      const xx=BigInt(x), yy=BigInt(y), d=BigInt(Math.abs(x))+BigInt(Math.abs(y));
      spread+=xx*xx+yy*yy; bumps+=BigInt(bu); returns+=BigInt(re);
      if(d>distance) {distance=d;id=j;}
    }
  } else {
    for (let j=start;j<end;j++) {
      let state=(seed+j)&mask, x=0n,y=0n,bu=0n,re=0n;
      for(let s=0n;s<steps;s++) {
        state=(state+0x9e3779b97f4a7c15n)&mask;
        let z=state; z=((z^(z>>30n))*0xbf58476d1ce4e5b9n)&mask; z=((z^(z>>27n))*0x94d049bb133111ebn)&mask;
        switch(Number(z>>62n)) {
          case 0: if(x<b) x++; else {bu++;continue;} break;
          case 1: if(x> -b) x--; else {bu++;continue;} break;
          case 2: if(y<b) y++; else {bu++;continue;} break;
          default: if(y> -b) y--; else {bu++;continue;}
        }
        if(x===0n && y===0n) re++;
      }
      const d=(x<0n?-x:x)+(y<0n?-y:y); spread+=x*x+y*y; bumps+=bu;returns+=re;
      if(d>distance) {distance=d;id=j;}
    }
  }
  require('node:worker_threads').parentPort.postMessage({spread,bumps,returns,id,distance});
}
