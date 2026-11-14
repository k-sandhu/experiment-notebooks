package main

import (
	"bufio"
	"encoding/json"
	"os"
	"runtime"
	"sort"
	"strconv"
	"unicode/utf8"
)

type parser struct {
	data    []byte
	pos     int
	scratch []byte
}

func (p *parser) whitespace() {
	for p.pos < len(p.data) && p.data[p.pos] <= ' ' {
		p.pos++
	}
}

func hex4(b []byte) rune {
	var n rune
	for _, c := range b[:4] {
		n <<= 4
		switch {
		case c <= '9':
			n |= rune(c - '0')
		case c <= 'F':
			n |= rune(c-'A') + 10
		default:
			n |= rune(c-'a') + 10
		}
	}
	return n
}

func (p *parser) stringValue() []byte {
	start := p.pos + 1
	for i := start; ; i++ {
		switch p.data[i] {
		case '"':
			p.pos = i + 1
			return p.data[start:i]
		case '\\':
			return p.escapedString(start, i)
		}
	}
}

func (p *parser) escapedString(start, i int) []byte {
	d := p.data
	begin := len(p.scratch)
	p.scratch = append(p.scratch, d[start:i]...)

	for {
		c := d[i]
		if c == '"' {
			p.pos = i + 1
			return p.scratch[begin:]
		}
		if c != '\\' {
			p.scratch = append(p.scratch, c)
			i++
			continue
		}

		c = d[i+1]
		i += 2
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
			r := hex4(d[i : i+4])
			i += 4
			if r >= 0xD800 && r <= 0xDBFF &&
				i+6 <= len(d) && d[i] == '\\' && d[i+1] == 'u' {
				low := hex4(d[i+2 : i+6])
				if low >= 0xDC00 && low <= 0xDFFF {
					r = 0x10000 + (r-0xD800)*0x400 + low - 0xDC00
					i += 6
				}
			}
			if r >= 0xD800 && r <= 0xDFFF {
				r = utf8.RuneError
			}
			p.scratch = utf8.AppendRune(p.scratch, r)
		}
	}
}

func (p *parser) skipString() {
	i := p.pos + 1
	for {
		switch p.data[i] {
		case '"':
			p.pos = i + 1
			return
		case '\\':
			i += 2
		default:
			i++
		}
	}
}

func (p *parser) skipValue() {
	switch p.data[p.pos] {
	case '"':
		p.skipString()
	case '{', '[':
		depth := 1
		p.pos++
		for depth != 0 {
			switch p.data[p.pos] {
			case '"':
				p.skipString()
			case '{', '[':
				depth++
				p.pos++
			case '}', ']':
				depth--
				p.pos++
			default:
				p.pos++
			}
		}
	default:
		for p.pos < len(p.data) {
			c := p.data[p.pos]
			if c <= ' ' || c == ',' || c == '}' || c == ']' {
				return
			}
			p.pos++
		}
	}
}

func (p *parser) tags() bool {
	p.pos++
	found := false
	for {
		p.whitespace()
		if p.data[p.pos] == ']' {
			p.pos++
			return found
		}
		if string(p.stringValue()) == "test" {
			found = true
		}
		p.whitespace()
		if p.data[p.pos] == ',' {
			p.pos++
		}
	}
}

func (p *parser) metaChannel() []byte {
	p.pos++
	var channel []byte
	for {
		p.whitespace()
		if p.data[p.pos] == '}' {
			p.pos++
			return channel
		}

		key := p.stringValue()
		p.whitespace()
		p.pos++
		p.whitespace()

		if string(key) == "channel" {
			channel = p.stringValue()
		} else {
			p.skipValue()
		}

		p.whitespace()
		if p.data[p.pos] == ',' {
			p.pos++
		}
	}
}

type transaction struct {
	account  []byte
	kind     []byte
	amount   []byte
	currency []byte
	channel  []byte
	test     bool
}

func (p *parser) transaction() transaction {
	var t transaction
	p.whitespace()
	p.pos++

	for {
		p.whitespace()
		if p.data[p.pos] == '}' {
			p.pos++
			return t
		}

		key := p.stringValue()
		p.whitespace()
		p.pos++
		p.whitespace()

		switch string(key) {
		case "account":
			t.account = p.stringValue()
		case "type":
			t.kind = p.stringValue()
		case "amount":
			t.amount = p.stringValue()
		case "currency":
			t.currency = p.stringValue()
		case "tags":
			t.test = p.tags()
		case "meta":
			t.channel = p.metaChannel()
		default:
			p.skipValue()
		}

		p.whitespace()
		if p.data[p.pos] == ',' {
			p.pos++
		}
	}
}

func hundredths(b []byte) int64 {
	var n int64
	i := 0
	for i < len(b) && b[i] != '.' {
		n = n*10 + int64(b[i]-'0')
		i++
	}
	n *= 100
	if i < len(b) {
		i++
		n += int64(b[i]-'0') * 10
		i++
		if i < len(b) {
			n += int64(b[i] - '0')
		}
	}
	return n
}

func readLine(r *bufio.Reader, scratch *[]byte) ([]byte, error) {
	line, err := r.ReadSlice('\n')
	if err != bufio.ErrBufferFull {
		return line, err
	}

	b := append((*scratch)[:0], line...)
	for err == bufio.ErrBufferFull {
		line, err = r.ReadSlice('\n')
		b = append(b, line...)
	}
	*scratch = b
	return b, err
}

type accountTotal struct {
	id  string
	net int64
}

type channelTotal struct {
	name  string
	count int64
	net   int64
}

func better(a, b accountTotal) bool {
	if a.net != b.net {
		return a.net > b.net
	}
	return a.id < b.id
}

func main() {
	runtime.GOMAXPROCS(1)

	if len(os.Args) < 2 {
		return
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		return
	}
	defer f.Close()

	reader := bufio.NewReaderSize(f, 1<<20)
	var lineScratch []byte

	line, err := readLine(reader, &lineScratch)
	if len(line) == 0 {
		return
	}

	var header map[string]json.RawMessage
	if json.Unmarshal(line, &header) != nil {
		return
	}
	var rates map[string]int64
	if json.Unmarshal(header["rates"], &rates) != nil {
		return
	}

	accountIndex := make(map[string]int)
	channelIndex := make(map[string]int)
	accounts := make([]accountTotal, 0, 1024)
	channels := make([]channelTotal, 0, 16)

	var counted, net int64
	p := parser{scratch: make([]byte, 0, 256)}

	for {
		line, err = readLine(reader, &lineScratch)
		if len(line) == 0 {
			break
		}

		p.data = line
		p.pos = 0
		p.scratch = p.scratch[:0]
		t := p.transaction()

		if !t.test && string(t.kind) != "void" {
			value := hundredths(t.amount) * rates[string(t.currency)] / 1000000
			if string(t.kind) == "debit" {
				value = -value
			}

			counted++
			net += value

			ai := accountIndex[string(t.account)]
			if ai == 0 {
				id := string(t.account)
				accounts = append(accounts, accountTotal{id: id})
				ai = len(accounts)
				accountIndex[id] = ai
			}
			accounts[ai-1].net += value

			ci := channelIndex[string(t.channel)]
			if ci == 0 {
				name := string(t.channel)
				channels = append(channels, channelTotal{name: name})
				ci = len(channels)
				channelIndex[name] = ci
			}
			channels[ci-1].count++
			channels[ci-1].net += value
		}

		if err != nil {
			break
		}
	}

	sort.Slice(channels, func(i, j int) bool {
		return channels[i].name < channels[j].name
	})

	top := make([]accountTotal, 0, 10)
	for _, a := range accounts {
		if len(top) == 10 && !better(a, top[9]) {
			continue
		}
		pos := len(top)
		if pos < 10 {
			top = append(top, accountTotal{})
		} else {
			pos = 9
		}
		for pos > 0 && better(a, top[pos-1]) {
			top[pos] = top[pos-1]
			pos--
		}
		top[pos] = a
	}

	out := bufio.NewWriterSize(os.Stdout, 64<<10)
	buf := make([]byte, 0, 256)

	buf = append(buf, "counted "...)
	buf = strconv.AppendInt(buf, counted, 10)
	buf = append(buf, '\n')
	buf = append(buf, "net "...)
	buf = strconv.AppendInt(buf, net, 10)
	buf = append(buf, '\n')
	_, _ = out.Write(buf)

	for _, c := range channels {
		buf = append(buf[:0], "channel "...)
		buf = append(buf, c.name...)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, c.count, 10)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, c.net, 10)
		buf = append(buf, '\n')
		_, _ = out.Write(buf)
	}

	for _, a := range top {
		buf = append(buf[:0], "account "...)
		buf = append(buf, a.id...)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, a.net, 10)
		buf = append(buf, '\n')
		_, _ = out.Write(buf)
	}

	_ = out.Flush()
}
