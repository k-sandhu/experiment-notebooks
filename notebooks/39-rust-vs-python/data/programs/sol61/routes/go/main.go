package main

import (
	"bufio"
	"fmt"
	"math/bits"
	"os"
)

type scanner struct {
	data []byte
	pos  int
}

func (s *scanner) read() int32 {
	p, data := s.pos, s.data
	for data[p] <= ' ' {
		p++
	}
	var x int32
	for p < len(data) && data[p] >= '0' && data[p] <= '9' {
		x = x*10 + int32(data[p]-'0')
		p++
	}
	s.pos = p
	return x
}

// Intrusive circular buckets, with bitmap searches instead of scanning gaps.
type bucketQueue struct {
	head    [1024]int32
	masks   [32]uint32
	summary uint32
	current uint32
	next    []int32
	prev    []int32
}

func (q *bucketQueue) reset() {
	for i := range q.head {
		q.head[i] = -1
	}
	q.masks = [32]uint32{}
	q.summary, q.current = 0, 0
}

func (q *bucketQueue) insert(v int32, b uint32) {
	h := q.head[b]
	q.next[v], q.prev[v] = h, -1
	if h >= 0 {
		q.prev[h] = v
	} else {
		q.masks[b>>5] |= 1 << (b & 31)
		q.summary |= 1 << (b >> 5)
	}
	q.head[b] = v
}

func (q *bucketQueue) remove(v int32, b uint32) {
	p, n := q.prev[v], q.next[v]
	if p >= 0 {
		q.next[p] = n
	} else {
		q.head[b] = n
	}
	if n >= 0 {
		q.prev[n] = p
	}
	if q.head[b] < 0 {
		g := b >> 5
		q.masks[g] &^= 1 << (b & 31)
		if q.masks[g] == 0 {
			q.summary &^= 1 << g
		}
	}
}

func (q *bucketQueue) pop() int32 {
	b := q.current
	if q.head[b] < 0 {
		g := b >> 5
		word := q.masks[g] & (uint32(0xffffffff) << (b & 31))
		if word == 0 {
			groups := q.summary & (uint32(0xfffffffe) << g)
			if groups == 0 {
				groups = q.summary
			}
			g = uint32(bits.TrailingZeros32(groups))
			word = q.masks[g]
		}
		b = g<<5 + uint32(bits.TrailingZeros32(word))
		q.current = b
	}
	v := q.head[b]
	q.remove(v, b)
	return v
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	in := scanner{data: data}
	n, m, queries := int(in.read()), int(in.read()), int(in.read())
	edgeStart := in.pos
	offset := make([]int32, n+1)
	for i := 0; i < m; i++ {
		u, v := in.read(), in.read()
		in.read()
		if u != v {
			offset[u+1]++
			offset[v+1]++
		}
	}
	for i := 1; i <= n; i++ {
		offset[i] += offset[i-1]
	}
	to := make([]int32, int(offset[n]))
	weight := make([]uint16, len(to))
	queue := bucketQueue{next: make([]int32, n), prev: make([]int32, n)}
	copy(queue.next, offset[:n])
	in.pos = edgeStart
	for i := 0; i < m; i++ {
		u, v, w := in.read(), in.read(), in.read()
		if u == v {
			continue
		}
		a, b := queue.next[u], queue.next[v]
		queue.next[u]++
		queue.next[v]++
		to[a], weight[a] = v, uint16(w)
		to[b], weight[b] = u, uint16(w)
	}
	sources := make([]int32, queries)
	for i := range sources {
		sources[i] = in.read()
	}
	in.data, data = nil, nil
	dist := make([]int64, n)
	const infinity int64 = 1<<63 - 1
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	for _, s := range sources {
		for i := range dist {
			dist[i] = infinity
		}
		queue.reset()
		dist[s] = 0
		queue.insert(s, 0)
		var reached, total, far int64
		farNode := s
		for queue.summary != 0 {
			u := queue.pop()
			d := dist[u]
			reached++
			total += d
			if d > far {
				far, farNode = d, u
			} else if d == far && u < farNode {
				farNode = u
			}
			for e, end := offset[u], offset[u+1]; e < end; e++ {
				v := to[e]
				nd, old := d+int64(weight[e]), dist[v]
				if nd >= old {
					continue
				}
				if old != infinity {
					queue.remove(v, uint32(old)&1023)
				}
				dist[v] = nd
				queue.insert(v, uint32(nd)&1023)
			}
		}
		fmt.Fprintln(out, s, reached, total, far, farNode)
	}
}
