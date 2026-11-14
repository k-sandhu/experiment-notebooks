package main

import (
	"fmt"
	"os"
	"sort"
	"strings"
)

type rate struct {
	name  string
	value int64
}

type tx struct {
	account  string
	typ      string
	hundred  int64
	currency string
	testTag  bool
	channel  string
}

type ch struct {
	count int64
	net   int64
}

type parser struct {
	data []byte
	end  int
	pos  int
	tmp  []byte
}

func (p *parser) cur() byte {
	if p.pos < p.end {
		return p.data[p.pos]
	}
	return 0
}

func (p *parser) skipWs() {
	for p.pos < p.end {
		c := p.data[p.pos]
		if c == ' ' || c == '\t' || c == '\r' || c == '\n' {
			p.pos++
		} else {
			return
		}
	}
}

// scanString assumes current char is '"'. Returns start index, length, hadEscape.
func (p *parser) scanString() (start int, length int, hadEscape bool) {
	p.pos++ // opening quote
	start = p.pos
	for p.pos < p.end && p.data[p.pos] != '"' {
		if p.data[p.pos] == '\\' {
			hadEscape = true
			p.pos++
			if p.pos < p.end {
				p.pos++
			}
		} else {
			p.pos++
		}
	}
	length = p.pos - start
	if p.pos < p.end {
		p.pos++ // closing quote
	}
	return
}

func hexVal(c byte) int {
	switch {
	case c >= '0' && c <= '9':
		return int(c - '0')
	case c >= 'a' && c <= 'f':
		return int(c - 'a' + 10)
	case c >= 'A' && c <= 'F':
		return int(c - 'A' + 10)
	}
	return 0
}

func (p *parser) unescape(start int, length int) {
	p.tmp = p.tmp[:0]
	i := 0
	for i < length {
		c := p.data[start+i]
		if c != '\\' {
			p.tmp = append(p.tmp, c)
			i++
			continue
		}
		e := p.data[start+i+1]
		i += 2
		switch e {
		case '"':
			p.tmp = append(p.tmp, '"')
		case '\\':
			p.tmp = append(p.tmp, '\\')
		case '/':
			p.tmp = append(p.tmp, '/')
		case 'n':
			p.tmp = append(p.tmp, '\n')
		case 't':
			p.tmp = append(p.tmp, '\t')
		case 'r':
			p.tmp = append(p.tmp, '\r')
		case 'b':
			p.tmp = append(p.tmp, '\b')
		case 'f':
			p.tmp = append(p.tmp, '\f')
		case 'u':
			cp := 0
			for k := 0; k < 4; k++ {
				cp = (cp << 4) | hexVal(p.data[start+i+k])
			}
			i += 4
			if cp >= 0xD800 && cp <= 0xDBFF && i+2 <= length && p.data[start+i] == '\\' && p.data[start+i+1] == 'u' {
				cp2 := 0
				for k := 0; k < 4; k++ {
					cp2 = (cp2 << 4) | hexVal(p.data[start+i+2+k])
				}
				i += 6
				if cp2 >= 0xDC00 && cp2 <= 0xDFFF {
					cp = 0x10000 + (cp-0xD800)<<10 + (cp2 - 0xDC00)
				}
			}
			if cp < 0x80 {
				p.tmp = append(p.tmp, byte(cp))
			} else if cp < 0x800 {
				p.tmp = append(p.tmp, byte(0xC0|cp>>6), byte(0x80|cp&0x3F))
			} else if cp < 0x10000 {
				p.tmp = append(p.tmp, byte(0xE0|cp>>12), byte(0x80|(cp>>6)&0x3F), byte(0x80|cp&0x3F))
			} else {
				p.tmp = append(p.tmp, byte(0xF0|cp>>18), byte(0x80|(cp>>12)&0x3F), byte(0x80|(cp>>6)&0x3F), byte(0x80|cp&0x3F))
			}
		}
	}
}

func (p *parser) matchLit(start int, length int, lit string) bool {
	if length != len(lit) {
		return false
	}
	equal := true
	for i := 0; i < length; i++ {
		if p.data[start+i] != lit[i] {
			equal = false
			break
		}
	}
	if equal {
		return true
	}
	p.unescape(start, length)
	if len(p.tmp) != len(lit) {
		return false
	}
	for i := 0; i < len(p.tmp); i++ {
		if p.tmp[i] != lit[i] {
			return false
		}
	}
	return true
}

func (p *parser) takeString(start int, length int) string {
	hasBackslash := false
	for i := 0; i < length; i++ {
		if p.data[start+i] == '\\' {
			hasBackslash = true
			break
		}
	}
	if !hasBackslash {
		return string(p.data[start : start+length])
	}
	p.unescape(start, length)
	return string(p.tmp)
}

func parseAmount(s []byte) int64 {
	var h int64
	dot := false
	var fr int64
	fd := 0
	for _, c := range s {
		if c >= '0' && c <= '9' {
			if !dot {
				h = h*10 + int64(c-'0')
			} else {
				fr = fr*10 + int64(c-'0')
				fd++
			}
		} else if c == '.' && !dot {
			dot = true
		}
	}
	if !dot {
		return h * 100
	}
	if fd == 1 {
		return h*100 + fr*10
	}
	return h*100 + fr
}

func (p *parser) skipArray() {
	p.pos++ // '['
	for {
		p.skipWs()
		if p.cur() == ']' {
			p.pos++
			return
		}
		p.skipValue()
		p.skipWs()
		if p.cur() == ',' {
			p.pos++
			continue
		}
		if p.cur() == ']' {
			p.pos++
			return
		}
	}
}

func (p *parser) skipObject() {
	p.pos++ // '{'
	for {
		p.skipWs()
		if p.cur() == '}' {
			p.pos++
			return
		}
		p.scanString() // key
		p.skipWs()
		if p.cur() == ':' {
			p.pos++
		}
		p.skipValue()
		p.skipWs()
		if p.cur() == ',' {
			p.pos++
			continue
		}
		if p.cur() == '}' {
			p.pos++
			return
		}
	}
}

func (p *parser) skipValue() {
	p.skipWs()
	c := p.cur()
	switch c {
	case '"':
		p.scanString()
	case '{':
		p.skipObject()
	case '[':
		p.skipArray()
	case 't':
		p.pos += 4 // true
	case 'f':
		p.pos += 5 // false
	case 'n':
		p.pos += 4 // null
	default:
		for p.pos < p.end && p.data[p.pos] >= '0' && p.data[p.pos] <= '9' {
			p.pos++
		}
		if p.pos < p.end && (p.data[p.pos] == '-' || p.data[p.pos] == '+' || p.data[p.pos] == '.' || p.data[p.pos] == 'e' || p.data[p.pos] == 'E') {
			p.pos++
		}
	}
}

// scanTags returns true if any element equals exactly "test".
func (p *parser) scanTags() bool {
	p.pos++ // '['
	found := false
	for {
		p.skipWs()
		if p.cur() == ']' {
			p.pos++
			return found
		}
		start, length, _ := p.scanString()
		if !found && p.matchLit(start, length, "test") {
			found = true
		}
		p.skipWs()
		if p.cur() == ',' {
			p.pos++
			continue
		}
		if p.cur() == ']' {
			p.pos++
			return found
		}
	}
}

func (p *parser) parseMeta(t *tx) {
	// p.pos is at '{' of meta object
	p.pos++ // '{'
	for {
		p.skipWs()
		if p.cur() == '}' {
			p.pos++
			return
		}
		ms, ml, _ := p.scanString() // key
		p.skipWs()
		if p.cur() == ':' {
			p.pos++
		}
		p.skipWs()
		if p.matchLit(ms, ml, "channel") && p.cur() == '"' {
			s, l, _ := p.scanString()
			t.channel = p.takeString(s, l)
		} else {
			p.skipValue()
		}
		p.skipWs()
		if p.cur() == ',' {
			p.pos++
			continue
		}
		if p.cur() == '}' {
			p.pos++
			return
		}
	}
}

func (p *parser) parseTxObject(t *tx) {
	p.pos++ // '{'
	for {
		p.skipWs()
		if p.cur() == '}' {
			p.pos++
			return
		}
		start, length, _ := p.scanString() // key
		p.skipWs()
		if p.cur() == ':' {
			p.pos++
		}
		p.skipWs()
		switch {
		case p.matchLit(start, length, "account") && p.cur() == '"':
			s, l, _ := p.scanString()
			t.account = p.takeString(s, l)
		case p.matchLit(start, length, "type") && p.cur() == '"':
			s, l, _ := p.scanString()
			t.typ = p.takeString(s, l)
		case p.matchLit(start, length, "amount") && p.cur() == '"':
			s, l, _ := p.scanString()
			t.hundred = parseAmount(p.data[s : s+l])
		case p.matchLit(start, length, "currency") && p.cur() == '"':
			s, l, _ := p.scanString()
			t.currency = p.takeString(s, l)
		case p.matchLit(start, length, "tags"):
			if p.cur() == '[' {
				t.testTag = p.scanTags()
			} else {
				p.skipArray()
			}
		case p.matchLit(start, length, "meta"):
			if p.cur() == '{' {
				p.parseMeta(t)
			} else {
				p.skipObject()
			}
		default:
			p.skipValue()
		}
		p.skipWs()
		if p.cur() == ',' {
			p.pos++
			continue
		}
		if p.cur() == '}' {
			p.pos++
			return
		}
	}
}

func appendInt(sb *strings.Builder, v int64) {
	if v == -9223372036854775808 {
		sb.WriteString("-9223372036854775808")
		return
	}
	if v < 0 {
		sb.WriteByte('-')
		v = -v
	}
	if v == 0 {
		sb.WriteByte('0')
		return
	}
	var buf [20]byte
	i := len(buf)
	for v > 0 {
		i--
		buf[i] = byte('0' + v%10)
		v /= 10
	}
	sb.Write(buf[i:])
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	end := len(data)

	// first newline
	firstNL := -1
	for i := 0; i < end; i++ {
		if data[i] == '\n' {
			firstNL = i
			break
		}
	}
	if firstNL < 0 {
		firstNL = end
	}

	// parse rates from first line using parser helpers
	var rates []rate
	p := parser{data: data, end: firstNL}
	p.pos = 0
	for p.pos < p.end && p.data[p.pos] != '{' {
		p.pos++
	}
	if p.pos < p.end {
		p.pos++ // outer '{'
		for p.pos < p.end {
			p.skipWs()
			if p.pos >= p.end || p.data[p.pos] == '}' {
				break
			}
			ks, kl, _ := p.scanString() // key
			p.skipWs()
			if p.cur() == ':' {
				p.pos++
			}
			p.skipWs()
			if p.matchLit(ks, kl, "rates") {
				p.skipWs()
				if p.cur() == '{' {
					p.pos++ // rates object
					for p.pos < p.end {
						p.skipWs()
						if p.pos >= p.end || p.data[p.pos] == '}' {
							break
						}
						ks2, kl2, _ := p.scanString()
						name := p.takeString(ks2, kl2)
						p.skipWs()
						if p.cur() == ':' {
							p.pos++
						}
						p.skipWs()
						var v int64
						neg := false
						if p.cur() == '-' {
							neg = true
							p.pos++
						}
						for p.pos < p.end && p.data[p.pos] >= '0' && p.data[p.pos] <= '9' {
							v = v*10 + int64(p.data[p.pos]-'0')
							p.pos++
						}
						if neg {
							v = -v
						}
						rates = append(rates, rate{name, v})
						p.skipWs()
						if p.cur() == ',' {
							p.pos++
							continue
						}
						if p.cur() == '}' {
							p.pos++
							break
						}
					}
				}
				break
			} else {
				p.skipValue()
			}
			p.skipWs()
			if p.cur() == ',' {
				p.pos++
				continue
			}
			if p.cur() == '}' {
				p.pos++
				break
			}
		}
	}

	accounts := map[string]int64{}
	channels := map[string]*ch{}
	var counted int64
	var net int64

	start := firstNL + 1
	for start < end {
		lineStart := start
		linend := start
		for linend < end && data[linend] != '\n' {
			linend++
		}
		lineEnd := linend
		start = lineEnd + 1
		if start > end {
			start = end
		}

		// Use a fresh parser over [lineStart, lineEnd)
		tp := parser{data: data, end: lineEnd}
		tp.pos = lineStart
		if tp.cur() == '{' {
			t := tx{}
			tp.parseTxObject(&t)
			if t.typ != "" && t.typ != "void" && !t.testTag {
				var rate int64
				for _, r := range rates {
					if r.name == t.currency {
						rate = r.value
						break
					}
				}
				usd := (t.hundred * rate) / 1000000
				val := usd
				if t.typ != "credit" && t.typ != "refund" {
					val = -usd
				}
				counted++
				net += val
				c, ok := channels[t.channel]
				if !ok {
					c = &ch{}
					channels[t.channel] = c
				}
				c.count++
				c.net += val
				accounts[t.account] += val
			}
		}
	}

	var sb strings.Builder
	sb.WriteString("counted ")
	appendInt(&sb, counted)
	sb.WriteByte('\n')
	sb.WriteString("net ")
	appendInt(&sb, net)
	sb.WriteByte('\n')

	// channels sorted by name ascending
	var chNames []string
	for name := range channels {
		chNames = append(chNames, name)
	}
	sort.Strings(chNames)
	for _, name := range chNames {
		c := channels[name]
		sb.WriteString("channel ")
		sb.WriteString(name)
		sb.WriteByte(' ')
		appendInt(&sb, c.count)
		sb.WriteByte(' ')
		appendInt(&sb, c.net)
		sb.WriteByte('\n')
	}

	// top 10 accounts: net desc, id asc
	type ac struct {
		id  string
		net int64
	}
	var acs []ac
	for id, netv := range accounts {
		acs = append(acs, ac{id, netv})
	}
	sort.Slice(acs, func(i, j int) bool {
		if acs[i].net != acs[j].net {
			return acs[i].net > acs[j].net
		}
		return acs[i].id < acs[j].id
	})
	m := len(acs)
	if m > 10 {
		m = 10
	}
	for i := 0; i < m; i++ {
		sb.WriteString("account ")
		sb.WriteString(acs[i].id)
		sb.WriteByte(' ')
		appendInt(&sb, acs[i].net)
		sb.WriteByte('\n')
	}

	fmt.Print(sb.String())
}
