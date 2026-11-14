package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"os"
	"slices"
	"strconv"
)

var pathChars [256]bool

const stamp = "0000-00-00T00:00:00.000Z "

func digit(c byte) bool { return c >= '0' && c <= '9' }

func init() {
	for c := 0; c < 256; c++ {
		pathChars[c] = digit(byte(c)) || c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z' || c == '_' || c == '/' || c == '-'
	}
}

type group struct {
	key    string
	values []uint64
	large  []string // Canonical tenths with more than 15 digits.
}

func (g *group) count() int { return len(g.values) + len(g.large) }

type scanner struct {
	groups           map[string]*group
	key              []byte
	statuses         [10]uint64
	lines, malformed uint64
}

func (s *scanner) parse(b []byte) bool {
	n := len(b)
	if n < 50 {
		return false
	}
	for j := 0; j < len(stamp); j++ {
		if stamp[j] == '0' {
			if !digit(b[j]) {
				return false
			}
		} else if b[j] != stamp[j] {
			return false
		}
	}
	i := 25
	start := i
	for i < n && b[i] >= 'a' && b[i] <= 'z' {
		i++
	}
	if i == start || i == n || b[i] != '-' {
		return false
	}
	i++
	start = i
	for i < n && digit(b[i]) {
		i++
	}
	if i == start || i == n || b[i] != ' ' {
		return false
	}
	i++
	start = i
	for i < n && b[i] != ' ' {
		i++
	}
	if i == n {
		return false
	}
	switch string(b[start:i]) {
	case "GET", "POST", "PUT", "DELETE", "PATCH":
	default:
		return false
	}
	i++
	if i == n || b[i] != '/' {
		return false
	}
	pathStart := i
	for i < n && pathChars[b[i]] {
		i++
	}
	pathEnd := i
	if i < n && b[i] == '?' {
		for i < n && b[i] != ' ' {
			i++
		}
	}
	if i == n || b[i] != ' ' {
		return false
	}
	i++
	if n-i < 4 || !digit(b[i]) || !digit(b[i+1]) || !digit(b[i+2]) || b[i+3] != ' ' {
		return false
	}
	status := b[i] - '0'
	i += 4
	start = i
	for i < n && digit(b[i]) {
		i++
	}
	if i == start || n-i < 2 || b[i] != 'B' || b[i+1] != ' ' {
		return false
	}
	i += 2
	start = i
	for i < n && b[i] == '0' {
		i++
	}
	significant := i
	for i < n && digit(b[i]) {
		i++
	}
	decimal := i
	if i == start || n-i < 7 || b[i] != '.' || !digit(b[i+1]) || b[i+2] != 'm' ||
		b[i+3] != 's' || b[i+4] != ' ' || b[i+5] != '"' || b[n-1] != '"' ||
		bytes.IndexByte(b[i+6:n-1], '"') >= 0 {
		return false
	}

	key := s.key[:0]
	p := pathStart
	for p < pathEnd {
		key = append(key, '/')
		p++
		start = p
		numeric := true
		for p < pathEnd && b[p] != '/' {
			if !digit(b[p]) {
				numeric = false
			}
			p++
		}
		if p != start && numeric {
			key = append(key, "{id}"...)
		} else {
			key = append(key, b[start:p]...)
		}
	}
	s.key = key
	// Go elides the temporary string allocation for a map lookup.
	g := s.groups[string(key)]
	if g == nil {
		stored := string(key)
		g = &group{key: stored}
		s.groups[stored] = g
	}
	if decimal-significant <= 14 {
		var value uint64
		for j := significant; j < decimal; j++ {
			value = value*10 + uint64(b[j]-'0')
		}
		g.values = append(g.values, value*10+uint64(b[decimal+1]-'0'))
	} else {
		value := make([]byte, decimal-significant+1)
		copy(value, b[significant:decimal])
		value[len(value)-1] = b[decimal+1]
		g.large = append(g.large, string(value))
	}
	s.statuses[status]++
	return true
}

func (s *scanner) read(path string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	r := bufio.NewReaderSize(f, 1<<20)
	var partial []byte
	for {
		line, err := r.ReadSlice('\n')
		if err == bufio.ErrBufferFull {
			partial = append(partial, line...)
			continue
		}
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
		if len(partial) > 0 {
			partial = append(partial, line...)
			line = partial
		}
		s.lines++
		if !s.parse(line[:len(line)-1]) {
			s.malformed++
		}
		partial = partial[:0]
	}
}

func better(a, b *group) bool {
	if a.count() != b.count() {
		return a.count() > b.count()
	}
	return a.key < b.key
}

func at(g *group, rank int) string {
	if rank < len(g.values) {
		v := g.values[rank]
		return strconv.FormatUint(v/10, 10) + "." + strconv.FormatUint(v%10, 10)
	}
	v := g.large[rank-len(g.values)]
	return v[:len(v)-1] + "." + v[len(v)-1:]
}

func (s *scanner) output() {
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	fmt.Fprintf(out, "lines %d\nmalformed %d\n", s.lines, s.malformed)
	for c, count := range s.statuses {
		if count != 0 {
			fmt.Fprintf(out, "status %dxx %d\n", c, count)
		}
	}
	var top [10]*group
	size := 0
	for _, g := range s.groups {
		pos := size
		for pos > 0 && better(g, top[pos-1]) {
			pos--
		}
		if pos >= 10 {
			continue
		}
		for j := min(size, 9); j > pos; j-- {
			top[j] = top[j-1]
		}
		top[pos] = g
		if size < 10 {
			size++
		}
	}
	for _, g := range top[:size] {
		slices.Sort(g.values)
		slices.SortFunc(g.large, func(a, b string) int {
			if len(a) < len(b) {
				return -1
			}
			if len(a) > len(b) {
				return 1
			}
			if a < b {
				return -1
			}
			if a > b {
				return 1
			}
			return 0
		})
		n := g.count()
		fmt.Fprintf(out, "path %s %d %s %s %s\n", g.key, n, at(g, (n-1)/2), at(g, n-1-n/20), at(g, n-1))
	}
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	s := scanner{groups: make(map[string]*group), key: make([]byte, 0, 256)}
	if err := s.read(os.Args[1]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	s.output()
}
