// Log scan: status-class counts and latency percentiles of the busiest path templates (see SPEC.md).
//
// The file is streamed in 1 MiB chunks. Each line is checked by a hand-written matcher that accepts
// exactly the language of the SPEC regex. Path templates are interned in a map; the lookup
// m[string(b)] does not allocate, so only new templates create a string. Only the ten busiest
// templates have their latencies sorted.
package main

import (
	"bytes"
	"io"
	"os"
	"slices"
	"strconv"
)

const (
	chunkSize = 1 << 20
	topN      = 10
)

// pathChar marks the characters allowed in the path group: [A-Za-z0-9_/-].
var pathChar = func() (t [256]bool) {
	for c := range t {
		t[c] = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
			c == '_' || c == '/' || c == '-'
	}
	return t
}()

type lineInfo struct {
	status int    // first digit of the status code
	path   []byte // path group, without the query string
	tenths int64  // latency in tenths of a millisecond
}

type template struct {
	name    string
	count   int
	latency []int64
}

type scanner struct {
	total     int
	malformed int
	status    [10]int
	tmpl      []byte
	index     map[string]int32
	templates []template
}

func isDigit(c byte) bool { return c-'0' < 10 }

func isLower(c byte) bool { return c-'a' < 26 }

// hasPrefix reports whether b starts with s. The string conversion in the comparison does not allocate.
func hasPrefix(b []byte, s string) bool {
	return len(b) >= len(s) && string(b[:len(s)]) == s
}

// parseLine matches one line (without its '\n') against the SPEC regex. It reports false if malformed.
func parseLine(l []byte, out *lineInfo) bool {
	n := len(l)
	if n < 25 {
		return false
	}
	const ts = "dddd-dd-ddTdd:dd:dd.dddZ"
	for i := 0; i < 24; i++ {
		if ts[i] == 'd' {
			if !isDigit(l[i]) {
				return false
			}
		} else if l[i] != ts[i] {
			return false
		}
	}
	if l[24] != ' ' {
		return false
	}

	// Host: [a-z]+-\d+ followed by a space.
	q := 25
	s := q
	for q < n && isLower(l[q]) {
		q++
	}
	if q == s || q == n || l[q] != '-' {
		return false
	}
	q++
	s = q
	for q < n && isDigit(l[q]) {
		q++
	}
	if q == s || q == n || l[q] != ' ' {
		return false
	}
	q++

	// Method, then a space.
	switch rest := l[q:]; {
	case hasPrefix(rest, "GET "):
		q += 4
	case hasPrefix(rest, "POST "):
		q += 5
	case hasPrefix(rest, "PUT "):
		q += 4
	case hasPrefix(rest, "DELETE "):
		q += 7
	case hasPrefix(rest, "PATCH "):
		q += 6
	default:
		return false
	}

	// Path: '/' and path characters, then an optional query running to the next space.
	if q == n || l[q] != '/' {
		return false
	}
	ps := q
	q++
	for q < n && pathChar[l[q]] {
		q++
	}
	pe := q
	if q < n && l[q] == '?' {
		for q < n && l[q] != ' ' {
			q++
		}
	}
	if q == n || l[q] != ' ' {
		return false
	}
	q++

	// Status: three digits, then a space.
	if n-q < 4 || !isDigit(l[q]) || !isDigit(l[q+1]) || !isDigit(l[q+2]) || l[q+3] != ' ' {
		return false
	}
	out.status = int(l[q] - '0')
	q += 4

	// Size: \d+B followed by a space.
	s = q
	for q < n && isDigit(l[q]) {
		q++
	}
	if q == s || q == n || l[q] != 'B' {
		return false
	}
	q++
	if q == n || l[q] != ' ' {
		return false
	}
	q++

	// Latency: \d+ '.' \d 'ms' followed by a space, kept in tenths of a millisecond.
	s = q
	var whole int64
	for q < n && isDigit(l[q]) {
		whole = whole*10 + int64(l[q]-'0')
		q++
	}
	if q == s || q == n || l[q] != '.' {
		return false
	}
	q++
	if q == n || !isDigit(l[q]) {
		return false
	}
	frac := int64(l[q] - '0')
	q++
	if n-q < 3 || l[q] != 'm' || l[q+1] != 's' || l[q+2] != ' ' {
		return false
	}
	q += 3
	out.tenths = whole*10 + frac

	// User agent: "[^"]*" which must end the line.
	if n-q < 2 || l[q] != '"' || l[n-1] != '"' {
		return false
	}
	if bytes.IndexByte(l[q+1:n-1], '"') >= 0 {
		return false
	}
	out.path = l[ps:pe]
	return true
}

// buildTemplate appends the path template of path to dst[:0]: each non-empty all-digit segment becomes {id}.
func buildTemplate(dst, path []byte) []byte {
	dst = dst[:0]
	s := 0
	for {
		end := len(path)
		if i := bytes.IndexByte(path[s:], '/'); i >= 0 {
			end = s + i
		}
		seg := path[s:end]
		if len(seg) > 0 && allDigits(seg) {
			dst = append(dst, "{id}"...)
		} else {
			dst = append(dst, seg...)
		}
		if end == len(path) {
			return dst
		}
		dst = append(dst, '/')
		s = end + 1
	}
}

func allDigits(b []byte) bool {
	for _, c := range b {
		if !isDigit(c) {
			return false
		}
	}
	return true
}

func (sc *scanner) add(line []byte) {
	sc.total++
	var li lineInfo
	if !parseLine(line, &li) {
		sc.malformed++
		return
	}
	sc.status[li.status]++
	sc.tmpl = buildTemplate(sc.tmpl, li.path)
	id, ok := sc.index[string(sc.tmpl)]
	if !ok {
		id = int32(len(sc.templates))
		name := string(sc.tmpl)
		sc.templates = append(sc.templates, template{name: name})
		sc.index[name] = id
	}
	t := &sc.templates[id]
	t.count++
	t.latency = append(t.latency, li.tenths)
}

// better orders templates by count descending, then name ascending (byte order).
func (sc *scanner) better(a, b int32) bool {
	ta, tb := &sc.templates[a], &sc.templates[b]
	if ta.count != tb.count {
		return ta.count > tb.count
	}
	return ta.name < tb.name
}

func appendTenths(out []byte, t int64) []byte {
	out = strconv.AppendInt(out, t/10, 10)
	return append(out, '.', byte('0'+t%10))
}

func (sc *scanner) report() []byte {
	out := make([]byte, 0, 4096)
	out = append(out, "lines "...)
	out = strconv.AppendInt(out, int64(sc.total), 10)
	out = append(out, "\nmalformed "...)
	out = strconv.AppendInt(out, int64(sc.malformed), 10)
	out = append(out, '\n')
	for c, n := range sc.status {
		if n != 0 {
			out = append(out, "status "...)
			out = strconv.AppendInt(out, int64(c), 10)
			out = append(out, "xx "...)
			out = strconv.AppendInt(out, int64(n), 10)
			out = append(out, '\n')
		}
	}

	// Keep the topN busiest templates, best first, by insertion into a small sorted list.
	top := make([]int32, 0, topN+1)
	for i := range sc.templates {
		id := int32(i)
		if len(top) == topN {
			if !sc.better(id, top[topN-1]) {
				continue
			}
			top[topN-1] = id
		} else {
			top = append(top, id)
		}
		for k := len(top) - 1; k > 0 && sc.better(top[k], top[k-1]); k-- {
			top[k], top[k-1] = top[k-1], top[k]
		}
	}

	for _, id := range top {
		t := &sc.templates[id]
		slices.Sort(t.latency)
		n := int64(len(t.latency))
		p50 := t.latency[(50*n+99)/100-1]
		p95 := t.latency[(95*n+99)/100-1]
		slowest := t.latency[n-1]
		out = append(out, "path "...)
		out = append(out, t.name...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, int64(t.count), 10)
		out = append(out, ' ')
		out = appendTenths(out, p50)
		out = append(out, ' ')
		out = appendTenths(out, p95)
		out = append(out, ' ')
		out = appendTenths(out, slowest)
		out = append(out, '\n')
	}
	return out
}

func main() {
	if len(os.Args) < 2 {
		os.Stderr.WriteString("usage: solution INPUT_PATH\n")
		os.Exit(2)
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Stderr.WriteString("cannot open " + os.Args[1] + "\n")
		os.Exit(1)
	}
	defer f.Close()

	sc := &scanner{index: make(map[string]int32)}
	buf := make([]byte, chunkSize)
	start := 0 // first byte of the unprocessed data
	end := 0   // one past the last byte read
	eof := false
	for {
		if i := bytes.IndexByte(buf[start:end], '\n'); i >= 0 {
			sc.add(buf[start : start+i])
			start += i + 1
			continue
		}
		if eof {
			if start < end {
				sc.add(buf[start:end]) // last line without '\n'
			}
			break
		}
		// No complete line in the buffer: move the partial line to the front and read more.
		if start > 0 {
			end = copy(buf, buf[start:end])
			start = 0
		}
		if end == len(buf) { // one line longer than the buffer
			grown := make([]byte, 2*len(buf))
			copy(grown, buf[:end])
			buf = grown
		}
		n, err := f.Read(buf[end:])
		end += n
		if err == io.EOF {
			eof = true
		} else if err != nil {
			os.Stderr.WriteString("read error: " + err.Error() + "\n")
			os.Exit(1)
		}
	}

	os.Stdout.Write(sc.report())
}
