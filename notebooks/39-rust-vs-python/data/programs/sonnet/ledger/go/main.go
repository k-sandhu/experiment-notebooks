package main

import (
	"bytes"
	"io"
	"os"
	"sort"
	"strconv"
	"unicode/utf8"
)

// ---- byte-keyed aggregation table ----

type table struct {
	index   []int32
	mask    uint32
	hashes  []uint32
	keyOff  []int32
	keyLen  []int32
	sums    []int64
	counts  []int64
	arena   []byte
}

func newTable() *table {
	t := &table{index: make([]int32, 1<<12), mask: 1<<12 - 1}
	for i := range t.index {
		t.index[i] = -1
	}
	return t
}

func (t *table) add(k []byte, v int64) {
	hash := uint32(2166136261)
	for _, c := range k {
		hash = (hash ^ uint32(c)) * 16777619
	}
	hash ^= hash >> 15
	h := hash & t.mask
	for {
		ix := t.index[h]
		if ix < 0 {
			break
		}
		if t.hashes[ix] == hash && int(t.keyLen[ix]) == len(k) {
			o := t.keyOff[ix]
			if string(t.arena[o:o+int32(len(k))]) == string(k) {
				t.sums[ix] += v
				t.counts[ix]++
				return
			}
		}
		h = (h + 1) & t.mask
	}
	id := int32(len(t.hashes))
	t.hashes = append(t.hashes, hash)
	t.keyOff = append(t.keyOff, int32(len(t.arena)))
	t.keyLen = append(t.keyLen, int32(len(k)))
	t.sums = append(t.sums, v)
	t.counts = append(t.counts, 1)
	t.arena = append(t.arena, k...)
	t.index[h] = id
	if len(t.hashes)*2 > len(t.index) {
		t.grow()
	}
}

func (t *table) grow() {
	c := len(t.index) * 2
	t.index = make([]int32, c)
	for i := range t.index {
		t.index[i] = -1
	}
	t.mask = uint32(c - 1)
	for i, hv := range t.hashes {
		h := hv & t.mask
		for t.index[h] >= 0 {
			h = (h + 1) & t.mask
		}
		t.index[h] = int32(i)
	}
}

func (t *table) key(i int) []byte {
	o := t.keyOff[i]
	return t.arena[o : o+t.keyLen[i]]
}

// ---- parser ----

var (
	buf        []byte
	p          int
	accounts   = newTable()
	channels   = newTable()
	totalCount int64
	totalNet   int64
	rateKeys   [][]byte
	rateVals   []int64
	ratesDone  bool
)

func hex4(b []byte) uint32 {
	var v uint32
	for i := 0; i < 4; i++ {
		c := b[i]
		v <<= 4
		switch {
		case c >= '0' && c <= '9':
			v |= uint32(c - '0')
		case c >= 'a' && c <= 'f':
			v |= uint32(c-'a') + 10
		default:
			v |= uint32(c-'A') + 10
		}
	}
	return v
}

// p at opening quote; leaves p after closing quote.
func parseStr() []byte {
	b := buf
	q := p + 1
	s := q
	for {
		c := b[q]
		if c == '"' {
			p = q + 1
			return b[s:q]
		}
		if c == '\\' {
			break
		}
		q++
	}
	return parseStrSlow(s, q)
}

func parseStrSlow(s, q int) []byte {
	b := buf
	out := append([]byte(nil), b[s:q]...)
	for {
		c := b[q]
		if c == '"' {
			q++
			break
		}
		if c == '\\' {
			e := b[q+1]
			q += 2
			switch e {
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
				cp := rune(hex4(b[q:]))
				q += 4
				if cp >= 0xD800 && cp < 0xDC00 && b[q] == '\\' && b[q+1] == 'u' {
					lo := rune(hex4(b[q+2:]))
					if lo >= 0xDC00 && lo < 0xE000 {
						cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
						q += 6
					}
				}
				out = utf8.AppendRune(out, cp)
			default:
				out = append(out, e)
			}
		} else {
			out = append(out, c)
			q++
		}
	}
	p = q
	return out
}

func skipWs() {
	b := buf
	q := p
	for {
		c := b[q]
		if c == ' ' || c == '\n' || c == '\t' || c == '\r' {
			q++
		} else {
			break
		}
	}
	p = q
}

func skipString(q int) int {
	b := buf
	q++
	for {
		c := b[q]
		if c == '"' {
			break
		}
		if c == '\\' {
			q++
		}
		q++
	}
	return q + 1
}

func skipValue() {
	b := buf
	q := p
	c := b[q]
	if c == '"' {
		p = skipString(q)
		return
	}
	if c == '{' || c == '[' {
		depth := 0
		for {
			c = b[q]
			if c == '"' {
				q = skipString(q)
				continue
			}
			q++
			if c == '{' || c == '[' {
				depth++
			} else if c == '}' || c == ']' {
				depth--
				if depth == 0 {
					break
				}
			}
		}
		p = q
		return
	}
	for c != ',' && c != '}' && c != ']' && c != ' ' && c != '\n' && c != '\r' && c != '\t' {
		q++
		c = b[q]
	}
	p = q
}

func parseInt() int64 {
	var v int64
	b := buf
	q := p
	for b[q] >= '0' && b[q] <= '9' {
		v = v*10 + int64(b[q]-'0')
		q++
	}
	p = q
	return v
}

func parseRates() {
	p++
	for {
		skipWs()
		k := parseStr()
		isRates := string(k) == "rates"
		skipWs()
		p++
		skipWs()
		if isRates {
			p++
			for {
				skipWs()
				if buf[p] == '}' {
					p++
					break
				}
				c := parseStr()
				rateKeys = append(rateKeys, append([]byte(nil), c...))
				skipWs()
				p++
				skipWs()
				rateVals = append(rateVals, parseInt())
				skipWs()
				if buf[p] == ',' {
					p++
				}
			}
		} else {
			skipValue()
		}
		skipWs()
		if buf[p] == ',' {
			p++
			continue
		}
		p++
		break
	}
}

func parseTx() {
	p++
	var acc, chan_ []byte
	var typ byte
	var hund, rate int64
	test := false
	for {
		skipWs()
		if buf[p] == '}' {
			p++
			break
		}
		k := parseStr()
		skipWs()
		p++
		skipWs()
		kind := 0
		switch len(k) {
		case 4:
			switch string(k) {
			case "type":
				kind = 2
			case "tags":
				kind = 5
			case "meta":
				kind = 6
			}
		case 6:
			if string(k) == "amount" {
				kind = 3
			}
		case 7:
			if string(k) == "account" {
				kind = 1
			}
		case 8:
			if string(k) == "currency" {
				kind = 4
			}
		}
		switch kind {
		case 1:
			acc = parseStr()
		case 2:
			t := parseStr()
			typ = 0
			if len(t) > 0 {
				typ = t[0]
			}
		case 3:
			a := parseStr()
			q := 0
			var ip int64
			for q < len(a) && a[q] != '.' {
				ip = ip*10 + int64(a[q]-'0')
				q++
			}
			var fr int64
			if q < len(a) {
				q++
				if q < len(a) {
					fr = int64(a[q]-'0') * 10
					q++
					if q < len(a) {
						fr += int64(a[q] - '0')
					}
				}
			}
			hund = ip*100 + fr
		case 4:
			c := parseStr()
			for i, rk := range rateKeys {
				if bytes.Equal(rk, c) {
					rate = rateVals[i]
					break
				}
			}
		case 5:
			p++
			skipWs()
			if buf[p] == ']' {
				p++
				break
			}
			for {
				skipWs()
				s := parseStr()
				if len(s) == 4 && s[0] == 't' && s[1] == 'e' && s[2] == 's' && s[3] == 't' {
					test = true
				}
				skipWs()
				if buf[p] == ',' {
					p++
					continue
				}
				p++
				break
			}
		case 6:
			p++
			for {
				skipWs()
				if buf[p] == '}' {
					p++
					break
				}
				mk := parseStr()
				isChannel := string(mk) == "channel"
				skipWs()
				p++
				skipWs()
				if isChannel && buf[p] == '"' {
					chan_ = parseStr()
				} else {
					skipValue()
				}
				skipWs()
				if buf[p] == ',' {
					p++
					continue
				}
				p++
				break
			}
		default:
			skipValue()
		}
		skipWs()
		if buf[p] == ',' {
			p++
			continue
		}
		p++
		break
	}
	if typ == 'v' || test {
		return
	}
	usd := hund * rate / 1000000
	v := usd
	if typ == 'd' {
		v = -usd
	}
	totalCount++
	totalNet += v
	accounts.add(acc, v)
	channels.add(chan_, v)
}

func processChunk(end int) {
	p = 0
	for {
		skipWs()
		if p >= end {
			break
		}
		if !ratesDone {
			parseRates()
			ratesDone = true
		} else {
			parseTx()
		}
	}
}

func main() {
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	defer f.Close()
	capacity := 1 << 22
	buf = make([]byte, capacity+16)
	have := 0
	eof := false
	for !eof {
		n, err := f.Read(buf[have:capacity])
		if n > 0 {
			have += n
		} else if err != nil {
			if err != io.EOF {
				os.Exit(1)
			}
			eof = true
		}
		var end int
		if eof {
			if have > 0 && buf[have-1] != '\n' {
				buf[have] = '\n'
				have++
			}
			end = have
			buf[end] = 0
		} else {
			i := have
			for i > 0 && buf[i-1] != '\n' {
				i--
			}
			if i == 0 {
				if have == capacity {
					capacity *= 2
					nb := make([]byte, capacity+16)
					copy(nb, buf[:have])
					buf = nb
				}
				continue
			}
			end = i
		}
		processChunk(end)
		if !eof {
			copy(buf, buf[end:have])
			have -= end
		}
	}

	out := make([]byte, 0, 1024)
	out = append(out, "counted "...)
	out = strconv.AppendInt(out, totalCount, 10)
	out = append(out, "\nnet "...)
	out = strconv.AppendInt(out, totalNet, 10)
	out = append(out, '\n')
	order := make([]int, len(channels.hashes))
	for i := range order {
		order[i] = i
	}
	sort.Slice(order, func(a, b int) bool { return bytes.Compare(channels.key(order[a]), channels.key(order[b])) < 0 })
	for _, i := range order {
		out = append(out, "channel "...)
		out = append(out, channels.key(i)...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, channels.counts[i], 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, channels.sums[i], 10)
		out = append(out, '\n')
	}
	accBefore := func(a, b int) bool {
		if accounts.sums[a] != accounts.sums[b] {
			return accounts.sums[a] > accounts.sums[b]
		}
		return bytes.Compare(accounts.key(a), accounts.key(b)) < 0
	}
	na := len(accounts.hashes)
	topN := 10
	if na < topN {
		topN = na
	}
	top := make([]int, topN)
	tn := 0
	for i := 0; i < na; i++ {
		if tn == topN && !accBefore(i, top[tn-1]) {
			continue
		}
		var j int
		if tn < topN {
			j = tn
			tn++
		} else {
			j = tn - 1
		}
		for j > 0 && accBefore(i, top[j-1]) {
			top[j] = top[j-1]
			j--
		}
		top[j] = i
	}
	for i := 0; i < tn; i++ {
		out = append(out, "account "...)
		out = append(out, accounts.key(top[i])...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, accounts.sums[top[i]], 10)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
