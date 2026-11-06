// Routes: shortest road distances from several sources.
// Multi-source Dijkstra (one run per source) over an undirected graph.
// Node.js, built-in modules only.
//
// Graph is stored in CSR form: start[node..node+1) indexes into gto/gw.
// Distances are int32 (JS doubles exactly represent ints up to 2^53).

'use strict';

const fs = require('fs');

const buf = fs.readFileSync(process.argv[2]); // Buffer
let pos = 0;
const len = buf.length;

function nextInt() {
	while (pos < len && buf[pos] <= 32) pos++;
	let neg = false;
	if (pos < len && buf[pos] === 0x2d) { // '-'
		neg = true;
		pos++;
	}
	let v = 0;
	while (pos < len && buf[pos] >= 0x30 && buf[pos] <= 0x39) {
		v = v * 10 + (buf[pos] - 0x30);
		pos++;
	}
	return neg ? -v : v;
}

const INF = 0x7fffffff;

const N = nextInt();
const M = nextInt();
const Q = nextInt();

const deg = new Int32Array(N + 1);
const eu = new Int32Array(M);
const ev = new Int32Array(M);
const ew = new Int32Array(M);
for (let i = 0; i < M; i++) {
	const u = nextInt();
	const v = nextInt();
	const w = nextInt();
	eu[i] = u;
	ev[i] = v;
	ew[i] = w;
	deg[u]++;
	deg[v]++;
}

const start = new Int32Array(N + 1);
for (let i = 0; i < N; i++) start[i + 1] = start[i] + deg[i];

const totalEdges = 2 * M;
const gto = new Int32Array(totalEdges);
const gw = new Int32Array(totalEdges);
const cur = new Int32Array(N);
for (let i = 0; i < N; i++) cur[i] = start[i];
for (let i = 0; i < M; i++) {
	const u = eu[i];
	const v = ev[i];
	const w = ew[i];
	let p = cur[u]++;
	gto[p] = v;
	gw[p] = w;
	p = cur[v]++;
	gto[p] = u;
	gw[p] = w;
}

const dist = new Int32Array(N);
const hd = [];
const hn = [];
let hsize = 0;

function push(d, n) {
	let i = hsize++;
	hd[i] = d;
	hn[i] = n;
	while (i > 0) {
		const p = (i - 1) >> 1;
		if (hd[p] <= d) break;
		hd[i] = hd[p];
		hn[i] = hn[p];
		i = p;
	}
	hd[i] = d;
	hn[i] = n;
}

const lines = [];
for (let q = 0; q < Q; q++) {
	const s = nextInt();
	for (let i = 0; i < N; i++) dist[i] = INF;
	dist[s] = 0;
	hsize = 0;
	push(0, s);
	while (hsize > 0) {
		let d = hd[0];
		let u = hn[0];
		--hsize;
		if (hsize > 0) {
			const lastD = hd[hsize];
			const lastN = hn[hsize];
			let i = 0;
			for (;;) {
				const l = 2 * i + 1;
				const r = l + 1;
				if (l >= hsize) break;
				let child = l;
				if (r < hsize && hd[r] < hd[l]) child = r;
				if (hd[child] >= lastD) break;
				hd[i] = hd[child];
				hn[i] = hn[child];
				i = child;
			}
			hd[i] = lastD;
			hn[i] = lastN;
		}
		if (d > dist[u]) continue;
		for (let e = start[u]; e < start[u + 1]; e++) {
			const v = gto[e];
			const nd = d + gw[e];
			if (nd < dist[v]) {
				dist[v] = nd;
				push(nd, v);
			}
		}
	}

	let R = 0;
	let total = 0;
	let far = -1;
	let node = -1;
	for (let i = 0; i < N; i++) {
		const d = dist[i];
		if (d !== INF) {
			R++;
			total += d;
			if (d > far) {
				far = d;
				node = i;
			}
		}
	}
	lines.push(`${s} ${R} ${total} ${far} ${node}`);
}

process.stdout.write(lines.join('\n') + '\n');
