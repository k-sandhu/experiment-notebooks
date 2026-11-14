// Log scan: reads the file in large chunks, matches each line with a hand-written
// parser and interns path templates in an open-addressing hash table.
package main

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"io"
	"os"
	"strconv"
)

const (
	cDigit = 1
	cLower = 2
	cPath  = 4
)

var ct [256]byte

func init() {
	for c := '0'; c <= '9'; c++ {
		ct[c] |= cDigit | cPath
	}
	for c := 'a'; c <= 'z'; c++ {
		ct[c] |= cLower | cPath
	}
	for c := 'A'; c <= 'Z'; c++ {
		ct[c] |= cPath
	}
	ct['_'] |= cPath
	ct['-'] |= cPath
	ct['/'] |= cPath
}

func isDigit(c byte) bool { return c-'0' < 10 }

type table struct {
	arena    []byte
	off, ln  []int32
	count    []int32
	slotID   []int32 // id + 1, 0 = empty
	slotHash []uint32
	mask     uint32
}

func newTable() *table {
	return &table{
		arena:    make([]byte, 0, 1<<16),
		slotID:   make([]int32, 1024),
		slotHash: make([]uint32, 1024),
		mask:     1023,
	}
}

func (t *table) key(id int32) []byte {
	return t.arena[t.off[id] : t.off[id]+t.ln[id]]
}

func (t *table) intern(key []byte, h uint32) int32 {
	i := h & t.mask
	for {
		s := t.slotID[i]
		if s == 0 {
			break
		}
		if t.slotHash[i] == h {
			id := s - 1
			if bytes.Equal(t.key(id), key) {
				t.count[id]++
				return id
			}
		}
		i = (i + 1) & t.mask
	}
	id := int32(len(t.off))
	t.off = append(t.off, int32(len(t.arena)))
	t.ln = append(t.ln, int32(len(key)))
	t.count = append(t.count, 1)
	t.arena = append(t.arena, key...)
	t.slotID[i] = id + 1
	t.slotHash[i] = h
	if len(t.off)*2 > len(t.slotID) {
		t.grow()
	}
	return id
}

func (t *table) grow() {
	oldID, oldHash := t.slotID, t.slotHash
	t.slotID = make([]int32, len(oldID)*2)
	t.slotHash = make([]uint32, len(oldID)*2)
	t.mask = uint32(len(t.slotID) - 1)
	for j, s := range oldID {
		if s == 0 {
			continue
		}
		i := oldHash[j] & t.mask
		for t.slotID[i] != 0 {
			i = (i + 1) & t.mask
		}
		t.slotID[i] = s
		t.slotHash[i] = oldHash[j]
	}
}

type state struct {
	lines, malformed int64
	status           [10]int64
	tbl              *table
	ids              []int32
	lats             []int64
	tbuf             []byte
}

// parseLine parses the line starting at b[p], which is terminated by '\n'. It returns
// the start of the next line and true if the line is well-formed, otherwise a position
// inside the line (at or before its '\n') and false.
func (st *state) parseLine(b []byte, p int) (int, bool) {
	if len(b)-p < 25 {
		return p, false
	}
	l := b[p : p+25]
	if !(isDigit(l[0]) && isDigit(l[1]) && isDigit(l[2]) && isDigit(l[3]) && l[4] == '-' && isDigit(l[5]) &&
		isDigit(l[6]) && l[7] == '-' && isDigit(l[8]) && isDigit(l[9]) && l[10] == 'T' && isDigit(l[11]) &&
		isDigit(l[12]) && l[13] == ':' && isDigit(l[14]) && isDigit(l[15]) && l[16] == ':' && isDigit(l[17]) &&
		isDigit(l[18]) && l[19] == '.' && isDigit(l[20]) && isDigit(l[21]) && isDigit(l[22]) && l[23] == 'Z' &&
		l[24] == ' ') {
		return p, false
	}
	p += 25
	// Host: [a-z]+-\d+
	if ct[b[p]]&cLower == 0 {
		return p, false
	}
	p++
	for ct[b[p]]&cLower != 0 {
		p++
	}
	if b[p] != '-' {
		return p, false
	}
	p++
	if !isDigit(b[p]) {
		return p, false
	}
	p++
	for isDigit(b[p]) {
		p++
	}
	if b[p] != ' ' {
		return p, false
	}
	p++
	// Method
	if len(b)-p < 7 {
		return p, false
	}
	m := b[p : p+7]
	switch m[0] {
	case 'G':
		if m[1] != 'E' || m[2] != 'T' {
			return p, false
		}
		p += 3
	case 'P':
		if m[1] == 'U' && m[2] == 'T' {
			p += 3
		} else if m[1] == 'O' && m[2] == 'S' && m[3] == 'T' {
			p += 4
		} else if m[1] == 'A' && m[2] == 'T' && m[3] == 'C' && m[4] == 'H' {
			p += 5
		} else {
			return p, false
		}
	case 'D':
		if m[1] != 'E' || m[2] != 'L' || m[3] != 'E' || m[4] != 'T' || m[5] != 'E' {
			return p, false
		}
		p += 6
	default:
		return p, false
	}
	if b[p] != ' ' {
		return p, false
	}
	p++
	// Path, building the template as we go.
	if b[p] != '/' {
		return p, false
	}
	p++
	t := append(st.tbuf[:0], '/')
	var c byte
	for {
		seg := p
		allDigit := true
		for {
			c = b[p]
			if ct[c]&cPath == 0 || c == '/' {
				break
			}
			allDigit = allDigit && isDigit(c)
			p++
		}
		if p != seg && allDigit {
			t = append(t, "{id}"...)
		} else {
			t = append(t, b[seg:p]...)
		}
		if c != '/' {
			break
		}
		t = append(t, '/')
		p++
	}
	st.tbuf = t
	if c == '?' {
		p++
		for b[p] != ' ' && b[p] != '\n' {
			p++
		}
	}
	if b[p] != ' ' {
		return p, false
	}
	p++
	// Status
	if len(b)-p < 4 {
		return p, false
	}
	s := b[p : p+4]
	if !(isDigit(s[0]) && isDigit(s[1]) && isDigit(s[2]) && s[3] == ' ') {
		return p, false
	}
	cls := s[0] - '0'
	p += 4
	// Size
	if !isDigit(b[p]) {
		return p, false
	}
	p++
	for isDigit(b[p]) {
		p++
	}
	if b[p] != 'B' || b[p+1] != ' ' {
		return p, false
	}
	p += 2
	// Latency
	if !isDigit(b[p]) {
		return p, false
	}
	var lat int64
	for isDigit(b[p]) {
		lat = lat*10 + int64(b[p]-'0')
		p++
	}
	if len(b)-p < 6 {
		return p, false
	}
	r := b[p : p+6]
	if r[0] != '.' || !isDigit(r[1]) || r[2] != 'm' || r[3] != 's' || r[4] != ' ' || r[5] != '"' {
		return p, false
	}
	lat = lat*10 + int64(r[1]-'0')
	p += 6
	// User agent
	nl := bytes.IndexByte(b[p:], '\n')
	if nl == 0 || b[p+nl-1] != '"' || bytes.IndexByte(b[p:p+nl-1], '"') >= 0 {
		return p, false
	}
	p += nl + 1

	id := st.tbl.intern(t, hashBytes(t))
	st.status[cls]++
	st.ids = append(st.ids, id)
	st.lats = append(st.lats, lat)
	return p, true
}

// hashBytes hashes b 8 bytes at a time.
func hashBytes(b []byte) uint32 {
	h := 0x9E3779B97F4A7C15 ^ uint64(len(b))
	for len(b) >= 8 {
		h = (h ^ binary.LittleEndian.Uint64(b)) * 0xFF51AFD7ED558CCD
		h ^= h >> 29
		b = b[8:]
	}
	if len(b) > 0 {
		var w uint64
		for i, c := range b {
			w |= uint64(c) << (8 * i)
		}
		h = (h ^ w) * 0xFF51AFD7ED558CCD
		h ^= h >> 29
	}
	h *= 0xC4CEB9FE1A85EC53
	return uint32(h ^ (h >> 32))
}

// processLines handles all complete lines in b (which ends with '\n').
func (st *state) processLines(b []byte) {
	p := 0
	var nLines, nBad int64
	for p < len(b) {
		nLines++
		r, ok := st.parseLine(b, p)
		if ok {
			p = r
		} else {
			nBad++
			p = r + bytes.IndexByte(b[r:], '\n') + 1
		}
	}
	st.lines += nLines
	st.malformed += nBad
}

// selectK places the k-th smallest element at a[k], partitioned around it.
func selectK(a []int64, lo, hi, k int) {
	for hi > lo {
		mid := int(uint(lo+hi) >> 1)
		if a[mid] < a[lo] {
			a[mid], a[lo] = a[lo], a[mid]
		}
		if a[hi] < a[lo] {
			a[hi], a[lo] = a[lo], a[hi]
		}
		if a[hi] < a[mid] {
			a[hi], a[mid] = a[mid], a[hi]
		}
		pivot := a[mid]
		i, j := lo, hi
		for i <= j {
			for a[i] < pivot {
				i++
			}
			for a[j] > pivot {
				j--
			}
			if i <= j {
				a[i], a[j] = a[j], a[i]
				i++
				j--
			}
		}
		if k <= j {
			hi = j
		} else if k >= i {
			lo = i
		} else {
			return
		}
	}
}

func appendLat(o []byte, v int64) []byte {
	o = strconv.AppendInt(o, v/10, 10)
	return append(o, '.', byte('0'+v%10))
}

func main() {
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	st := &state{
		tbl:  newTable(),
		ids:  make([]int32, 0, 1<<20),
		lats: make([]int64, 0, 1<<20),
		tbuf: make([]byte, 0, 4096),
	}

	bufSize := 1 << 22
	buf := make([]byte, bufSize)
	have := 0
	for {
		n, err := io.ReadFull(f, buf[have:])
		have += n
		eof := err != nil
		if have == 0 {
			break
		}
		lastNl := bytes.LastIndexByte(buf[:have], '\n')
		if lastNl < 0 {
			if eof {
				// Trailing data without a newline (not expected): treat it as a line.
				if have == len(buf) {
					buf = append(buf, '\n')
				} else {
					buf[have] = '\n'
				}
				have++
				lastNl = have - 1
			} else {
				nb := make([]byte, len(buf)*2)
				copy(nb, buf[:have])
				buf = nb
				continue
			}
		}
		st.processLines(buf[:lastNl+1])
		have = copy(buf, buf[lastNl+1:have])
		if eof && have == 0 {
			break
		}
	}
	f.Close()

	tbl := st.tbl
	nt := len(tbl.off)
	better := func(a, b int32) bool {
		if tbl.count[a] != tbl.count[b] {
			return tbl.count[a] > tbl.count[b]
		}
		return bytes.Compare(tbl.key(a), tbl.key(b)) < 0
	}
	top := make([]int32, 0, 11)
	for id := int32(0); id < int32(nt); id++ {
		if len(top) == 10 && !better(id, top[9]) {
			continue
		}
		top = append(top, id)
		for pos := len(top) - 1; pos > 0 && better(top[pos], top[pos-1]); pos-- {
			top[pos], top[pos-1] = top[pos-1], top[pos]
		}
		if len(top) > 10 {
			top = top[:10]
		}
	}

	rank := make([]int8, nt)
	for i := range rank {
		rank[i] = -1
	}
	buckets := make([][]int64, len(top))
	for r, id := range top {
		rank[id] = int8(r)
		buckets[r] = make([]int64, 0, tbl.count[id])
	}
	for i, id := range st.ids {
		if r := rank[id]; r >= 0 {
			buckets[r] = append(buckets[r], st.lats[i])
		}
	}

	o := make([]byte, 0, 1024)
	o = append(o, "lines "...)
	o = strconv.AppendInt(o, st.lines, 10)
	o = append(o, "\nmalformed "...)
	o = strconv.AppendInt(o, st.malformed, 10)
	o = append(o, '\n')
	for c := 0; c < 10; c++ {
		if st.status[c] != 0 {
			o = append(o, "status "...)
			o = append(o, byte('0'+c), 'x', 'x', ' ')
			o = strconv.AppendInt(o, st.status[c], 10)
			o = append(o, '\n')
		}
	}
	for r, id := range top {
		v := buckets[r]
		n := len(v)
		k50 := (50*n+99)/100 - 1
		k95 := (95*n+99)/100 - 1
		selectK(v, 0, n-1, k50)
		p50 := v[k50]
		selectK(v, k50, n-1, k95)
		p95 := v[k95]
		mx := p95
		for _, x := range v[k95+1:] {
			if x > mx {
				mx = x
			}
		}
		o = append(o, "path "...)
		o = append(o, tbl.key(id)...)
		o = append(o, ' ')
		o = strconv.AppendInt(o, int64(n), 10)
		o = append(o, ' ')
		o = appendLat(o, p50)
		o = append(o, ' ')
		o = appendLat(o, p95)
		o = append(o, ' ')
		o = appendLat(o, mx)
		o = append(o, '\n')
	}
	w := bufio.NewWriter(os.Stdout)
	w.Write(o)
	w.Flush()
}
