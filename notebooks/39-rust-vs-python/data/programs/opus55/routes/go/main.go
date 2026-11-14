// Routes: Dijkstra from each source with a monotone radix heap on a CSR graph.
package main

import (
	"math"
	"math/bits"
	"os"
	"strconv"
)

func main() {
	buf, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	p := 0
	next := func() uint64 {
		for buf[p] < '0' || buf[p] > '9' {
			p++
		}
		x := uint64(buf[p] - '0')
		p++
		for p < len(buf) && buf[p] >= '0' && buf[p] <= '9' {
			x = x*10 + uint64(buf[p]-'0')
			p++
		}
		return x
	}

	n := int(next())
	m := int(next())
	q := int(next())

	eu := make([]int32, m)
	ev := make([]int32, m)
	ew := make([]int32, m)
	start := make([]int32, n+1)
	for i := 0; i < m; i++ {
		u, v, w := int32(next()), int32(next()), int32(next())
		eu[i], ev[i], ew[i] = u, v, w
		if u != v { // self-loops never shorten a path
			start[u+1]++
			start[v+1]++
		}
	}
	for i := 0; i < n; i++ {
		start[i+1] += start[i]
	}
	// Neighbours of u: adj[2k] (node), adj[2k+1] (length) for k in start[u]..start[u+1).
	adj := make([]int32, 2*int(start[n]))
	fill := make([]int32, n)
	copy(fill, start[:n])
	for i := 0; i < m; i++ {
		u, v, w := eu[i], ev[i], ew[i]
		if u == v {
			continue
		}
		pu := fill[u] << 1
		fill[u]++
		adj[pu], adj[pu+1] = v, w
		pv := fill[v] << 1
		fill[v]++
		adj[pv], adj[pv+1] = u, w
	}
	eu, ev, ew, fill = nil, nil, nil, nil

	shift := 0
	if n > 1 {
		shift = bits.Len32(uint32(n - 1))
	}
	dist := make([]uint64, n)
	var h radixHeap
	h.shift = uint(shift)
	out := make([]byte, 0, 64*q)
	for i := 0; i < q; i++ {
		s := int(next())
		out = solve(s, start, adj, dist, &h, out)
	}
	os.Stdout.Write(out)
}

// radixHeap holds keys packed as (dist << shift) | node, bucketed by the highest bit where dist differs from last.
type radixHeap struct {
	buckets [65][]uint64
	last    uint64
	size    int
	shift   uint
}

func (h *radixHeap) reset() {
	for i := range h.buckets {
		h.buckets[i] = h.buckets[i][:0]
	}
	h.last = 0
	h.size = 0
}

func (h *radixHeap) push(key uint64) {
	d := key >> h.shift
	b := 0
	if d != h.last {
		b = bits.Len64(d ^ h.last)
	}
	h.buckets[b] = append(h.buckets[b], key)
	h.size++
}

func (h *radixHeap) pop() uint64 {
	if len(h.buckets[0]) == 0 {
		i := 1
		for len(h.buckets[i]) == 0 {
			i++
		}
		a := h.buckets[i]
		mn := uint64(math.MaxUint64)
		for _, k := range a {
			if k < mn {
				mn = k
			}
		}
		last := mn >> h.shift
		h.last = last
		for _, k := range a {
			d := k >> h.shift
			b := 0
			if d != last {
				b = bits.Len64(d ^ last)
			}
			h.buckets[b] = append(h.buckets[b], k)
		}
		h.buckets[i] = a[:0]
	}
	h.size--
	b0 := h.buckets[0]
	k := b0[len(b0)-1]
	h.buckets[0] = b0[:len(b0)-1]
	return k
}

func solve(s int, start, adj []int32, dist []uint64, h *radixHeap, out []byte) []byte {
	sh := h.shift
	mask := uint64(1)<<sh - 1
	for i := range dist {
		dist[i] = math.MaxUint64
	}
	h.reset()
	dist[s] = 0
	h.push(uint64(s))
	var reach, total, far uint64
	farNode := s
	for h.size > 0 {
		key := h.pop()
		d := key >> sh
		u := int(key & mask)
		if d != dist[u] {
			continue
		}
		reach++
		total += d
		if d > far {
			far = d
			farNode = u
		} else if d == far && u < farNode {
			farNode = u
		}
		e := adj[start[u]<<1 : start[u+1]<<1]
		for k := 0; k+1 < len(e); k += 2 {
			v := e[k]
			nd := d + uint64(e[k+1])
			if nd < dist[v] {
				dist[v] = nd
				h.push(nd<<sh | uint64(v))
			}
		}
	}
	out = strconv.AppendInt(out, int64(s), 10)
	out = append(out, ' ')
	out = strconv.AppendUint(out, reach, 10)
	out = append(out, ' ')
	out = strconv.AppendUint(out, total, 10)
	out = append(out, ' ')
	out = strconv.AppendUint(out, far, 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(farNode), 10)
	return append(out, '\n')
}
