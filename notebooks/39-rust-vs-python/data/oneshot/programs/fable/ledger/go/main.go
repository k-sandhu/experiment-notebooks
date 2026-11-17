package main

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"math/bits"
	"os"
	"runtime/debug"
	"slices"
	"strconv"
	"strings"
	"unicode/utf8"
)

const (
	swarLo = 0x0101010101010101
	swarHi = 0x8080808080808080
	hk1    = 0x9E3779B97F4A7C15
	hk2    = 0xBF58476D1CE4E5B9
)

type entry struct {
	key   string
	hash  uint64
	net   int64
	count int64
}

type table struct {
	entries []entry
	slots   []uint64
	mask    uint64
}

func newTable(size int) *table {
	return &table{slots: make([]uint64, size), mask: uint64(size - 1)}
}

func hashBytes(b []byte) uint64 {
	h := uint64(len(b)) * hk1
	for len(b) >= 8 {
		h = (h ^ binary.LittleEndian.Uint64(b)) * hk1
		h ^= h >> 32
		b = b[8:]
	}
	if len(b) > 0 {
		var v uint64
		for i := len(b) - 1; i >= 0; i-- {
			v = v<<8 | uint64(b[i])
		}
		h = (h ^ v) * hk1
		h ^= h >> 32
	}
	h *= hk2
	h ^= h >> 29
	return h
}

func (t *table) get(k []byte) *entry {
	h := hashBytes(k)
	tag := h &^ 0xFFFFFFFF
	pos := h & t.mask
	for {
		s := t.slots[pos]
		if s == 0 {
			break
		}
		if s&^0xFFFFFFFF == tag {
			e := &t.entries[uint32(s)-1]
			if e.key == string(k) {
				return e
			}
		}
		pos = (pos + 1) & t.mask
	}
	t.entries = append(t.entries, entry{key: string(k), hash: h})
	idx := len(t.entries)
	t.slots[pos] = tag | uint64(idx)
	if idx*2 > len(t.slots) {
		t.grow()
	}
	return &t.entries[idx-1]
}

func (t *table) grow() {
	ns := make([]uint64, len(t.slots)*2)
	mask := uint64(len(ns) - 1)
	for idx := range t.entries {
		h := t.entries[idx].hash
		pos := h & mask
		for ns[pos] != 0 {
			pos = (pos + 1) & mask
		}
		ns[pos] = h&^0xFFFFFFFF | uint64(idx+1)
	}
	t.slots = ns
	t.mask = mask
}

type rateEnt struct {
	name string
	rate int64
}

type ledger struct {
	haveRates bool
	rates     []rateEnt
	rateMap   map[string]int64
	scratch   []byte
	counted   int64
	net       int64
	chans     *table
	accts     *table
}

func (L *ledger) setRate(name string, v int64) {
	for i := range L.rates {
		if L.rates[i].name == name {
			L.rates[i].rate = v
			L.rateMap[name] = v
			return
		}
	}
	L.rates = append(L.rates, rateEnt{name, v})
	L.rateMap[name] = v
}

func (L *ledger) rate(v []byte) int64 {
	if len(L.rates) <= 8 {
		for i := range L.rates {
			if L.rates[i].name == string(v) {
				return L.rates[i].rate
			}
		}
		return 0
	}
	return L.rateMap[string(v)]
}

// scanStr: i is the index just after the opening quote. Returns the index of
// the closing quote (or -1) and whether any escape was seen.
func scanStr(d []byte, i int) (int, bool) {
	esc := false
	n := len(d)
	for i+8 <= n {
		w := binary.LittleEndian.Uint64(d[i:])
		q := w ^ 0x2222222222222222
		b := w ^ 0x5c5c5c5c5c5c5c5c
		m := ((q-swarLo)&^q | (b-swarLo)&^b) & swarHi
		if m != 0 {
			j := i + bits.TrailingZeros64(m)>>3
			if d[j] == '"' {
				return j, esc
			}
			esc = true
			i = j + 2
			continue
		}
		i += 8
	}
	for i < n {
		c := d[i]
		if c == '"' {
			return i, esc
		}
		if c == '\\' {
			esc = true
			i += 2
			continue
		}
		i++
	}
	return -1, esc
}

// skipValue skips a JSON value starting at i; returns index after it or -1.
func skipValue(d []byte, i int) int {
	n := len(d)
	if i >= n {
		return -1
	}
	c := d[i]
	if c == '"' {
		e, _ := scanStr(d, i+1)
		if e < 0 {
			return -1
		}
		return e + 1
	}
	if c == '{' || c == '[' {
		depth := 1
		i++
		for i < n {
			c = d[i]
			switch c {
			case '"':
				e, _ := scanStr(d, i+1)
				if e < 0 {
					return -1
				}
				i = e + 1
			case '{', '[':
				depth++
				i++
			case '}', ']':
				depth--
				i++
				if depth == 0 {
					return i
				}
			default:
				i++
			}
		}
		return -1
	}
	for i < n {
		c = d[i]
		if c == ',' || c == '}' || c == ']' || c <= ' ' {
			return i
		}
		i++
	}
	return i
}

func hex4(s []byte, i int) int {
	if i+4 > len(s) {
		return -1
	}
	r := 0
	for j := i; j < i+4; j++ {
		c := s[j]
		var v int
		switch {
		case c >= '0' && c <= '9':
			v = int(c - '0')
		case c >= 'a' && c <= 'f':
			v = int(c-'a') + 10
		case c >= 'A' && c <= 'F':
			v = int(c-'A') + 10
		default:
			return -1
		}
		r = r<<4 | v
	}
	return r
}

func (L *ledger) unescape(s []byte) []byte {
	start := len(L.scratch)
	out := L.scratch
	for i := 0; i < len(s); {
		c := s[i]
		if c != '\\' {
			out = append(out, c)
			i++
			continue
		}
		i++
		if i >= len(s) {
			break
		}
		c = s[i]
		i++
		switch c {
		case 'n':
			out = append(out, '\n')
		case 't':
			out = append(out, '\t')
		case 'r':
			out = append(out, '\r')
		case 'b':
			out = append(out, '\b')
		case 'f':
			out = append(out, '\f')
		case 'u':
			r := hex4(s, i)
			if r < 0 {
				out = utf8.AppendRune(out, 0xFFFD)
				continue
			}
			i += 4
			if r >= 0xD800 && r < 0xDC00 {
				if i+6 <= len(s) && s[i] == '\\' && s[i+1] == 'u' {
					r2 := hex4(s, i+2)
					if r2 >= 0xDC00 && r2 < 0xE000 {
						r = 0x10000 + (r-0xD800)<<10 + (r2 - 0xDC00)
						i += 6
					} else {
						r = 0xFFFD
					}
				} else {
					r = 0xFFFD
				}
			} else if r >= 0xDC00 && r < 0xE000 {
				r = 0xFFFD
			}
			out = utf8.AppendRune(out, rune(r))
		default:
			out = append(out, c)
		}
	}
	L.scratch = out
	return out[start:]
}

func (L *ledger) parseRates(d []byte, i int) int {
	n := len(d)
	if i+3 <= n && d[i] == 0xEF && d[i+1] == 0xBB && d[i+2] == 0xBF {
		i += 3
	}
	for i < n && d[i] <= ' ' {
		i++
	}
	if i >= n || d[i] != '{' {
		return -1
	}
	i++
	L.scratch = L.scratch[:0]
	for {
		for i < n && d[i] <= ' ' {
			i++
		}
		if i >= n {
			return -1
		}
		c := d[i]
		if c == '}' {
			return i + 1
		}
		if c == ',' {
			i++
			continue
		}
		if c != '"' {
			return -1
		}
		ks := i + 1
		ke, kesc := scanStr(d, ks)
		if ke < 0 {
			return -1
		}
		i = ke + 1
		for i < n && d[i] <= ' ' {
			i++
		}
		if i >= n || d[i] != ':' {
			return -1
		}
		i++
		for i < n && d[i] <= ' ' {
			i++
		}
		if i >= n {
			return -1
		}
		key := d[ks:ke]
		if kesc {
			key = L.unescape(key)
		}
		if string(key) == "rates" && d[i] == '{' {
			i++
			for {
				for i < n && d[i] <= ' ' {
					i++
				}
				if i >= n {
					return -1
				}
				c := d[i]
				if c == '}' {
					i++
					break
				}
				if c == ',' {
					i++
					continue
				}
				if c != '"' {
					return -1
				}
				ns := i + 1
				ne, nesc := scanStr(d, ns)
				if ne < 0 {
					return -1
				}
				i = ne + 1
				for i < n && d[i] <= ' ' {
					i++
				}
				if i >= n || d[i] != ':' {
					return -1
				}
				i++
				for i < n && d[i] <= ' ' {
					i++
				}
				name := d[ns:ne]
				if nesc {
					name = L.unescape(name)
				}
				neg := false
				if i < n && d[i] == '-' {
					neg = true
					i++
				}
				var v int64
				st := i
				for i < n && d[i] >= '0' && d[i] <= '9' {
					v = v*10 + int64(d[i]-'0')
					i++
				}
				if i == st {
					i = skipValue(d, i)
					if i < 0 {
						return -1
					}
					continue
				}
				if neg {
					v = -v
				}
				for i < n {
					c := d[i]
					if c == ',' || c == '}' || c <= ' ' {
						break
					}
					i++
				}
				L.setRate(string(name), v)
			}
			continue
		}
		i = skipValue(d, i)
		if i < 0 {
			return -1
		}
	}
}

func (L *ledger) parseTx(d []byte, i int) int {
	n := len(d)
	if d[i] != '{' {
		return -1
	}
	i++
	L.scratch = L.scratch[:0]
	var account, channel []byte
	hasAcc, hasCh := false, false
	typ := 0
	var amount, rate int64
	test := false
	for {
		for i < n && d[i] <= ' ' {
			i++
		}
		if i >= n {
			return -1
		}
		c := d[i]
		if c == '}' {
			i++
			break
		}
		if c == ',' {
			i++
			continue
		}
		if c != '"' {
			return -1
		}
		ks := i + 1
		ke, kesc := scanStr(d, ks)
		if ke < 0 {
			return -1
		}
		i = ke + 1
		for i < n && d[i] <= ' ' {
			i++
		}
		if i >= n || d[i] != ':' {
			return -1
		}
		i++
		for i < n && d[i] <= ' ' {
			i++
		}
		if i >= n {
			return -1
		}
		key := d[ks:ke]
		if kesc {
			key = L.unescape(key)
		}
		c = d[i]
		if c == '"' {
			s := i + 1
			e, esc := scanStr(d, s)
			if e < 0 {
				return -1
			}
			i = e + 1
			switch string(key) {
			case "type":
				v := d[s:e]
				if esc {
					v = L.unescape(v)
				}
				switch string(v) {
				case "credit", "refund":
					typ = 1
				case "debit":
					typ = 2
				case "void":
					typ = 3
				default:
					typ = 0
				}
			case "amount":
				v := d[s:e]
				if esc {
					v = L.unescape(v)
				}
				var a int64
				j := 0
				for j < len(v) && v[j] != '.' {
					a = a*10 + int64(v[j]-'0')
					j++
				}
				a *= 100
				if j < len(v) {
					j++
					if j < len(v) {
						a += int64(v[j]-'0') * 10
						j++
					}
					if j < len(v) {
						a += int64(v[j] - '0')
					}
				}
				amount = a
			case "currency":
				v := d[s:e]
				if esc {
					v = L.unescape(v)
				}
				rate = L.rate(v)
			case "account":
				v := d[s:e]
				if esc {
					v = L.unescape(v)
				}
				account = v
				hasAcc = true
			}
			continue
		}
		if c == '[' && string(key) == "tags" {
			i++
			test = false
			for {
				for i < n && d[i] <= ' ' {
					i++
				}
				if i >= n {
					return -1
				}
				c := d[i]
				if c == ']' {
					i++
					break
				}
				if c == ',' {
					i++
					continue
				}
				if c == '"' {
					s := i + 1
					e, esc := scanStr(d, s)
					if e < 0 {
						return -1
					}
					v := d[s:e]
					if esc {
						v = L.unescape(v)
					}
					if string(v) == "test" {
						test = true
					}
					i = e + 1
					continue
				}
				i = skipValue(d, i)
				if i < 0 {
					return -1
				}
			}
			continue
		}
		if c == '{' && string(key) == "meta" {
			i++
			for {
				for i < n && d[i] <= ' ' {
					i++
				}
				if i >= n {
					return -1
				}
				c := d[i]
				if c == '}' {
					i++
					break
				}
				if c == ',' {
					i++
					continue
				}
				if c != '"' {
					return -1
				}
				ms := i + 1
				me, mesc := scanStr(d, ms)
				if me < 0 {
					return -1
				}
				i = me + 1
				for i < n && d[i] <= ' ' {
					i++
				}
				if i >= n || d[i] != ':' {
					return -1
				}
				i++
				for i < n && d[i] <= ' ' {
					i++
				}
				if i >= n {
					return -1
				}
				mk := d[ms:me]
				if mesc {
					mk = L.unescape(mk)
				}
				if d[i] == '"' && string(mk) == "channel" {
					s := i + 1
					e, esc := scanStr(d, s)
					if e < 0 {
						return -1
					}
					v := d[s:e]
					if esc {
						v = L.unescape(v)
					}
					channel = v
					hasCh = true
					i = e + 1
					continue
				}
				i = skipValue(d, i)
				if i < 0 {
					return -1
				}
			}
			continue
		}
		i = skipValue(d, i)
		if i < 0 {
			return -1
		}
	}

	if (typ == 1 || typ == 2) && !test {
		usd := amount * rate / 1000000
		if typ == 2 {
			usd = -usd
		}
		L.counted++
		L.net += usd
		if hasCh {
			e := L.chans.get(channel)
			e.count++
			e.net += usd
		}
		if hasAcc {
			e := L.accts.get(account)
			e.net += usd
		}
	}
	return i
}

func (L *ledger) process(d []byte) {
	i, n := 0, len(d)
	for i < n {
		for i < n && d[i] <= ' ' {
			i++
		}
		if i >= n {
			break
		}
		var ni int
		if L.haveRates {
			ni = L.parseTx(d, i)
		} else {
			ni = L.parseRates(d, i)
			L.haveRates = true
		}
		if ni < 0 {
			k := bytes.IndexByte(d[i:], '\n')
			if k < 0 {
				return
			}
			i += k + 1
		} else {
			i = ni
		}
	}
}

func better(a, b *entry) bool {
	if a.net != b.net {
		return a.net > b.net
	}
	return a.key < b.key
}

func main() {
	debug.SetGCPercent(-1)
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Exit(1)
	}

	L := &ledger{
		rateMap: make(map[string]int64),
		chans:   newTable(64),
		accts:   newTable(1 << 12),
	}

	buf := make([]byte, 1<<20)
	n := 0
	for {
		if n == len(buf) {
			nb := make([]byte, len(buf)*2)
			copy(nb, buf[:n])
			buf = nb
		}
		m, rerr := f.Read(buf[n:])
		if m > 0 {
			k := bytes.LastIndexByte(buf[n:n+m], '\n')
			n += m
			if k >= 0 {
				k += n - m
				L.process(buf[:k+1])
				copy(buf, buf[k+1:n])
				n -= k + 1
			}
		}
		if rerr != nil {
			break
		}
	}
	if n > 0 {
		L.process(buf[:n])
	}
	f.Close()

	w := bufio.NewWriterSize(os.Stdout, 1<<16)
	var nb []byte

	w.WriteString("counted ")
	w.Write(strconv.AppendInt(nb[:0], L.counted, 10))
	w.WriteByte('\n')
	w.WriteString("net ")
	w.Write(strconv.AppendInt(nb[:0], L.net, 10))
	w.WriteByte('\n')

	chans := L.chans.entries
	slices.SortFunc(chans, func(a, b entry) int {
		return strings.Compare(a.key, b.key)
	})
	for i := range chans {
		e := &chans[i]
		w.WriteString("channel ")
		w.WriteString(e.key)
		w.WriteByte(' ')
		w.Write(strconv.AppendInt(nb[:0], e.count, 10))
		w.WriteByte(' ')
		w.Write(strconv.AppendInt(nb[:0], e.net, 10))
		w.WriteByte('\n')
	}

	entries := L.accts.entries
	top := make([]int, 0, 11)
	for idx := range entries {
		e := &entries[idx]
		if len(top) == 10 && !better(e, &entries[top[9]]) {
			continue
		}
		pos := len(top)
		top = append(top, idx)
		for pos > 0 && better(e, &entries[top[pos-1]]) {
			top[pos] = top[pos-1]
			pos--
		}
		top[pos] = idx
		if len(top) > 10 {
			top = top[:10]
		}
	}
	for _, idx := range top {
		e := &entries[idx]
		w.WriteString("account ")
		w.WriteString(e.key)
		w.WriteByte(' ')
		w.Write(strconv.AppendInt(nb[:0], e.net, 10))
		w.WriteByte('\n')
	}
	w.Flush()
}
