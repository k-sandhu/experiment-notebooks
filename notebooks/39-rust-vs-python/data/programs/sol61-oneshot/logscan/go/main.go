package main

import (
	"bufio"
	"bytes"
	"fmt"
	"math/bits"
	"os"
	"runtime"
	"slices"
	"strconv"
)

var timestampDigits = [...]uint8{
	0, 1, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 22,
}

var pathAllowed = func() [256]bool {
	var a [256]bool
	for c := byte('a'); c <= 'z'; c++ {
		a[c] = true
	}
	for c := byte('A'); c <= 'Z'; c++ {
		a[c] = true
	}
	for c := byte('0'); c <= '9'; c++ {
		a[c] = true
	}
	a['_'], a['/'], a['-'] = true, true, true
	return a
}()

type pathStats struct {
	values []uint64
	large  []string
}

type entry struct {
	name  string
	stats *pathStats
	count int
}

func digit(c byte) bool {
	return c-'0' <= 9
}

func parseLine(s []byte) (path []byte, status byte, value uint64, large string, ok bool) {
	n := len(s)
	if n < 50 {
		return
	}
	if s[4] != '-' || s[7] != '-' || s[10] != 'T' ||
		s[13] != ':' || s[16] != ':' || s[19] != '.' ||
		s[23] != 'Z' || s[24] != ' ' {
		return
	}
	for _, p := range timestampDigits[:] {
		if !digit(s[p]) {
			return
		}
	}

	i := 25
	start := i
	for i < n && s[i] >= 'a' && s[i] <= 'z' {
		i++
	}
	if i == start || i >= n || s[i] != '-' {
		return
	}
	i++
	start = i
	for i < n && digit(s[i]) {
		i++
	}
	if i == start || i >= n || s[i] != ' ' {
		return
	}
	i++

	if n-i < 7 {
		return
	}
	switch {
	case string(s[i:i+4]) == "GET ":
		i += 4
	case string(s[i:i+5]) == "POST ":
		i += 5
	case string(s[i:i+4]) == "PUT ":
		i += 4
	case string(s[i:i+7]) == "DELETE ":
		i += 7
	case string(s[i:i+6]) == "PATCH ":
		i += 6
	default:
		return
	}

	if i >= n || s[i] != '/' {
		return
	}
	start = i
	for i < n && pathAllowed[s[i]] {
		i++
	}
	path = s[start:i]

	if i < n && s[i] == '?' {
		i++
		for i < n && s[i] != ' ' {
			i++
		}
	}
	if i >= n || s[i] != ' ' {
		return
	}
	i++

	if n-i < 4 || !digit(s[i]) || !digit(s[i+1]) ||
		!digit(s[i+2]) || s[i+3] != ' ' {
		return
	}
	status = s[i] - '0'
	i += 4

	start = i
	for i < n && digit(s[i]) {
		i++
	}
	if i == start || n-i < 2 || s[i] != 'B' || s[i+1] != ' ' {
		return
	}
	i += 2

	start = i
	overflow := false
	const limit = uint64(1844674407370955161)

	for i < n && digit(s[i]) {
		d := uint64(s[i] - '0')
		if !overflow {
			if value > limit || (value == limit && d > 5) {
				overflow = true
			} else {
				value = value*10 + d
			}
		}
		i++
	}

	if i == start || n-i < 7 ||
		s[i] != '.' || !digit(s[i+1]) ||
		s[i+2] != 'm' || s[i+3] != 's' ||
		s[i+4] != ' ' || s[i+5] != '"' ||
		s[n-1] != '"' {
		return
	}
	if bytes.IndexByte(s[i+6:n-1], '"') >= 0 {
		return
	}

	d := uint64(s[i+1] - '0')
	if !overflow {
		if value > limit || (value == limit && d > 5) {
			overflow = true
		} else {
			value = value*10 + d
		}
	}

	if overflow {
		for start < i && s[start] == '0' {
			start++
		}
		large = string(s[start:i]) + string(s[i+1:i+2])
	}
	ok = true
	return
}

func makeTemplate(dst, path []byte) []byte {
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
			dst = append(dst, "{id}"...)
		} else {
			dst = append(dst, path[start:i]...)
		}
	}
	return dst
}

func better(a, b entry) bool {
	return a.count > b.count || (a.count == b.count && a.name < b.name)
}

func selectK(a []uint64, k int) uint64 {
	budget := 2 * bits.Len(uint(len(a)))
	for len(a) > 24 {
		if budget == 0 {
			slices.Sort(a)
			return a[k]
		}
		budget--

		x, y, z := a[0], a[len(a)/2], a[len(a)-1]
		if x > y {
			x, y = y, x
		}
		if y > z {
			y, z = z, y
		}
		if x > y {
			x, y = y, x
		}
		pivot := y

		lt, i, gt := 0, 0, len(a)
		for i < gt {
			v := a[i]
			if v < pivot {
				a[lt], a[i] = v, a[lt]
				lt++
				i++
			} else if v > pivot {
				gt--
				a[i], a[gt] = a[gt], v
			} else {
				i++
			}
		}

		if k < lt {
			a = a[:lt]
		} else if k >= gt {
			a = a[gt:]
			k -= gt
		} else {
			return pivot
		}
	}
	slices.Sort(a)
	return a[k]
}

func formatSmall(v uint64) string {
	var storage [32]byte
	b := strconv.AppendUint(storage[:0], v/10, 10)
	b = append(b, '.', byte(v%10)+'0')
	return string(b)
}

func formatLarge(v string) string {
	if len(v) == 1 {
		return "0." + v
	}
	return v[:len(v)-1] + "." + v[len(v)-1:]
}

func summarize(s *pathStats) (p50, p95, maximum string) {
	small := s.values
	large := s.large
	n := len(small) + len(large)
	k50 := (n - 1) / 2
	k95 := n - 1 - n/20

	if len(large) > 1 {
		slices.SortFunc(large, func(a, b string) int {
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
	}

	var v50 uint64
	if k50 < len(small) {
		v50 = selectK(small, k50)
		p50 = formatSmall(v50)
	} else {
		p50 = formatLarge(large[k50-len(small)])
	}

	if k95 < len(small) {
		if k95 == k50 {
			p95 = formatSmall(v50)
		} else {
			v95 := selectK(small[k50+1:], k95-k50-1)
			p95 = formatSmall(v95)
		}
	} else {
		p95 = formatLarge(large[k95-len(small)])
	}

	if len(large) != 0 {
		maximum = formatLarge(large[len(large)-1])
	} else {
		var maximumValue uint64
		for _, v := range small {
			if v > maximumValue {
				maximumValue = v
			}
		}
		maximum = formatSmall(maximumValue)
	}
	return
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
	paths := make(map[string]*pathStats)
	template := make([]byte, 0, 256)
	var longLine []byte
	var lines, malformed uint64
	var statuses [10]uint64

	for {
		line, readErr := reader.ReadSlice('\n')
		if readErr == bufio.ErrBufferFull {
			longLine = append(longLine, line...)
			continue
		}
		if len(longLine) != 0 {
			longLine = append(longLine, line...)
			line = longLine
		}

		if len(line) != 0 && line[len(line)-1] == '\n' {
			lines++
			path, status, value, large, valid := parseLine(line[:len(line)-1])
			if !valid {
				malformed++
			} else {
				statuses[status]++
				template = makeTemplate(template, path)
				stats := paths[string(template)]
				if stats == nil {
					key := string(template)
					stats = &pathStats{}
					paths[key] = stats
				}
				if large == "" {
					stats.values = append(stats.values, value)
				} else {
					stats.large = append(stats.large, large)
				}
			}
		}

		longLine = longLine[:0]
		if readErr != nil {
			break
		}
	}

	var top [10]entry
	used := 0
	for name, stats := range paths {
		e := entry{
			name:  name,
			stats: stats,
			count: len(stats.values) + len(stats.large),
		}
		if used == len(top) && !better(e, top[len(top)-1]) {
			continue
		}
		pos := used
		if pos == len(top) {
			pos--
		}
		for pos > 0 && better(e, top[pos-1]) {
			top[pos] = top[pos-1]
			pos--
		}
		top[pos] = e
		if used < len(top) {
			used++
		}
	}

	out := bufio.NewWriterSize(os.Stdout, 64<<10)
	fmt.Fprintf(out, "lines %d\nmalformed %d\n", lines, malformed)
	for class, count := range statuses {
		if count != 0 {
			fmt.Fprintf(out, "status %dxx %d\n", class, count)
		}
	}
	for _, e := range top[:used] {
		p50, p95, maximum := summarize(e.stats)
		fmt.Fprintf(out, "path %s %d %s %s %s\n",
			e.name, e.count, p50, p95, maximum)
	}
	out.Flush()
}
