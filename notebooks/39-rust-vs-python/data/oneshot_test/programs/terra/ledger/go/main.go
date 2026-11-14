package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
	"unsafe"
)

type parser struct {
	b []byte
	i int
}

func (p *parser) space() {
	for p.i < len(p.b) {
		switch p.b[p.i] {
		case ' ', '\t', '\r', '\n':
			p.i++
		default:
			return
		}
	}
}

func (p *parser) str() string {
	start := p.i
	p.i++ // opening quote
	content := p.i
	escaped := false

	for {
		c := p.b[p.i]
		if c == '"' {
			end := p.i
			p.i++
			if !escaped {
				if end == content {
					return ""
				}
				return unsafe.String(&p.b[content], end-content)
			}
			var s string
			_ = json.Unmarshal(p.b[start:p.i], &s)
			return s
		}
		if c == '\\' {
			escaped = true
			p.i += 2
		} else {
			p.i++
		}
	}
}

func (p *parser) skip() {
	p.space()
	switch p.b[p.i] {
	case '"':
		p.i++
		for {
			switch p.b[p.i] {
			case '\\':
				p.i += 2
			case '"':
				p.i++
				return
			default:
				p.i++
			}
		}
	case '{', '[':
		depth := 0
		for {
			switch p.b[p.i] {
			case '{', '[':
				depth++
				p.i++
			case '}', ']':
				depth--
				p.i++
				if depth == 0 {
					return
				}
			case '"':
				p.i++
				for {
					if p.b[p.i] == '\\' {
						p.i += 2
					} else if p.b[p.i] == '"' {
						p.i++
						break
					} else {
						p.i++
					}
				}
			default:
				p.i++
			}
		}
	default:
		for p.i < len(p.b) {
			switch p.b[p.i] {
			case ',', '}', ']', ' ', '\t', '\r', '\n':
				return
			default:
				p.i++
			}
		}
	}
}

func (p *parser) tags() bool {
	p.i++ // [
	p.space()
	found := false
	if p.b[p.i] == ']' {
		p.i++
		return false
	}
	for {
		p.space()
		if p.str() == "test" {
			found = true
		}
		p.space()
		if p.b[p.i] == ']' {
			p.i++
			return found
		}
		p.i++ // comma
	}
}

func (p *parser) meta() string {
	p.i++ // {
	p.space()
	var channel string
	if p.b[p.i] == '}' {
		p.i++
		return channel
	}
	for {
		p.space()
		key := p.str()
		p.space()
		p.i++ // colon
		p.space()
		if key == "channel" {
			channel = p.str()
		} else {
			p.skip()
		}
		p.space()
		if p.b[p.i] == '}' {
			p.i++
			return channel
		}
		p.i++ // comma
	}
}

func hundredths(s string) int64 {
	var n int64
	i := 0
	for i < len(s) && s[i] != '.' {
		n = n*10 + int64(s[i]-'0')
		i++
	}
	if i == len(s) {
		return n * 100
	}
	i++
	n = n*10 + int64(s[i]-'0')
	i++
	if i < len(s) {
		n = n*10 + int64(s[i]-'0')
	} else {
		n *= 10
	}
	return n
}

type transaction struct {
	account  string
	channel  string
	currency string
	typ      string
	amount   int64
	test     bool
}

func parseTransaction(b []byte) transaction {
	p := parser{b: b}
	var t transaction

	p.space()
	p.i++ // {
	p.space()
	if p.b[p.i] == '}' {
		return t
	}
	for {
		p.space()
		key := p.str()
		p.space()
		p.i++ // colon
		p.space()

		switch key {
		case "account":
			t.account = p.str()
		case "type":
			t.typ = p.str()
		case "amount":
			t.amount = hundredths(p.str())
		case "currency":
			t.currency = p.str()
		case "tags":
			t.test = p.tags()
		case "meta":
			t.channel = p.meta()
		default:
			p.skip()
		}

		p.space()
		if p.b[p.i] == '}' {
			return t
		}
		p.i++ // comma
	}
}

type channelTotal struct {
	count int64
	net   int64
}

type accountTotal struct {
	name string
	net  int64
}

func readLine(r *bufio.Reader) ([]byte, error) {
	line, err := r.ReadSlice('\n')
	if err != bufio.ErrBufferFull {
		return line, err
	}

	long := append([]byte(nil), line...)
	for {
		part, e := r.ReadSlice('\n')
		long = append(long, part...)
		if e != bufio.ErrBufferFull {
			return long, e
		}
	}
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		return
	}
	defer f.Close()

	reader := bufio.NewReaderSize(f, 1<<20)
	first, err := readLine(reader)
	if err != nil && err != io.EOF {
		return
	}
	var header struct {
		Rates map[string]int64 `json:"rates"`
	}
	if json.Unmarshal(first, &header) != nil {
		return
	}

	accounts := make(map[string]int64)
	channels := make(map[string]channelTotal)
	var count, net int64

	for {
		line, readErr := readLine(reader)
		if len(line) != 0 {
			t := parseTransaction(line)
			if t.typ != "void" && !t.test {
				product := t.amount * header.Rates[t.currency]
				value := product / 1000000
				if product < 0 && product%1000000 != 0 {
					value--
				}
				if t.typ == "debit" {
					value = -value
				}

				count++
				net += value

				if old, ok := accounts[t.account]; ok {
					accounts[t.account] = old + value
				} else {
					accounts[strings.Clone(t.account)] = value
				}

				if total, ok := channels[t.channel]; ok {
					total.count++
					total.net += value
					channels[t.channel] = total
				} else {
					channels[strings.Clone(t.channel)] = channelTotal{count: 1, net: value}
				}
			}
		}
		if readErr != nil {
			break
		}
	}

	names := make([]string, 0, len(channels))
	for name := range channels {
		names = append(names, name)
	}
	sort.Strings(names)

	top := make([]accountTotal, 0, 10)
	for name, total := range accounts {
		pos := 0
		for pos < len(top) && (top[pos].net > total ||
			(top[pos].net == total && top[pos].name < name)) {
			pos++
		}
		if pos >= 10 {
			continue
		}
		if len(top) < 10 {
			top = append(top, accountTotal{})
		}
		copy(top[pos+1:], top[pos:len(top)-1])
		top[pos] = accountTotal{name: name, net: total}
	}

	out := bufio.NewWriterSize(os.Stdout, 64<<10)
	fmt.Fprintf(out, "counted %d\nnet %d\n", count, net)
	for _, name := range names {
		total := channels[name]
		fmt.Fprintf(out, "channel %s %d %d\n", name, total.count, total.net)
	}
	for _, account := range top {
		fmt.Fprintf(out, "account %s %d\n", account.name, account.net)
	}
	out.Flush()
}
