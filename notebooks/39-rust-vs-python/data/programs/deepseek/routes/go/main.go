package main

import (
	"os"
	"strconv"
)

var data []byte
var pos int

func nextInt() int {
	a := data
	n := len(a)
	i := pos
	for i < n {
		c := int(a[i]) - 48
		if c >= 0 && c <= 9 {
			break
		}
		i++
	}
	x := 0
	for i < n {
		c := int(a[i]) - 48
		if c < 0 || c > 9 {
			break
		}
		x = x*10 + c
		i++
	}
	pos = i
	return x
}

var hp []uint64

func heapPush(x uint64) {
	h := append(hp, x)
	i := len(h) - 1
	for i > 0 {
		p := (i - 1) >> 1
		if h[p] <= x {
			break
		}
		h[i] = h[p]
		i = p
	}
	h[i] = x
	hp = h
}

func heapPop() uint64 {
	h := hp
	top := h[0]
	x := h[len(h)-1]
	h = h[:len(h)-1]
	n := len(h)
	if n > 0 {
		i := 0
		for {
			c := i*2 + 1
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
	hp = h
	return top
}

func main() {
	var err error
	data, err = os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}

	N := nextInt()
	M := nextInt()
	Q := nextInt()

	eu := make([]int32, M)
	ev := make([]int32, M)
	ew := make([]int32, M)
	deg := make([]int32, N+1)
	for i := 0; i < M; i++ {
		u := int32(nextInt())
		v := int32(nextInt())
		w := int32(nextInt())
		eu[i] = u
		ev[i] = v
		ew[i] = w
		deg[u]++
		deg[v]++
	}
	src := make([]int32, Q)
	for i := 0; i < Q; i++ {
		src[i] = int32(nextInt())
	}

	off := make([]int32, N+1)
	acc := int32(0)
	for i := 0; i < N; i++ {
		off[i] = acc
		acc += deg[i]
	}
	off[N] = acc

	fill := make([]int32, N+1)
	copy(fill, off)
	adj := make([]uint32, 2*M)
	for i := 0; i < M; i++ {
		u := eu[i]
		v := ev[i]
		w := ew[i]
		p := fill[u]
		adj[p] = uint32(v)<<10 | uint32(w)
		fill[u] = p + 1
		p = fill[v]
		adj[p] = uint32(u)<<10 | uint32(w)
		fill[v] = p + 1
	}
	eu = nil
	ev = nil
	ew = nil
	deg = nil
	fill = nil

	const INF int32 = 0x3f3f3f3f
	dist := make([]int32, N)

	shift := 0
	for (int64(1) << shift) < int64(N) {
		shift++
	}
	mask := uint64(1)<<shift - 1

	hp = make([]uint64, 0, 2*M+16)

	out := make([]byte, 0, 256)

	for qi := 0; qi < Q; qi++ {
		s := src[qi]
		for i := range dist {
			dist[i] = INF
		}
		hp = hp[:0]
		dist[s] = 0
		heapPush(uint64(s))

		total := int64(0)
		reach := 0
		far := int32(0)
		farNode := s

		for len(hp) > 0 {
			key := heapPop()
			v := int32(key & mask)
			d := int32(key >> shift)
			if d != dist[v] {
				continue
			}

			reach++
			total += int64(d)
			if d > far {
				far = d
				farNode = v
			}

			end := off[v+1]
			for e := off[v]; e < end; e++ {
				a := adj[e]
				u := int32(a >> 10)
				nd := d + int32(a&1023)
				if nd < dist[u] {
					dist[u] = nd
					heapPush(uint64(nd)<<shift | uint64(uint32(u)))
				}
			}
		}

		out = strconv.AppendInt(out, int64(s), 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, int64(reach), 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, total, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, int64(far), 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, int64(farNode), 10)
		out = append(out, '\n')
	}

	os.Stdout.Write(out)
}
