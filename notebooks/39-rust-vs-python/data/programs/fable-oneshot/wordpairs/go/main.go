package main

import (
	"bytes"
	"encoding/binary"
	"io"
	"math/bits"
	"os"
	"runtime/debug"
	"slices"
	"strconv"
)

const (
	lo20   = 0x2020202020202020
	c1F    = 0x1F1F1F1F1F1F1F1F
	c05    = 0x0505050505050505
	hi80   = 0x8080808080808080
	mulC   = 0x9E3779B97F4A7C15
	idMask = 0x7FFFFFFF
)

type entry struct {
	key uint64
	id  uint32
}

type state struct {
	data   []byte
	tab    []entry
	mask   uint64
	shift  uint
	nw     uint32
	growAt uint32
	arena  []byte
	wend   []int
	fc     []uint32
}

func (s *state) grow() {
	old := s.tab
	n := len(old) * 2
	tab := make([]entry, n)
	s.shift--
	s.mask = uint64(n - 1)
	shift, mask := s.shift, s.mask
	for _, e := range old {
		if e.key != 0 {
			h := (e.key * mulC) >> shift
			for tab[h].key != 0 {
				h = (h + 1) & mask
			}
			tab[h] = e
		}
	}
	s.tab = tab
	s.growAt = uint32(n / 10 * 7)
}

func (s *state) insert(key uint64) uint32 {
	if s.nw >= s.growAt {
		s.grow()
	}
	h := (key * mulC) >> s.shift
	for s.tab[h].key != 0 {
		h = (h + 1) & s.mask
	}
	s.nw++
	s.tab[h] = entry{key, s.nw}
	s.fc = append(s.fc, 0)
	return s.nw
}

func (s *state) addShort(key uint64) uint32 {
	for k := key; k != 0; k >>= 8 {
		s.arena = append(s.arena, byte(k))
	}
	s.wend = append(s.wend, len(s.arena))
	return s.insert(key)
}

func (s *state) same(id uint32, start, ln int) bool {
	end := s.wend[id]
	off := s.wend[id-1]
	if end-off != ln {
		return false
	}
	a := s.arena[off:end]
	d := s.data[start : start+ln]
	k := 0
	for ; k+8 <= ln; k += 8 {
		if binary.LittleEndian.Uint64(d[k:])|lo20 != binary.LittleEndian.Uint64(a[k:]) {
			return false
		}
	}
	if k < ln {
		k = ln - 8
		if binary.LittleEndian.Uint64(d[k:])|lo20 != binary.LittleEndian.Uint64(a[k:]) {
			return false
		}
	}
	return true
}

// long handles a word of at least 9 letters starting at i; lw is its first
// 8 letters, lower-cased.
func (s *state) long(i int, lw uint64) (uint32, int) {
	data := s.data
	start := i
	h := lw * mulC
	h ^= h >> 32
	j := i + 8
	for {
		w := binary.LittleEndian.Uint64(data[j:])
		l := w | lo20
		nl := ((l + c1F) &^ (l + c05) & hi80) ^ hi80
		if nl != 0 {
			sh := uint(bits.TrailingZeros64(nl)) & 56
			h = (h ^ (l & (uint64(1)<<sh - 1))) * mulC
			h ^= h >> 32
			j += int(sh >> 3)
			break
		}
		h = (h ^ l) * mulC
		h ^= h >> 32
		j += 8
	}
	key := h | 1<<63
	ln := j - start
	tab, mask := s.tab, s.mask
	p := (key * mulC) >> s.shift
	for {
		e := tab[p]
		if e.key == key && s.same(e.id, start, ln) {
			return e.id, j
		}
		if e.key == 0 {
			break
		}
		p = (p + 1) & mask
	}
	for k := start; k < j; k++ {
		s.arena = append(s.arena, data[k]|0x20)
	}
	s.wend = append(s.wend, len(s.arena))
	return s.insert(key), j
}

type pairCnt struct{ c, a, b uint32 }

type topk struct {
	s    *state
	n    int
	minC uint32
	e    [20]pairCnt
}

func (t *topk) word(id uint32) []byte {
	return t.s.arena[t.s.wend[id-1]:t.s.wend[id]]
}

func (t *topk) before(c, a, b uint32, y *pairCnt) bool {
	if c != y.c {
		return c > y.c
	}
	if a != y.a {
		return bytes.Compare(t.word(a), t.word(y.a)) < 0
	}
	return bytes.Compare(t.word(b), t.word(y.b)) < 0
}

func (t *topk) add(c, a, b uint32) {
	j := t.n
	if j == 20 {
		if !t.before(c, a, b, &t.e[19]) {
			return
		}
		j = 19
	} else {
		t.n++
	}
	for j > 0 && t.before(c, a, b, &t.e[j-1]) {
		t.e[j] = t.e[j-1]
		j--
	}
	t.e[j] = pairCnt{c, a, b}
	if t.n == 20 {
		t.minC = t.e[19].c
	}
}

func main() {
	debug.SetGCPercent(-1)
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	st, err := f.Stat()
	if err != nil {
		os.Exit(1)
	}
	size := int(st.Size())
	data := make([]byte, size+16)
	n, _ := io.ReadFull(f, data[:size])
	f.Close()

	var class [256]uint8
	for c := 'a'; c <= 'z'; c++ {
		class[c] = 1
		class[c-32] = 1
	}
	class['.'], class['!'], class['?'] = 2, 2, 2

	s := &state{data: data}
	s.tab = make([]entry, 1<<16)
	s.mask = 1<<16 - 1
	s.shift = 64 - 16
	s.growAt = (1 << 16) / 10 * 7
	s.wend = make([]int, 1, 1<<16)
	s.fc = make([]uint32, 1, 1<<16)
	s.arena = make([]byte, 0, 1<<19)

	tab, mask, shift, fc := s.tab, s.mask, s.shift, s.fc
	ids := make([]uint32, n/4+1024)
	m := 0
	var brk, prev uint32
	i := 0
	for i < n {
		cl := uint32(class[data[i]])
		if cl != 1 {
			brk |= cl
			i++
			continue
		}
		w := binary.LittleEndian.Uint64(data[i:])
		lw := w | lo20
		nl := ((lw + c1F) &^ (lw + c05) & hi80) ^ hi80
		var id uint32
		if nl == 0 && class[data[i+8]] == 1 {
			id, i = s.long(i, lw)
			tab, mask, shift, fc = s.tab, s.mask, s.shift, s.fc
		} else {
			sh := uint(bits.TrailingZeros64(nl)) &^ 7
			key := lw & (uint64(1)<<sh - 1)
			i += int(sh >> 3)
			h := (key * mulC) >> shift
			for {
				e := &tab[h]
				if e.key == key {
					id = e.id
					break
				}
				if e.key == 0 {
					id = s.addShort(key)
					tab, mask, shift, fc = s.tab, s.mask, s.shift, s.fc
					break
				}
				h = (h + 1) & mask
			}
		}
		if m == len(ids) {
			nids := make([]uint32, 2*len(ids))
			copy(nids, ids)
			ids = nids
		}
		ids[m] = id | brk<<30
		m++
		fc[prev&(brk>>1-1)]++
		brk = 0
		prev = id
	}

	fc = s.fc
	V := int(s.nw)
	var T uint64
	for _, c := range fc[1:] {
		T += uint64(c)
	}
	D := 0
	tk := &topk{s: s}

	if m > 0 {
		if V < 1<<21 {
			Tn := int(T)
			nb := uint(bits.Len32(uint32(V)))
			w1 := (nb + 1) / 2
			m1 := uint32(1)<<w1 - 1
			bm := uint32(1)<<nb - 1
			var pos1, pos2 [2048]uint32
			for a := 1; a <= V; a++ {
				c := fc[a]
				pos1[uint32(a)&m1] += c
				pos2[uint32(a)>>w1] += c
			}
			var s1, s2 uint32
			for k := range pos1 {
				c := pos1[k]
				pos1[k] = s1
				s1 += c
			}
			for k := range pos2 {
				c := pos2[k]
				pos2[k] = s2
				s2 += c
			}
			tmp := make([]uint32, Tn+1)
			bs := make([]uint32, Tn)
			tdum := uint32(Tn)

			a := ids[0] & idMask
			for _, x := range ids[1:m] {
				v := 1 - x>>31
				b := x & idMask
				d := (a & m1) & 2047
				p := pos1[d]
				pos1[d] = p + v
				mk := -v
				q := p&mk | tdum&^mk
				tmp[q] = (a>>(w1&31))<<(nb&31) | b
				a = b
			}
			for _, e := range tmp[:Tn] {
				h := (e >> (nb & 31)) & 2047
				p := pos2[h]
				pos2[h] = p + 1
				bs[p] = e & bm
			}

			cnt := make([]uint32, V+1)
			touched := make([]uint32, V+1)
			p := 0
			for a := 1; a <= V; a++ {
				g := int(fc[a])
				if g == 0 {
					continue
				}
				grp := bs[p : p+g]
				p += g
				nt := 0
				for _, b := range grp {
					c := cnt[b]
					touched[nt] = b
					nt += int((c - 1) >> 31)
					cnt[b] = c + 1
				}
				D += nt
				for _, b := range touched[:nt] {
					c := cnt[b]
					cnt[b] = 0
					if c >= tk.minC {
						tk.add(c, uint32(a), b)
					}
				}
			}
		} else {
			keys := make([]uint64, 0, int(T))
			a := ids[0] & idMask
			for _, x := range ids[1:m] {
				b := x & idMask
				if x>>31 == 0 {
					keys = append(keys, uint64(a)<<32|uint64(b))
				}
				a = b
			}
			slices.Sort(keys)
			for i := 0; i < len(keys); {
				k := keys[i]
				j := i + 1
				for j < len(keys) && keys[j] == k {
					j++
				}
				D++
				c := uint32(j - i)
				if c >= tk.minC {
					tk.add(c, uint32(k>>32), uint32(k))
				}
				i = j
			}
		}
	}

	out := make([]byte, 0, 4096)
	out = append(out, "words "...)
	out = strconv.AppendInt(out, int64(m), 10)
	out = append(out, "\npairs "...)
	out = strconv.AppendUint(out, T, 10)
	out = append(out, "\ndistinct "...)
	out = strconv.AppendInt(out, int64(D), 10)
	out = append(out, '\n')
	for k := 0; k < tk.n; k++ {
		e := tk.e[k]
		out = strconv.AppendUint(out, uint64(e.c), 10)
		out = append(out, ' ')
		out = append(out, tk.word(e.a)...)
		out = append(out, ' ')
		out = append(out, tk.word(e.b)...)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
