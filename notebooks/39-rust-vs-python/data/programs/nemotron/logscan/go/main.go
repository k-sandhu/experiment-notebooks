package main

import (
	"bytes"
	"os"
	"sort"
	"strconv"
)

// Summarise a web server access log (see SPEC.md).
// Single pass over the input: validate every line against the grammar, count
// status classes, group latency tenths by path template, then report the top 10.

type Stats struct {
	count int
	lat   []int // latency in tenths of a ms
}

// Open-addressing map from path template -> *Stats. Keys are interned strings;
// lookups compare raw bytes against stored strings, so only unique templates
// are ever allocated as strings.
type TMap struct {
	keys []string
	vals []*Stats
	mask int
	size int
}

func newTMap(cap int) *TMap {
	return &TMap{keys: make([]string, cap), vals: make([]*Stats, cap), mask: cap - 1}
}

func (m *TMap) FindOrAdd(buf []byte, start, end int) *Stats {
	h := hashBytes(buf[start:end])
	mask := uint64(m.mask)
	for slot := int(h & mask); ; slot = (slot + 1) & int(mask) {
		k := m.keys[slot]
		if k == "" {
			m.keys[slot] = string(buf[start:end])
			v := &Stats{}
			m.vals[slot] = v
			m.size++
			if m.size*4 > len(m.keys)*3 {
				m.grow()
			}
			return v
		}
		if len(k) == end-start && bytesEqStr(k, buf[start:end]) {
			return m.vals[slot]
		}
	}
}

func (m *TMap) grow() {
	oldK := m.keys
	oldV := m.vals
	cap := len(oldK) * 2
	m.keys = make([]string, cap)
	m.vals = make([]*Stats, cap)
	m.mask = cap - 1
	m.size = 0
	for i, k := range oldK {
		if k != "" {
			m.put0(k, oldV[i])
		}
	}
}

func (m *TMap) put0(k string, v *Stats) {
	h := hashStr(k)
	mask := uint64(m.mask)
	for slot := int(h & mask); ; slot = (slot + 1) & int(mask) {
		if m.keys[slot] == "" {
			m.keys[slot] = k
			m.vals[slot] = v
			m.size++
			return
		}
	}
}

func hashBytes(b []byte) uint64 {
	var h uint64 = 1469598103934665603
	for _, c := range b {
		h ^= uint64(c)
		h *= 1099511628211
	}
	return h
}

func hashStr(s string) uint64 {
	var h uint64 = 1469598103934665603
	for i := 0; i < len(s); i++ {
		h ^= uint64(s[i])
		h *= 1099511628211
	}
	return h
}

type item struct {
	name string
	st   *Stats
}

func isDig(c byte) bool { return c >= '0' && c <= '9' }
func pathChar(c byte) bool {
	return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
		c == '_' || c == '/' || c == '-'
}

// Validates one line (without its newline) against the SPEC.md regex and
// extracts status class, latency (tenths of a ms) and the path span.
// ok is false for malformed lines.
func parseLine(d []byte, start, end int, res *[4]int) bool {
	// res: [0]=cls, [1]=lat, [2]=pathStart, [3]=pathEnd
	length := end - start
	if length < 49 {
		return false // shortest possible well-formed line
	}

	// timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<sp>
	if d[start+4] != '-' || d[start+7] != '-' || d[start+10] != 'T' ||
		d[start+13] != ':' || d[start+16] != ':' || d[start+19] != '.' ||
		d[start+23] != 'Z' || d[start+24] != ' ' {
		return false
	}
	for _, off := range []int{0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22} {
		if !isDig(d[start+off]) {
			return false
		}
	}

	// host: [a-z]+-\d+<sp>
	h := start + 25
	if h >= end || d[h] < 'a' || d[h] > 'z' {
		return false
	}
	for h < end && d[h] >= 'a' && d[h] <= 'z' {
		h++
	}
	if h >= end || d[h] != '-' {
		return false
	}
	h++
	if h >= end || !isDig(d[h]) {
		return false
	}
	for h < end && isDig(d[h]) {
		h++
	}
	if h >= end || d[h] != ' ' {
		return false
	}
	h++ // method

	var mlen int
	rem := end - h
	switch {
	case rem >= 3 && (match(d, h, "GET") || match(d, h, "PUT")):
		mlen = 3
	case rem >= 4 && match(d, h, "POST"):
		mlen = 4
	case rem >= 6 && match(d, h, "DELETE"):
		mlen = 6
	case rem >= 5 && match(d, h, "PATCH"):
		mlen = 5
	}
	if mlen == 0 {
		return false
	}
	h += mlen
	if h >= end || d[h] != ' ' {
		return false
	}
	h++

	// path: /[A-Za-z0-9_/-]* then optional \?[^ ]* then <sp>
	if h >= end || d[h] != '/' {
		return false
	}
	pathStart := h
	h++
	for h < end {
		c := d[h]
		if c == ' ' || c == '?' {
			break
		}
		if !pathChar(c) {
			return false
		}
		h++
	}
	pathEnd := h
	if h < end && d[h] == '?' {
		h++
		for h < end && d[h] != ' ' {
			h++
		}
	}
	if h >= end || d[h] != ' ' {
		return false
	}
	h++

	// status: \d{3}<sp>
	if end-h < 3 || !isDig(d[h]) || !isDig(d[h+1]) || !isDig(d[h+2]) {
		return false
	}
	res[0] = int(d[h] - '0')
	h += 3
	if h >= end || d[h] != ' ' {
		return false
	}
	h++

	// size: \d+B<sp>
	if h >= end || !isDig(d[h]) {
		return false
	}
	for h < end && isDig(d[h]) {
		h++
	}
	if h >= end || d[h] != 'B' {
		return false
	}
	h++
	if h >= end || d[h] != ' ' {
		return false
	}
	h++

	// latency: \d+.\dms "<ua>"<end>
	var lat int
	if h >= end || !isDig(d[h]) {
		return false
	}
	for h < end && isDig(d[h]) {
		lat = lat*10 + int(d[h]-'0')
		h++
	}
	if h >= end || d[h] != '.' {
		return false
	}
	h++
	if h >= end || !isDig(d[h]) {
		return false
	}
	lat = lat*10 + int(d[h]-'0')
	h++
	if end-h < 4 || d[h] != 'm' || d[h+1] != 's' || d[h+2] != ' ' || d[h+3] != '"' {
		return false
	}
	h += 4
	for h < end && d[h] != '"' {
		h++
	}
	if h >= end || d[h] != '"' {
		return false
	}
	h++
	if h != end {
		return false
	}

	res[1] = lat
	res[2] = pathStart
	res[3] = pathEnd
	return true
}

func bytesEqStr(s string, b []byte) bool {
	if len(s) != len(b) {
		return false
	}
	for i := 0; i < len(s); i++ {
		if s[i] != b[i] {
			return false
		}
	}
	return true
}

func match(d []byte, pos int, lit string) bool {
	for i := 0; i < len(lit); i++ {
		if d[pos+i] != lit[i] {
			return false
		}
	}
	return true
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n := len(data)
	p := 0
	var nLines, nMalformed int64
	statusCount := [10]int{}
	tmap := newTMap(1 << 14)
	tmpl := make([]byte, 0, 128)
	res := [4]int{}

	for p < n {
		nLines++
		lineStart := p
		e := bytes.IndexByte(data[p:], '\n')
		var lineEnd int
		if e < 0 {
			lineEnd = n
		} else {
			lineEnd = p + e
		}
		// line is [lineStart, lineEnd)
		p = lineEnd + 1

		if parseLine(data, lineStart, lineEnd, &res) {
			statusCount[res[0]]++

			// path template: split on '/', replace all-digit segments with {id}
			tmpl = tmpl[:0]
			tmpl = append(tmpl, '/')
			segStart := res[2] + 1
			i := segStart
			for {
				if i == res[3] || data[i] == '/' {
					seglen := i - segStart
					if seglen > 0 {
						allDig := true
						for j := segStart; j < i; j++ {
							if !isDig(data[j]) {
								allDig = false
								break
							}
						}
						if allDig {
							tmpl = append(tmpl, '{', 'i', 'd', '}')
						} else {
							tmpl = append(tmpl, data[segStart:i]...)
						}
					}
					if i < res[3] {
						tmpl = append(tmpl, '/')
					}
					segStart = i + 1
				}
				if i == res[3] {
					break
				}
				i++
			}

			st := tmap.FindOrAdd(tmpl, 0, len(tmpl))
			st.count++
			st.lat = append(st.lat, res[1])
		} else {
			nMalformed++
		}
	}

	// collect items and sort: count descending, then template ascending (byte order)
	var items []item
	for slot, k := range tmap.keys {
		if k != "" {
			items = append(items, item{name: k, st: tmap.vals[slot]})
		}
	}
	sort.Slice(items, func(a, b int) bool {
		if items[a].st.count != items[b].st.count {
			return items[a].st.count > items[b].st.count
		}
		return items[a].name < items[b].name // byte order
	})

	var out bytes.Buffer
	out.WriteString("lines ")
	out.WriteString(strconv.FormatInt(nLines, 10))
	out.WriteByte('\n')
	out.WriteString("malformed ")
	out.WriteString(strconv.FormatInt(nMalformed, 10))
	out.WriteByte('\n')
	for c := 0; c < 10; c++ {
		if statusCount[c] != 0 {
			out.WriteString("status ")
			out.WriteByte(byte('0' + c))
			out.WriteString("xx ")
			out.WriteString(strconv.Itoa(statusCount[c]))
			out.WriteByte('\n')
		}
	}
	top := len(items)
	if top > 10 {
		top = 10
	}
	for i := 0; i < top; i++ {
		st := items[i].st
		sort.Ints(st.lat)
		nn := len(st.lat)
		kth := func(pct int) int {
			return st.lat[((int64(pct)*int64(nn)+99)/100)-1]
		}
		out.WriteString("path ")
		out.WriteString(items[i].name)
		out.WriteByte(' ')
		out.WriteString(strconv.Itoa(st.count))
		out.WriteByte(' ')
		fmtLat(&out, kth(50))
		out.WriteByte(' ')
		fmtLat(&out, kth(95))
		out.WriteByte(' ')
		fmtLat(&out, st.lat[nn-1])
		out.WriteByte('\n')
	}

	_, _ = os.Stdout.Write(out.Bytes())
}

func fmtLat(out *bytes.Buffer, t int) {
	out.WriteString(strconv.Itoa(t / 10))
	out.WriteByte('.')
	out.WriteString(strconv.Itoa(t % 10))
}
