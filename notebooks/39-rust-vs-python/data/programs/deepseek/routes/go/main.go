package main

import (
	"math/bits"
	"os"
	"runtime/debug"
	"strconv"
)

type parser struct {
	data []byte
	pos  int
}

func (p *parser) nextInt() int {
	for p.data[p.pos] <= ' ' {
		p.pos++
	}
	x := 0
	for p.data[p.pos] > ' ' {
		x = x*10 + int(p.data[p.pos]-'0')
		p.pos++
	}
	return x
}

// Monotone circular bucket queue (Dial) with a bitset to skip empty ranges.
type dialQueue struct {
	nb      int
	words   int
	cur     int64
	bits    []uint64
	buckets [][]int
}

func (q *dialQueue) init(maxW int) {
	nb := maxW + 1
	if nb < 2 {
		nb = 2
	}
	q.nb = nb
	q.words = (nb + 63) >> 6
	q.bits = make([]uint64, q.words)
	q.buckets = make([][]int, nb)
	for i := range q.buckets {
		q.buckets[i] = make([]int, 0, 64)
	}
	q.cur = 0
}

func (q *dialQueue) clear() {
	for i := range q.buckets {
		q.buckets[i] = q.buckets[i][:0]
	}
	for i := range q.bits {
		q.bits[i] = 0
	}
	q.cur = 0
}

func (q *dialQueue) push(node, idx int) {
	q.buckets[idx] = append(q.buckets[idx], node)
	q.bits[idx>>6] |= uint64(1) << uint(idx&63)
}

func (q *dialQueue) nextSetBit(p int) int {
	wi := p >> 6
	w := q.bits[wi] & (^uint64(0) << uint(p&63))
	if w != 0 {
		return (wi << 6) + bits.TrailingZeros64(w)
	}
	for i := wi + 1; i < q.words; i++ {
		if q.bits[i] != 0 {
			return (i << 6) + bits.TrailingZeros64(q.bits[i])
		}
	}
	for i := 0; i < wi; i++ {
		if q.bits[i] != 0 {
			return (i << 6) + bits.TrailingZeros64(q.bits[i])
		}
	}
	low := q.bits[wi] & ((uint64(1) << uint(p&63)) - 1)
	if low != 0 {
		return (wi << 6) + bits.TrailingZeros64(low)
	}
	return -1
}

func runInt(N, Q int, src, off, at, aw []int32, maxW int, out []int64) {
	const INF int32 = 1<<31 - 1
	dist := make([]int32, N)
	q := &dialQueue{}
	q.init(maxW)
	nb := int32(q.nb)

	for qi := 0; qi < Q; qi++ {
		s := src[qi]
		for i := range dist {
			dist[i] = INF
		}
		q.clear()
		dist[s] = 0
		q.push(int(s), 0)

		var reach, total, far int64 = 0, 0, -1
		farNode := -1

		for {
			p := int(q.cur % int64(nb))
			idx := q.nextSetBit(p)
			if idx < 0 {
				break
			}
			offset := idx - p
			if offset < 0 {
				offset += int(nb)
			}
			q.cur += int64(offset)
			d := int32(q.cur)

			bk := q.buckets[idx]
			for len(bk) > 0 {
				u := bk[len(bk)-1]
				bk = bk[:len(bk)-1]
				if dist[u] != d {
					continue
				}

				reach++
				total += int64(d)
				if int64(d) > far {
					far = int64(d)
					farNode = u
				} else if int64(d) == far && u < farNode {
					farNode = u
				}

				end := int(off[u+1])
				for e := int(off[u]); e < end; e++ {
					v := at[e]
					w := aw[e]
					nd := d + w
					if nd < dist[v] {
						dist[v] = nd
						idx2 := idx + int(w)
						if idx2 >= int(nb) {
							idx2 -= int(nb)
						}
						q.push(int(v), idx2)
					}
				}
			}
			q.buckets[idx] = bk
			q.bits[idx>>6] &^= uint64(1) << uint(idx&63)
		}

		out[qi*5+0] = int64(s)
		out[qi*5+1] = reach
		out[qi*5+2] = total
		out[qi*5+3] = far
		out[qi*5+4] = int64(farNode)
	}
}

func runLong(N, Q int, src, off, at, aw []int32, maxW int, out []int64) {
	const INF int64 = 1<<63 - 1
	dist := make([]int64, N)
	q := &dialQueue{}
	q.init(maxW)
	nb := int64(q.nb)

	for qi := 0; qi < Q; qi++ {
		s := src[qi]
		for i := range dist {
			dist[i] = INF
		}
		q.clear()
		dist[s] = 0
		q.push(int(s), 0)

		var reach, total, far int64 = 0, 0, -1
		farNode := -1

		for {
			p := int(q.cur % nb)
			idx := q.nextSetBit(p)
			if idx < 0 {
				break
			}
			offset := idx - p
			if offset < 0 {
				offset += int(nb)
			}
			q.cur += int64(offset)
			d := q.cur

			bk := q.buckets[idx]
			for len(bk) > 0 {
				u := bk[len(bk)-1]
				bk = bk[:len(bk)-1]
				if dist[u] != d {
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

				end := int(off[u+1])
				for e := int(off[u]); e < end; e++ {
					v := at[e]
					w := aw[e]
					nd := d + int64(w)
					if nd < dist[v] {
						dist[v] = nd
						idx2 := idx + int(w)
						if idx2 >= int(nb) {
							idx2 -= int(nb)
						}
						q.push(int(v), idx2)
					}
				}
			}
			q.buckets[idx] = bk
			q.bits[idx>>6] &^= uint64(1) << uint(idx&63)
		}

		out[qi*5+0] = int64(s)
		out[qi*5+1] = reach
		out[qi*5+2] = total
		out[qi*5+3] = far
		out[qi*5+4] = int64(farNode)
	}
}

func main() {
	debug.SetGCPercent(-1)

	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	data = append(data, 0) // sentinel for the parser
	p := parser{data: data, pos: 0}

	N := p.nextInt()
	M := p.nextInt()
	Q := p.nextInt()

	eu := make([]int32, M)
	ev := make([]int32, M)
	ew := make([]int32, M)
	deg := make([]int32, N)
	maxW := 0

	for i := 0; i < M; i++ {
		u := p.nextInt()
		v := p.nextInt()
		w := p.nextInt()
		eu[i] = int32(u)
		ev[i] = int32(v)
		ew[i] = int32(w)
		deg[u]++
		deg[v]++
		if w > maxW {
			maxW = w
		}
	}

	off := make([]int32, N+1)
	acc := 0
	for i := 0; i < N; i++ {
		off[i] = int32(acc)
		acc += int(deg[i])
	}
	off[N] = int32(acc)

	at := make([]int32, acc)
	aw := make([]int32, acc)
	cur := make([]int32, N+1)
	copy(cur, off)
	for i := 0; i < M; i++ {
		u := eu[i]
		v := ev[i]
		w := ew[i]
		at[cur[u]] = v
		aw[cur[u]] = w
		cur[u]++
		at[cur[v]] = u
		aw[cur[v]] = w
		cur[v]++
	}

	src := make([]int32, Q)
	for i := 0; i < Q; i++ {
		src[i] = int32(p.nextInt())
	}

	eu = nil
	ev = nil
	ew = nil
	deg = nil
	cur = nil
	data = nil
	p.data = nil

	out := make([]int64, Q*5)
	if int64(N)*int64(maxW) < int64(1<<31-1) {
		runInt(N, Q, src, off, at, aw, maxW, out)
	} else {
		runLong(N, Q, src, off, at, aw, maxW, out)
	}

	buf := make([]byte, 0, 256)
	for qi := 0; qi < Q; qi++ {
		buf = buf[:0]
		buf = strconv.AppendInt(buf, out[qi*5], 10)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, out[qi*5+1], 10)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, out[qi*5+2], 10)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, out[qi*5+3], 10)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, out[qi*5+4], 10)
		buf = append(buf, '\n')
		os.Stdout.Write(buf)
	}
}
