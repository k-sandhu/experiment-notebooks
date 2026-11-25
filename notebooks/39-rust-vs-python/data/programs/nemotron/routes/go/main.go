package main

import (
	"bufio"
	"fmt"
	"os"
	"math"
)

var (
	data []byte
	pos  int
	dataLen int
)

func readInt() int {
	for pos < dataLen && (data[pos] < '0' || data[pos] > '9') {
		pos++
	}
	x := 0
	for pos < dataLen && data[pos] >= '0' && data[pos] <= '9' {
		x = x*10 + int(data[pos]-'0')
		pos++
	}
	return x
}

func heapPop(h []uint64, n int) (uint64, int) {
	top := h[0]
	n--
	x := h[n]
	if n > 0 {
		i := 0
		h[0] = x
		for {
			c := 2*i + 1
			if c >= n {
				break
			}
			if c+1 < n && h[c+1] < h[c] {
				c++
			}
			if h[c] >= x {
				break
			}
			h[i] = h[c]
			i = c
		}
		h[i] = x
	}
	return top, n
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	var err error
	data, err = os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	dataLen = len(data)

	N := readInt()
	M := readInt()
	Q := readInt()

	eu := make([]int, M)
	ev := make([]int, M)
	ew := make([]int, M)
	deg := make([]int, N)
	for i := 0; i < M; i++ {
		u := readInt()
		v := readInt()
		w := readInt()
		eu[i] = u
		ev[i] = v
		ew[i] = w
		deg[u]++
		deg[v]++
	}

	off := make([]int, N + 1)
	for i := 0; i < N; i++ {
		off[i+1] = off[i] + deg[i]
	}
	to := make([]int, 2 * M)
	wt := make([]int, 2 * M)
	cur := make([]int, N)
	copy(cur, off[:N])
	for i := 0; i < M; i++ {
		u := eu[i]
		v := ev[i]
		w := ew[i]
		p := cur[u]
		cur[u]++
		to[p] = v
		wt[p] = w
		q := cur[v]
		cur[v]++
		to[q] = u
		wt[q] = w
	}

	sources := make([]int, Q)
	for i := 0; i < Q; i++ {
		sources[i] = readInt()
	}

	dist := make([]int, N)
	const inf = math.MaxInt32
	h := make([]uint64, 0, M + 1)
	hn := 0

	w := bufio.NewWriter(os.Stdout)
	for _, s := range sources {
		for i := range dist {
			dist[i] = inf
		}
		dist[s] = 0
		hn = 0
		h = h[:0]
		h, hn = heapPushAppend(h[:0], 0, (uint64(0)<<32)|uint64(s))

		for hn > 0 {
			var packed uint64
			packed, hn = heapPop(h, hn)
			d := int(packed >> 32)
			v := int(packed & 0xFFFFFFFF)
			if d > dist[v] {
				continue // stale entry
			}
			e0 := off[v]
			e1 := off[v+1]
			for e := e0; e < e1; e++ {
				t := to[e]
				nd := d + wt[e]
				if nd < dist[t] {
					dist[t] = nd
					h, hn = heapPushAppend(h, hn, (uint64(nd) << 32) | uint64(t))
				}
			}
		}

		reach := 0
		var total int64
		far := -1
		node := -1
		for v := 0; v < N; v++ {
			dv := dist[v]
			if dv != inf {
				reach++
				total += int64(dv)
				if dv > far {
					far = dv
					node = v
				}
			}
		}

		fmt.Fprintf(w, "%d %d %d %d %d\n", s, reach, total, far, node)
	}
	w.Flush()
}

func heapPushAppend(h []uint64, n int, x uint64) ([]uint64, int) {
	if n == len(h) {
		g := make([]uint64, n*2+1)
		copy(g, h[:n])
		h = g
	}
	i := n
	n++
	for i > 0 {
		p := (i - 1) / 2
		if h[p] <= x {
			break
		}
		h[i] = h[p]
		i = p
	}
	h[i] = x
	return h, n
}
