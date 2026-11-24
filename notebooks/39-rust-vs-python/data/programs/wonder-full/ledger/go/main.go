package main

import (
	"bytes"
	"os"
	"sort"
	"strconv"
)

// Open-addressing map from byte-string keys to {net, cnt}; keys copied once into an arena.
type entry struct {
	hash uint64
	off  int
	len  int
	net  int64
	cnt  int64
	used bool
}

type strMap struct {
	t       []entry
	arena   []byte
	mask    int
	usedCnt int
}

func newStrMap(capHint int) *strMap {
	c := 16
	for c < capHint {
		c <<= 1
	}
	return &strMap{t: make([]entry, c), mask: c - 1}
}

func hashBytes(b []byte) uint64 {
	h := uint64(1469598103934665603)
	for _, c := range b {
		h ^= uint64(c)
		h *= 1099511628211
	}
	h ^= h >> 33
	h *= 0xff51afd7ed558ccd
	h ^= h >> 33
	return h
}

func (m *strMap) grow() {
	old := m.t
	m.t = make([]entry, len(old)*2)
	m.mask = len(m.t) - 1
	for i := range old {
		if old[i].used {
			j := int(old[i].hash) & m.mask
			for m.t[j].used {
				j = (j + 1) & m.mask
			}
			m.t[j] = old[i]
		}
	}
}

func (m *strMap) findOrInsert(key []byte) *entry {
	if (m.usedCnt+1)*10 > len(m.t)*7 {
		m.grow()
	}
	h := hashBytes(key)
	i := int(h) & m.mask
	for {
		e := &m.t[i]
		if !e.used {
			e.used = true
			e.hash = h
			e.off = len(m.arena)
			e.len = len(key)
			m.arena = append(m.arena, key...)
			e.net, e.cnt = 0, 0
			m.usedCnt++
			return e
		}
		if e.hash == h && e.len == len(key) && bytes.Equal(m.arena[e.off:e.off+e.len], key) {
			return e
		}
		i = (i + 1) & m.mask
	}
}

func (m *strMap) find(key []byte) *entry {
	h := hashBytes(key)
	i := int(h) & m.mask
	for {
		e := &m.t[i]
		if !e.used {
			return nil
		}
		if e.hash == h && e.len == len(key) && bytes.Equal(m.arena[e.off:e.off+e.len], key) {
			return e
		}
		i = (i + 1) & m.mask
	}
}

func (m *strMap) keyOf(e *entry) []byte { return m.arena[e.off : e.off+e.len] }

type parser struct {
	d                         []byte
	n, pos                    int
	keyDec, acctDec, chanDec, miscDec []byte
}

func (p *parser) skipWs() {
	for p.pos < p.n {
		c := p.d[p.pos]
		if c == ' ' || c == '\t' || c == '\n' || c == '\r' {
			p.pos++
		} else {
			break
		}
	}
}

func (p *parser) skipStringRaw() {
	p.pos++
	for p.pos < p.n {
		c := p.d[p.pos]
		if c == '"' {
			p.pos++
			return
		}
		if c == '\\' {
			p.pos += 2
		} else {
			p.pos++
		}
	}
}

func appendUtf8(s []byte, cp uint32) []byte {
	switch {
	case cp < 0x80:
		return append(s, byte(cp))
	case cp < 0x800:
		return append(s, byte(0xC0|(cp>>6)), byte(0x80|(cp&0x3F)))
	case cp < 0x10000:
		return append(s, byte(0xE0|(cp>>12)), byte(0x80|((cp>>6)&0x3F)), byte(0x80|(cp&0x3F)))
	default:
		return append(s, byte(0xF0|(cp>>18)), byte(0x80|((cp>>12)&0x3F)), byte(0x80|((cp>>6)&0x3F)), byte(0x80|(cp&0x3F)))
	}
}

func (p *parser) hex4(i *int, end int) uint32 {
	var v uint32
	for k := 0; k < 4 && *i < end; k++ {
		c := p.d[*i]
		*i++
		v <<= 4
		switch {
		case c >= '0' && c <= '9':
			v |= uint32(c - '0')
		case c >= 'a' && c <= 'f':
			v |= uint32(c-'a') + 10
		case c >= 'A' && c <= 'F':
			v |= uint32(c-'A') + 10
		}
	}
	return v
}

// d[pos]=='"'. Returns slice into data, or into *dec when escapes present.
func (p *parser) parseString(dec *[]byte) []byte {
	p.pos++
	start := p.pos
	esc := false
	for p.pos < p.n {
		c := p.d[p.pos]
		if c == '"' {
			break
		}
		if c == '\\' {
			esc = true
			p.pos += 2
		} else {
			p.pos++
		}
	}
	end := p.pos
	if p.pos < p.n {
		p.pos++
	}
	if !esc {
		return p.d[start:end]
	}
	out := (*dec)[:0]
	i := start
	for i < end {
		c := p.d[i]
		if c != '\\' {
			out = append(out, c)
			i++
			continue
		}
		i++
		if i >= end {
			break
		}
		e := p.d[i]
		i++
		switch e {
		case '"':
			out = append(out, '"')
		case '\\':
			out = append(out, '\\')
		case '/':
			out = append(out, '/')
		case 'b':
			out = append(out, '\b')
		case 'f':
			out = append(out, '\f')
		case 'n':
			out = append(out, '\n')
		case 'r':
			out = append(out, '\r')
		case 't':
			out = append(out, '\t')
		case 'u':
			cp := p.hex4(&i, end)
			if cp >= 0xD800 && cp <= 0xDBFF && i+1 < end && p.d[i] == '\\' && p.d[i+1] == 'u' {
				i += 2
				lo := p.hex4(&i, end)
				if lo >= 0xDC00 && lo <= 0xDFFF {
					cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
				} else {
					out = appendUtf8(out, cp)
					cp = lo
				}
			}
			out = appendUtf8(out, cp)
		default:
			out = append(out, e)
		}
	}
	*dec = out
	return out
}

func (p *parser) skipValue() {
	p.skipWs()
	if p.pos >= p.n {
		return
	}
	c := p.d[p.pos]
	if c == '"' {
		p.skipStringRaw()
		return
	}
	if c == '{' || c == '[' {
		depth := 0
		for p.pos < p.n {
			ch := p.d[p.pos]
			switch ch {
			case '"':
				p.skipStringRaw()
			case '{', '[':
				depth++
				p.pos++
			case '}', ']':
				depth--
				p.pos++
				if depth == 0 {
					return
				}
			default:
				p.pos++
			}
		}
		return
	}
	for p.pos < p.n {
		ch := p.d[p.pos]
		if ch == ',' || ch == '}' || ch == ']' || ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r' {
			break
		}
		p.pos++
	}
}

func (p *parser) parseInt64() int64 {
	p.skipWs()
	neg := false
	if p.pos < p.n && p.d[p.pos] == '-' {
		neg = true
		p.pos++
	}
	var v int64
	for p.pos < p.n && p.d[p.pos] >= '0' && p.d[p.pos] <= '9' {
		v = v*10 + int64(p.d[p.pos]-'0')
		p.pos++
	}
	if neg {
		return -v
	}
	return v
}

func parseAmount(v []byte) int64 {
	i := 0
	var ip int64
	for i < len(v) && v[i] != '.' {
		ip = ip*10 + int64(v[i]-'0')
		i++
	}
	h := ip * 100
	if i < len(v) {
		i++
		if i < len(v) {
			h += int64(v[i]-'0') * 10
			i++
		}
		if i < len(v) {
			h += int64(v[i] - '0')
		}
	}
	return h
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	p := &parser{d: data, n: len(data)}
	rates := newStrMap(64)
	channels := newStrMap(64)
	accounts := newStrMap(1 << 16)

	// First object: rates.
	p.skipWs()
	if p.pos < p.n && p.d[p.pos] == '{' {
		p.pos++
		p.skipWs()
		if p.pos < p.n && p.d[p.pos] == '}' {
			p.pos++
		} else {
		rateLoop:
			for {
				p.skipWs()
				key := p.parseString(&p.keyDec)
				p.skipWs()
				p.pos++ // ':'
				p.skipWs()
				if string(key) == "rates" {
					p.pos++
					p.skipWs()
					if p.pos < p.n && p.d[p.pos] == '}' {
						p.pos++
					} else {
						for {
							p.skipWs()
							ck := p.parseString(&p.miscDec)
							p.skipWs()
							p.pos++
							rv := p.parseInt64()
							rates.findOrInsert(ck).net = rv
							p.skipWs()
							if p.pos < p.n && p.d[p.pos] == ',' {
								p.pos++
								continue
							}
							if p.pos < p.n && p.d[p.pos] == '}' {
								p.pos++
							}
							break
						}
					}
				} else {
					p.skipValue()
				}
				p.skipWs()
				if p.pos < p.n && p.d[p.pos] == ',' {
					p.pos++
					continue
				}
				if p.pos < p.n && p.d[p.pos] == '}' {
					p.pos++
				}
				break rateLoop
			}
		}
	}

	var counted, net int64
	for {
		p.skipWs()
		if p.pos >= p.n {
			break
		}
		var acct, chn []byte
		sign := int64(1)
		isVoid, hasTest := false, false
		var hundredths, rate int64
		p.pos++ // '{'
		p.skipWs()
		if p.pos < p.n && p.d[p.pos] == '}' {
			p.pos++
		} else {
		txLoop:
			for {
				p.skipWs()
				key := p.parseString(&p.keyDec)
				p.skipWs()
				p.pos++ // ':'
				p.skipWs()
				switch string(key) {
				case "account":
					acct = p.parseString(&p.acctDec)
				case "type":
					v := p.parseString(&p.miscDec)
					switch string(v) {
					case "void":
						isVoid = true
					case "debit":
						sign = -1
					default:
						sign = 1
					}
				case "amount":
					hundredths = parseAmount(p.parseString(&p.miscDec))
				case "currency":
					v := p.parseString(&p.miscDec)
					if e := rates.find(v); e != nil {
						rate = e.net
					}
				case "tags":
					p.pos++
					p.skipWs()
					if p.pos < p.n && p.d[p.pos] == ']' {
						p.pos++
					} else {
						for {
							p.skipWs()
							if p.pos < p.n && p.d[p.pos] == '"' {
								if string(p.parseString(&p.miscDec)) == "test" {
									hasTest = true
								}
							} else {
								p.skipValue()
							}
							p.skipWs()
							if p.pos < p.n && p.d[p.pos] == ',' {
								p.pos++
								continue
							}
							if p.pos < p.n && p.d[p.pos] == ']' {
								p.pos++
							}
							break
						}
					}
				case "meta":
					p.pos++
					p.skipWs()
					if p.pos < p.n && p.d[p.pos] == '}' {
						p.pos++
					} else {
						for {
							p.skipWs()
							k2 := p.parseString(&p.keyDec)
							p.skipWs()
							p.pos++
							p.skipWs()
							if string(k2) == "channel" {
								chn = p.parseString(&p.chanDec)
							} else {
								p.skipValue()
							}
							p.skipWs()
							if p.pos < p.n && p.d[p.pos] == ',' {
								p.pos++
								continue
							}
							if p.pos < p.n && p.d[p.pos] == '}' {
								p.pos++
							}
							break
						}
					}
				default:
					p.skipValue()
				}
				p.skipWs()
				if p.pos < p.n && p.d[p.pos] == ',' {
					p.pos++
					continue
				}
				if p.pos < p.n && p.d[p.pos] == '}' {
					p.pos++
				}
				break txLoop
			}
		}
		if isVoid || hasTest {
			continue
		}
		usd := (hundredths * rate) / 1000000
		signed := usd
		if sign < 0 {
			signed = -usd
		}
		counted++
		net += signed
		accounts.findOrInsert(acct).net += signed
		ce := channels.findOrInsert(chn)
		ce.net += signed
		ce.cnt++
	}

	var chans, accts []*entry
	for i := range channels.t {
		if channels.t[i].used {
			chans = append(chans, &channels.t[i])
		}
	}
	for i := range accounts.t {
		if accounts.t[i].used {
			accts = append(accts, &accounts.t[i])
		}
	}
	sort.Slice(chans, func(i, j int) bool {
		return bytes.Compare(channels.keyOf(chans[i]), channels.keyOf(chans[j])) < 0
	})
	sort.Slice(accts, func(i, j int) bool {
		if accts[i].net != accts[j].net {
			return accts[i].net > accts[j].net
		}
		return bytes.Compare(accounts.keyOf(accts[i]), accounts.keyOf(accts[j])) < 0
	})

	out := make([]byte, 0, 4096)
	out = append(out, "counted "...)
	out = strconv.AppendInt(out, counted, 10)
	out = append(out, '\n', 'n', 'e', 't', ' ')
	out = strconv.AppendInt(out, net, 10)
	out = append(out, '\n')
	for _, e := range chans {
		out = append(out, "channel "...)
		out = append(out, channels.keyOf(e)...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, e.cnt, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, e.net, 10)
		out = append(out, '\n')
	}
	top := len(accts)
	if top > 10 {
		top = 10
	}
	for i := 0; i < top; i++ {
		out = append(out, "account "...)
		out = append(out, accounts.keyOf(accts[i])...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, accts[i].net, 10)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
