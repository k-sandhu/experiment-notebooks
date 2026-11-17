package main

import (
	"bufio"
	"os"
	"sort"
	"strconv"
	"unicode/utf8"
)

type parser struct {
	b       []byte
	i       int
	scratch []byte
}

func (p *parser) ws() {
	b, i := p.b, p.i
	for i < len(b) && b[i] <= ' ' {
		i++
	}
	p.i = i
}

func hex4(b []byte) rune {
	var v rune
	for _, c := range b[:4] {
		v <<= 4
		switch {
		case c >= '0' && c <= '9':
			v |= rune(c - '0')
		case c >= 'a' && c <= 'f':
			v |= rune(c-'a') + 10
		default:
			v |= rune(c-'A') + 10
		}
	}
	return v
}

func (p *parser) str() []byte {
	b := p.b
	start := p.i + 1
	i := start
	for {
		c := b[i]
		if c == '"' {
			p.i = i + 1
			return b[start:i]
		}
		if c == '\\' {
			return p.escaped(start, i)
		}
		i++
	}
}

func (p *parser) escaped(start, i int) []byte {
	b := p.b
	off := len(p.scratch)
	p.scratch = append(p.scratch, b[start:i]...)

	for {
		c := b[i]
		i++
		if c == '"' {
			p.i = i
			return p.scratch[off:]
		}
		if c != '\\' {
			p.scratch = append(p.scratch, c)
			continue
		}

		c = b[i]
		i++
		switch c {
		case '"', '\\', '/':
			p.scratch = append(p.scratch, c)
		case 'b':
			p.scratch = append(p.scratch, '\b')
		case 'f':
			p.scratch = append(p.scratch, '\f')
		case 'n':
			p.scratch = append(p.scratch, '\n')
		case 'r':
			p.scratch = append(p.scratch, '\r')
		case 't':
			p.scratch = append(p.scratch, '\t')
		case 'u':
			r := hex4(b[i:])
			i += 4
			if r >= 0xD800 && r <= 0xDBFF &&
				i+6 <= len(b) && b[i] == '\\' && b[i+1] == 'u' {
				lo := hex4(b[i+2:])
				if lo >= 0xDC00 && lo <= 0xDFFF {
					r = 0x10000 + (r-0xD800)*0x400 + lo - 0xDC00
					i += 6
				}
			}
			p.scratch = utf8.AppendRune(p.scratch, r)
		}
	}
}

func skipString(b []byte, i int) int {
	i++
	for {
		switch b[i] {
		case '"':
			return i + 1
		case '\\':
			i += 2
		default:
			i++
		}
	}
}

// i points just after the opening delimiter.
func skipContainer(b []byte, i int) int {
	depth := 1
	for {
		switch b[i] {
		case '"':
			i = skipString(b, i)
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
}

func (p *parser) skipValue() {
	b, i := p.b, p.i
	switch b[i] {
	case '"':
		p.i = skipString(b, i)
	case '{', '[':
		p.i = skipContainer(b, i+1)
	default:
		for i < len(b) {
			c := b[i]
			if c <= ' ' || c == ',' || c == '}' || c == ']' {
				break
			}
			i++
		}
		p.i = i
	}
}

func (p *parser) integer() int64 {
	b, i := p.b, p.i
	negative := b[i] == '-'
	if negative {
		i++
	}
	var v int64
	for i < len(b) && b[i] >= '0' && b[i] <= '9' {
		v = v*10 + int64(b[i]-'0')
		i++
	}
	p.i = i
	if negative {
		return -v
	}
	return v
}

func (p *parser) readRates() map[string]int64 {
	rates := make(map[string]int64, 16)
	p.ws()
	p.i++
	for {
		p.ws()
		if p.b[p.i] == '}' {
			return rates
		}
		key := p.str()
		p.ws()
		p.i++
		p.ws()

		if string(key) == "rates" {
			p.i++
			for {
				p.ws()
				if p.b[p.i] == '}' {
					return rates
				}
				name := p.str()
				p.ws()
				p.i++
				p.ws()
				rates[string(name)] = p.integer()
				p.ws()
				if p.b[p.i] != ',' {
					return rates
				}
				p.i++
			}
		}

		p.skipValue()
		p.ws()
		if p.b[p.i] != ',' {
			return rates
		}
		p.i++
	}
}

func cents(s []byte) int64 {
	var v int64
	i := 0
	for i < len(s) && s[i] != '.' {
		v = v*10 + int64(s[i]-'0')
		i++
	}
	v *= 100
	if i < len(s) {
		i++
		v += int64(s[i]-'0') * 10
		i++
		if i < len(s) {
			v += int64(s[i] - '0')
		}
	}
	return v
}

func (p *parser) testTags() bool {
	p.i++
	for {
		p.ws()
		if p.b[p.i] == ']' {
			p.i++
			return false
		}
		if string(p.str()) == "test" {
			return true
		}
		p.ws()
		if p.b[p.i] != ',' {
			p.i++
			return false
		}
		p.i++
	}
}

func (p *parser) channel() []byte {
	p.i++
	for {
		p.ws()
		if p.b[p.i] == '}' {
			p.i++
			return nil
		}
		key := p.str()
		p.ws()
		p.i++
		p.ws()
		if string(key) == "channel" {
			name := p.str()
			p.i = skipContainer(p.b, p.i)
			return name
		}
		p.skipValue()
		p.ws()
		c := p.b[p.i]
		p.i++
		if c == '}' {
			return nil
		}
	}
}

type accountTotal struct {
	name string
	net  int64
}

type channelTotal struct {
	name  string
	count int64
	net   int64
}

type ledger struct {
	rates        map[string]int64
	accountIndex map[string]int
	channelIndex map[string]int
	accounts     []accountTotal
	channels     []channelTotal
	count        int64
	net          int64
}

func (p *parser) transaction(l *ledger) {
	var account, channel []byte
	var amount, rate int64
	var debit bool
	var fields uint8

	p.ws()
	p.i++
	for {
		p.ws()
		if p.b[p.i] == '}' {
			break
		}
		key := p.str()
		p.ws()
		p.i++
		p.ws()

		switch string(key) {
		case "account":
			account = p.str()
			fields |= 1
		case "type":
			switch string(p.str()) {
			case "void":
				return
			case "debit":
				debit = true
			default:
				debit = false
			}
			fields |= 2
		case "amount":
			amount = cents(p.str())
			fields |= 4
		case "currency":
			rate = l.rates[string(p.str())]
			fields |= 8
		case "tags":
			if p.testTags() {
				return
			}
			fields |= 16
		case "meta":
			channel = p.channel()
			fields |= 32
		default:
			p.skipValue()
		}

		if fields == 63 {
			break
		}
		p.ws()
		if p.b[p.i] != ',' {
			break
		}
		p.i++
	}

	product := amount * rate
	value := product / 1000000
	if product < 0 && product%1000000 != 0 {
		value--
	}
	if debit {
		value = -value
	}

	l.count++
	l.net += value

	if index := l.accountIndex[string(account)]; index != 0 {
		l.accounts[index-1].net += value
	} else {
		name := string(account)
		l.accounts = append(l.accounts, accountTotal{name: name, net: value})
		l.accountIndex[name] = len(l.accounts)
	}

	if index := l.channelIndex[string(channel)]; index != 0 {
		c := &l.channels[index-1]
		c.count++
		c.net += value
	} else {
		name := string(channel)
		l.channels = append(l.channels, channelTotal{
			name: name, count: 1, net: value,
		})
		l.channelIndex[name] = len(l.channels)
	}
}

func better(a, b accountTotal) bool {
	return a.net > b.net || (a.net == b.net && a.name < b.name)
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		panic(err)
	}
	defer f.Close()

	l := ledger{
		accountIndex: make(map[string]int, 16384),
		channelIndex: make(map[string]int, 16),
		accounts:     make([]accountTotal, 0, 16384),
		channels:     make([]channelTotal, 0, 16),
	}
	p := parser{scratch: make([]byte, 0, 256)}
	reader := bufio.NewReaderSize(f, 1<<20)
	var long []byte
	first := true

	for {
		line, readErr := reader.ReadSlice('\n')
		if readErr == bufio.ErrBufferFull {
			long = append(long, line...)
			continue
		}
		if len(long) != 0 {
			long = append(long, line...)
			line = long
		}
		if len(line) != 0 {
			p.b = line
			p.i = 0
			p.scratch = p.scratch[:0]
			if first {
				l.rates = p.readRates()
				first = false
			} else {
				p.transaction(&l)
			}
		}
		long = long[:0]
		if readErr != nil {
			break
		}
	}

	sort.Slice(l.channels, func(i, j int) bool {
		return l.channels[i].name < l.channels[j].name
	})

	top := make([]accountTotal, 0, 10)
	for _, a := range l.accounts {
		n := len(top)
		if n == 10 && !better(a, top[9]) {
			continue
		}
		if n < 10 {
			top = append(top, a)
			n++
		}
		i := n - 1
		for i > 0 && better(a, top[i-1]) {
			top[i] = top[i-1]
			i--
		}
		top[i] = a
	}

	w := bufio.NewWriterSize(os.Stdout, 64<<10)
	out := make([]byte, 0, 256)

	out = append(out, "counted "...)
	out = strconv.AppendInt(out, l.count, 10)
	out = append(out, '\n')
	out = append(out, "net "...)
	out = strconv.AppendInt(out, l.net, 10)
	out = append(out, '\n')
	_, _ = w.Write(out)

	for _, c := range l.channels {
		out = append(out[:0], "channel "...)
		out = append(out, c.name...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, c.count, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, c.net, 10)
		out = append(out, '\n')
		_, _ = w.Write(out)
	}
	for _, a := range top {
		out = append(out[:0], "account "...)
		out = append(out, a.name...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, a.net, 10)
		out = append(out, '\n')
		_, _ = w.Write(out)
	}
	_ = w.Flush()
}
