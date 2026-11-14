// Shortest paths from each source with Dial's bucket queue. Edge weights are 1..1000, so a ring of
// 1024 buckets replaces a heap: the bucket of distance d is d & 1023.
package main

import (
	"bufio"
	"fmt"
	"os"
)

const (
	buckets   = 1024 // greater than the largest weight (1000)
	nilEntry  = -1
	unreached = int64(1) << 62
)

type scanner struct {
	buf []byte
	pos int
}

func (s *scanner) next() int {
	b, p := s.buf, s.pos
	for p < len(b) && (b[p] < '0' || b[p] > '9') {
		p++
	}
	x := 0
	for p < len(b) && b[p] >= '0' && b[p] <= '9' {
		x = x*10 + int(b[p]-'0')
		p++
	}
	s.pos = p
	return x
}

type arc struct {
	to, w int32
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: solution INPUT_PATH")
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	in := &scanner{buf: data}
	n, m, q := in.next(), in.next(), in.next()

	// Two passes over the edge lines: the first counts degrees, the second fills the adjacency arrays.
	edgesAt := in.pos
	start := make([]int32, n+1)
	for i := 0; i < m; i++ {
		start[in.next()+1]++
		start[in.next()+1]++
		in.next()
	}
	for v := 0; v < n; v++ {
		start[v+1] += start[v]
	}

	arcs := make([]arc, 2*m)
	fill := make([]int32, n)
	copy(fill, start)
	in.pos = edgesAt
	for i := 0; i < m; i++ {
		u, v, w := in.next(), in.next(), int32(in.next())
		arcs[fill[u]] = arc{int32(v), w}
		fill[u]++
		arcs[fill[v]] = arc{int32(u), w}
		fill[v]++
	}

	dist := make([]int64, n)
	head := make([]int32, buckets)
	entNode := make([]int32, 2*m+1)
	entNext := make([]int32, 2*m+1)
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()

	for k := 0; k < q; k++ {
		s := in.next()
		for i := range dist {
			dist[i] = unreached
		}
		for i := range head {
			head[i] = nilEntry
		}

		used := int32(0)
		pending := 0
		dist[s] = 0
		entNode[used] = int32(s)
		entNext[used] = nilEntry
		head[0] = used
		used++
		pending++

		var reached, total, far int64
		node := int32(s)
		for cur := int64(0); pending > 0; cur++ {
			b := cur & (buckets - 1)
			e := head[b]
			head[b] = nilEntry
			for e != nilEntry {
				v := entNode[e]
				e = entNext[e]
				pending--
				if dist[v] != cur {
					continue
				}

				reached++
				total += cur
				if cur > far || (cur == far && v < node) {
					far = cur
					node = v
				}
				end := start[v+1]
				for i := start[v]; i < end; i++ {
					a := arcs[i]
					nd := cur + int64(a.w)
					if nd < dist[a.to] {
						dist[a.to] = nd
						nb := nd & (buckets - 1)
						entNode[used] = a.to
						entNext[used] = head[nb]
						head[nb] = used
						used++
						pending++
					}
				}
			}
		}
		fmt.Fprintf(out, "%d %d %d %d %d\n", s, reached, total, far, node)
	}
}
