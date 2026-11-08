package main

import (
	"bytes"
	"os"
	"slices"
	"sort"
	"strconv"
)

var (
	mGET    = []byte("GET ")
	mPOST   = []byte("POST ")
	mPUT    = []byte("PUT ")
	mDELETE = []byte("DELETE ")
	mPATCH  = []byte("PATCH ")
)

type agg struct {
	count int64
	lats  []int64
}

var (
	scratch []byte
	tsMask  = [25]byte{
		'D', 'D', 'D', 'D', '-', 'D', 'D', '-', 'D', 'D', 'T', 'D', 'D',
		':', 'D', 'D', ':', 'D', 'D', '.', 'D', 'D', 'D', 'Z', ' ',
	}
)

func isDig(c byte) bool { return c >= '0' && c <= '9' }

func isSeg(c byte) bool {
	return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '-'
}

// parseLine returns (class, latencyTenths, ok).
func parseLine(line []byte) (int, int64, bool) {
	p := 0
	e := len(line)
	if e < 26 {
		return 0, 0, false
	}
	for i := 0; i < 25; i++ {
		c := line[p+i]
		m := tsMask[i]
		if m == 'D' {
			if !isDig(c) {
				return 0, 0, false
			}
		} else if c != m {
			return 0, 0, false
		}
	}
	p += 25
	s0 := p
	for p < e && line[p] >= 'a' && line[p] <= 'z' {
		p++
	}
	if p == s0 || p+1 >= e || line[p] != '-' {
		return 0, 0, false
	}
	p++
	d0 := p
	for p < e && isDig(line[p]) {
		p++
	}
	if p == d0 || p+1 >= e || line[p] != ' ' {
		return 0, 0, false
	}
	p++
	// method
	if e-p >= 4 && bytes.HasPrefix(line[p:], mGET) {
		p += 4
	} else if e-p >= 5 && bytes.HasPrefix(line[p:], mPOST) {
		p += 5
	} else if e-p >= 4 && bytes.HasPrefix(line[p:], mPUT) {
		p += 4
	} else if e-p >= 7 && bytes.HasPrefix(line[p:], mDELETE) {
		p += 7
	} else if e-p >= 6 && bytes.HasPrefix(line[p:], mPATCH) {
		p += 6
	} else {
		return 0, 0, false
	}
	// path
	if line[p] != '/' {
		return 0, 0, false
	}
	if cap(scratch) < ((e-p)<<2)+16 {
		scratch = make([]byte, 0, 1024)
	}
	sc := scratch[:0]
	for {
		segStart := len(sc)
		for p < e && isSeg(line[p]) {
			sc = append(sc, line[p])
			p++
		}
		allDig := len(sc) > segStart
		for q := segStart; allDig && q < len(sc); q++ {
			allDig = isDig(sc[q])
		}
		if allDig {
			sc = sc[:segStart]
			sc = append(sc, '{', 'i', 'd', '}')
		}
		if p < e && line[p] == '/' {
			sc = append(sc, '/')
			p++
			continue
		}
		break
	}
	if p < e && line[p] == '?' {
		p++
		for p < e && line[p] != ' ' {
			p++
		}
	}
	if p+1 >= e || line[p] != ' ' {
		return 0, 0, false
	}
	p++
	// status
	if e-p < 4 || !isDig(line[p]) || !isDig(line[p+1]) || !isDig(line[p+2]) {
		return 0, 0, false
	}
	cls := int(line[p] - '0')
	p += 3
	if p+1 >= e || line[p] != ' ' {
		return 0, 0, false
	}
	p++
	// size
	b0 := p
	for p < e && isDig(line[p]) {
		p++
	}
	if p == b0 || e-p < 2 || line[p] != 'B' || line[p+1] != ' ' {
		return 0, 0, false
	}
	p += 2
	// latency
	l0 := p
	for p < e && isDig(line[p]) {
		p++
	}
	if p == l0 || e-p < 5 || line[p] != '.' || !isDig(line[p+1]) || line[p+2] != 'm' || line[p+3] != 's' || line[p+4] != ' ' {
		return 0, 0, false
	}
	var v int64
	if p-l0 > 18 {
		v = 1_000_000_000_000_000 // saturate absurdly large latencies
	} else {
		for l0 < p {
			v = v*10 + int64(line[l0]-'0')
			l0++
		}
		v = v*10 + int64(line[p+1]-'0')
		if v > 1_000_000_000_000_000 {
			v = 1_000_000_000_000_000
		}
	}
	p += 5
	// user agent
	if line[p] != '"' {
		return 0, 0, false
	}
	p++
	for p < e && line[p] != '"' {
		p++
	}
	if p != e-1 {
		return 0, 0, false
	}
	scratch = sc
	return cls, v, true
}

func appendNum(out []byte, v uint64) []byte {
	return strconv.AppendUint(out, v, 10)
}

func appendTenths(out []byte, v int64) []byte {
	out = strconv.AppendInt(out, v/10, 10)
	out = append(out, '.')
	return append(out, byte('0'+v%10))
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	var lines, malformed int64
	var statusCnt [10]int64
	aggs := make(map[string]*agg, 256)

	i := 0
	n := len(data)
	for i < n {
		j := bytes.IndexByte(data[i:], '\n')
		var le int
		if j < 0 {
			le = n
		} else {
			le = i + j
		}
		lines++
		if cls, lat, ok := parseLine(data[i:le]); ok {
			statusCnt[cls]++
			a, found := aggs[string(scratch)]
			if !found {
				a = &agg{}
				aggs[string(scratch)] = a
			}
			a.count++
			a.lats = append(a.lats, lat)
		} else {
			malformed++
		}
		if j < 0 {
			break
		}
		i = le + 1
	}

	out := make([]byte, 0, 4096)
	out = append(out, "lines "...)
	out = appendNum(out, uint64(lines))
	out = append(out, "\nmalformed "...)
	out = appendNum(out, uint64(malformed))
	out = append(out, '\n')
	for d := 0; d < 10; d++ {
		if statusCnt[d] == 0 {
			continue
		}
		out = append(out, "status "...)
		out = append(out, byte('0'+d), 'x', 'x', ' ')
		out = appendNum(out, uint64(statusCnt[d]))
		out = append(out, '\n')
	}
	type ranked struct {
		tmpl string
		a    *agg
	}
	rs := make([]ranked, 0, len(aggs))
	for t, a := range aggs {
		rs = append(rs, ranked{t, a})
	}
	sort.Slice(rs, func(x, y int) bool {
		if rs[x].a.count != rs[y].a.count {
			return rs[x].a.count > rs[y].a.count
		}
		return rs[x].tmpl < rs[y].tmpl
	})
	if len(rs) > 10 {
		rs = rs[:10]
	}
	for _, r := range rs {
		lats := r.a.lats
		m := len(lats)
		slices.Sort(lats)
		out = append(out, "path "...)
		out = append(out, r.tmpl...)
		out = append(out, ' ')
		out = appendNum(out, uint64(r.a.count))
		out = append(out, ' ')
		out = appendTenths(out, lats[(50*m+99)/100-1])
		out = append(out, ' ')
		out = appendTenths(out, lats[(95*m+99)/100-1])
		out = append(out, ' ')
		out = appendTenths(out, lats[m-1])
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
