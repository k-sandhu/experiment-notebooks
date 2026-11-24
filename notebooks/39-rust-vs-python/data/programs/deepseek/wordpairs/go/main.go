package main

import (
	"encoding/binary"
	"os"
	"runtime/debug"
	"strconv"
)

var lower [256]byte

var buf []byte
var tab []uint64
var mask uint32
var nWords int
var wOff = make([]int32, 0, 1<<16)
var wLen = make([]int32, 0, 1<<16)

func mixKey(p0, p1 uint64, length int) uint64 {
	h := p0 * 0x9E3779B97F4A7C15
	h ^= (p1 + uint64(length)) * 0xC2B2AE3D27D4EB4F
	h ^= h >> 29
	h *= 0xBF58476D1CE4E5B9
	h ^= h >> 32
	return h
}

func rehash(slots int) {
	t := make([]uint64, slots*3)
	for i := range t {
		t[i] = ^uint64(0)
	}
	m := uint32(slots - 1)
	oldSlots := len(tab) / 3
	for s := 0; s < oldSlots; s++ {
		idl := tab[s*3+2]
		if int32(idl) < 0 {
			continue
		}
		p0 := tab[s*3]
		p1 := tab[s*3+1]
		length := int(idl >> 32)
		idx := uint32(mixKey(p0, p1, length)) & m
		for int32(t[idx*3+2]) >= 0 {
			idx = (idx + 1) & m
		}
		t[idx*3] = p0
		t[idx*3+1] = p1
		t[idx*3+2] = idl
	}
	tab = t
	mask = m
}

func eqTail(a, b int32, length int32) bool {
	d := buf
	for i := int32(16); i < length; i++ {
		if d[a+i] != d[b+i] {
			return false
		}
	}
	return true
}

func intern(p0, p1 uint64, length int, off int32) int32 {
	idx := uint32(mixKey(p0, p1, length)) & mask
	for {
		idl := tab[idx*3+2]
		id := int32(idl)
		if id < 0 {
			break
		}
		if int(idl>>32) == length && tab[idx*3] == p0 && tab[idx*3+1] == p1 {
			if length <= 16 || eqTail(wOff[id], off, int32(length)) {
				return id
			}
		}
		idx = (idx + 1) & mask
	}
	id := int32(nWords)
	nWords++
	wOff = append(wOff, off)
	wLen = append(wLen, int32(length))
	tab[idx*3] = p0
	tab[idx*3+1] = p1
	tab[idx*3+2] = uint64(uint32(length))<<32 | uint64(uint32(id))
	if nWords*10 > (len(tab)/3)*7 {
		rehash((len(tab) / 3) * 2)
	}
	return id
}

func cmpWord(x, y int32) int32 {
	ox, oy := wOff[x], wOff[y]
	lx, ly := wLen[x], wLen[y]
	l := lx
	if ly < l {
		l = ly
	}
	d := buf
	for i := int32(0); i < l; i++ {
		a, b := d[ox+i], d[oy+i]
		if a != b {
			return int32(a) - int32(b)
		}
	}
	return lx - ly
}

func better(c1 int32, a1, a2 int32, c2 int32, b1, b2 int32) bool {
	if c1 != c2 {
		return c1 > c2
	}
	c := cmpWord(a1, b1)
	if c != 0 {
		return c < 0
	}
	return cmpWord(a2, b2) < 0
}

func worse(c1 int32, a1, a2 int32, c2 int32, b1, b2 int32) bool {
	return better(c2, b1, b2, c1, a1, a2)
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	debug.SetGCPercent(-1)

	for c := byte('a'); c <= 'z'; c++ {
		lower[c] = c
	}
	for c := byte('A'); c <= 'Z'; c++ {
		lower[c] = c + 32
	}

	raw, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	buf = make([]byte, len(raw)+16)
	copy(buf, raw)
	raw = nil
	n := len(buf) - 16

	tab = make([]uint64, 4096*3)
	for i := range tab {
		tab[i] = ^uint64(0)
	}
	mask = 4095

	capPairs := n/6 + 1024
	if capPairs < 1024 {
		capPairs = 1024
	}
	pairs := make([]uint64, 0, capPairs)

	prev := int32(-1)
	var W, T int64
	i := 0

	for i < n {
		lc := lower[buf[i]]
		if lc != 0 {
			start := i
			for {
				buf[i] = lc
				i++
				if i < n {
					lc = lower[buf[i]]
					if lc != 0 {
						continue
					}
				}
				break
			}
			length := i - start

			r0 := binary.LittleEndian.Uint64(buf[start:])
			var p0 uint64
			if length >= 8 {
				p0 = r0
			} else {
				p0 = r0 & ((uint64(1) << uint(8*length)) - 1)
			}
			var p1 uint64
			if length > 8 {
				r1 := binary.LittleEndian.Uint64(buf[start+8:])
				rem := length - 8
				if rem >= 8 {
					p1 = r1
				} else {
					p1 = r1 & ((uint64(1) << uint(8*rem)) - 1)
				}
			}

			id := intern(p0, p1, length, int32(start))
			W++
			if prev >= 0 {
				pairs = append(pairs, uint64(uint32(prev))<<32|uint64(uint32(id)))
				T++
			}
			prev = id
		} else {
			c := buf[i]
			if c == '.' || c == '!' || c == '?' {
				prev = -1
			}
			i++
		}
	}

	np := len(pairs)
	keys := pairs
	if np > 1 {
		var orAll uint64
		for k := 0; k < np; k++ {
			orAll |= pairs[k]
		}
		tmp := make([]uint64, np)
		src := pairs
		dst := tmp
		cnt := make([]int32, 256)
		for pass := 0; pass < 8; pass++ {
			shift := uint(pass * 8)
			if ((orAll >> shift) & 0xFF) == 0 {
				continue
			}
			for d := range cnt {
				cnt[d] = 0
			}
			for k := 0; k < np; k++ {
				cnt[(src[k]>>shift)&0xFF]++
			}
			var sum int32
			for d := 0; d < 256; d++ {
				c := cnt[d]
				cnt[d] = sum
				sum += c
			}
			for k := 0; k < np; k++ {
				key := src[k]
				d := (key >> shift) & 0xFF
				dst[cnt[d]] = key
				cnt[d]++
			}
			src, dst = dst, src
		}
		keys = src
	}

	var bestC [20]int32
	var bestA [20]int32
	var bestB [20]int32
	bn := 0
	var distinct int64

	for k := 0; k < np; {
		j := k + 1
		key := keys[k]
		for j < np && keys[j] == key {
			j++
		}
		c := int32(j - k)
		a := int32(key >> 32)
		b2 := int32(key & 0xFFFFFFFF)
		if bn < 20 {
			bestC[bn], bestA[bn], bestB[bn] = c, a, b2
			idx := bn
			bn++
			for idx > 0 {
				p := (idx - 1) >> 1
				if worse(bestC[idx], bestA[idx], bestB[idx], bestC[p], bestA[p], bestB[p]) {
					bestC[idx], bestC[p] = bestC[p], bestC[idx]
					bestA[idx], bestA[p] = bestA[p], bestA[idx]
					bestB[idx], bestB[p] = bestB[p], bestB[idx]
					idx = p
				} else {
					break
				}
			}
		} else if better(c, a, b2, bestC[0], bestA[0], bestB[0]) {
			bestC[0], bestA[0], bestB[0] = c, a, b2
			idx := 0
			for {
				l, r, w := 2*idx+1, 2*idx+2, idx
				if l < bn && worse(bestC[l], bestA[l], bestB[l], bestC[w], bestA[w], bestB[w]) {
					w = l
				}
				if r < bn && worse(bestC[r], bestA[r], bestB[r], bestC[w], bestA[w], bestB[w]) {
					w = r
				}
				if w == idx {
					break
				}
				bestC[idx], bestC[w] = bestC[w], bestC[idx]
				bestA[idx], bestA[w] = bestA[w], bestA[idx]
				bestB[idx], bestB[w] = bestB[w], bestB[idx]
				idx = w
			}
		}
		distinct++
		k = j
	}

	for q := 1; q < bn; q++ {
		cq, aq, bq := bestC[q], bestA[q], bestB[q]
		r := q - 1
		for r >= 0 && better(cq, aq, bq, bestC[r], bestA[r], bestB[r]) {
			bestC[r+1], bestA[r+1], bestB[r+1] = bestC[r], bestA[r], bestB[r]
			r--
		}
		bestC[r+1], bestA[r+1], bestB[r+1] = cq, aq, bq
	}

	out := make([]byte, 0, 512)
	out = append(out, "words "...)
	out = strconv.AppendInt(out, W, 10)
	out = append(out, "\npairs "...)
	out = strconv.AppendInt(out, T, 10)
	out = append(out, "\ndistinct "...)
	out = strconv.AppendInt(out, distinct, 10)
	out = append(out, '\n')
	for q := 0; q < bn; q++ {
		out = strconv.AppendInt(out, int64(bestC[q]), 10)
		out = append(out, ' ')
		out = append(out, buf[wOff[bestA[q]]:wOff[bestA[q]]+wLen[bestA[q]]]...)
		out = append(out, ' ')
		out = append(out, buf[wOff[bestB[q]]:wOff[bestB[q]]+wLen[bestB[q]]]...)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
