package main

import (
	"os"
	"strconv"
)

type parser struct {
	d   []byte
	pos int
}

func (p *parser) next() int64 {
	d := p.d
	n := len(d)
	i := p.pos
	for i < n && (d[i] < '0' || d[i] > '9') {
		i++
	}
	var v int64
	for i < n && d[i] >= '0' && d[i] <= '9' {
		v = v*10 + int64(d[i]-'0')
		i++
	}
	p.pos = i
	return v
}

// binary min-heap of (dist, node)
var hd []int64
var hn []int32

func hpush(d int64, v int32) {
	i := len(hd)
	hd = append(hd, d)
	hn = append(hn, v)
	for i > 0 {
		par := (i - 1) >> 2
		if hd[par] <= d {
			break
		}
		hd[i] = hd[par]
		hn[i] = hn[par]
		i = par
	}
	hd[i] = d
	hn[i] = v
}

func hpop() (int64, int32) {
	d := hd[0]
	v := hn[0]
	last := len(hd) - 1
	d0 := hd[last]
	v0 := hn[last]
	hd[0] = d0
	hn[0] = v0
	hd = hd[:last]
	hn = hn[:last]
	n := last
	i := 0
	x := d0
	for n > 0 {
		c := 4*i + 1
		m := i
		mv := x
		e := c + 4
		if e > n {
			e = n
		}
		for j := c; j < e; j++ {
			if hd[j] < mv {
				mv = hd[j]
				m = j
			}
		}
		if m == i {
			break
		}
		hd[i] = mv
		hn[i] = hn[m]
		i = m
	}
	if n > 0 {
		hd[i] = x
		hn[i] = v0
	}
	return d, v
}

func main() {
	data, _ := os.ReadFile(os.Args[1])
	p := &parser{d: data}

	n := int(p.next())
	m := int(p.next())
	q := int(p.next())

	eu := make([]int32, m)
	ev := make([]int32, m)
	ew := make([]int32, m)
	for i := 0; i < m; i++ {
		eu[i] = int32(p.next())
		ev[i] = int32(p.next())
		ew[i] = int32(p.next())
	}
	src := make([]int32, q)
	for i := 0; i < q; i++ {
		src[i] = int32(p.next())
	}

	// CSR adjacency (skip self-loops)
	off := make([]int32, n+1)
	for i := 0; i < m; i++ {
		if eu[i] != ev[i] {
			off[eu[i]]++
			off[ev[i]]++
		}
	}
	run := int32(0)
	for v := 0; v < n; v++ {
		d := off[v]
		off[v] = run
		run += d
	}
	off[n] = run
	adj := make([]int32, run)
	wt := make([]int32, run)
	pos := make([]int32, n)
	copy(pos, off)
	for i := 0; i < m; i++ {
		u := eu[i]
		v := ev[i]
		w := ew[i]
		if u == v {
			continue
		}
		adj[pos[u]] = v
		wt[pos[u]] = w
		pos[u]++
		adj[pos[v]] = u
		wt[pos[v]] = w
		pos[v]++
	}

	const INF = int64(1) << 60
	dist := make([]int64, n)
	hd = make([]int64, 0, 2*m+16)
	hn = make([]int32, 0, 2*m+16)

	obuf := make([]byte, 0, 1<<20)

	for qi := 0; qi < q; qi++ {
		s := src[qi]
		for v := range dist {
			dist[v] = INF
		}
		hd = hd[:0]
		hn = hn[:0]
		dist[s] = 0
		hpush(0, s)
		var total, far, cnt int64
		far = -1
		var farNode int32 = s

		for len(hd) > 0 {
			d, v := hpop()
			if d != dist[v] {
				continue
			}
			cnt++
			total += d
			if d > far || (d == far && v < farNode) {
				far = d
				farNode = v
			}
			for e := off[v]; e < off[v+1]; e++ {
				to := adj[e]
				nd := d + int64(wt[e])
				if nd < dist[to] {
					dist[to] = nd
					hpush(nd, to)
				}
			}
		}

		obuf = strconv.AppendInt(obuf, int64(s), 10)
		obuf = append(obuf, ' ')
		obuf = strconv.AppendInt(obuf, cnt, 10)
		obuf = append(obuf, ' ')
		obuf = strconv.AppendInt(obuf, total, 10)
		obuf = append(obuf, ' ')
		obuf = strconv.AppendInt(obuf, far, 10)
		obuf = append(obuf, ' ')
		obuf = strconv.AppendInt(obuf, int64(farNode), 10)
		obuf = append(obuf, '\n')
	}

	os.Stdout.Write(obuf)
}
