package main

import (
	"bufio"
	"bytes"
	"os"
	"slices"
	"sort"
	"strconv"
)

type stat struct {
	tmpl  string
	count int64
	lat   []int32
}

func isd(c byte) bool { return c >= '0' && c <= '9' }

var (
	tbuf   = make([]byte, 512)
	tlen   int
	tenths int32
	cls    byte
	ps, pe int
)

// parse validates the line d[base:base+n] and fills ps, pe, tenths, cls, tbuf/tlen.
func parse(d []byte, base, n int) bool {
	if n < 50 {
		return false
	}
	i := base
	end := base + n
	// timestamp: dddd-dd-ddTdd:dd:dd.dddZ
	ts := d[i : i+24]
	for _, j := range [17]int{0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22} {
		if !isd(ts[j]) {
			return false
		}
	}
	if ts[4] != '-' || ts[7] != '-' || ts[10] != 'T' || ts[13] != ':' || ts[16] != ':' || ts[19] != '.' || ts[23] != 'Z' {
		return false
	}
	i += 24
	if d[i] != ' ' {
		return false
	}
	i++
	// host [a-z]+-\d+
	st := i
	for i < end && d[i] >= 'a' && d[i] <= 'z' {
		i++
	}
	if i == st || i >= end || d[i] != '-' {
		return false
	}
	i++
	st = i
	for i < end && isd(d[i]) {
		i++
	}
	if i == st || i >= end || d[i] != ' ' {
		return false
	}
	i++
	// method
	rem := end - i
	if rem >= 4 && string(d[i:i+4]) == "GET " {
		i += 4
	} else if rem >= 4 && string(d[i:i+4]) == "PUT " {
		i += 4
	} else if rem >= 5 && string(d[i:i+5]) == "POST " {
		i += 5
	} else if rem >= 6 && string(d[i:i+6]) == "PATCH " {
		i += 6
	} else if rem >= 7 && string(d[i:i+7]) == "DELETE " {
		i += 7
	} else {
		return false
	}
	if end-i < 17 {
		return false
	}
	if d[i] != '/' {
		return false
	}
	ps = i
	i++
	for i < end {
		c := d[i]
		if (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || isd(c) || c == '_' || c == '-' || c == '/' {
			i++
		} else {
			break
		}
	}
	pe = i
	if i < end && d[i] == '?' {
		i++
		for i < end && d[i] != ' ' {
			i++
		}
	}
	if i >= end || d[i] != ' ' {
		return false
	}
	i++
	if end-i < 15 {
		return false
	}
	if !isd(d[i]) || !isd(d[i+1]) || !isd(d[i+2]) {
		return false
	}
	cls = d[i] - '0'
	i += 3
	if d[i] != ' ' {
		return false
	}
	i++
	if end-i < 11 {
		return false
	}
	st = i
	for i < end && isd(d[i]) {
		i++
	}
	if i == st || d[i] != 'B' {
		return false
	}
	i++
	if d[i] != ' ' {
		return false
	}
	i++
	st = i
	var v int64
	nd := 0
	for i < end && isd(d[i]) {
		if nd < 15 {
			v = v*10 + int64(d[i]-'0')
		}
		i++
		nd++
	}
	if i == st || d[i] != '.' {
		return false
	}
	i++
	if !isd(d[i]) {
		return false
	}
	v = v*10 + int64(d[i]-'0')
	i++
	if d[i] != 'm' || d[i+1] != 's' || d[i+2] != ' ' {
		return false
	}
	if v > 0xFFFFFFFF {
		v = 0xFFFFFFFF
	}
	tenths = int32(v)
	i += 3
	if d[i] != '"' {
		return false
	}
	i++
	for i < end && d[i] != '"' {
		i++
	}
	if i+1 != end {
		return false
	}

	// build template
	need := (pe - ps) * 5 + 8
	if len(tbuf) < need {
		tbuf = make([]byte, need*2)
	}
	t := 0
	k := ps
	for k < pe {
		tbuf[t] = '/'
		t++
		k++
		s0 := k
		for k < pe && d[k] != '/' {
			k++
		}
		slen := k - s0
		dig := slen > 0
		for z := 0; dig && z < slen; z++ {
			if !isd(d[s0+z]) {
				dig = false
				break
			}
		}
		if dig {
			tbuf[t] = '{'
			tbuf[t+1] = 'i'
			tbuf[t+2] = 'd'
			tbuf[t+3] = '}'
			t += 4
		} else {
			copy(tbuf[t:], d[s0:k])
			t += slen
		}
	}
	tlen = t
	return true
}

func main() {
	d, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n := len(d)

	var lines, malformed int64
	var clsCount [10]int64
	stats := make(map[string]*stat, 256)

	i := 0
	for i < n {
		rel := bytes.IndexByte(d[i:], '\n') // SIMD-accelerated
		var le int
		if rel < 0 {
			le = n
		} else {
			le = i + rel
		}
		lines++
		if parse(d, i, le-i) {
			// map lookup with string([]byte) avoids allocation; only new templates allocate
			s, ok := stats[string(tbuf[:tlen])]
			if !ok {
				s = &stat{tmpl: string(tbuf[:tlen])}
				stats[string(tbuf[:tlen])] = s
			}
			s.count++
			s.lat = append(s.lat, tenths)
			clsCount[cls]++
		} else {
			malformed++
		}
		i = le + 1
	}

	entries := make([]*stat, 0, len(stats))
	for _, s := range stats {
		entries = append(entries, s)
	}
	sort.Slice(entries, func(a, b int) bool {
		if entries[a].count != entries[b].count {
			return entries[a].count > entries[b].count
		}
		return entries[a].tmpl < entries[b].tmpl
	})

	w := bufio.NewWriterSize(os.Stdout, 1<<16)
	nb := strconv.AppendInt(make([]byte, 0, 24), lines, 10)
	w.WriteString("lines ")
	w.Write(nb)
	w.WriteByte('\n')
	nb = strconv.AppendInt(nb[:0], malformed, 10)
	w.WriteString("malformed ")
	w.Write(nb)
	w.WriteByte('\n')
	for dd := 0; dd < 10; dd++ {
		if clsCount[dd] > 0 {
			w.WriteString("status ")
			w.WriteByte(byte('0' + dd))
			w.WriteString("xx ")
			nb = strconv.AppendInt(nb[:0], clsCount[dd], 10)
			w.Write(nb)
			w.WriteByte('\n')
		}
	}
	top := len(entries)
	if top > 10 {
		top = 10
	}
	for r := 0; r < top; r++ {
		s := entries[r]
		lat := s.lat
		slices.Sort(lat)
		nn := len(lat)
		p50 := lat[(50*nn+99)/100-1]
		p95 := lat[(95*nn+99)/100-1]
		mx := lat[nn-1]
		w.WriteString("path ")
		w.WriteString(s.tmpl)
		w.WriteByte(' ')
		nb = strconv.AppendInt(nb[:0], s.count, 10)
		w.Write(nb)
		for _, v := range [3]int32{p50, p95, mx} {
			w.WriteByte(' ')
			nb = strconv.AppendInt(nb[:0], int64(v/10), 10)
			w.Write(nb)
			w.WriteByte('.')
			w.WriteByte(byte('0' + v%10))
		}
		w.WriteByte('\n')
	}
	w.Flush()
}
