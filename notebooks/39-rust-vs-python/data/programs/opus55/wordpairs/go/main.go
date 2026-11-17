// Word pairs: count adjacent word pairs within sentences, report the top 20.
//
//  1. Scan the input once. Words are found 8 bytes at a time (SWAR) and
//     interned to dense ids by an open-addressing table whose slots hold the
//     first 8 bytes of the word. The scan records the id sequence, with a flag
//     on each word that starts a sentence, and counts pairs per first word.
//  2. Counting-sort the pairs by first word (second words only).
//  3. For each first word, count its second words in a dense counter array
//     that stays in cache, and keep the 20 best pairs. Ties are broken by each
//     word's lexicographic rank, so the selection compares integers only.
package main

import (
	"bytes"
	"encoding/binary"
	"io"
	"math/bits"
	"os"
	"slices"
	"strconv"
)

const (
	ones   = 0x0101010101010101
	high   = 0x8080808080808080
	fold   = 0x2020202020202020
	kStart = 0x80000000 // flag: word starts a sentence
)

// letterMask sets the high bit of each byte of v (bytes < 0x80) that is an ASCII letter.
func letterMask(v uint64) uint64 {
	x := v | fold
	geA := x + 0x1F*ones // >= 0x80 iff x >= 'a'
	gtZ := x + 0x05*ones // >= 0x80 iff x > 'z'
	return geA &^ gtZ & high
}

// lowBytes is a mask covering the low n bytes.
func lowBytes(n int) uint64 {
	if n >= 8 {
		return ^uint64(0)
	}
	return 1<<(8*uint(n)) - 1
}

var class = func() (t [256]uint8) {
	for c := 'a'; c <= 'z'; c++ {
		t[c] = 1
		t[c-32] = 1
	}
	t['.'], t['!'], t['?'] = 2, 2, 2
	return
}()

type slot struct {
	prefix uint64 // first 8 lower-case bytes, zero padded
	hash   uint32
	id     uint32 // 0 = empty
}

type wordTable struct {
	slots []slot
	bits  uint
	mask  uint32
	off   []uint32 // per id, index 0 unused
	len   []uint32
}

func newWordTable() *wordTable {
	w := &wordTable{off: make([]uint32, 1, 1<<16), len: make([]uint32, 1, 1<<16)}
	w.resize(16)
	return w
}

func (w *wordTable) resize(b uint) {
	old := w.slots
	w.slots = make([]slot, 1<<b)
	w.bits = b
	w.mask = 1<<b - 1
	for _, s := range old {
		if s.id == 0 {
			continue
		}
		i := s.hash >> (32 - b)
		for w.slots[i].id != 0 {
			i = (i + 1) & w.mask
		}
		w.slots[i] = s
	}
}

// tailEq reports whether bytes 8..n of a (lower case) and b (any case) match, ignoring case.
func tailEq(a, b []byte, n int) bool {
	for j := 8; j < n; j += 8 {
		m := lowBytes(n - j)
		if (binary.LittleEndian.Uint64(a[j:])^(binary.LittleEndian.Uint64(b[j:])|fold))&m != 0 {
			return false
		}
	}
	return true
}

func (w *wordTable) intern(buf []byte, start, n int, prefix uint64, h uint32) uint32 {
	slots := w.slots
	mask := w.mask
	i := h >> (32 - w.bits)
	for {
		s := &slots[i]
		if s.id == 0 {
			break
		}
		if s.hash == h && s.prefix == prefix {
			if n < 8 {
				return s.id
			}
			if int(w.len[s.id]) == n && tailEq(buf[w.off[s.id]:], buf[start:], n) {
				return s.id
			}
		}
		i = (i + 1) & mask
	}
	id := uint32(len(w.off))
	for j := start; j < start+n; j++ {
		buf[j] |= 0x20 // lower-case the stored copy
	}
	w.off = append(w.off, uint32(start))
	w.len = append(w.len, uint32(n))
	slots[i] = slot{prefix, h, id}
	if uint64(id)*2 > uint64(len(slots)) {
		w.resize(w.bits + 1)
	}
	return id
}

type top struct {
	cnt, r1, r2, a, b uint32
}

// better reports whether x ranks before y in the output order.
func better(x, y *top) bool {
	if x.cnt != y.cnt {
		return x.cnt > y.cnt
	}
	if x.r1 != y.r1 {
		return x.r1 < y.r1
	}
	return x.r2 < y.r2
}

func main() {
	if len(os.Args) < 2 {
		os.Stderr.WriteString("usage: solution INPUT\n")
		os.Exit(1)
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Stderr.WriteString(err.Error() + "\n")
		os.Exit(1)
	}
	st, err := f.Stat()
	if err != nil {
		os.Stderr.WriteString(err.Error() + "\n")
		os.Exit(1)
	}
	buf := make([]byte, st.Size()+16) // zero padding: non-letters, safe 8-byte loads
	n, err := io.ReadFull(f, buf[:st.Size()])
	if err != nil {
		os.Stderr.WriteString(err.Error() + "\n")
		os.Exit(1)
	}
	f.Close()

	words := newWordTable()
	seq := make([]uint32, 0, n/2+2) // word id sequence; at most one word per two bytes, plus one
	deg := make([]uint32, 1, 1<<16)  // pairs per first word
	var totalPairs uint64
	var prev uint32 // previous word id in the current sentence, 0 = none

	i := 0
	for i < n {
		c := buf[i]
		if k := class[c]; k != 1 {
			if k == 2 {
				prev = 0
			}
			i++
			continue
		}
		// Word starting at i: fold case and hash it 8 bytes at a time.
		start := i
		v := binary.LittleEndian.Uint64(buf[i:])
		nl := ^letterMask(v) & high
		var prefix, h uint64
		if nl != 0 {
			k := bits.TrailingZeros64(nl) >> 3
			prefix = (v | fold) & lowBytes(k)
			h = prefix * 0x9E3779B97F4A7C15
			i += k
		} else {
			prefix = v | fold
			h = prefix * 0x9E3779B97F4A7C15
			i += 8
			for {
				v = binary.LittleEndian.Uint64(buf[i:])
				nl = ^letterMask(v) & high
				if nl != 0 {
					k := bits.TrailingZeros64(nl) >> 3
					if k != 0 {
						h = (h ^ ((v | fold) & lowBytes(k))) * 0xC2B2AE3D27D4EB4F
						i += k
					}
					break
				}
				h = (h ^ (v | fold)) * 0xC2B2AE3D27D4EB4F
				i += 8
			}
		}
		wl := i - start
		h ^= h >> 31
		h += uint64(wl)
		h *= 0xBF58476D1CE4E5B9
		id := words.intern(buf, start, wl, prefix, uint32(h>>32))
		if int(id) == len(deg) {
			deg = append(deg, 0)
		}
		if prev != 0 {
			deg[prev]++
			totalPairs++
			seq = append(seq, id)
		} else {
			seq = append(seq, id|kStart)
		}
		prev = id
	}
	totalWords := len(seq)
	nw := len(words.off) - 1

	// Bucket the second word of every pair by its first word.
	pos := make([]int, nw+2)
	for id := 1; id <= nw; id++ {
		pos[id+1] = pos[id] + int(deg[id])
	}
	fill := slices.Clone(pos)
	second := make([]uint32, totalPairs)
	for j := 1; j < len(seq); j++ {
		x := seq[j]
		if x&kStart == 0 {
			a := seq[j-1] &^ kStart
			second[fill[a]] = x
			fill[a]++
		}
	}
	seq = nil

	// Lexicographic rank of each word id.
	off, wlen := words.off, words.len
	order := make([]uint32, nw)
	for id := range order {
		order[id] = uint32(id + 1)
	}
	slices.SortFunc(order, func(a, b uint32) int {
		return bytes.Compare(buf[off[a]:off[a]+wlen[a]], buf[off[b]:off[b]+wlen[b]])
	})
	rank := make([]uint32, nw+1)
	for r, id := range order {
		rank[id] = uint32(r)
	}

	// Count second words per first word; keep the 20 best pairs.
	const K = 20
	var best [K]top
	nt := 0
	var distinct uint64
	cnt := make([]uint32, nw+1)
	for a := 1; a <= nw; a++ {
		seg := second[pos[a]:pos[a+1]]
		if len(seg) == 0 {
			continue
		}
		for _, b := range seg {
			cnt[b]++
		}
		for _, b := range seg {
			c := cnt[b]
			if c == 0 {
				continue
			}
			cnt[b] = 0
			distinct++
			if nt == K && c < best[K-1].cnt {
				continue
			}
			t := top{c, rank[a], rank[b], uint32(a), b}
			if nt == K && !better(&t, &best[K-1]) {
				continue
			}
			p := K - 1
			if nt < K {
				p = nt
				nt++
			}
			for p > 0 && better(&t, &best[p-1]) {
				best[p] = best[p-1]
				p--
			}
			best[p] = t
		}
	}

	out := make([]byte, 0, 4096)
	out = append(out, "words "...)
	out = strconv.AppendInt(out, int64(totalWords), 10)
	out = append(out, "\npairs "...)
	out = strconv.AppendUint(out, totalPairs, 10)
	out = append(out, "\ndistinct "...)
	out = strconv.AppendUint(out, distinct, 10)
	out = append(out, '\n')
	for _, t := range best[:nt] {
		out = strconv.AppendUint(out, uint64(t.cnt), 10)
		out = append(out, ' ')
		out = append(out, buf[off[t.a]:off[t.a]+wlen[t.a]]...)
		out = append(out, ' ')
		out = append(out, buf[off[t.b]:off[t.b]+wlen[t.b]]...)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
