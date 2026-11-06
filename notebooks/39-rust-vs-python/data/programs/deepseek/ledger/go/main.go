package main

import (
	"os"
	"sort"
	"strconv"
)

type Parser struct {
	b   []byte
	i   int
	end int

	sBeg int
	sLen int
	sEsc bool

	scratch []byte
}

func (p *Parser) skipWs() {
	b := p.b
	i := p.i
	for i < p.end {
		c := b[i]
		if c == ' ' || c == '\t' || c == '\r' || c == '\n' {
			i++
		} else {
			break
		}
	}
	p.i = i
}

func (p *Parser) scanString() {
	b := p.b
	i := p.i + 1
	s := i
	esc := false
	for b[i] != '"' {
		if b[i] == '\\' {
			esc = true
			i++
			if b[i] == 'u' {
				i += 5
			} else {
				i++
			}
		} else {
			i++
		}
	}
	p.sBeg = s
	p.sLen = i - s
	p.sEsc = esc
	p.i = i + 1
}

func (p *Parser) skipString() {
	b := p.b
	i := p.i + 1
	for b[i] != '"' {
		if b[i] == '\\' {
			i++
			if b[i] == 'u' {
				i += 5
			} else {
				i++
			}
		} else {
			i++
		}
	}
	p.i = i + 1
}

func hex4(b []byte, q int) int {
	v := 0
	for k := 0; k < 4; k++ {
		c := b[q+k]
		var d int
		switch {
		case c >= '0' && c <= '9':
			d = int(c - '0')
		case c >= 'a' && c <= 'f':
			d = int(c-'a') + 10
		default:
			d = int(c-'A') + 10
		}
		v = v<<4 | d
	}
	return v
}

func (p *Parser) unescape() []byte {
	out := p.scratch[:0]
	b := p.b
	q := p.sBeg
	e := p.sBeg + p.sLen
	for q < e {
		c := b[q]
		q++
		if c != '\\' {
			out = append(out, c)
			continue
		}
		esc := b[q]
		q++
		switch esc {
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
			cp := hex4(b, q)
			q += 4
			if cp >= 0xD800 && cp <= 0xDBFF && q+6 <= e && b[q] == '\\' && b[q+1] == 'u' {
				lo := hex4(b, q+2)
				if lo >= 0xDC00 && lo <= 0xDFFF {
					cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
					q += 6
				}
			}
			if cp < 0x80 {
				out = append(out, byte(cp))
			} else if cp < 0x800 {
				out = append(out, byte(0xC0|(cp>>6)), byte(0x80|(cp&0x3F)))
			} else if cp < 0x10000 {
				out = append(out, byte(0xE0|(cp>>12)), byte(0x80|((cp>>6)&0x3F)), byte(0x80|(cp&0x3F)))
			} else {
				out = append(out, byte(0xF0|(cp>>18)), byte(0x80|((cp>>12)&0x3F)), byte(0x80|((cp>>6)&0x3F)), byte(0x80|(cp&0x3F)))
			}
		default:
			out = append(out, esc)
		}
	}
	p.scratch = out
	return out
}

func (p *Parser) str() []byte {
	if !p.sEsc {
		return p.b[p.sBeg : p.sBeg+p.sLen]
	}
	return p.unescape()
}

func eqLit(a []byte, lit string) bool {
	if len(a) != len(lit) {
		return false
	}
	for i := 0; i < len(a); i++ {
		if a[i] != lit[i] {
			return false
		}
	}
	return true
}

func (p *Parser) skipValue() {
	p.skipWs()
	b := p.b
	i := p.i
	c := b[i]
	if c == '"' {
		i++
		for b[i] != '"' {
			if b[i] == '\\' {
				i++
				if b[i] == 'u' {
					i += 5
				} else {
					i++
				}
			} else {
				i++
			}
		}
		p.i = i + 1
		return
	}
	if c == '{' || c == '[' {
		depth := 0
		for {
			d := b[i]
			if d == '"' {
				i++
				for b[i] != '"' {
					if b[i] == '\\' {
						i++
						if b[i] == 'u' {
							i += 5
						} else {
							i++
						}
					} else {
						i++
					}
				}
				i++
			} else if d == '{' || d == '[' {
				depth++
				i++
			} else if d == '}' || d == ']' {
				i++
				depth--
				if depth == 0 {
					p.i = i
					return
				}
			} else {
				i++
			}
		}
	}
	for i < p.end {
		d := b[i]
		if d == ',' || d == '}' || d == ']' || d == ' ' || d == '\t' || d == '\r' || d == '\n' {
			break
		}
		i++
	}
	p.i = i
}

// ---------------- rates
var rateKeys []string
var rateVals []int64

func lookupRate(s []byte) int64 {
	for i := 0; i < len(rateKeys); i++ {
		if eqLit(s, rateKeys[i]) {
			return rateVals[i]
		}
	}
	return 0
}

// ---------------- accounts
var accountIndex = make(map[string]int, 1<<14)
var accStart []int32
var accLen []int32
var accSum []int64
var accCnt []int32
var arena []byte

func internAccount(s []byte) int {
	if idx, ok := accountIndex[string(s)]; ok {
		return idx
	}
	idx := len(accSum)
	start := len(arena)
	arena = append(arena, s...)
	accStart = append(accStart, int32(start))
	accLen = append(accLen, int32(len(s)))
	accSum = append(accSum, 0)
	accCnt = append(accCnt, 0)
	accountIndex[string(s)] = idx
	return idx
}

// ---------------- channels
type channel struct {
	name string
	cnt  int64
	net  int64
}

var channels []channel

func internChannel(s []byte) int {
	for i := range channels {
		if len(channels[i].name) != len(s) {
			continue
		}
		same := true
		for j := 0; j < len(s); j++ {
			if channels[i].name[j] != s[j] {
				same = false
				break
			}
		}
		if same {
			return i
		}
	}
	channels = append(channels, channel{name: string(s)})
	return len(channels) - 1
}

func parseAmount(s []byte) int64 {
	var whole int64
	i := 0
	for i < len(s) {
		c := s[i]
		if c < '0' || c > '9' {
			break
		}
		whole = whole*10 + int64(c-'0')
		i++
	}
	var f1, f2 int64
	if i < len(s) && s[i] == '.' {
		i++
		if i < len(s) {
			f1 = int64(s[i] - '0')
			i++
		}
		if i < len(s) {
			f2 = int64(s[i] - '0')
		}
	}
	return whole*100 + f1*10 + f2
}

// ---------------- transactions
var totalCount int64
var totalNet int64

func (p *Parser) parseTags() bool {
	p.i++ // '['
	p.skipWs()
	b := p.b
	if b[p.i] == ']' {
		p.i++
		return false
	}
	hasTest := false
	for {
		p.skipWs()
		if b[p.i] == '"' {
			p.scanString()
			if !hasTest {
				if eqLit(p.str(), "test") {
					hasTest = true
				}
			}
		} else {
			p.skipValue()
		}
		p.skipWs()
		if b[p.i] == ',' {
			p.i++
			continue
		}
		p.i++ // ']'
		return hasTest
	}
}

func (p *Parser) parseMeta() int {
	chIdx := -1
	p.i++ // '{'
	p.skipWs()
	b := p.b
	if b[p.i] == '}' {
		p.i++
		return chIdx
	}
	for {
		p.skipWs()
		p.scanString()
		isChannel := eqLit(p.str(), "channel")
		p.skipWs()
		p.i++ // ':'
		p.skipWs()
		if isChannel {
			p.scanString()
			chIdx = internChannel(p.str())
		} else {
			p.skipValue()
		}
		p.skipWs()
		if b[p.i] == ',' {
			p.i++
			continue
		}
		p.i++ // '}'
		return chIdx
	}
}

func (p *Parser) parseTransaction() {
	acctIdx := -1
	chIdx := -1
	sign := 1
	hasTest := false
	var hundredths int64
	var rate int64

	b := p.b
	p.i++ // '{'
	p.skipWs()
	if b[p.i] == '}' {
		p.i++
		return
	}
	for {
		p.skipWs()
		p.scanString()
		key := p.str()
		first := byte(0)
		if len(key) > 0 {
			first = key[0]
		}
		p.skipWs()
		p.i++ // ':'
		p.skipWs()
		switch first {
		case 'a':
			if eqLit(key, "account") {
				p.scanString()
				acctIdx = internAccount(p.str())
			} else if eqLit(key, "amount") {
				p.scanString()
				hundredths = parseAmount(p.str())
			} else {
				p.skipValue()
			}
		case 't':
			if eqLit(key, "type") {
				p.scanString()
				s := p.str()
				if eqLit(s, "void") {
					sign = 0
				} else if eqLit(s, "debit") {
					sign = -1
				} else {
					sign = 1
				}
			} else if eqLit(key, "tags") {
				hasTest = p.parseTags()
			} else {
				p.skipValue()
			}
		case 'm':
			if eqLit(key, "meta") {
				chIdx = p.parseMeta()
			} else {
				p.skipValue()
			}
		case 'c':
			if eqLit(key, "currency") {
				p.scanString()
				rate = lookupRate(p.str())
			} else {
				p.skipValue()
			}
		default:
			p.skipValue()
		}
		p.skipWs()
		if b[p.i] == ',' {
			p.i++
			continue
		}
		p.i++ // '}'
		break
	}

	if sign == 0 || hasTest {
		return
	}
	usd := (hundredths * rate) / 1000000
	val := usd
	if sign < 0 {
		val = -usd
	}
	totalCount++
	totalNet += val
	if acctIdx >= 0 {
		accSum[acctIdx] += val
		accCnt[acctIdx]++
	}
	if chIdx >= 0 {
		channels[chIdx].cnt++
		channels[chIdx].net += val
	}
}

func cmpBytes(a, b []byte) int {
	n := len(a)
	if len(b) < n {
		n = len(b)
	}
	for i := 0; i < n; i++ {
		if a[i] != b[i] {
			if a[i] < b[i] {
				return -1
			}
			return 1
		}
	}
	return len(a) - len(b)
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	p := &Parser{b: data, i: 0, end: len(data)}

	// {"rates": {...}}
	p.skipWs()
	p.i++ // '{'
	p.skipWs()
	b := p.b
	if b[p.i] != '}' {
		for {
			p.skipWs()
			p.scanString()
			isRates := eqLit(p.str(), "rates")
			p.skipWs()
			p.i++ // ':'
			p.skipWs()
			if isRates && b[p.i] == '{' {
				p.i++
				p.skipWs()
				if b[p.i] != '}' {
					for {
						p.skipWs()
						p.scanString()
						cur := string(p.str())
						p.skipWs()
						p.i++ // ':'
						p.skipWs()
						neg := false
						if b[p.i] == '-' {
							neg = true
							p.i++
						}
						var v int64
						for b[p.i] >= '0' && b[p.i] <= '9' {
							v = v*10 + int64(b[p.i]-'0')
							p.i++
						}
						if neg {
							v = -v
						}
						rateKeys = append(rateKeys, cur)
						rateVals = append(rateVals, v)
						p.skipWs()
						if b[p.i] == ',' {
							p.i++
							continue
						}
						p.i++ // '}'
						break
					}
				} else {
					p.i++
				}
			} else {
				p.skipValue()
			}
			p.skipWs()
			if b[p.i] == ',' {
				p.i++
				continue
			}
			p.i++ // '}'
			break
		}
	} else {
		p.i++
	}

	for {
		p.skipWs()
		if p.i >= p.end {
			break
		}
		if b[p.i] != '{' {
			p.i++
			continue
		}
		p.parseTransaction()
	}

	sort.Slice(channels, func(x, y int) bool {
		return channels[x].name < channels[y].name
	})

	// top ten accounts
	var best [10]int
	bn := 0
	for i := 0; i < len(accSum); i++ {
		if accCnt[i] == 0 {
			continue
		}
		s := accSum[i]
		pos := bn
		for pos > 0 {
			o := best[pos-1]
			var better bool
			if s != accSum[o] {
				better = s > accSum[o]
			} else {
				better = cmpBytes(arena[accStart[i]:accStart[i]+accLen[i]], arena[accStart[o]:accStart[o]+accLen[o]]) < 0
			}
			if !better {
				break
			}
			pos--
		}
		if pos >= 10 {
			continue
		}
		if bn < 10 {
			bn++
		}
		for j := bn - 1; j > pos; j-- {
			best[j] = best[j-1]
		}
		best[pos] = i
	}

	out := make([]byte, 0, 4096)
	out = append(out, "counted "...)
	out = strconv.AppendInt(out, totalCount, 10)
	out = append(out, '\n')
	out = append(out, "net "...)
	out = strconv.AppendInt(out, totalNet, 10)
	out = append(out, '\n')
	for i := range channels {
		c := &channels[i]
		if c.cnt == 0 {
			continue
		}
		out = append(out, "channel "...)
		out = append(out, c.name...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, c.cnt, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, c.net, 10)
		out = append(out, '\n')
	}
	for i := 0; i < bn; i++ {
		a := best[i]
		out = append(out, "account "...)
		out = append(out, arena[accStart[a]:accStart[a]+accLen[a]]...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, accSum[a], 10)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}
