package main

import (
	"os"
	"strconv"
)

var buf []byte
var pos int

func readInt() int {
	for buf[pos] < '0' {
		pos++
	}
	x := 0
	for pos < len(buf) && buf[pos] >= '0' {
		x = x*10 + int(buf[pos]-'0')
		pos++
	}
	return x
}

func main() {
	var err error
	buf, err = os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n, m, q := readInt(), readInt(), readInt()
	eu := make([]int32, m)
	ev := make([]int32, m)
	ew := make([]int32, m)
	start := make([]int32, n+2)
	for i := 0; i < m; i++ {
		u, v, w := readInt(), readInt(), readInt()
		eu[i], ev[i], ew[i] = int32(u), int32(v), int32(w)
		if u != v {
			start[u+2]++
			start[v+2]++
		}
	}
	for i := 2; i <= n+1; i++ {
		start[i] += start[i-1]
	}
	adj := make([]int32, start[n+1])
	for i := 0; i < m; i++ {
		u, v, w := eu[i], ev[i], ew[i]
		if u == v {
			continue
		}
		adj[start[u+1]] = v*1024 + w
		start[u+1]++
		adj[start[v+1]] = u*1024 + w
		start[v+1]++
	}
	const inf = int64(0x7fffffffffffffff)
	dist := make([]int64, n)
	h := make([]uint64, len(adj)+2)
	out := make([]byte, 0, 256)
	for qi := 0; qi < q; qi++ {
		s := readInt()
		for i := range dist {
			dist[i] = inf
		}
		dist[s] = 0
		h[0] = uint64(s)
		hs := 1
		for hs > 0 {
			top := h[0]
			hs--
			last := h[hs]
			if hs > 0 {
				i := 0
				for {
					c := 2*i + 1
					if c >= hs {
						break
					}
					if c+1 < hs && h[c+1] < h[c] {
						c++
					}
					if h[c] >= last {
						break
					}
					h[i] = h[c]
					i = c
				}
				h[i] = last
			}
			u := int(top & 0xffffffff)
			d := int64(top >> 32)
			if d != dist[u] {
				continue
			}
			for e, ee := start[u], start[u+1]; e < ee; e++ {
				x := adj[e]
				v := int(x >> 10)
				nd := d + int64(x&1023)
				if nd < dist[v] {
					dist[v] = nd
					key := uint64(nd)<<32 | uint64(v)
					i := hs
					hs++
					for i > 0 {
						par := (i - 1) >> 1
						if h[par] <= key {
							break
						}
						h[i] = h[par]
						i = par
					}
					h[i] = key
				}
			}
		}
		var total, far, cnt int64
		for _, d := range dist {
			if d != inf {
				cnt++
				total += d
				if d > far {
					far = d
				}
			}
		}
		node := 0
		for i, d := range dist {
			if d == far {
				node = i
				break
			}
		}
		out = strconv.AppendInt(out, int64(s), 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, cnt, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, total, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, far, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, int64(node), 10)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
