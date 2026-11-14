package main

import (
	"cmp"
	"os"
	"slices"
	"strconv"
	"strings"
	"unsafe"
)

var (
	d           []byte
	n           int
	pos         int
	pathS       int
	pathE       int
	statusDigit int
	latency     int
	pathCharTab [256]bool
)

func isDigit(c byte) bool { return c >= '0' && c <= '9' }

func parseLine() bool {
	i := pos
	fail := func() bool { pos = i; return false }
	if i+25 > n {
		return fail()
	}
	if !(isDigit(d[i]) && isDigit(d[i+1]) && isDigit(d[i+2]) && isDigit(d[i+3]) && d[i+4] == '-' &&
		isDigit(d[i+5]) && isDigit(d[i+6]) && d[i+7] == '-' && isDigit(d[i+8]) && isDigit(d[i+9]) &&
		d[i+10] == 'T' && isDigit(d[i+11]) && isDigit(d[i+12]) && d[i+13] == ':' && isDigit(d[i+14]) &&
		isDigit(d[i+15]) && d[i+16] == ':' && isDigit(d[i+17]) && isDigit(d[i+18]) && d[i+19] == '.' &&
		isDigit(d[i+20]) && isDigit(d[i+21]) && isDigit(d[i+22]) && d[i+23] == 'Z' && d[i+24] == ' ') {
		return fail()
	}
	i += 25
	{
		s := i
		for i < n && d[i] >= 'a' && d[i] <= 'z' {
			i++
		}
		if i == s {
			return fail()
		}
	}
	if i >= n || d[i] != '-' {
		return fail()
	}
	i++
	{
		s := i
		for i < n && isDigit(d[i]) {
			i++
		}
		if i == s {
			return fail()
		}
	}
	if i >= n || d[i] != ' ' {
		return fail()
	}
	i++
	if i >= n {
		return fail()
	}
	switch d[i] {
	case 'G':
		if i+4 <= n && d[i+1] == 'E' && d[i+2] == 'T' && d[i+3] == ' ' {
			i += 4
		} else {
			return fail()
		}
	case 'D':
		if i+7 <= n && d[i+1] == 'E' && d[i+2] == 'L' && d[i+3] == 'E' && d[i+4] == 'T' && d[i+5] == 'E' && d[i+6] == ' ' {
			i += 7
		} else {
			return fail()
		}
	case 'P':
		if i+1 >= n {
			return fail()
		}
		if d[i+1] == 'O' {
			if i+5 <= n && d[i+2] == 'S' && d[i+3] == 'T' && d[i+4] == ' ' {
				i += 5
			} else {
				return fail()
			}
		} else if d[i+1] == 'U' {
			if i+4 <= n && d[i+2] == 'T' && d[i+3] == ' ' {
				i += 4
			} else {
				return fail()
			}
		} else if d[i+1] == 'A' {
			if i+6 <= n && d[i+2] == 'T' && d[i+3] == 'C' && d[i+4] == 'H' && d[i+5] == ' ' {
				i += 6
			} else {
				return fail()
			}
		} else {
			return fail()
		}
	default:
		return fail()
	}
	if i >= n || d[i] != '/' {
		return fail()
	}
	pathS = i
	i++
	for i < n && pathCharTab[d[i]] {
		i++
	}
	pathE = i
	if i < n && d[i] == '?' {
		i++
		for i < n && d[i] != ' ' && d[i] != '\n' {
			i++
		}
	}
	if i >= n || d[i] != ' ' {
		return fail()
	}
	i++
	if i+3 > n || !isDigit(d[i]) || !isDigit(d[i+1]) || !isDigit(d[i+2]) {
		return fail()
	}
	statusDigit = int(d[i] - '0')
	i += 3
	if i >= n || d[i] != ' ' {
		return fail()
	}
	i++
	{
		s := i
		for i < n && isDigit(d[i]) {
			i++
		}
		if i == s {
			return fail()
		}
	}
	if i >= n || d[i] != 'B' {
		return fail()
	}
	i++
	if i >= n || d[i] != ' ' {
		return fail()
	}
	i++
	{
		s := i
		v := 0
		for i < n && isDigit(d[i]) {
			v = v*10 + int(d[i]-'0')
			i++
		}
		if i == s {
			return fail()
		}
		if i >= n || d[i] != '.' {
			return fail()
		}
		i++
		if i >= n || !isDigit(d[i]) {
			return fail()
		}
		v = v*10 + int(d[i]-'0')
		i++
		latency = v
	}
	if i+2 > n || d[i] != 'm' || d[i+1] != 's' {
		return fail()
	}
	i += 2
	if i >= n || d[i] != ' ' {
		return fail()
	}
	i++
	if i >= n || d[i] != '"' {
		return fail()
	}
	i++
	for i < n && d[i] != '"' && d[i] != '\n' {
		i++
	}
	if i >= n || d[i] != '"' {
		return fail()
	}
	i++
	if i < n && d[i] != '\n' {
		return fail()
	}
	pos = i
	return true
}

func main() {
	for c := 0; c < 256; c++ {
		pathCharTab[c] = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-'
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	d = data
	n = len(d)
	pos = 0

	var lines, malformed int64
	var statusCnt [10]int64

	templates := make([]string, 0, 1024)
	counts := make([]int, 0, 1024)
	m := make(map[string]int, 1024)

	est := n/100 + 16
	lats := make([]int32, 0, est)
	ids := make([]int32, 0, est)
	scratch := make([]byte, 0, 256)

	for pos < n {
		lines++
		if parseLine() {
			statusCnt[statusDigit]++
			scratch = scratch[:0]
			j := pathS
			for {
				segS := j
				allDig := true
				for j < pathE && d[j] != '/' {
					if !isDigit(d[j]) {
						allDig = false
					}
					j++
				}
				if j > segS && allDig {
					scratch = append(scratch, "{id}"...)
				} else if j > segS {
					scratch = append(scratch, d[segS:j]...)
				}
				if j >= pathE {
					break
				}
				scratch = append(scratch, '/')
				j++
			}
			key := unsafe.String(&scratch[0], len(scratch))
			id, ok := m[key]
			if !ok {
				s := string(scratch)
				id = len(templates)
				m[s] = id
				templates = append(templates, s)
				counts = append(counts, 0)
			}
			counts[id]++
			lats = append(lats, int32(latency))
			ids = append(ids, int32(id))
			if pos < n {
				pos++
			}
		} else {
			malformed++
			for pos < n && d[pos] != '\n' {
				pos++
			}
			if pos < n {
				pos++
			}
		}
	}
	d = nil

	T := len(templates)
	order := make([]int, T)
	for k := range order {
		order[k] = k
	}
	slices.SortFunc(order, func(a, b int) int {
		if counts[a] != counts[b] {
			return cmp.Compare(counts[b], counts[a])
		}
		return strings.Compare(templates[a], templates[b])
	})
	K := T
	if K > 10 {
		K = 10
	}
	tops := make([][]int32, K)
	slot := make([]int, T)
	for k := range slot {
		slot[k] = -1
	}
	for k := 0; k < K; k++ {
		slot[order[k]] = k
		tops[k] = make([]int32, counts[order[k]])
	}
	fill := make([]int, K)
	for q, id := range ids {
		s := slot[id]
		if s >= 0 {
			tops[s][fill[s]] = lats[q]
			fill[s]++
		}
	}
	for k := 0; k < K; k++ {
		slices.Sort(tops[k])
	}

	var sb strings.Builder
	sb.Grow(1024)
	sb.WriteString("lines ")
	sb.WriteString(strconv.FormatInt(lines, 10))
	sb.WriteByte('\n')
	sb.WriteString("malformed ")
	sb.WriteString(strconv.FormatInt(malformed, 10))
	sb.WriteByte('\n')
	for dig := 0; dig < 10; dig++ {
		if statusCnt[dig] > 0 {
			sb.WriteString("status ")
			sb.WriteByte(byte('0' + dig))
			sb.WriteString("xx ")
			sb.WriteString(strconv.FormatInt(statusCnt[dig], 10))
			sb.WriteByte('\n')
		}
	}
	appendLat := func(v int32) {
		sb.WriteString(strconv.Itoa(int(v / 10)))
		sb.WriteByte('.')
		sb.WriteByte(byte('0' + v%10))
	}
	for k := 0; k < K; k++ {
		id := order[k]
		vec := tops[k]
		nn := int64(len(vec))
		p50 := vec[(50*nn+99)/100-1]
		p95 := vec[(95*nn+99)/100-1]
		mx := vec[len(vec)-1]
		sb.WriteString("path ")
		sb.WriteString(templates[id])
		sb.WriteByte(' ')
		sb.WriteString(strconv.Itoa(counts[id]))
		sb.WriteByte(' ')
		appendLat(p50)
		sb.WriteByte(' ')
		appendLat(p95)
		sb.WriteByte(' ')
		appendLat(mx)
		sb.WriteByte('\n')
	}
	os.Stdout.WriteString(sb.String())
}
