package main

import (
	"bytes"
	"encoding/binary"
	"math/bits"
	"os"
	"runtime/debug"
	"slices"
	"strconv"
)

const (
	cDigit   = 1
	cWord    = 2
	cSlash   = 3
	idWord   = uint32('{') | uint32('i')<<8 | uint32('d')<<16 | uint32('}')<<24
	hashK    = 0x9E3779B97F4A7C15
	hashSeed = 0xA0761D6478BD642F
)

type tmpl struct {
	key  string
	hash uint64
	lats []uint64
}

type state struct {
	lines, good uint64
	status      [10]uint64
	templates   []tmpl
	table       []int32
	scratch     []byte
}

var cls [256]uint8
var tsP, tsM, tsA [3]uint64

func initTables() {
	for c := '0'; c <= '9'; c++ {
		cls[c] = cDigit
	}
	for c := 'a'; c <= 'z'; c++ {
		cls[c] = cWord
	}
	for c := 'A'; c <= 'Z'; c++ {
		cls[c] = cWord
	}
	cls['_'] = cWord
	cls['-'] = cWord
	cls['/'] = cSlash

	const tsPat = "0000-00-00T00:00:00.000Z"
	for w := 0; w < 3; w++ {
		for b := 0; b < 8; b++ {
			c := tsPat[w*8+b]
			sh := uint(b * 8)
			tsP[w] |= uint64(c) << sh
			if c == '0' {
				tsM[w] |= uint64(0xF0) << sh
				tsA[w] |= uint64(0x06) << sh
			} else {
				tsM[w] |= uint64(0xFF) << sh
			}
		}
	}
}

func rebuild(templates []tmpl, size int) []int32 {
	tb := make([]int32, size)
	mask := uint64(size - 1)
	for i := range templates {
		s := templates[i].hash & mask
		for tb[s] != 0 {
			s = (s + 1) & mask
		}
		tb[s] = int32(i + 1)
	}
	return tb
}

func (s *state) process(buf []byte) {
	p0, p1, p2 := tsP[0], tsP[1], tsP[2]
	m0, m1, m2 := tsM[0], tsM[1], tsM[2]
	a0, a1, a2 := tsA[0], tsA[1], tsA[2]
	lines, good := s.lines, s.good
	templates := s.templates
	table := s.table
	mask := uint64(len(table) - 1)
	sc := s.scratch
	status := &s.status
	pos := 0
	n := len(buf)
	for pos < n {
		rel := bytes.IndexByte(buf[pos:], '\n')
		if rel < 0 {
			break
		}
		ln := buf[pos : pos+rel+1]
		pos += rel + 1
		lines++
		if rel < 50 {
			continue
		}
		x0 := binary.LittleEndian.Uint64(ln) ^ p0
		x1 := binary.LittleEndian.Uint64(ln[8:]) ^ p1
		x2 := binary.LittleEndian.Uint64(ln[16:]) ^ p2
		if ((x0 & m0) | ((x0 + a0) & m0) | (x1 & m1) | ((x1 + a1) & m1) | (x2 & m2) | ((x2 + a2) & m2)) != 0 {
			continue
		}
		if ln[24] != ' ' {
			continue
		}
		i := 25
		// host
		j := i
		for ln[i]-'a' < 26 {
			i++
		}
		if i == j || ln[i] != '-' {
			continue
		}
		i++
		j = i
		for ln[i]-'0' < 10 {
			i++
		}
		if i == j || ln[i] != ' ' {
			continue
		}
		i++
		// method
		switch ln[i] {
		case 'G':
			if ln[i+1] != 'E' || ln[i+2] != 'T' || ln[i+3] != ' ' {
				continue
			}
			i += 4
		case 'P':
			switch ln[i+1] {
			case 'O':
				if ln[i+2] != 'S' || ln[i+3] != 'T' || ln[i+4] != ' ' {
					continue
				}
				i += 5
			case 'U':
				if ln[i+2] != 'T' || ln[i+3] != ' ' {
					continue
				}
				i += 4
			case 'A':
				if ln[i+2] != 'T' || ln[i+3] != 'C' || ln[i+4] != 'H' || ln[i+5] != ' ' {
					continue
				}
				i += 6
			default:
				continue
			}
		case 'D':
			if ln[i+1] != 'E' || ln[i+2] != 'L' || ln[i+3] != 'E' || ln[i+4] != 'T' || ln[i+5] != 'E' || ln[i+6] != ' ' {
				continue
			}
			i += 7
		default:
			continue
		}
		// path
		if ln[i] != '/' {
			continue
		}
		if need := len(ln)*4 + 16; need > len(sc) {
			sc = make([]byte, need*2)
		}
		t := 0
		seg := 0
		var flags uint8
		for {
			c := ln[i]
			k := cls[c]
			if k == 0 {
				break
			}
			sc[t] = c
			t++
			i++
			if k == cSlash {
				if flags == cDigit {
					binary.LittleEndian.PutUint32(sc[seg:], idWord)
					sc[seg+4] = '/'
					t = seg + 5
				}
				seg = t
				flags = 0
			} else {
				flags |= k
			}
		}
		if flags == cDigit {
			binary.LittleEndian.PutUint32(sc[seg:], idWord)
			t = seg + 4
		}
		// query
		if ln[i] == '?' {
			i++
			for {
				c := ln[i]
				if c == ' ' || c == '\n' {
					break
				}
				i++
			}
		}
		if ln[i] != ' ' {
			continue
		}
		i++
		// status
		d0 := ln[i] - '0'
		if d0 > 9 || ln[i+1]-'0' > 9 || ln[i+2]-'0' > 9 || ln[i+3] != ' ' {
			continue
		}
		i += 4
		// bytes
		j = i
		for ln[i]-'0' < 10 {
			i++
		}
		if i == j || ln[i] != 'B' || ln[i+1] != ' ' {
			continue
		}
		i += 2
		// latency
		var lat uint64
		j = i
		for {
			dd := ln[i] - '0'
			if dd > 9 {
				break
			}
			lat = lat*10 + uint64(dd)
			i++
		}
		if i == j || ln[i] != '.' {
			continue
		}
		d := ln[i+1] - '0'
		if d > 9 || ln[i+2] != 'm' || ln[i+3] != 's' || ln[i+4] != ' ' || ln[i+5] != '"' {
			continue
		}
		lat = lat*10 + uint64(d)
		i += 6
		end := rel
		if i >= end || ln[end-1] != '"' {
			continue
		}
		if bytes.IndexByte(ln[i:end-1], '"') >= 0 {
			continue
		}

		// well-formed
		good++
		status[d0]++

		binary.LittleEndian.PutUint64(sc[t:], 0)
		h := uint64(t) ^ hashSeed
		for o := 0; o < t; o += 8 {
			hi, lo := bits.Mul64(h^binary.LittleEndian.Uint64(sc[o:]), hashK)
			h = hi ^ lo
		}
		slot := h & mask
		var tp *tmpl
		for {
			idx := table[slot]
			if idx == 0 {
				templates = append(templates, tmpl{key: string(sc[:t]), hash: h})
				table[slot] = int32(len(templates))
				tp = &templates[len(templates)-1]
				if len(templates)*2 > len(table) {
					table = rebuild(templates, len(table)*2)
					mask = uint64(len(table) - 1)
				}
				break
			}
			e := &templates[idx-1]
			if e.hash == h && e.key == string(sc[:t]) {
				tp = e
				break
			}
			slot = (slot + 1) & mask
		}
		tp.lats = append(tp.lats, lat)
	}
	s.lines, s.good = lines, good
	s.templates = templates
	s.table = table
	s.scratch = sc
}

func better(a, b *tmpl) bool {
	if len(a.lats) != len(b.lats) {
		return len(a.lats) > len(b.lats)
	}
	return a.key < b.key
}

func appendTenths(b []byte, v uint64) []byte {
	b = strconv.AppendUint(b, v/10, 10)
	b = append(b, '.', byte('0'+v%10))
	return b
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
	initTables()
	s := &state{table: make([]int32, 1024), scratch: make([]byte, 1<<16)}
	buf := make([]byte, 1<<20)
	filled := 0
	for {
		n, rerr := f.Read(buf[filled:])
		if n > 0 {
			prev := filled
			filled += n
			last := bytes.LastIndexByte(buf[prev:filled], '\n')
			if last >= 0 {
				last += prev
				s.process(buf[:last+1])
				copy(buf, buf[last+1:filled])
				filled -= last + 1
			}
		}
		if rerr != nil {
			break
		}
		if filled == len(buf) {
			nb := make([]byte, len(buf)*2)
			copy(nb, buf[:filled])
			buf = nb
		}
	}
	f.Close()

	out := make([]byte, 0, 4096)
	out = append(out, "lines "...)
	out = strconv.AppendUint(out, s.lines, 10)
	out = append(out, "\nmalformed "...)
	out = strconv.AppendUint(out, s.lines-s.good, 10)
	out = append(out, '\n')
	for c := 0; c < 10; c++ {
		if s.status[c] > 0 {
			out = append(out, "status "...)
			out = append(out, byte('0'+c), 'x', 'x', ' ')
			out = strconv.AppendUint(out, s.status[c], 10)
			out = append(out, '\n')
		}
	}

	top := make([]*tmpl, 0, 11)
	for i := range s.templates {
		e := &s.templates[i]
		if len(top) == 10 && !better(e, top[9]) {
			continue
		}
		p := len(top)
		top = append(top, e)
		for p > 0 && better(e, top[p-1]) {
			top[p] = top[p-1]
			p--
		}
		top[p] = e
		if len(top) > 10 {
			top = top[:10]
		}
	}

	var cnt []uint32
	for _, e := range top {
		l := e.lats
		n := uint64(len(l))
		r50 := (50*n + 99) / 100
		r95 := (95*n + 99) / 100
		var mx uint64
		for _, v := range l {
			if v > mx {
				mx = v
			}
		}
		var p50, p95 uint64
		if mx < 1<<20 && n >= 256 {
			sz := int(mx) + 1
			if len(cnt) < sz {
				cnt = make([]uint32, sz)
			} else {
				clear(cnt[:sz])
			}
			c := cnt[:sz]
			for _, v := range l {
				c[v]++
			}
			var cum uint64
			got := false
			for v := 0; v < sz; v++ {
				cum += uint64(c[v])
				if !got && cum >= r50 {
					p50 = uint64(v)
					got = true
				}
				if cum >= r95 {
					p95 = uint64(v)
					break
				}
			}
		} else {
			slices.Sort(l)
			p50 = l[r50-1]
			p95 = l[r95-1]
		}
		out = append(out, "path "...)
		out = append(out, e.key...)
		out = append(out, ' ')
		out = strconv.AppendUint(out, n, 10)
		out = append(out, ' ')
		out = appendTenths(out, p50)
		out = append(out, ' ')
		out = appendTenths(out, p95)
		out = append(out, ' ')
		out = appendTenths(out, mx)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
