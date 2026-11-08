package main

import (
	"os"
	"sort"
	"strconv"
)

var B []byte
var LEN, P int

// ---------------------------------------------------------------------------
// Open addressing hash map whose keys are spans of the input buffer.
// ---------------------------------------------------------------------------
type SpanMap struct {
	off  []int64
	klen []int32
	v1   []int64
	v2   []int64
	cap  int
	cnt  int
}

func newSpanMap(c int) *SpanMap {
	m := &SpanMap{}
	m.init(c)
	return m
}

func (m *SpanMap) init(c int) {
	m.cap = c
	m.cnt = 0
	m.off = make([]int64, c)
	m.klen = make([]int32, c)
	m.v1 = make([]int64, c)
	m.v2 = make([]int64, c)
	for i := range m.klen {
		m.klen[i] = -1
	}
}

func hashBytes(s, n int) uint64 {
	h := uint64(1469598103934665603)
	for i := 0; i < n; i++ {
		h ^= uint64(B[s+i])
		h *= 1099511628211
	}
	return h
}

func (m *SpanMap) grow() {
	nc := m.cap * 2
	if nc == 0 {
		nc = 1024
	}
	no := make([]int64, nc)
	nl := make([]int32, nc)
	n1 := make([]int64, nc)
	n2 := make([]int64, nc)
	for i := range nl {
		nl[i] = -1
	}
	mask := nc - 1
	for j := 0; j < m.cap; j++ {
		if m.klen[j] < 0 {
			continue
		}
		i := int(hashBytes(int(m.off[j]), int(m.klen[j]))) & mask
		for nl[i] >= 0 {
			i = (i + 1) & mask
		}
		no[i] = m.off[j]
		nl[i] = m.klen[j]
		n1[i] = m.v1[j]
		n2[i] = m.v2[j]
	}
	m.off, m.klen, m.v1, m.v2 = no, nl, n1, n2
	m.cap = nc
}

func (m *SpanMap) find(s, n int) int {
	mask := m.cap - 1
	i := int(hashBytes(s, n)) & mask
	for m.klen[i] >= 0 {
		if int(m.klen[i]) == n && spanEqBytes(int(m.off[i]), int(m.off[i])+n, s, s+n) {
			return i
		}
		i = (i + 1) & mask
	}
	return -1
}

func (m *SpanMap) getOrInsert(s, n int) int {
	if (m.cnt+1)*10 > m.cap*7 {
		m.grow()
	}
	mask := m.cap - 1
	i := int(hashBytes(s, n)) & mask
	for m.klen[i] >= 0 {
		if int(m.klen[i]) == n && spanEqBytes(int(m.off[i]), int(m.off[i])+n, s, s+n) {
			return i
		}
		i = (i + 1) & mask
	}
	m.off[i] = int64(s)
	m.klen[i] = int32(n)
	m.v1[i] = 0
	m.v2[i] = 0
	m.cnt++
	return i
}

var rates, channels, accounts *SpanMap

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	B = data
	LEN = len(B)

	rates = newSpanMap(64)
	channels = newSpanMap(64)
	accounts = newSpanMap(1 << 14)

	P = 0
	skipWs()
	P++ // '{'
	for {
		skipWs()
		if B[P] == '}' {
			P++
			break
		}
		ks, ke, esc := parseString()
		if esc {
			ke = decode(ks, ke)
		}
		skipWs()
		P++ // ':'
		skipWs()
		if spanEq(ks, ke, "rates") {
			parseRatesObject()
		} else {
			skipValue()
		}
		skipWs()
		if B[P] == ',' {
			P++
			continue
		}
		if B[P] == '}' {
			P++
			break
		}
	}

	for {
		skipWs()
		if P >= LEN {
			break
		}
		parseTransaction()
	}

	writeOutput()
}

func skipWs() {
	for P < LEN {
		c := B[P]
		if c == ' ' || c == '\t' || c == '\n' || c == '\r' {
			P++
		} else {
			break
		}
	}
}

func parseString() (int, int, bool) {
	P++
	s := P
	esc := false
	for {
		c := B[P]
		if c == '"' {
			e := P
			P++
			return s, e, esc
		}
		if c == '\\' {
			esc = true
			P += 2
		} else {
			P++
		}
	}
}

func hex4(p []byte) uint32 {
	var v uint32
	for i := 0; i < 4; i++ {
		c := p[i]
		var d uint32
		if c >= '0' && c <= '9' {
			d = uint32(c - '0')
		} else if c >= 'a' && c <= 'f' {
			d = uint32(c-'a') + 10
		} else {
			d = uint32(c-'A') + 10
		}
		v = (v << 4) | d
	}
	return v
}

func decode(s, e int) int {
	w, r := s, s
	for r < e {
		c := B[r]
		r++
		if c != '\\' {
			B[w] = c
			w++
			continue
		}
		x := B[r]
		r++
		switch x {
		case '"':
			B[w] = '"'
			w++
		case '\\':
			B[w] = '\\'
			w++
		case '/':
			B[w] = '/'
			w++
		case 'b':
			B[w] = 8
			w++
		case 'f':
			B[w] = 12
			w++
		case 'n':
			B[w] = '\n'
			w++
		case 'r':
			B[w] = '\r'
			w++
		case 't':
			B[w] = '\t'
			w++
		case 'u':
			cp := hex4(B[r:])
			r += 4
			if cp >= 0xD800 && cp <= 0xDBFF && r+6 <= e && B[r] == '\\' && B[r+1] == 'u' {
				lo := hex4(B[r+2:])
				if lo >= 0xDC00 && lo <= 0xDFFF {
					cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
					r += 6
				}
			}
			if cp < 0x80 {
				B[w] = byte(cp)
				w++
			} else if cp < 0x800 {
				B[w] = byte(0xC0 | (cp >> 6))
				B[w+1] = byte(0x80 | (cp & 0x3F))
				w += 2
			} else if cp < 0x10000 {
				B[w] = byte(0xE0 | (cp >> 12))
				B[w+1] = byte(0x80 | ((cp >> 6) & 0x3F))
				B[w+2] = byte(0x80 | (cp & 0x3F))
				w += 3
			} else {
				B[w] = byte(0xF0 | (cp >> 18))
				B[w+1] = byte(0x80 | ((cp >> 12) & 0x3F))
				B[w+2] = byte(0x80 | ((cp >> 6) & 0x3F))
				B[w+3] = byte(0x80 | (cp & 0x3F))
				w += 4
			}
		default:
			B[w] = x
			w++
		}
	}
	return w
}

func parseStringValue() (int, int) {
	s, e, esc := parseString()
	if esc {
		e = decode(s, e)
	}
	return s, e
}

func spanEq(s, e int, lit string) bool {
	n := e - s
	if n != len(lit) {
		return false
	}
	for i := 0; i < n; i++ {
		if B[s+i] != lit[i] {
			return false
		}
	}
	return true
}

func spanEqBytes(s, e, s2, e2 int) bool {
	n := e - s
	if n != e2-s2 {
		return false
	}
	for i := 0; i < n; i++ {
		if B[s+i] != B[s2+i] {
			return false
		}
	}
	return true
}

func skipValue() {
	skipWs()
	c := B[P]
	if c == '"' {
		parseString()
		return
	}
	if c == '{' || c == '[' {
		depth := 0
		for {
			c = B[P]
			if c == '"' {
				parseString()
			} else {
				P++
				if c == '{' || c == '[' {
					depth++
				} else if c == '}' || c == ']' {
					depth--
					if depth == 0 {
						return
					}
				}
			}
		}
	}
	for P < LEN {
		c = B[P]
		if c == ',' || c == '}' || c == ']' || c == ' ' || c == '\t' || c == '\n' || c == '\r' {
			return
		}
		P++
	}
}

func parseAmount(s, e int) int64 {
	var ip int64
	i := s
	for i < e && B[i] != '.' {
		ip = ip*10 + int64(B[i]-'0')
		i++
	}
	var frac int64
	if i < e {
		i++
		digits := 0
		for i < e {
			frac = frac*10 + int64(B[i]-'0')
			i++
			digits++
		}
		if digits == 1 {
			frac *= 10
		}
	}
	return ip*100 + frac
}

func typeKind(s, e int) int {
	n := e - s
	if n == 6 {
		if spanEq(s, e, "credit") {
			return 0
		}
		if spanEq(s, e, "refund") {
			return 2
		}
	} else if n == 5 {
		if spanEq(s, e, "debit") {
			return 1
		}
	} else if n == 4 {
		if spanEq(s, e, "void") {
			return 3
		}
	}
	return -1
}

func parseTags() bool {
	P++
	hasTest := false
	for {
		skipWs()
		if B[P] == ']' {
			P++
			return hasTest
		}
		s, e := parseStringValue()
		if spanEq(s, e, "test") {
			hasTest = true
		}
		skipWs()
		if B[P] == ',' {
			P++
			continue
		}
		if B[P] == ']' {
			P++
			return hasTest
		}
	}
}

func parseMeta() (int, int, bool) {
	P++
	var chS, chE int
	chSet := false
	for {
		skipWs()
		if B[P] == '}' {
			P++
			return chS, chE, chSet
		}
		ks, ke, esc := parseString()
		if esc {
			ke = decode(ks, ke)
		}
		skipWs()
		P++
		skipWs()
		if spanEq(ks, ke, "channel") {
			chS, chE = parseStringValue()
			chSet = true
		} else {
			skipValue()
		}
		skipWs()
		if B[P] == ',' {
			P++
			continue
		}
		if B[P] == '}' {
			P++
			return chS, chE, chSet
		}
	}
}

func parseRatesObject() {
	P++
	for {
		skipWs()
		if B[P] == '}' {
			P++
			return
		}
		ks, ke, esc := parseString()
		if esc {
			ke = decode(ks, ke)
		}
		skipWs()
		P++
		skipWs()
		var v int64
		neg := false
		if B[P] == '-' {
			neg = true
			P++
		}
		for P < LEN {
			c := B[P]
			if c < '0' || c > '9' {
				break
			}
			v = v*10 + int64(c-'0')
			P++
		}
		if neg {
			v = -v
		}
		idx := rates.getOrInsert(ks, ke-ks)
		rates.v1[idx] = v
		skipWs()
		if B[P] == ',' {
			P++
			continue
		}
		if B[P] == '}' {
			P++
			return
		}
	}
}

var totalNet int64
var totalCount int64

func parseTransaction() {
	P++
	var accS, accE int
	var chS, chE int
	var hundredths int64
	var rate int64
	typ := -1
	hasTest := false

	for {
		skipWs()
		if B[P] == '}' {
			P++
			break
		}
		ks, ke, esc := parseString()
		if esc {
			ke = decode(ks, ke)
		}
		skipWs()
		P++
		skipWs()

		switch {
		case spanEq(ks, ke, "account"):
			accS, accE = parseStringValue()
		case spanEq(ks, ke, "type"):
			s, e := parseStringValue()
			typ = typeKind(s, e)
		case spanEq(ks, ke, "amount"):
			s, e := parseStringValue()
			hundredths = parseAmount(s, e)
		case spanEq(ks, ke, "currency"):
			s, e := parseStringValue()
			ri := rates.find(s, e-s)
			if ri >= 0 {
				rate = rates.v1[ri]
			} else {
				rate = 0
			}
		case spanEq(ks, ke, "tags"):
			hasTest = parseTags()
		case spanEq(ks, ke, "meta"):
			chS, chE, _ = parseMeta()
		default:
			skipValue()
		}

		skipWs()
		if B[P] == ',' {
			P++
			continue
		}
		if B[P] == '}' {
			P++
			break
		}
	}

	if typ == 3 || typ == -1 || hasTest {
		return
	}

	usd := (hundredths * rate) / 1000000
	var signed int64
	if typ == 1 {
		signed = -usd
	} else {
		signed = usd
	}
	totalNet += signed
	totalCount++

	ci := channels.getOrInsert(chS, chE-chS)
	channels.v1[ci]++
	channels.v2[ci] += signed

	ai := accounts.getOrInsert(accS, accE-accS)
	accounts.v1[ai] += signed
}

func spanLess(o1 int64, l1 int32, o2 int64, l2 int32) bool {
	n := int(l1)
	if int(l2) < n {
		n = int(l2)
	}
	a := B[o1 : o1+int64(n)]
	b := B[o2 : o2+int64(n)]
	for i := 0; i < n; i++ {
		if a[i] != b[i] {
			return a[i] < b[i]
		}
	}
	return l1 < l2
}

func writeOutput() {
	var chIdx []int
	for i := 0; i < channels.cap; i++ {
		if channels.klen[i] >= 0 {
			chIdx = append(chIdx, i)
		}
	}
	sort.Slice(chIdx, func(a, b int) bool {
		i, j := chIdx[a], chIdx[b]
		return spanLess(channels.off[i], channels.klen[i], channels.off[j], channels.klen[j])
	})

	var accIdx []int
	for i := 0; i < accounts.cap; i++ {
		if accounts.klen[i] >= 0 {
			accIdx = append(accIdx, i)
		}
	}
	k := len(accIdx)
	if k > 10 {
		k = 10
	}
	if k > 0 {
		sort.Slice(accIdx, func(a, b int) bool {
			i, j := accIdx[a], accIdx[b]
			if accounts.v1[i] != accounts.v1[j] {
				return accounts.v1[i] > accounts.v1[j]
			}
			return spanLess(accounts.off[i], accounts.klen[i], accounts.off[j], accounts.klen[j])
		})
		accIdx = accIdx[:k]
	}

	out := make([]byte, 0, 8192)
	out = append(out, "counted "...)
	out = strconv.AppendInt(out, totalCount, 10)
	out = append(out, "\nnet "...)
	out = strconv.AppendInt(out, totalNet, 10)
	out = append(out, '\n')

	for _, idx := range chIdx {
		out = append(out, "channel "...)
		out = append(out, B[channels.off[idx]:channels.off[idx]+int64(channels.klen[idx])]...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, channels.v1[idx], 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, channels.v2[idx], 10)
		out = append(out, '\n')
	}

	for _, idx := range accIdx {
		out = append(out, "account "...)
		out = append(out, B[accounts.off[idx]:accounts.off[idx]+int64(accounts.klen[idx])]...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, accounts.v1[idx], 10)
		out = append(out, '\n')
	}

	os.Stdout.Write(out)
}
