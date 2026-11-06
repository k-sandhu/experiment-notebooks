package main

import (
	"bytes"
	"os"
	"slices"
	"strconv"
)

var data []byte
var scratch = make([]byte, 1024)

type entry struct {
	tmpl  []byte
	count int
	lat   []int64
}

var entries []entry
var table []int32

func isDig(c byte) bool { return c >= '0' && c <= '9' }

func hashBytes(b []byte) uint32 {
	h := uint32(2166136261)
	for _, c := range b {
		h = (h ^ uint32(c)) * 16777619
	}
	h ^= h >> 16
	return h
}

func findEntry(l int) int {
	mask := len(table) - 1
	idx := int(hashBytes(scratch[:l]) & uint32(mask))
	for {
		s := table[idx]
		if s == 0 {
			return -1
		}
		e := int(s - 1)
		if len(entries[e].tmpl) == l && bytes.Equal(entries[e].tmpl, scratch[:l]) {
			return e
		}
		idx = (idx + 1) & mask
	}
}

func addEntry(l int) int {
	e := len(entries)
	t := make([]byte, l)
	copy(t, scratch[:l])
	entries = append(entries, entry{tmpl: t, lat: make([]int64, 0, 16)})
	if (len(entries))*2 >= len(table) {
		tbl := make([]int32, len(table)*2)
		mask := len(tbl) - 1
		for i := range entries {
			idx := int(hashBytes(entries[i].tmpl) & uint32(mask))
			for tbl[idx] != 0 {
				idx = (idx + 1) & mask
			}
			tbl[idx] = int32(i + 1)
		}
		table = tbl
	} else {
		mask := len(table) - 1
		idx := int(hashBytes(t) & uint32(mask))
		for table[idx] != 0 {
			idx = (idx + 1) & mask
		}
		table[idx] = int32(e + 1)
	}
	return e
}

func ensureScratch(need int) {
	if need > len(scratch) {
		scratch = make([]byte, need)
	}
}

// parseLine returns ok, status class digit, latency in tenths, template length.
func parseLine(p, le int) (bool, int, int64, int) {
	d := data
	if le-p < 25 {
		return false, 0, 0, 0
	}
	if !(isDig(d[p]) && isDig(d[p+1]) && isDig(d[p+2]) && isDig(d[p+3]) && d[p+4] == '-' &&
		isDig(d[p+5]) && isDig(d[p+6]) && d[p+7] == '-' && isDig(d[p+8]) && isDig(d[p+9]) &&
		d[p+10] == 'T' && isDig(d[p+11]) && isDig(d[p+12]) && d[p+13] == ':' &&
		isDig(d[p+14]) && isDig(d[p+15]) && d[p+16] == ':' && isDig(d[p+17]) && isDig(d[p+18]) &&
		d[p+19] == '.' && isDig(d[p+20]) && isDig(d[p+21]) && isDig(d[p+22]) &&
		d[p+23] == 'Z' && d[p+24] == ' ') {
		return false, 0, 0, 0
	}

	i := p + 25
	j := i
	for j < le && d[j] >= 'a' && d[j] <= 'z' {
		j++
	}
	if j == i || j >= le || d[j] != '-' {
		return false, 0, 0, 0
	}
	j++
	ds := j
	for j < le && isDig(d[j]) {
		j++
	}
	if j == ds || j >= le || d[j] != ' ' {
		return false, 0, 0, 0
	}
	j++

	if j+4 <= le && d[j] == 'G' && d[j+1] == 'E' && d[j+2] == 'T' && d[j+3] == ' ' {
		j += 4
	} else if j+5 <= le && d[j] == 'P' && d[j+1] == 'O' && d[j+2] == 'S' && d[j+3] == 'T' && d[j+4] == ' ' {
		j += 5
	} else if j+4 <= le && d[j] == 'P' && d[j+1] == 'U' && d[j+2] == 'T' && d[j+3] == ' ' {
		j += 4
	} else if j+7 <= le && d[j] == 'D' && d[j+1] == 'E' && d[j+2] == 'L' && d[j+3] == 'E' && d[j+4] == 'T' && d[j+5] == 'E' && d[j+6] == ' ' {
		j += 7
	} else if j+6 <= le && d[j] == 'P' && d[j+1] == 'A' && d[j+2] == 'T' && d[j+3] == 'C' && d[j+4] == 'H' && d[j+5] == ' ' {
		j += 6
	} else {
		return false, 0, 0, 0
	}

	if j >= le || d[j] != '/' {
		return false, 0, 0, 0
	}
	q := j + 1
	for q < le {
		c := d[q]
		if (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
			c == '_' || c == '/' || c == '-' {
			q++
		} else {
			break
		}
	}

	var fieldEnd int
	if q < le && d[q] == '?' {
		r := q + 1
		for r < le && d[r] != ' ' {
			r++
		}
		if r >= le {
			return false, 0, 0, 0
		}
		fieldEnd = r
	} else if q < le && d[q] == ' ' {
		fieldEnd = q
	} else {
		return false, 0, 0, 0
	}

	ensureScratch((q-j)*4 + 16)
	sc := scratch
	t := 0
	s := j
	for s < q {
		if d[s] == '/' {
			sc[t] = '/'
			t++
			s++
			continue
		}
		e := s
		allDig := true
		for e < q && d[e] != '/' {
			if !isDig(d[e]) {
				allDig = false
			}
			e++
		}
		if allDig {
			sc[t] = '{'
			sc[t+1] = 'i'
			sc[t+2] = 'd'
			sc[t+3] = '}'
			t += 4
		} else {
			t += copy(sc[t:], d[s:e])
		}
		s = e
	}

	k := fieldEnd
	if k+4 >= le {
		return false, 0, 0, 0
	}
	if !isDig(d[k+1]) || !isDig(d[k+2]) || !isDig(d[k+3]) || d[k+4] != ' ' {
		return false, 0, 0, 0
	}
	status := int(d[k+1] - '0')
	k += 5

	e := k
	for e < le && isDig(d[e]) {
		e++
	}
	if e == k || e >= le || d[e] != 'B' {
		return false, 0, 0, 0
	}
	e++
	if e >= le || d[e] != ' ' {
		return false, 0, 0, 0
	}
	e++

	ls := e
	var v int64
	for e < le && isDig(d[e]) {
		v = v*10 + int64(d[e]-'0')
		e++
	}
	if e == ls || e >= le || d[e] != '.' {
		return false, 0, 0, 0
	}
	e++
	if e >= le || !isDig(d[e]) {
		return false, 0, 0, 0
	}
	v = v*10 + int64(d[e]-'0')
	e++
	if e+3 >= le || d[e] != 'm' || d[e+1] != 's' || d[e+2] != ' ' {
		return false, 0, 0, 0
	}
	e += 3
	if d[e] != '"' {
		return false, 0, 0, 0
	}
	e++
	r := e
	for r < le && d[r] != '"' {
		r++
	}
	if r != le-1 {
		return false, 0, 0, 0
	}

	return true, status, v, t
}

func better(a, b int) bool {
	if entries[a].count != entries[b].count {
		return entries[a].count > entries[b].count
	}
	return bytes.Compare(entries[a].tmpl, entries[b].tmpl) < 0
}

func appendTenths(out []byte, v int64) []byte {
	out = strconv.AppendInt(out, int64(v/10), 10)
	out = append(out, '.')
	out = append(out, byte('0'+v%10))
	return out
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	var err error
	data, err = os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	n := len(data)

	table = make([]int32, 2048)
	entries = make([]entry, 0, 1024)

	lines := 0
	malformed := 0
	var statusCount [10]int64
	p := 0
	for p < n {
		rel := bytes.IndexByte(data[p:], '\n')
		var le int
		if rel < 0 {
			le = n
		} else {
			le = p + rel
		}
		lines++
		ok, status, lat, tlen := parseLine(p, le)
		if ok {
			statusCount[status]++
			e := findEntry(tlen)
			if e < 0 {
				e = addEntry(tlen)
			}
			entries[e].count++
			entries[e].lat = append(entries[e].lat, lat)
			if rel < 0 {
				p = n
			} else {
				p = le + 1
			}
		} else {
			malformed++
			if rel < 0 {
				p = n
			} else {
				p = le + 1
			}
		}
	}

	best := make([]int, 0, 10)
	for e := range entries {
		pos := 0
		for pos < len(best) && better(best[pos], e) {
			pos++
		}
		if pos < 10 {
			if len(best) < 10 {
				best = append(best, 0)
			}
			copy(best[pos+1:], best[pos:])
			best[pos] = e
		}
	}

	out := make([]byte, 0, 4096)
	out = append(out, "lines "...)
	out = strconv.AppendInt(out, int64(lines), 10)
	out = append(out, "\nmalformed "...)
	out = strconv.AppendInt(out, int64(malformed), 10)
	out = append(out, '\n')
	for c := 0; c < 10; c++ {
		if statusCount[c] != 0 {
			out = append(out, "status "...)
			out = append(out, byte('0'+c), 'x', 'x', ' ')
			out = strconv.AppendInt(out, statusCount[c], 10)
			out = append(out, '\n')
		}
	}
	for bi := 0; bi < len(best); bi++ {
		e := best[bi]
		lv := entries[e].lat
		slices.Sort(lv)
		l := len(lv)
		i50 := (50*l+99)/100 - 1
		i95 := (95*l+99)/100 - 1
		out = append(out, "path "...)
		out = append(out, entries[e].tmpl...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, int64(entries[e].count), 10)
		out = append(out, ' ')
		out = appendTenths(out, lv[i50])
		out = append(out, ' ')
		out = appendTenths(out, lv[i95])
		out = append(out, ' ')
		out = appendTenths(out, lv[l-1])
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
