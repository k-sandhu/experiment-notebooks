package main

import (
	"bufio"
	"bytes"
	"fmt"
	"math/bits"
	"os"
	"runtime"
	"slices"
	"strings"
)

var pathChars = func() [256]bool {
	var t [256]bool
	for c := byte('a'); c <= 'z'; c++ {
		t[c] = true
	}
	for c := byte('A'); c <= 'Z'; c++ {
		t[c] = true
	}
	for c := byte('0'); c <= '9'; c++ {
		t[c] = true
	}
	t['_'], t['/'], t['-'] = true, true, true
	return t
}()

var timestampDigits = [...]int{
	0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22,
}

type group struct {
	path     string
	small    []uint64
	large    []string
	maxSmall uint64
}

func digit(c byte) bool {
	return c >= '0' && c <= '9'
}

func parseLine(b []byte) (path, whole []byte, fraction, status byte, ok bool) {
	n := len(b)
	if n < 25 {
		return
	}
	if b[4] != '-' || b[7] != '-' || b[10] != 'T' ||
		b[13] != ':' || b[16] != ':' || b[19] != '.' ||
		b[23] != 'Z' || b[24] != ' ' {
		return
	}
	for _, p := range timestampDigits {
		if !digit(b[p]) {
			return
		}
	}

	i := 25
	start := i
	for i < n && b[i] >= 'a' && b[i] <= 'z' {
		i++
	}
	if i == start || i >= n || b[i] != '-' {
		return
	}
	i++
	start = i
	for i < n && digit(b[i]) {
		i++
	}
	if i == start || i >= n || b[i] != ' ' {
		return
	}
	i++

	j := bytes.IndexByte(b[i:], ' ')
	if j < 0 {
		return
	}
	switch string(b[i : i+j]) {
	case "GET", "POST", "PUT", "DELETE", "PATCH":
	default:
		return
	}
	i += j + 1

	if i >= n || b[i] != '/' {
		return
	}
	start = i
	for i < n && pathChars[b[i]] {
		i++
	}
	pathEnd := i

	if i < n && b[i] == '?' {
		i++
		j = bytes.IndexByte(b[i:], ' ')
		if j < 0 {
			return
		}
		i += j
	}
	if i >= n || b[i] != ' ' {
		return
	}
	path = b[start:pathEnd]
	i++

	if n-i < 4 || !digit(b[i]) || !digit(b[i+1]) ||
		!digit(b[i+2]) || b[i+3] != ' ' {
		return
	}
	status = b[i] - '0'
	i += 4

	start = i
	for i < n && digit(b[i]) {
		i++
	}
	if i == start || n-i < 2 || b[i] != 'B' || b[i+1] != ' ' {
		return
	}
	i += 2

	start = i
	for i < n && digit(b[i]) {
		i++
	}
	if i == start || n-i < 7 ||
		b[i] != '.' || !digit(b[i+1]) ||
		b[i+2] != 'm' || b[i+3] != 's' ||
		b[i+4] != ' ' || b[i+5] != '"' ||
		b[n-1] != '"' {
		return
	}
	if bytes.IndexByte(b[i+6:n-1], '"') >= 0 {
		return
	}

	whole = b[start:i]
	fraction = b[i+1] - '0'
	ok = true
	return
}

func templatePath(path, dst []byte) []byte {
	dst = dst[:0]
	for i := 0; i < len(path); {
		if path[i] == '/' {
			dst = append(dst, '/')
			i++
			continue
		}

		start := i
		numeric := true
		for i < len(path) && path[i] != '/' {
			if !digit(path[i]) {
				numeric = false
			}
			i++
		}
		if numeric {
			dst = append(dst, '{', 'i', 'd', '}')
		} else {
			dst = append(dst, path[start:i]...)
		}
	}
	return dst
}

func parseLatency(whole []byte, fraction byte) (uint64, string) {
	i := 0
	for i < len(whole) && whole[i] == '0' {
		i++
	}
	whole = whole[i:]

	if len(whole) <= 19 {
		var v uint64
		for _, c := range whole {
			v = v*10 + uint64(c-'0')
		}
		if v <= (^uint64(0)-uint64(fraction))/10 {
			return v*10 + uint64(fraction), ""
		}
	}

	b := make([]byte, len(whole)+1)
	copy(b, whole)
	b[len(whole)] = '0' + fraction
	return 0, string(b)
}

func median(a, b, c uint64) uint64 {
	if a > b {
		a, b = b, a
	}
	if b > c {
		b = c
	}
	if a > b {
		b = a
	}
	return b
}

func selectValue(a []uint64, k int) uint64 {
	lo, hi := 0, len(a)
	budget := 2 * bits.Len(uint(len(a)))

	for hi-lo > 24 && budget > 0 {
		budget--
		pivot := median(a[lo], a[lo+(hi-lo)/2], a[hi-1])
		lt, i, gt := lo, lo, hi

		for i < gt {
			v := a[i]
			if v < pivot {
				a[i], a[lt] = a[lt], a[i]
				lt++
				i++
			} else if v > pivot {
				gt--
				a[i], a[gt] = a[gt], a[i]
			} else {
				i++
			}
		}

		if k < lt {
			hi = lt
		} else if k >= gt {
			lo = gt
		} else {
			return pivot
		}
	}

	slices.Sort(a[lo:hi])
	return a[k]
}

func compareLarge(a, b string) int {
	if len(a) < len(b) {
		return -1
	}
	if len(a) > len(b) {
		return 1
	}
	return strings.Compare(a, b)
}

func count(g *group) int {
	return len(g.small) + len(g.large)
}

func better(a, b *group) bool {
	ac, bc := count(a), count(b)
	if ac != bc {
		return ac > bc
	}
	return a.path < b.path
}

func writeLatency(w *bufio.Writer, small uint64, large string) {
	if large == "" {
		fmt.Fprintf(w, "%d.%d", small/10, small%10)
		return
	}
	w.WriteString(large[:len(large)-1])
	w.WriteByte('.')
	w.WriteByte(large[len(large)-1])
}

func writeRank(w *bufio.Writer, g *group, k int) {
	if k < len(g.small) {
		writeLatency(w, selectValue(g.small, k), "")
	} else {
		writeLatency(w, 0, g.large[k-len(g.small)])
	}
}

func main() {
	runtime.GOMAXPROCS(1)
	if len(os.Args) < 2 {
		return
	}

	f, err := os.Open(os.Args[1])
	if err != nil {
		return
	}
	defer f.Close()

	reader := bufio.NewReaderSize(f, 1<<20)
	groups := make(map[string]*group)
	var statuses [10]uint64
	var lines, malformed uint64
	var pending []byte
	scratch := make([]byte, 0, 128)

	for {
		part, readErr := reader.ReadSlice('\n')
		if readErr == bufio.ErrBufferFull {
			pending = append(pending, part...)
			continue
		}

		if len(part) > 0 && part[len(part)-1] == '\n' {
			line := part[:len(part)-1]
			if len(pending) > 0 {
				pending = append(pending, line...)
				line = pending
			}

			lines++
			path, whole, fraction, status, valid := parseLine(line)
			if !valid {
				malformed++
			} else {
				statuses[status]++
				scratch = templatePath(path, scratch)
				g := groups[string(scratch)]
				if g == nil {
					key := string(scratch)
					g = &group{path: key}
					groups[key] = g
				}

				value, large := parseLatency(whole, fraction)
				if large == "" {
					g.small = append(g.small, value)
					if value > g.maxSmall {
						g.maxSmall = value
					}
				} else {
					g.large = append(g.large, large)
				}
			}
			pending = pending[:0]
		}

		if readErr != nil {
			break
		}
	}

	var top [10]*group
	topN := 0
	for _, g := range groups {
		if topN == len(top) && !better(g, top[topN-1]) {
			continue
		}

		pos := topN
		if pos == len(top) {
			pos--
		}
		for pos > 0 && better(g, top[pos-1]) {
			top[pos] = top[pos-1]
			pos--
		}
		top[pos] = g
		if topN < len(top) {
			topN++
		}
	}

	out := bufio.NewWriterSize(os.Stdout, 64<<10)
	fmt.Fprintf(out, "lines %d\nmalformed %d\n", lines, malformed)
	for class, requests := range statuses {
		if requests != 0 {
			fmt.Fprintf(out, "status %dxx %d\n", class, requests)
		}
	}

	for _, g := range top[:topN] {
		n := count(g)
		if len(g.large) > 1 {
			slices.SortFunc(g.large, compareLarge)
		}

		fmt.Fprintf(out, "path %s %d ", g.path, n)
		writeRank(out, g, (n-1)/2)
		out.WriteByte(' ')
		writeRank(out, g, n-n/20-1)
		out.WriteByte(' ')
		if len(g.large) > 0 {
			writeLatency(out, 0, g.large[len(g.large)-1])
		} else {
			writeLatency(out, g.maxSmall, "")
		}
		out.WriteByte('\n')
	}
	out.Flush()
}
