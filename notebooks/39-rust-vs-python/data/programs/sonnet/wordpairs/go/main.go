package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
)

const (
	pm    = 0x9E3779B97F4A7C15
	empty = ^uint64(0)
	none  = ^uint32(0)
	batch = 512
)

type wordInfo struct {
	start, len uint32
	hash       uint64
}

type wslot struct {
	id1, h uint32
}

type pslot struct {
	key   uint64
	count uint32
}

var (
	data   []byte
	words  []wordInfo
	wtab   []wslot
	wmask  uint32
	ptab   []pslot
	pmask  uint64
	pshift uint

	distinct uint64
	tcount   uint64
	sink     uint64
)

func growWords() {
	ncap := len(wtab) * 2
	nt := make([]wslot, ncap)
	nmask := uint32(ncap - 1)
	for id := range words {
		p := uint32(words[id].hash>>20) & nmask
		for nt[p].id1 != 0 {
			p = (p + 1) & nmask
		}
		nt[p] = wslot{uint32(id) + 1, uint32(words[id].hash)}
	}
	wtab = nt
	wmask = nmask
}

func lookupWord(start, length uint32, h uint64) uint32 {
	p := uint32(h>>20) & wmask
	h32 := uint32(h)
	s := data[start : start+length]
	for {
		sl := wtab[p]
		if sl.id1 == 0 {
			break
		}
		if sl.h == h32 {
			w := &words[sl.id1-1]
			if w.len == length {
				t := data[w.start : w.start+length]
				k := 0
				for k < len(s) && (s[k]^t[k])|0x20 == 0x20 {
					k++
				}
				if k == len(s) {
					return sl.id1 - 1
				}
			}
		}
		p = (p + 1) & wmask
	}
	id := uint32(len(words))
	words = append(words, wordInfo{start, length, h})
	wtab[p] = wslot{id + 1, h32}
	if len(words)*2 > len(wtab) {
		growWords()
	}
	return id
}

func growPairs() {
	ncap := len(ptab) * 2
	nshift := pshift - 1
	nt := make([]pslot, ncap)
	for i := range nt {
		nt[i].key = empty
	}
	nmask := uint64(ncap - 1)
	for _, s := range ptab {
		if s.key == empty {
			continue
		}
		p := (s.key * pm) >> nshift
		for nt[p].key != empty {
			p = (p + 1) & nmask
		}
		nt[p] = s
	}
	ptab = nt
	pshift = nshift
	pmask = nmask
}

// ids[0] is the previous word (or none); none marks a sentence end.
func flush(ids []uint32, cnt int) {
	var acc uint64
	for k := 1; k <= cnt; k++ {
		key := uint64(ids[k-1])<<32 | uint64(ids[k])
		acc += ptab[(key*pm)>>pshift].key
	}
	sink += acc
	for k := 1; k <= cnt; k++ {
		a, b := ids[k-1], ids[k]
		if a == none || b == none {
			continue
		}
		tcount++
		key := uint64(a)<<32 | uint64(b)
		p := (key * pm) >> pshift
		for {
			s := &ptab[p]
			if s.key == key {
				s.count++
				break
			}
			if s.key == empty {
				s.key = key
				s.count = 1
				distinct++
				if distinct*10 > uint64(len(ptab))*7 {
					growPairs()
				}
				break
			}
			p = (p + 1) & pmask
		}
	}
}

func cmpWords(x, y uint32) int {
	if x == y {
		return 0
	}
	wx, wy := words[x], words[y]
	a := data[wx.start : wx.start+wx.len]
	b := data[wy.start : wy.start+wy.len]
	n := len(a)
	if len(b) < n {
		n = len(b)
	}
	for i := 0; i < n; i++ {
		cx, cy := a[i]|0x20, b[i]|0x20
		if cx != cy {
			if cx < cy {
				return -1
			}
			return 1
		}
	}
	if len(a) < len(b) {
		return -1
	}
	if len(a) > len(b) {
		return 1
	}
	return 0
}

type top struct {
	count, a, b uint32
}

func better(x, y top) bool {
	if x.count != y.count {
		return x.count > y.count
	}
	if c := cmpWords(x.a, y.a); c != 0 {
		return c < 0
	}
	return cmpWords(x.b, y.b) < 0
}

func wordString(id uint32) string {
	w := words[id]
	b := make([]byte, w.len)
	for i := range b {
		b[i] = data[w.start+uint32(i)] | 0x20
	}
	return string(b)
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	var err error
	data, err = os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n := len(data)
	data = append(data, '\n')

	wtab = make([]wslot, 1<<16)
	wmask = 1<<16 - 1
	words = make([]wordInfo, 0, 1<<15)

	pcap := 1 << 16
	for pcap < n/12 && pcap < 1<<28 {
		pcap <<= 1
	}
	pshift = 64
	for t := pcap; t > 1; t >>= 1 {
		pshift--
	}
	pmask = uint64(pcap - 1)
	ptab = make([]pslot, pcap)
	for i := range ptab {
		ptab[i].key = empty
	}

	var W uint64
	var ids [batch + 1]uint32
	ids[0] = none
	cnt := 0
	i := 0
	for i < n {
		c := data[i]
		if (c|0x20)-'a' < 26 {
			st := i
			h := uint64(0xcbf29ce484222325)
			for (c|0x20)-'a' < 26 {
				h = (h ^ uint64(c|0x20)) * 0x100000001b3
				i++
				c = data[i]
			}
			h ^= h >> 29
			h *= pm
			h ^= h >> 32
			cnt++
			ids[cnt] = lookupWord(uint32(st), uint32(i-st), h)
			W++
			if cnt == batch {
				flush(ids[:], cnt)
				ids[0] = ids[batch]
				cnt = 0
			}
		} else {
			if c == '.' || c == '!' || c == '?' {
				if ids[cnt] != none {
					cnt++
					ids[cnt] = none
					if cnt == batch {
						flush(ids[:], cnt)
						ids[0] = ids[batch]
						cnt = 0
					}
				}
			}
			i++
		}
	}
	flush(ids[:], cnt)

	var tops [21]top
	nt := 0
	for q := range ptab {
		s := &ptab[q]
		if s.key == empty {
			continue
		}
		if nt == 20 && s.count < tops[19].count {
			continue
		}
		t := top{s.count, uint32(s.key >> 32), uint32(s.key)}
		if nt == 20 && !better(t, tops[19]) {
			continue
		}
		j := 19
		if nt < 20 {
			j = nt
			nt++
		}
		for j > 0 && better(t, tops[j-1]) {
			tops[j] = tops[j-1]
			j--
		}
		tops[j] = t
	}

	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	fmt.Fprintf(w, "words %d\npairs %d\ndistinct %d\n", W, tcount, distinct)
	for k := 0; k < nt; k++ {
		w.WriteString(strconv.FormatUint(uint64(tops[k].count), 10))
		w.WriteByte(' ')
		w.WriteString(wordString(tops[k].a))
		w.WriteByte(' ')
		w.WriteString(wordString(tops[k].b))
		w.WriteByte('\n')
	}
	if sink == 42 {
		w.WriteString("")
	}
}
