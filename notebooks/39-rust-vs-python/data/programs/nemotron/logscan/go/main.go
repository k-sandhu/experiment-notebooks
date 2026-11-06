// Log scan: summarise an access log by status class and path-template latency percentiles.
// Go 1.27, stdlib only, CGO_ENABLED=0.

package main

import (
	"bytes"
	"fmt"
	"os"
	"sort"
)

type Stats struct {
	count int
	maxT  int // max latency in tenths of a ms
	lats  []int
}

func (s *Stats) add(t int) {
	s.count++
	if t > s.maxT {
		s.maxT = t
	}
	s.lats = append(s.lats, t)
}

func isDigit(c byte) bool { return c >= '0' && c <= '9' }
func isUpper(c byte) bool { return c >= 'A' && c <= 'Z' }
func isLower(c byte) bool { return c >= 'a' && c <= 'z' }

// parseLine strictly validates one line (content without the trailing \n) and,
// if well-formed, returns status class, latency in tenths of a ms, path
// template, and true. Otherwise returns false.
func parseLine(line []byte) (int, int, string, bool) {
	i := 0
	n := len(line)

	// 1. timestamp: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z<space>
	if n-i < 25 {
		return 0, 0, "", false
	}
	if !isDigit(line[i]) || !isDigit(line[i+1]) || !isDigit(line[i+2]) || !isDigit(line[i+3]) {
		return 0, 0, "", false
	}
	if line[i+4] != '-' {
		return 0, 0, "", false
	}
	if !isDigit(line[i+5]) || !isDigit(line[i+6]) {
		return 0, 0, "", false
	}
	if line[i+7] != '-' {
		return 0, 0, "", false
	}
	if !isDigit(line[i+8]) || !isDigit(line[i+9]) {
		return 0, 0, "", false
	}
	if line[i+10] != 'T' {
		return 0, 0, "", false
	}
	if !isDigit(line[i+11]) || !isDigit(line[i+12]) {
		return 0, 0, "", false
	}
	if line[i+13] != ':' {
		return 0, 0, "", false
	}
	if !isDigit(line[i+14]) || !isDigit(line[i+15]) {
		return 0, 0, "", false
	}
	if line[i+16] != ':' {
		return 0, 0, "", false
	}
	if !isDigit(line[i+17]) || !isDigit(line[i+18]) {
		return 0, 0, "", false
	}
	if line[i+19] != '.' {
		return 0, 0, "", false
	}
	if !isDigit(line[i+20]) || !isDigit(line[i+21]) || !isDigit(line[i+22]) {
		return 0, 0, "", false
	}
	if line[i+23] != 'Z' || line[i+24] != ' ' {
		return 0, 0, "", false
	}
	i += 25

	// 2. host: [a-z]+-\d+<space>
	if i >= n || !isLower(line[i]) {
		return 0, 0, "", false
	}
	for i < n && isLower(line[i]) {
		i++
	}
	if i >= n || line[i] != '-' {
		return 0, 0, "", false
	}
	i++
	if i >= n || !isDigit(line[i]) {
		return 0, 0, "", false
	}
	for i < n && isDigit(line[i]) {
		i++
	}
	if i >= n || line[i] != ' ' {
		return 0, 0, "", false
	}
	i++

	// 3. method
	ok := false
	if !ok && n-i > 3 && line[i] == 'G' && line[i+1] == 'E' && line[i+2] == 'T' && line[i+3] == ' ' {
		i += 4; ok = true
	}
	if !ok && n-i > 4 && line[i] == 'P' && line[i+1] == 'O' && line[i+2] == 'S' && line[i+3] == 'T' && line[i+4] == ' ' {
		i += 5; ok = true
	}
	if !ok && n-i > 3 && line[i] == 'P' && line[i+1] == 'U' && line[i+2] == 'T' && line[i+3] == ' ' {
		i += 4; ok = true
	}
	if !ok && n-i > 6 && line[i] == 'D' && line[i+1] == 'E' && line[i+2] == 'L' && line[i+3] == 'E' && line[i+4] == 'T' && line[i+5] == 'E' && line[i+6] == ' ' {
		i += 7; ok = true
	}
	if !ok && n-i > 5 && line[i] == 'P' && line[i+1] == 'A' && line[i+2] == 'T' && line[i+3] == 'C' && line[i+4] == 'H' && line[i+5] == ' ' {
		i += 6; ok = true
	}
	if !ok {
		return 0, 0, "", false
	}

	// 4. path + template
	var tb bytes.Buffer
	tb.WriteByte('/') // leading '/'
	i++
	segStart := tb.Len() // tb.Len() at start of current segment (right after a '/')
	segDigits := true
	segLen := 0
	done := false
	for {
		if i >= n {
			return 0, 0, "", false
		}
		c := line[i]
		if c == '/' {
			if segLen > 0 && segDigits {
				tb.Truncate(segStart)
				tb.WriteString("{id}")
			}
			tb.WriteByte('/')
			i++
			segStart = tb.Len()
			segDigits = true
			segLen = 0
		} else if c == ' ' {
			if segLen > 0 && segDigits {
				tb.Truncate(segStart)
				tb.WriteString("{id}")
			}
			i++
			done = true
			break
		} else if c == '?' {
			if segLen > 0 && segDigits {
				tb.Truncate(segStart)
				tb.WriteString("{id}")
			}
			i++
			for i < n && line[i] != ' ' {
				i++
			}
			if i >= n {
				return 0, 0, "", false
			}
			i++
			done = true
			break
		} else {
			if !isDigit(c) && !isUpper(c) && !isLower(c) && c != '_' && c != '-' {
				return 0, 0, "", false
			}
			if segLen == 0 {
				segDigits = isDigit(c)
			} else if segDigits && !isDigit(c) {
				segDigits = false
			}
			segLen++
			tb.WriteByte(c)
			i++
		}
	}
	if !done {
		return 0, 0, "", false
	}

	// 5. status: \d{3}<space>
	if n-i < 4 {
		return 0, 0, "", false
	}
	if !isDigit(line[i]) || !isDigit(line[i+1]) || !isDigit(line[i+2]) {
		return 0, 0, "", false
	}
	if line[i+3] != ' ' {
		return 0, 0, "", false
	}
	statusClass := int(line[i] - '0')
	i += 4

	// 6. size: \d+B<space>
	if i >= n || !isDigit(line[i]) {
		return 0, 0, "", false
	}
	for i < n && isDigit(line[i]) {
		i++
	}
	if i >= n || line[i] != 'B' {
		return 0, 0, "", false
	}
	i++
	if i >= n || line[i] != ' ' {
		return 0, 0, "", false
	}
	i++

// 7. latency: \d+\.d ms<space>
	ls := i
	ip := 0
	for i < n && isDigit(line[i]) {
		ip = ip*10 + int(line[i]-'0')
		i++
	}
	if i == ls || i >= n || line[i] != '.' {
		return 0, 0, "", false
	}
	i++
	if i >= n || !isDigit(line[i]) {
		return 0, 0, "", false
	}
	frac := int(line[i] - '0')
	i++
	if n-i < 3 || line[i] != 'm' || line[i+1] != 's' || line[i+2] != ' ' {
		return 0, 0, "", false
	}
	i += 3
	latencyT := ip*10 + frac
	if i >= n || line[i] != '"' {
		return 0, 0, "", false
	}
	i++
	for i < n && line[i] != '"' {
		i++
	}
	if i >= n {
		return 0, 0, "", false
	}
	i++
	if i != n {
		return 0, 0, "", false
	}

	return statusClass, latencyT, tb.String(), true
}

func pos(pct, nn int) int {
	return (pct*nn+99)/100 - 1 // nearest-rank, 0-based index
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	b, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n := len(b)
	p := 0
	var lines, malformed int64
	statusCount := [10]int64{}
	m := make(map[string]*Stats)

	var out bytes.Buffer

	for p < n {
		nl := p
		for nl < n && b[nl] != '\n' {
			nl++
		}
		line := b[p:nl]
		p = nl + 1
		lines++
		sc, lat, tmpl, ok := parseLine(line)
		if !ok {
			malformed++
			continue
		}
		statusCount[sc]++
		s := m[tmpl]
		if s == nil {
			s = &Stats{}
			m[tmpl] = s
		}
		s.add(lat)
	}

	out.WriteString("lines ")
	fmt.Fprint(&out, lines)
	out.WriteByte('\n')
	out.WriteString("malformed ")
	fmt.Fprint(&out, malformed)
	out.WriteByte('\n')
	for d := 0; d < 10; d++ {
		if statusCount[d] != 0 {
			out.WriteString("status ")
			out.WriteByte(byte('0' + d))
			out.WriteString("xx ")
			fmt.Fprint(&out, statusCount[d])
			out.WriteByte('\n')
		}
	}

	type pathEntry struct {
		key   string
		stats *Stats
	}
	paths := make([]pathEntry, 0, len(m))
	for k, v := range m {
		paths = append(paths, pathEntry{k, v})
	}
	sort.Slice(paths, func(a, b int) bool {
		if paths[a].stats.count != paths[b].stats.count {
			return paths[a].stats.count > paths[b].stats.count
		}
		return paths[a].key < paths[b].key
	})
	limit := 10
	if len(paths) < limit {
		limit = len(paths)
	}
	for i := 0; i < limit; i++ {
		pe := paths[i]
		s := pe.stats
		sort.Ints(s.lats)
		nn := len(s.lats)
		out.WriteString("path ")
		out.WriteString(pe.key)
		out.WriteByte(' ')
		fmt.Fprint(&out, s.count)
		out.WriteByte(' ')
		fmt.Fprint(&out, s.lats[pos(50,nn)]/10)
		out.WriteByte('.')
		out.WriteByte(byte('0' + s.lats[pos(50,nn)]%10))
		out.WriteByte(' ')
		fmt.Fprint(&out, s.lats[pos(95,nn)]/10)
		out.WriteByte('.')
		out.WriteByte(byte('0' + s.lats[pos(95,nn)]%10))
		out.WriteByte(' ')
		fmt.Fprint(&out, s.maxT/10)
		out.WriteByte('.')
		out.WriteByte(byte('0' + s.maxT%10))
		out.WriteByte('\n')
	}

	os.Stdout.Write(out.Bytes())
}
