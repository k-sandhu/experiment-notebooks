package main

import (
	"math"
	"math/bits"
	"os"
	"strconv"
)

func readInt(data []byte, pos int) (int, int, bool) {
	for pos < len(data) && data[pos]-'0' > 9 {
		pos++
	}
	if pos >= len(data) {
		return 0, pos, false
	}
	v := 0
	for pos < len(data) {
		c := data[pos] - '0'
		if c > 9 {
			break
		}
		v = v*10 + int(c)
		pos++
	}
	return v, pos, true
}

func solve[T int32 | int64, E uint32 | uint64](n int, es []int32, off []uint32, wbits uint, sources []int, inf T) []byte {
	// prefix sums: off[u+1] becomes start of u
	for i := 2; i <= n+1; i++ {
		off[i] += off[i-1]
	}
	total := int(off[n+1])
	adj := make([]E, total)
	wmask := E(1)<<wbits - 1
	for i := 0; i+2 < len(es); i += 3 {
		u, v, w := es[i], es[i+1], es[i+2]
		if u == v {
			continue
		}
		p := off[u+1]
		adj[p] = E(v)<<wbits | E(w)
		off[u+1] = p + 1
		p = off[v+1]
		adj[p] = E(u)<<wbits | E(w)
		off[v+1] = p + 1
	}

	bb := wbits
	if bb < 6 {
		bb = 6
	}
	B := 1 << bb
	mask := B - 1
	nw := B >> 6
	buckets := make([][]int32, B)
	bm := make([]uint64, nw)
	dist := make([]T, n)

	out := make([]byte, 0, 64*len(sources)+16)

	for _, s := range sources {
		if s < 0 || s >= n {
			continue
		}
		for i := range dist {
			dist[i] = inf
		}
		dist[s] = 0
		buckets[0] = append(buckets[0][:0], int32(s))
		bm[0] |= 1

		var r int64
		var sum int64
		var far int64
		node := int32(s)
		idx := 0
		var d int64

		for {
			bk := buckets[idx]
			buckets[idx] = bk[:0]
			bm[idx>>6] &^= 1 << uint(idx&63)
			dT := T(d)
			for _, v := range bk {
				if dist[v] != dT {
					continue
				}
				r++
				sum += d
				if d > far {
					far = d
					node = v
				} else if d == far && v < node {
					node = v
				}
				for _, e := range adj[off[v]:off[v+1]] {
					to := int(e >> wbits)
					nd := dT + T(e&wmask)
					if nd < dist[to] {
						dist[to] = nd
						b := int(nd) & mask
						buckets[b] = append(buckets[b], int32(to))
						bm[b>>6] |= 1 << uint(b&63)
					}
				}
			}
			// find next non-empty bucket
			start := (idx + 1) & mask
			wi := start >> 6
			w := bm[wi] & (^uint64(0) << uint(start&63))
			found := -1
			if w != 0 {
				found = wi<<6 + bits.TrailingZeros64(w)
			} else {
				for k := 1; k <= nw; k++ {
					wj := (wi + k) & (nw - 1)
					if x := bm[wj]; x != 0 {
						found = wj<<6 + bits.TrailingZeros64(x)
						break
					}
				}
			}
			if found < 0 {
				break
			}
			d += int64((found - idx) & mask)
			idx = found
		}

		out = strconv.AppendInt(out, int64(s), 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, r, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, sum, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, far, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, int64(node), 10)
		out = append(out, '\n')
	}
	return out
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	pos := 0
	var n, m, q int
	n, pos, _ = readInt(data, pos)
	m, pos, _ = readInt(data, pos)
	q, pos, _ = readInt(data, pos)

	es := make([]int32, 3*m)
	off := make([]uint32, n+2)
	dl := len(data)
	maxW := 0
	for i := 0; i < m; i++ {
		for pos < dl && data[pos]-'0' > 9 {
			pos++
		}
		u := 0
		for pos < dl {
			c := data[pos] - '0'
			if c > 9 {
				break
			}
			u = u*10 + int(c)
			pos++
		}
		for pos < dl && data[pos]-'0' > 9 {
			pos++
		}
		v := 0
		for pos < dl {
			c := data[pos] - '0'
			if c > 9 {
				break
			}
			v = v*10 + int(c)
			pos++
		}
		for pos < dl && data[pos]-'0' > 9 {
			pos++
		}
		w := 0
		for pos < dl {
			c := data[pos] - '0'
			if c > 9 {
				break
			}
			w = w*10 + int(c)
			pos++
		}
		j := 3 * i
		es[j] = int32(u)
		es[j+1] = int32(v)
		es[j+2] = int32(w)
		if u != v {
			off[u+2]++
			off[v+2]++
			if w > maxW {
				maxW = w
			}
		}
	}

	sources := make([]int, 0, q)
	for i := 0; i < q; i++ {
		var s int
		var ok bool
		s, pos, ok = readInt(data, pos)
		if !ok {
			break
		}
		sources = append(sources, s)
	}

	wbits := uint(bits.Len(uint(maxW)))
	var out []byte
	if wbits <= 20 && n <= 1<<(32-wbits) && int64(n)*int64(maxW) < math.MaxInt32 {
		out = solve[int32, uint32](n, es, off, wbits, sources, math.MaxInt32)
	} else {
		out = solve[int64, uint64](n, es, off, wbits, sources, math.MaxInt64)
	}
	os.Stdout.Write(out)
}
