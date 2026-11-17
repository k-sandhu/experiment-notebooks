package main

import (
	"bytes"
	"os"
	"sort"
	"strconv"
)

func mix64(x uint64) uint64 {
	x += 0x9e3779b97f4a7c15
	x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9
	x = (x ^ (x >> 27)) * 0x94d049bb133111eb
	return x ^ (x >> 31)
}

var rankv []int

func better(c1, a1, b1, c2, a2, b2 int) bool {
	if c1 != c2 {
		return c1 > c2
	}
	if rankv[a1] != rankv[a2] {
		return rankv[a1] < rankv[a2]
	}
	return rankv[b1] < rankv[b2]
}
func findWorst(C, A, B []int, n int) int {
	w := 0
	for q := 1; q < n; q++ {
		if better(C[w], A[w], B[w], C[q], A[q], B[q]) {
			w = q
		}
	}
	return w
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n := len(data)

	wcap := 1024
	for wcap < (1<<17) && wcap*64 < n {
		wcap <<= 1
	}
	wtab := make([]int32, wcap)
	for i := range wtab {
		wtab[i] = -1
	}
	wmask := wcap - 1

	arena := make([]byte, 0, 1<<20)
	woff := make([]int, 0, 65536)
	wlen := make([]int, 0, 65536)
	whash := make([]uint64, 0, 65536)
	V := 0

	est := n/6 + 1024
	if est > (1 << 24) {
		est = 1 << 24
	}
	pairs := make([]uint64, 0, est)

	var W int64
	prev := -1
	i := 0
	for i < n {
		b := data[i]
		lo := b | 32
		if lo-97 < 26 {
			start := i
			h := uint64(14695981039346656037)
			for {
				h ^= uint64(lo)
				h *= 1099511628211
				i++
				if i >= n {
					break
				}
				b = data[i]
				lo = b | 32
				if lo-97 >= 26 {
					break
				}
			}
			length := i - start
			mh := mix64(h)
			idx := int(mh) & wmask
			var id int
			for {
				got := wtab[idx]
				if got < 0 {
					id = V
					V++
					wtab[idx] = int32(id)
					whash = append(whash, mh)
					woff = append(woff, len(arena))
					wlen = append(wlen, length)
					for k := 0; k < length; k++ {
						arena = append(arena, data[start+k]|32)
					}
					if V*4 > wcap*3 {
						ncap := wcap << 1
						nt := make([]int32, ncap)
						for t := range nt {
							nt[t] = -1
						}
						nmask := ncap - 1
						for wi := 0; wi < V; wi++ {
							j := int(whash[wi]) & nmask
							for nt[j] >= 0 {
								j = (j + 1) & nmask
							}
							nt[j] = int32(wi)
						}
						wtab = nt
						wcap = ncap
						wmask = nmask
					}
					break
				}
				id = int(got)
				if whash[id] == mh && wlen[id] == length {
					off := woff[id]
					eq := true
					for k := 0; k < length; k++ {
						if arena[off+k] != data[start+k]|32 {
							eq = false
							break
						}
					}
					if eq {
						break
					}
				}
				idx = (idx + 1) & wmask
			}
			W++
			if prev >= 0 {
				pairs = append(pairs, uint64(uint32(prev))<<32|uint64(uint32(id)))
			}
			prev = id
		} else {
			if b == '.' || b == '!' || b == '?' {
				prev = -1
			}
			i++
		}
	}
	T := int64(len(pairs))
	data = nil

	ids := make([]int, V)
	for k := range ids {
		ids[k] = k
	}
	sort.Slice(ids, func(x, y int) bool {
		a, b := ids[x], ids[y]
		return bytes.Compare(arena[woff[a]:woff[a]+wlen[a]], arena[woff[b]:woff[b]+wlen[b]]) < 0
	})
	rankv = make([]int, V)
	for k, id := range ids {
		rankv[id] = k
	}

	topC := make([]int, 20)
	topA := make([]int, 20)
	topB := make([]int, 20)
	topN, worst := 0, 0
	var D int64
	pc := len(pairs)
	if pc > 0 && V <= 65536 {
		keys := make([]uint32, pc)
		for k := 0; k < pc; k++ {
			v := pairs[k]
			keys[k] = uint32(v>>32)<<16 | uint32(v)
		}
		pairs = nil
		aux := make([]uint32, pc)
		src, dst := keys, aux
		cnt := make([]int, 65536)
		for shift := 0; shift < 32; shift += 16 {
			for k := range cnt {
				cnt[k] = 0
			}
			for k := 0; k < pc; k++ {
				cnt[(src[k]>>uint(shift))&0xFFFF]++
			}
			sum := 0
			for k := 0; k < 65536; k++ {
				t := cnt[k]
				cnt[k] = sum
				sum += t
			}
			for k := 0; k < pc; k++ {
				v := src[k]
				d := (v >> uint(shift)) & 0xFFFF
				dst[cnt[d]] = v
				cnt[d]++
			}
			src, dst = dst, src
		}
		k := 0
		for k < pc {
			j := k + 1
			v := src[k]
			for j < pc && src[j] == v {
				j++
			}
			c := j - k
			D++
			a := int(v >> 16)
			bb := int(v & 0xFFFF)
			if topN < 20 {
				topC[topN] = c
				topA[topN] = a
				topB[topN] = bb
				topN++
				if topN == 20 {
					worst = findWorst(topC, topA, topB, topN)
				}
			} else if better(c, a, bb, topC[worst], topA[worst], topB[worst]) {
				topC[worst] = c
				topA[worst] = a
				topB[worst] = bb
				worst = findWorst(topC, topA, topB, topN)
			}
			k = j
		}
	} else if pc > 0 {
		aux := make([]uint64, pc)
		src, dst := pairs, aux
		cnt := make([]int, 65536)
		for shift := 0; shift < 64; shift += 16 {
			for k := range cnt {
				cnt[k] = 0
			}
			for k := 0; k < pc; k++ {
				cnt[(src[k]>>uint(shift))&0xFFFF]++
			}
			sum := 0
			for k := 0; k < 65536; k++ {
				t := cnt[k]
				cnt[k] = sum
				sum += t
			}
			for k := 0; k < pc; k++ {
				v := src[k]
				d := (v >> uint(shift)) & 0xFFFF
				dst[cnt[d]] = v
				cnt[d]++
			}
			src, dst = dst, src
		}
		k := 0
		for k < pc {
			j := k + 1
			v := src[k]
			for j < pc && src[j] == v {
				j++
			}
			c := j - k
			D++
			a := int(v >> 32)
			bb := int(uint32(v))
			if topN < 20 {
				topC[topN] = c
				topA[topN] = a
				topB[topN] = bb
				topN++
				if topN == 20 {
					worst = findWorst(topC, topA, topB, topN)
				}
			} else if better(c, a, bb, topC[worst], topA[worst], topB[worst]) {
				topC[worst] = c
				topA[worst] = a
				topB[worst] = bb
				worst = findWorst(topC, topA, topB, topN)
			}
			k = j
		}
	}
	for a := 1; a < topN; a++ {
		c, x, y := topC[a], topA[a], topB[a]
		b := a - 1
		for b >= 0 && better(c, x, y, topC[b], topA[b], topB[b]) {
			topC[b+1] = topC[b]
			topA[b+1] = topA[b]
			topB[b+1] = topB[b]
			b--
		}
		topC[b+1] = c
		topA[b+1] = x
		topB[b+1] = y
	}

	var buf bytes.Buffer
	buf.WriteString("words ")
	buf.WriteString(strconv.FormatInt(W, 10))
	buf.WriteByte('\n')
	buf.WriteString("pairs ")
	buf.WriteString(strconv.FormatInt(T, 10))
	buf.WriteByte('\n')
	buf.WriteString("distinct ")
	buf.WriteString(strconv.FormatInt(D, 10))
	buf.WriteByte('\n')
	for k := 0; k < topN; k++ {
		buf.WriteString(strconv.Itoa(topC[k]))
		buf.WriteByte(' ')
		a := topA[k]
		buf.Write(arena[woff[a] : woff[a]+wlen[a]])
		buf.WriteByte(' ')
		b := topB[k]
		buf.Write(arena[woff[b] : woff[b]+wlen[b]])
		buf.WriteByte('\n')
	}
	os.Stdout.Write(buf.Bytes())
}
