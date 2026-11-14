package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"sort"
	"unicode/utf8"
)

type parser struct {
	b []byte
	i int
}

func (p *parser) ws() {
	for p.i < len(p.b) && p.b[p.i] <= ' ' {
		p.i++
	}
}
func (p *parser) take() { p.ws(); p.i++ }
func (p *parser) more(end byte) bool {
	p.ws()
	if p.b[p.i] == ',' {
		p.i++
		p.ws()
	}
	if p.b[p.i] == end {
		p.i++
		return false
	}
	return true
}
func hex(c byte) rune {
	if c <= '9' {
		return rune(c - '0')
	}
	return rune((c | 32) - 'a' + 10)
}
func (p *parser) hex4() rune {
	var n rune
	for j := 0; j < 4; j++ {
		n = n*16 + hex(p.b[p.i])
		p.i++
	}
	return n
}

// Return a borrowed slice on the usual unescaped path.
func (p *parser) str(scratch *[]byte) []byte {
	p.ws()
	p.i++
	start := p.i
	for p.b[p.i] != '"' && p.b[p.i] != '\\' {
		p.i++
	}
	if p.b[p.i] == '"' {
		result := p.b[start:p.i]
		p.i++
		return result
	}
	s := append((*scratch)[:0], p.b[start:p.i]...)
	for {
		c := p.b[p.i]
		p.i++
		if c == '"' {
			*scratch = s
			return s
		}
		if c != '\\' {
			s = append(s, c)
			continue
		}
		c = p.b[p.i]
		p.i++
		switch c {
		case 'b':
			s = append(s, '\b')
		case 'f':
			s = append(s, '\f')
		case 'n':
			s = append(s, '\n')
		case 'r':
			s = append(s, '\r')
		case 't':
			s = append(s, '\t')
		case 'u':
			cp := p.hex4()
			if cp >= 0xd800 && cp <= 0xdbff && p.b[p.i] == '\\' && p.b[p.i+1] == 'u' {
				saved := p.i
				p.i += 2
				low := p.hex4()
				if low >= 0xdc00 && low <= 0xdfff {
					cp = 0x10000 + ((cp - 0xd800) << 10) + low - 0xdc00
				} else {
					p.i = saved
				}
			}
			if cp >= 0xd800 && cp <= 0xdfff {
				s = append(s, byte(0xe0|(cp>>12)), byte(0x80|((cp>>6)&63)), byte(0x80|(cp&63)))
			} else {
				s = utf8.AppendRune(s, cp)
			}
		default:
			s = append(s, c)
		}
	}
}
func (p *parser) skipString() {
	p.i++
	for p.b[p.i] != '"' {
		if p.b[p.i] == '\\' {
			p.i++
		}
		p.i++
	}
	p.i++
}
func (p *parser) skip() {
	p.ws()
	c := p.b[p.i]
	if c == '"' {
		p.skipString()
		return
	}
	if c == '{' || c == '[' {
		depth := 1
		p.i++
		for depth != 0 {
			c = p.b[p.i]
			if c == '"' {
				p.skipString()
				continue
			}
			p.i++
			if c == '{' || c == '[' {
				depth++
			} else if c == '}' || c == ']' {
				depth--
			}
		}
	} else {
		for p.i < len(p.b) {
			c = p.b[p.i]
			if c <= ' ' || c == ',' || c == '}' || c == ']' {
				break
			}
			p.i++
		}
	}
}
func (p *parser) integer() int64 {
	p.ws()
	negative := p.b[p.i] == '-'
	if negative {
		p.i++
	}
	start := p.i
	var digits, fraction int64
	dot := false
	for p.b[p.i] >= '0' && p.b[p.i] <= '9' || p.b[p.i] == '.' {
		if p.b[p.i] == '.' {
			dot = true
		} else {
			digits++
			if dot {
				fraction++
			}
		}
		p.i++
	}
	end := p.i
	var exponent int64
	const cap int64 = 1 << 60
	if p.b[p.i] == 'e' || p.b[p.i] == 'E' {
		p.i++
		eneg := p.b[p.i] == '-'
		if p.b[p.i] == '+' || p.b[p.i] == '-' {
			p.i++
		}
		for p.b[p.i] >= '0' && p.b[p.i] <= '9' {
			if exponent > cap/10 {
				exponent = cap
			} else {
				exponent = min(cap, exponent*10+int64(p.b[p.i]-'0'))
			}
			p.i++
		}
		if eneg {
			exponent = -exponent
		}
	}
	scale := exponent - fraction
	keep := digits + min(scale, 0)
	var n int64
	for i := start; i < end && keep > 0; i++ {
		if p.b[i] != '.' {
			n = n*10 + int64(p.b[i]-'0')
			keep--
		}
	}
	if scale >= 64 {
		n = 0
	} else {
		for i := int64(0); i < scale; i++ {
			n *= 10
		}
	}
	if negative {
		return -n
	}
	return n
}
func hundredths(s []byte) int64 {
	var n int64
	i := 0
	for i < len(s) && s[i] != '.' {
		n = n*10 + int64(s[i]-'0')
		i++
	}
	n *= 100
	if i < len(s) {
		i++
		n += int64(s[i]-'0') * 10
		i++
		if i < len(s) {
			n += int64(s[i] - '0')
		}
	}
	return n
}

type total struct{ count, net int64 }
type ledger struct {
	rates                                          map[string]int64
	accounts, channels                             map[string]*total
	count, net                                     int64
	key, value, account, channel, currency, amount []byte
}

func (l *ledger) header(line []byte) {
	p := parser{b: line}
	p.take()
	for p.more('}') {
		key := p.str(&l.key)
		p.take()
		if string(key) != "rates" {
			p.skip()
			continue
		}
		p.take()
		for p.more('}') {
			name := string(p.str(&l.value))
			p.take()
			l.rates[name] = p.integer()
		}
	}
}
func (l *ledger) transaction(line []byte) {
	p := parser{b: line}
	p.take()
	var account, channel, currency, amount []byte
	debit := false
	for p.more('}') {
		key := p.str(&l.key)
		p.take()
		switch string(key) {
		case "account":
			account = p.str(&l.account)
		case "currency":
			currency = p.str(&l.currency)
		case "amount":
			amount = p.str(&l.amount)
		case "type":
			typ := p.str(&l.value)
			if string(typ) == "void" {
				return
			}
			debit = string(typ) == "debit"
		case "tags":
			p.take()
			for p.more(']') {
				if string(p.str(&l.value)) == "test" {
					return
				}
			}
		case "meta":
			p.take()
			for p.more('}') {
				key := p.str(&l.key)
				p.take()
				if string(key) == "channel" {
					channel = p.str(&l.channel)
				} else {
					p.skip()
				}
			}
		default:
			p.skip()
		}
	}
	product := hundredths(amount) * l.rates[string(currency)]
	value := product / 1000000
	if product < 0 && product%1000000 != 0 {
		value--
	}
	if debit {
		value = -value
	}
	l.count++
	l.net += value
	// Conversion in a map lookup borrows the bytes; copy only new identifiers.
	if a := l.accounts[string(account)]; a != nil {
		a.net += value
	} else {
		l.accounts[string(account)] = &total{net: value}
	}
	if c := l.channels[string(channel)]; c != nil {
		c.count++
		c.net += value
	} else {
		l.channels[string(channel)] = &total{count: 1, net: value}
	}
}

type row struct {
	name string
	net  int64
}

func better(a, b row) bool { return a.net > b.net || a.net == b.net && a.name < b.name }
func (l *ledger) output() {
	out := bufio.NewWriter(os.Stdout)
	fmt.Fprintf(out, "counted %d\nnet %d\n", l.count, l.net)
	names := make([]string, 0, len(l.channels))
	for name := range l.channels {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		c := l.channels[name]
		fmt.Fprintf(out, "channel %s %d %d\n", name, c.count, c.net)
	}
	var top [10]row
	length := 0
	for name, a := range l.accounts {
		r := row{name, a.net}
		pos := 0
		for pos < length && !better(r, top[pos]) {
			pos++
		}
		if pos == 10 {
			continue
		}
		last := length
		if last > 9 {
			last = 9
		}
		for i := last; i > pos; i-- {
			top[i] = top[i-1]
		}
		top[pos] = r
		if length < 10 {
			length++
		}
	}
	for _, a := range top[:length] {
		fmt.Fprintf(out, "account %s %d\n", a.name, a.net)
	}
	out.Flush()
}
func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		panic(err)
	}
	defer f.Close()
	l := ledger{rates: make(map[string]int64), accounts: make(map[string]*total), channels: make(map[string]*total)}
	in := bufio.NewReaderSize(f, 1<<20)
	first := true
	var pending []byte
	for {
		part, err := in.ReadSlice('\n')
		if err == bufio.ErrBufferFull {
			pending = append(pending, part...)
			continue
		}
		line := part
		if len(pending) != 0 {
			pending = append(pending, part...)
			line = pending
		}
		if len(line) != 0 {
			if first {
				l.header(line)
				first = false
			} else {
				l.transaction(line)
			}
		}
		pending = pending[:0]
		if err == io.EOF {
			break
		}
		if err != nil {
			panic(err)
		}
	}
	l.output()
}
