// Ledger: streams a JSON Lines file, parses only the fields it needs straight from bytes,
// and sums converted amounts per channel and per account with exact integer arithmetic.
package main

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"sort"
	"strconv"
	"unicode/utf8"
)

const chunkSize = 1 << 22

type rate struct {
	name  string
	value int64
}

// index maps byte-string keys to dense slots, each holding a sum and a count.
type index struct {
	ids    map[string]int
	keys   []string
	sums   []int64
	counts []int64
}

func newIndex() index {
	return index{ids: make(map[string]int)}
}

func (x *index) find(k []byte) int {
	if i, ok := x.ids[string(k)]; ok { // lookup does not allocate
		return i
	}
	s := string(k)
	x.ids[s] = len(x.keys)
	x.keys = append(x.keys, s)
	x.sums = append(x.sums, 0)
	x.counts = append(x.counts, 0)
	return len(x.keys) - 1
}

type ledger struct {
	rates     []rate
	haveRates bool
	testFlag  bool
	counted   int64
	net       int64
	channels  index
	accounts  index

	// Scratch storage for strings that contain escapes, reused for every line.
	keyBuf, typeBuf, accBuf, curBuf, amtBuf, chanBuf, tagBuf []byte
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: solution INPUT_PATH")
		os.Exit(2)
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer f.Close()

	l := &ledger{channels: newIndex(), accounts: newIndex()}
	if err := l.run(f); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	l.print()
}

func (l *ledger) run(f io.Reader) error {
	buf := make([]byte, chunkSize)
	carry := 0
	for {
		if carry == len(buf) {
			buf = append(buf, make([]byte, len(buf))...)
		}
		n, err := f.Read(buf[carry:])
		end := carry + n
		eof := err == io.EOF
		if err != nil && !eof {
			return err
		}
		stop := end // at end of file the last line may lack a newline
		if !eof {
			stop = bytes.LastIndexByte(buf[:end], '\n') + 1
		}
		l.processLines(buf[:stop])
		carry = copy(buf, buf[stop:end])
		if eof {
			return nil
		}
	}
}

func (l *ledger) processLines(data []byte) {
	for len(data) > 0 {
		var line []byte
		if i := bytes.IndexByte(data, '\n'); i >= 0 {
			line, data = data[:i], data[i+1:]
		} else {
			line, data = data, nil
		}
		for len(line) > 0 && (line[0] == ' ' || line[0] == '\t' || line[0] == '\r') {
			line = line[1:]
		}
		if len(line) == 0 {
			continue
		}
		if l.haveRates {
			l.parseTxn(line)
		} else {
			l.parseRates(line)
			l.haveRates = true
		}
	}
}

// Skipping and reading helpers. Each returns the position after the item.

func skipWs(b []byte, p int) int {
	for b[p] == ' ' || b[p] == '\t' || b[p] == '\r' || b[p] == '\n' {
		p++
	}
	return p
}

// colon skips whitespace, the ':' after a key, and whitespace.
func colon(b []byte, p int) int {
	return skipWs(b, skipWs(b, p)+1)
}

func skipString(b []byte, p int) int {
	p++
	for b[p] != '"' {
		if b[p] == '\\' {
			p += 2
		} else {
			p++
		}
	}
	return p + 1
}

func skipValue(b []byte, p int) int {
	switch b[p] {
	case '"':
		return skipString(b, p)
	case '{', '[':
		depth := 0
		for {
			switch b[p] {
			case '"':
				p = skipString(b, p)
				continue
			case '{', '[':
				depth++
			case '}', ']':
				depth--
				if depth == 0 {
					return p + 1
				}
			}
			p++
		}
	}
	for {
		switch b[p] {
		case ',', '}', ']', ' ', '\t', '\r', '\n':
			return p
		}
		p++
	}
}

// readString decodes the string whose opening quote is b[p]. Plain strings alias b; strings
// with escapes are decoded into *scratch. It returns the value and the position after the closing quote.
func readString(b []byte, p int, scratch *[]byte) ([]byte, int) {
	start := p + 1
	q := start
	escaped := false
	for b[q] != '"' {
		if b[q] == '\\' {
			escaped = true
			q++
		}
		q++
	}
	if !escaped {
		return b[start:q], q + 1
	}
	*scratch = decode((*scratch)[:0], b[start:q])
	return *scratch, q + 1
}

func decode(dst, src []byte) []byte {
	for i := 0; i < len(src); {
		c := src[i]
		if c != '\\' {
			dst = append(dst, c)
			i++
			continue
		}
		e := src[i+1]
		i += 2
		switch e {
		case 'b':
			dst = append(dst, '\b')
		case 'f':
			dst = append(dst, '\f')
		case 'n':
			dst = append(dst, '\n')
		case 'r':
			dst = append(dst, '\r')
		case 't':
			dst = append(dst, '\t')
		case 'u':
			cp := hex4(src[i:])
			i += 4
			if cp >= 0xD800 && cp <= 0xDBFF && i+1 < len(src) && src[i] == '\\' && src[i+1] == 'u' {
				if lo := hex4(src[i+2:]); lo >= 0xDC00 && lo <= 0xDFFF {
					cp = 0x10000 + (cp-0xD800)<<10 + (lo - 0xDC00)
					i += 6
				}
			}
			dst = utf8.AppendRune(dst, rune(cp))
		default: // \" \\ \/
			dst = append(dst, e)
		}
	}
	return dst
}

func hex4(b []byte) uint32 {
	var v uint32
	for i := 0; i < 4; i++ {
		c := b[i]
		if c <= '9' {
			v = v*16 + uint32(c-'0')
		} else {
			v = v*16 + uint32((c|0x20)-'a'+10)
		}
	}
	return v
}

func (l *ledger) parseRates(b []byte) {
	p := skipWs(b, 1) // '{'
	if b[p] == '}' {
		return
	}
	for {
		var key []byte
		key, p = readString(b, skipWs(b, p), &l.keyBuf)
		p = colon(b, p)
		if string(key) == "rates" {
			p = l.parseRateObject(b, p)
		} else {
			p = skipValue(b, p)
		}
		p = skipWs(b, p)
		if b[p] == '}' {
			return
		}
		p++ // ','
	}
}

func (l *ledger) parseRateObject(b []byte, p int) int {
	p = skipWs(b, p+1) // '{'
	if b[p] == '}' {
		return p + 1
	}
	for {
		var key []byte
		key, p = readString(b, skipWs(b, p), &l.keyBuf)
		p = colon(b, p)
		neg := b[p] == '-'
		if neg {
			p++
		}
		var v int64
		for b[p] >= '0' && b[p] <= '9' {
			v = v*10 + int64(b[p]-'0')
			p++
		}
		if neg {
			v = -v
		}
		l.rates = append(l.rates, rate{name: string(key), value: v})
		p = skipWs(b, p)
		if b[p] == '}' {
			return p + 1
		}
		p++ // ','
	}
}

func (l *ledger) parseTxn(b []byte) {
	var typ, account, currency, amount, channel []byte
	l.testFlag = false
	p := skipWs(b, 1) // '{'
	if b[p] == '}' {
		return
	}
	for {
		var key []byte
		key, p = readString(b, skipWs(b, p), &l.keyBuf)
		p = colon(b, p)
		switch {
		case string(key) == "account":
			account, p = readString(b, p, &l.accBuf)
		case string(key) == "type":
			typ, p = readString(b, p, &l.typeBuf)
		case string(key) == "currency":
			currency, p = readString(b, p, &l.curBuf)
		case string(key) == "amount":
			if b[p] == '"' {
				amount, p = readString(b, p, &l.amtBuf)
			} else {
				e := skipValue(b, p)
				amount = b[p:e]
				p = e
			}
		case string(key) == "tags":
			p = l.parseTags(b, p)
		case string(key) == "meta":
			var ch []byte
			ch, p = l.parseMeta(b, p)
			if ch != nil {
				channel = ch
			}
		default:
			p = skipValue(b, p)
		}
		p = skipWs(b, p)
		if b[p] == '}' {
			break
		}
		p++ // ','
	}

	if string(typ) == "void" || l.testFlag {
		return
	}
	r := -1
	for i := range l.rates {
		if l.rates[i].name == string(currency) {
			r = i
			break
		}
	}
	if r < 0 {
		return
	}

	usd := hundredths(amount) * l.rates[r].value / 1000000
	value := usd
	if string(typ) == "debit" {
		value = -usd
	}

	l.counted++
	l.net += value
	c := l.channels.find(channel)
	l.channels.counts[c]++
	l.channels.sums[c] += value
	a := l.accounts.find(account)
	l.accounts.sums[a] += value
}

func (l *ledger) parseTags(b []byte, p int) int {
	p = skipWs(b, p+1) // '['
	if b[p] == ']' {
		return p + 1
	}
	for {
		p = skipWs(b, p)
		if b[p] == '"' {
			var t []byte
			t, p = readString(b, p, &l.tagBuf)
			if string(t) == "test" {
				l.testFlag = true
			}
		} else {
			p = skipValue(b, p)
		}
		p = skipWs(b, p)
		if b[p] == ']' {
			return p + 1
		}
		p++ // ','
	}
}

// parseMeta returns the channel value (nil if absent) and the position after the object.
func (l *ledger) parseMeta(b []byte, p int) ([]byte, int) {
	p = skipWs(b, p+1) // '{'
	if b[p] == '}' {
		return nil, p + 1
	}
	var channel []byte
	for {
		var key []byte
		key, p = readString(b, skipWs(b, p), &l.keyBuf)
		p = colon(b, p)
		if string(key) == "channel" && b[p] == '"' {
			channel, p = readString(b, p, &l.chanBuf)
		} else {
			p = skipValue(b, p)
		}
		p = skipWs(b, p)
		if b[p] == '}' {
			return channel, p + 1
		}
		p++ // ','
	}
}

// hundredths parses an amount such as "12", "12.5" or "12.05" into hundredths.
func hundredths(a []byte) int64 {
	var v int64
	i := 0
	for ; i < len(a) && a[i] != '.'; i++ {
		v = v*10 + int64(a[i]-'0')
	}
	v *= 100
	if i < len(a) {
		i++
		var frac int64
		digits := 0
		for ; digits < 2 && i < len(a); i, digits = i+1, digits+1 {
			frac = frac*10 + int64(a[i]-'0')
		}
		if digits == 1 {
			frac *= 10
		}
		v += frac
	}
	return v
}

func (l *ledger) print() {
	out := make([]byte, 0, 1<<12)
	out = append(out, "counted "...)
	out = strconv.AppendInt(out, l.counted, 10)
	out = append(out, "\nnet "...)
	out = strconv.AppendInt(out, l.net, 10)
	out = append(out, '\n')

	ch := &l.channels
	chanOrder := make([]int, len(ch.keys))
	for i := range chanOrder {
		chanOrder[i] = i
	}
	sort.Slice(chanOrder, func(i, j int) bool { return ch.keys[chanOrder[i]] < ch.keys[chanOrder[j]] })
	for _, i := range chanOrder {
		out = append(out, "channel "...)
		out = append(out, ch.keys[i]...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, ch.counts[i], 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, ch.sums[i], 10)
		out = append(out, '\n')
	}

	ac := &l.accounts
	accOrder := make([]int, len(ac.keys))
	for i := range accOrder {
		accOrder[i] = i
	}
	sort.Slice(accOrder, func(i, j int) bool {
		a, b := accOrder[i], accOrder[j]
		if ac.sums[a] != ac.sums[b] {
			return ac.sums[a] > ac.sums[b]
		}
		return ac.keys[a] < ac.keys[b]
	})
	for k := 0; k < len(accOrder) && k < 10; k++ {
		i := accOrder[k]
		out = append(out, "account "...)
		out = append(out, ac.keys[i]...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, ac.sums[i], 10)
		out = append(out, '\n')
	}

	os.Stdout.Write(out)
}
