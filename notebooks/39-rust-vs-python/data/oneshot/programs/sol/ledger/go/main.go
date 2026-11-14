package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"os"
	"runtime"
	"sort"
	"strconv"
	"unsafe"
)

type parser struct {
	data string
	pos  int
}

func (p *parser) space() {
	for p.pos < len(p.data) && p.data[p.pos] <= ' ' {
		p.pos++
	}
}

func (p *parser) readString() string {
	start := p.pos + 1
	i := start

	for {
		c := p.data[i]
		if c == '"' {
			p.pos = i + 1
			return p.data[start:i]
		}
		if c == '\\' {
			break
		}
		i++
	}

	for {
		switch p.data[i] {
		case '\\':
			i += 2
		case '"':
			p.pos = i + 1
			var s string
			_ = json.Unmarshal([]byte(p.data[start-1:p.pos]), &s)
			return s
		default:
			i++
		}
	}
}

func (p *parser) skipString() {
	i := p.pos + 1
	for {
		switch p.data[i] {
		case '\\':
			i += 2
		case '"':
			p.pos = i + 1
			return
		default:
			i++
		}
	}
}

// The opening delimiter has already been consumed.
func (p *parser) skipComposite(depth int) {
	i := p.pos
	for depth > 0 {
		switch p.data[i] {
		case '"':
			i++
			for {
				if p.data[i] == '\\' {
					i += 2
				} else if p.data[i] == '"' {
					i++
					break
				} else {
					i++
				}
			}
		case '{', '[':
			depth++
			i++
		case '}', ']':
			depth--
			i++
		default:
			i++
		}
	}
	p.pos = i
}

func (p *parser) skipValue() {
	p.space()
	switch p.data[p.pos] {
	case '"':
		p.skipString()
	case '{', '[':
		p.pos++
		p.skipComposite(1)
	default:
		for {
			switch p.data[p.pos] {
			case ',', '}', ']', ' ', '\t', '\r', '\n':
				return
			default:
				p.pos++
			}
		}
	}
}

func (p *parser) testTags() bool {
	p.pos++ // [
	for {
		p.space()
		if p.data[p.pos] == ']' {
			p.pos++
			return false
		}

		if p.readString() == "test" {
			p.skipComposite(1)
			return true
		}

		p.space()
		if p.data[p.pos] == ',' {
			p.pos++
		}
	}
}

func (p *parser) metaChannel() string {
	p.pos++ // {
	var channel string

	for {
		p.space()
		if p.data[p.pos] == '}' {
			p.pos++
			return channel
		}

		key := p.readString()
		p.space()
		p.pos++ // :
		p.space()

		if key == "channel" {
			channel = p.readString()
		} else {
			p.skipValue()
		}

		p.space()
		if p.data[p.pos] == ',' {
			p.pos++
		}
	}
}

func amountCents(s string) int64 {
	var whole int64
	i := 0
	for i < len(s) && s[i] != '.' {
		whole = whole*10 + int64(s[i]-'0')
		i++
	}

	result := whole * 100
	if i < len(s) {
		i++
		result += int64(s[i]-'0') * 10
		if i+1 < len(s) {
			result += int64(s[i+1] - '0')
		}
	}
	return result
}

type transaction struct {
	account  string
	kind     string
	currency string
	channel  string
	cents    int64
	test     bool
}

func (p *parser) readTransaction() transaction {
	var t transaction
	p.pos++ // {

	for {
		p.space()
		if p.data[p.pos] == '}' {
			p.pos++
			return t
		}

		key := p.readString()
		p.space()
		p.pos++ // :
		p.space()

		switch key {
		case "account":
			t.account = p.readString()
		case "type":
			t.kind = p.readString()
		case "amount":
			t.cents = amountCents(p.readString())
		case "currency":
			t.currency = p.readString()
		case "tags":
			t.test = p.testTags()
		case "meta":
			t.channel = p.metaChannel()
		default:
			p.skipValue()
		}

		p.space()
		if p.data[p.pos] == ',' {
			p.pos++
		}
	}
}

type channelTotal struct {
	count int64
	net   int64
}

type accountTotal struct {
	id  string
	net int64
}

func main() {
	runtime.GOMAXPROCS(1)

	if len(os.Args) < 2 {
		return
	}
	input, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	firstEnd := bytes.IndexByte(input, '\n')
	if firstEnd < 0 {
		return
	}

	var header struct {
		Rates map[string]int64 `json:"rates"`
	}
	if json.Unmarshal(input[:firstEnd], &header) != nil {
		return
	}

	// The input remains immutable for the lifetime of these string views.
	p := parser{
		data: unsafe.String(unsafe.SliceData(input), len(input)),
		pos:  firstEnd + 1,
	}

	accounts := make(map[string]int64, 1<<16)
	channels := make(map[string]*channelTotal, 16)
	var counted, net int64

	for {
		p.space()
		if p.pos == len(p.data) {
			break
		}

		t := p.readTransaction()
		if t.test || t.kind == "void" {
			continue
		}

		value := (t.cents * header.Rates[t.currency]) / 1000000
		if t.kind == "debit" {
			value = -value
		}

		counted++
		net += value
		accounts[t.account] += value

		total := channels[t.channel]
		if total == nil {
			total = &channelTotal{}
			channels[t.channel] = total
		}
		total.count++
		total.net += value
	}

	names := make([]string, 0, len(channels))
	for name := range channels {
		names = append(names, name)
	}
	sort.Strings(names)

	var top [10]accountTotal
	topCount := 0
	for id, value := range accounts {
		pos := topCount
		for pos > 0 {
			prev := top[pos-1]
			if value < prev.net || (value == prev.net && id >= prev.id) {
				break
			}
			pos--
		}
		if pos >= len(top) {
			continue
		}
		if topCount < len(top) {
			topCount++
		}
		for j := topCount - 1; j > pos; j-- {
			top[j] = top[j-1]
		}
		top[pos] = accountTotal{id: id, net: value}
	}

	out := bufio.NewWriterSize(os.Stdout, 1<<16)
	line := make([]byte, 0, 256)

	line = append(line, "counted "...)
	line = strconv.AppendInt(line, counted, 10)
	line = append(line, '\n')
	line = append(line, "net "...)
	line = strconv.AppendInt(line, net, 10)
	line = append(line, '\n')
	_, _ = out.Write(line)

	for _, name := range names {
		total := channels[name]
		line = line[:0]
		line = append(line, "channel "...)
		line = append(line, name...)
		line = append(line, ' ')
		line = strconv.AppendInt(line, total.count, 10)
		line = append(line, ' ')
		line = strconv.AppendInt(line, total.net, 10)
		line = append(line, '\n')
		_, _ = out.Write(line)
	}

	for i := 0; i < topCount; i++ {
		line = line[:0]
		line = append(line, "account "...)
		line = append(line, top[i].id...)
		line = append(line, ' ')
		line = strconv.AppendInt(line, top[i].net, 10)
		line = append(line, '\n')
		_, _ = out.Write(line)
	}

	_ = out.Flush()
}
