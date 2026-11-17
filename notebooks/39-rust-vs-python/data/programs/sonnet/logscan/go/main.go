package main

import (
	"bytes"
	"io"
	"os"
	"slices"
	"sort"
	"strconv"
)

type entry struct {
	off, length, count int32
	hash               uint64
}

var (
	arena     []byte
	entries   []entry
	table     []int32
	tableMask uint64
	recTid    []int32
	recLat    []int64
	tmpl      = make([]byte, 1024)

	lines, malformed uint64
	statusCount      [10]uint64
)

func growTable() {
	c := 1024
	if table != nil {
		c = len(table) * 2
	}
	table = make([]int32, c)
	for i := range table {
		table[i] = -1
	}
	tableMask = uint64(c - 1)
	for i := range entries {
		h := entries[i].hash & tableMask
		for table[h] >= 0 {
			h = (h + 1) & tableMask
		}
		table[h] = int32(i)
	}
}

func lookup(t []byte) int32 {
	h := uint64(14695981039346656037)
	for _, c := range t {
		h = (h ^ uint64(c)) * 1099511628211
	}
	h ^= h >> 29
	slot := h & tableMask
	for {
		id := table[slot]
		if id < 0 {
			break
		}
		e := &entries[id]
		if e.hash == h && int(e.length) == len(t) && bytes.Equal(arena[e.off:e.off+e.length], t) {
			return id
		}
		slot = (slot + 1) & tableMask
	}
	off := int32(len(arena))
	arena = append(arena, t...)
	entries = append(entries, entry{off: off, length: int32(len(t)), hash: h})
	id := int32(len(entries) - 1)
	if len(entries)*2 > len(table) {
		growTable()
	} else {
		table[slot] = id
	}
	return id
}

func dig(c byte) bool { return c-'0' < 10 }

func pathChar(c byte) bool {
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-'
}

func processLine(b []byte) {
	lines++
	if len(b) < 40 {
		malformed++
		return
	}
	if !(dig(b[0]) && dig(b[1]) && dig(b[2]) && dig(b[3]) && b[4] == '-' && dig(b[5]) &&
		dig(b[6]) && b[7] == '-' && dig(b[8]) && dig(b[9]) && b[10] == 'T' && dig(b[11]) &&
		dig(b[12]) && b[13] == ':' && dig(b[14]) && dig(b[15]) && b[16] == ':' && dig(b[17]) &&
		dig(b[18]) && b[19] == '.' && dig(b[20]) && dig(b[21]) && dig(b[22]) && b[23] == 'Z' &&
		b[24] == ' ') {
		malformed++
		return
	}
	e := len(b)
	p := 25
	q := p
	for q < e && b[q] >= 'a' && b[q] <= 'z' {
		q++
	}
	if q == p || q >= e || b[q] != '-' {
		malformed++
		return
	}
	q++
	p = q
	for q < e && dig(b[q]) {
		q++
	}
	if q == p || q >= e || b[q] != ' ' {
		malformed++
		return
	}
	p = q + 1
	if e-p < 8 {
		malformed++
		return
	}
	switch {
	case bytes.HasPrefix(b[p:], []byte("GET ")):
		p += 4
	case bytes.HasPrefix(b[p:], []byte("PUT ")):
		p += 4
	case bytes.HasPrefix(b[p:], []byte("POST ")):
		p += 5
	case bytes.HasPrefix(b[p:], []byte("PATCH ")):
		p += 6
	case bytes.HasPrefix(b[p:], []byte("DELETE ")):
		p += 7
	default:
		malformed++
		return
	}
	if p >= e || b[p] != '/' {
		malformed++
		return
	}
	pathStart := p
	p++
	for p < e && pathChar(b[p]) {
		p++
	}
	pathEnd := p
	if p >= e {
		malformed++
		return
	}
	if b[p] == '?' {
		p++
		for p < e && b[p] != ' ' {
			p++
		}
		if p >= e {
			malformed++
			return
		}
	}
	if b[p] != ' ' {
		malformed++
		return
	}
	p++
	if e-p < 5 || !(dig(b[p]) && dig(b[p+1]) && dig(b[p+2]) && b[p+3] == ' ') {
		malformed++
		return
	}
	cls := b[p] - '0'
	p += 4
	q = p
	for q < e && dig(b[q]) {
		q++
	}
	if q == p || e-q < 2 || b[q] != 'B' || b[q+1] != ' ' {
		malformed++
		return
	}
	p = q + 2
	var lat int64
	q = p
	for q < e && dig(b[q]) {
		lat = lat*10 + int64(b[q]-'0')
		q++
	}
	if q == p || e-q < 6 || b[q] != '.' || !dig(b[q+1]) || b[q+2] != 'm' || b[q+3] != 's' || b[q+4] != ' ' || b[q+5] != '"' {
		malformed++
		return
	}
	lat = lat*10 + int64(b[q+1]-'0')
	p = q + 6
	last := e - 1
	if p > last || b[last] != '"' || bytes.IndexByte(b[p:last], '"') >= 0 {
		malformed++
		return
	}

	statusCount[cls]++
	plen := pathEnd - pathStart
	if len(tmpl) < plen*4+8 {
		tmpl = make([]byte, plen*4+8)
	}
	t := tmpl
	o := 0
	t[o] = '/'
	o++
	segStart := o
	allDigits := true
	for c := pathStart + 1; ; c++ {
		if c == pathEnd || b[c] == '/' {
			if allDigits && o > segStart {
				o = segStart
				t[o], t[o+1], t[o+2], t[o+3] = '{', 'i', 'd', '}'
				o += 4
			}
			if c == pathEnd {
				break
			}
			t[o] = '/'
			o++
			segStart = o
			allDigits = true
		} else {
			ch := b[c]
			t[o] = ch
			o++
			allDigits = allDigits && dig(ch)
		}
	}
	id := lookup(t[:o])
	entries[id].count++
	recTid = append(recTid, id)
	recLat = append(recLat, lat)
}

func fmtLat(o []byte, v int64) []byte {
	o = strconv.AppendInt(o, v/10, 10)
	o = append(o, '.', byte('0'+v%10))
	return o
}

func main() {
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	growTable()
	recTid = make([]int32, 0, 1<<16)
	recLat = make([]int64, 0, 1<<16)
	buf := make([]byte, 1<<22)
	have := 0
	for {
		n, rerr := f.Read(buf[have:])
		eof := n == 0 && rerr != nil
		if rerr != nil && rerr != io.EOF {
			eof = true
		}
		have += n
		cur := 0
		for cur < have {
			idx := bytes.IndexByte(buf[cur:have], '\n')
			if idx < 0 {
				break
			}
			processLine(buf[cur : cur+idx])
			cur += idx + 1
		}
		if eof {
			if cur < have {
				processLine(buf[cur:have])
			}
			break
		}
		rest := have - cur
		if cur > 0 {
			copy(buf, buf[cur:have])
		}
		have = rest
		if have == len(buf) {
			nb := make([]byte, len(buf)*2)
			copy(nb, buf)
			buf = nb
		}
	}
	f.Close()

	o := make([]byte, 0, 4096)
	o = append(o, "lines "...)
	o = strconv.AppendUint(o, lines, 10)
	o = append(o, "\nmalformed "...)
	o = strconv.AppendUint(o, malformed, 10)
	o = append(o, '\n')
	for c := 0; c < 10; c++ {
		if statusCount[c] != 0 {
			o = append(o, "status "...)
			o = append(o, byte('0'+c))
			o = append(o, "xx "...)
			o = strconv.AppendUint(o, statusCount[c], 10)
			o = append(o, '\n')
		}
	}
	order := make([]int32, len(entries))
	for i := range order {
		order[i] = int32(i)
	}
	sort.Slice(order, func(i, j int) bool {
		a, b := &entries[order[i]], &entries[order[j]]
		if a.count != b.count {
			return a.count > b.count
		}
		return bytes.Compare(arena[a.off:a.off+a.length], arena[b.off:b.off+b.length]) < 0
	})
	top := min(10, len(order))
	var v []int64
	var hist []int32
	for k := 0; k < top; k++ {
		id := order[k]
		e := &entries[id]
		cnt := int(e.count)
		v = v[:0]
		var mx int64
		for i, t := range recTid {
			if t == id {
				x := recLat[i]
				v = append(v, x)
				if x > mx {
					mx = x
				}
			}
		}
		r50 := (50*cnt + 99) / 100
		r95 := (95*cnt + 99) / 100
		var p50, p95 int64 = -1, -1
		if mx < 1<<22 {
			if cap(hist) < int(mx)+1 {
				hist = make([]int32, mx+1)
			} else {
				hist = hist[:mx+1]
				clear(hist)
			}
			for _, x := range v {
				hist[x]++
			}
			acc := 0
			for b := int64(0); b <= mx; b++ {
				acc += int(hist[b])
				if p50 < 0 && acc >= r50 {
					p50 = b
				}
				if acc >= r95 {
					p95 = b
					break
				}
			}
		} else {
			slices.Sort(v)
			p50 = v[r50-1]
			p95 = v[r95-1]
		}
		o = append(o, "path "...)
		o = append(o, arena[e.off:e.off+e.length]...)
		o = append(o, ' ')
		o = strconv.AppendInt(o, int64(cnt), 10)
		o = append(o, ' ')
		o = fmtLat(o, p50)
		o = append(o, ' ')
		o = fmtLat(o, p95)
		o = append(o, ' ')
		o = fmtLat(o, mx)
		o = append(o, '\n')
	}
	os.Stdout.Write(o)
}
