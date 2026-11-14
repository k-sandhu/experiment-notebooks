// Ledger: streaming JSON Lines scanner with exact integer currency conversion.
package main

import (
	"bufio"
	"bytes"
	"io"
	"os"
	"slices"
	"strconv"
)

var isWs = [256]bool{' ': true, '\t': true, '\n': true, '\r': true}

// structural marks bytes that matter while skipping a nested container.
var structural = [256]bool{'"': true, '{': true, '}': true, '[': true, ']': true}

func skipWs(b []byte, i int) int {
	for isWs[b[i]] {
		i++
	}
	return i
}

func hexVal(c byte) rune {
	switch {
	case c >= '0' && c <= '9':
		return rune(c - '0')
	case c >= 'a' && c <= 'f':
		return rune(c - 'a' + 10)
	}
	return rune(c - 'A' + 10)
}

func hex4(b []byte) rune {
	return hexVal(b[0])<<12 | hexVal(b[1])<<8 | hexVal(b[2])<<4 | hexVal(b[3])
}

// decodeStr decodes a string with escapes; start is the content start, i the first backslash.
func decodeStr(b []byte, start, i int, scratch *[]byte) ([]byte, int) {
	out := append((*scratch)[:0], b[start:i]...)
	for {
		c := b[i]
		if c == '"' {
			break
		}
		if c != '\\' {
			out = append(out, c)
			i++
			continue
		}
		e := b[i+1]
		i += 2
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
			cp := hex4(b[i:])
			i += 4
			if cp >= 0xD800 && cp < 0xDC00 && b[i] == '\\' && b[i+1] == 'u' {
				lo := hex4(b[i+2:])
				if lo >= 0xDC00 && lo < 0xE000 {
					cp = 0x10000 + (cp-0xD800)<<10 + (lo - 0xDC00)
					i += 6
				}
			}
			out = appendUTF8(out, cp)
		default:
			out = append(out, e)
		}
	}
	*scratch = out
	return out, i + 1
}

// appendUTF8 encodes cp as UTF-8, including lone surrogates (WTF-8), so equal escapes stay equal.
func appendUTF8(out []byte, cp rune) []byte {
	switch {
	case cp < 0x80:
		return append(out, byte(cp))
	case cp < 0x800:
		return append(out, byte(0xC0|cp>>6), byte(0x80|cp&0x3F))
	case cp < 0x10000:
		return append(out, byte(0xE0|cp>>12), byte(0x80|(cp>>6)&0x3F), byte(0x80|cp&0x3F))
	}
	return append(out, byte(0xF0|cp>>18), byte(0x80|(cp>>12)&0x3F), byte(0x80|(cp>>6)&0x3F), byte(0x80|cp&0x3F))
}

// parseStr reads the string whose opening quote is at i. The result aliases b unless it had escapes.
func parseStr(b []byte, i int, scratch *[]byte) ([]byte, int) {
	i++
	start := i
	for {
		c := b[i]
		if c == '"' {
			return b[start:i], i + 1
		}
		if c == '\\' {
			return decodeStr(b, start, i, scratch)
		}
		i++
	}
}

// skipStrBody skips from just past an opening quote to just past the closing quote.
func skipStrBody(b []byte, i int) int {
	for {
		k := bytes.IndexByte(b[i:], '"')
		i += k
		// The quote is escaped only if preceded by an odd number of backslashes.
		n := 0
		for b[i-1-n] == '\\' {
			n++
		}
		i++
		if n&1 == 0 {
			return i
		}
	}
}

func skipContainer(b []byte, i int) int {
	depth := 1
	i++
	for {
		for !structural[b[i]] {
			i++
		}
		c := b[i]
		i++
		switch c {
		case '"':
			i = skipStrBody(b, i)
		case '{', '[':
			depth++
		default:
			depth--
			if depth == 0 {
				return i
			}
		}
	}
}

func skipVal(b []byte, i int) int {
	switch b[i] {
	case '"':
		return skipStrBody(b, i+1)
	case '{', '[':
		return skipContainer(b, i)
	}
	for {
		c := b[i]
		if c == ',' || c == '}' || c == ']' || isWs[c] {
			return i
		}
		i++
	}
}

type channelStat struct {
	count, sum int64
}

type ledger struct {
	rates    map[string]int64
	channels map[string]*channelStat
	accounts map[string]*int64
	counted  int64
	net      int64

	sKey, sAcc, sChan, sType, sAmt, sCur, sTag []byte
}

func (l *ledger) parseRates(b []byte, i int) int {
	i = skipWs(b, i+1)
	if b[i] == '}' {
		return i + 1
	}
	for {
		var key []byte
		key, i = parseStr(b, i, &l.sKey)
		i = skipWs(b, skipWs(b, i)+1)
		if string(key) == "rates" && b[i] == '{' {
			i = skipWs(b, i+1)
			if b[i] != '}' {
				for {
					var cur []byte
					cur, i = parseStr(b, i, &l.sCur)
					i = skipWs(b, skipWs(b, i)+1)
					neg := false
					if b[i] == '-' {
						neg = true
						i++
					}
					var v int64
					for b[i] >= '0' && b[i] <= '9' {
						v = v*10 + int64(b[i]-'0')
						i++
					}
					i = skipVal(b, i)
					if neg {
						v = -v
					}
					l.rates[string(cur)] = v
					i = skipWs(b, i)
					if b[i] == ',' {
						i = skipWs(b, i+1)
						continue
					}
					break
				}
			}
			i++
		} else {
			i = skipVal(b, i)
		}
		i = skipWs(b, i)
		if b[i] == ',' {
			i = skipWs(b, i+1)
			continue
		}
		return i + 1
	}
}

func (l *ledger) parseTx(b []byte, i int) int {
	var acc, chn, cur, amt []byte
	sign := int64(0)
	test := false

	i = skipWs(b, i+1)
	if b[i] == '}' {
		return i + 1
	}
	for {
		var key []byte
		key, i = parseStr(b, i, &l.sKey)
		i = skipWs(b, skipWs(b, i)+1)
		switch string(key) {
		case "type":
			var t []byte
			t, i = parseStr(b, i, &l.sType)
			switch string(t) {
			case "credit", "refund":
				sign = 1
			case "debit":
				sign = -1
			default:
				sign = 0
			}
		case "tags":
			i = skipWs(b, i+1)
			if b[i] != ']' {
				for {
					if b[i] == '"' {
						var tag []byte
						tag, i = parseStr(b, i, &l.sTag)
						if string(tag) == "test" {
							test = true
						}
					} else {
						i = skipVal(b, i)
					}
					i = skipWs(b, i)
					if b[i] == ',' {
						i = skipWs(b, i+1)
						continue
					}
					break
				}
			}
			i++
		case "meta":
			i = skipWs(b, i+1)
			if b[i] != '}' {
				for {
					var mk []byte
					mk, i = parseStr(b, i, &l.sKey)
					i = skipWs(b, skipWs(b, i)+1)
					if string(mk) == "channel" && b[i] == '"' {
						chn, i = parseStr(b, i, &l.sChan)
					} else {
						i = skipVal(b, i)
					}
					i = skipWs(b, i)
					if b[i] == ',' {
						i = skipWs(b, i+1)
						continue
					}
					break
				}
			}
			i++
		case "amount":
			amt, i = parseStr(b, i, &l.sAmt)
		case "account":
			acc, i = parseStr(b, i, &l.sAcc)
		case "currency":
			cur, i = parseStr(b, i, &l.sCur)
		default:
			i = skipVal(b, i)
		}
		i = skipWs(b, i)
		if b[i] == ',' {
			i = skipWs(b, i+1)
			continue
		}
		i++
		break
	}

	if sign == 0 || test {
		return i
	}

	var hund int64
	k := 0
	for k < len(amt) && amt[k] != '.' {
		hund = hund*10 + int64(amt[k]-'0')
		k++
	}
	hund *= 100
	if k < len(amt) {
		k++
		if k < len(amt) {
			hund += int64(amt[k]-'0') * 10
		}
		if k+1 < len(amt) {
			hund += int64(amt[k+1] - '0')
		}
	}
	v := hund * l.rates[string(cur)] / 1000000 * sign

	l.counted++
	l.net += v
	cs := l.channels[string(chn)]
	if cs == nil {
		cs = &channelStat{}
		l.channels[string(chn)] = cs
	}
	cs.count++
	cs.sum += v
	as := l.accounts[string(acc)]
	if as == nil {
		as = new(int64)
		l.accounts[string(acc)] = as
	}
	*as += v
	return i
}

func main() {
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	defer f.Close()

	l := &ledger{
		rates:    make(map[string]int64),
		channels: make(map[string]*channelStat),
		accounts: make(map[string]*int64, 1<<14),
	}

	const slack = 64
	buf := make([]byte, 8<<20+slack)
	capacity := len(buf) - slack
	n := 0
	first := true
	for {
		if n == capacity {
			nb := make([]byte, 2*capacity+slack)
			copy(nb, buf[:n])
			buf = nb
			capacity *= 2
		}
		got, rerr := f.Read(buf[n:capacity])
		n += got
		eof := rerr == io.EOF || (rerr == nil && got == 0)
		if rerr != nil && rerr != io.EOF {
			os.Exit(1)
		}
		var lim int
		if eof {
			if n == 0 {
				break
			}
			if buf[n-1] != '\n' {
				buf[n] = '\n'
				n++
			}
			lim = n
		} else {
			lim = bytes.LastIndexByte(buf[:n], '\n') + 1
			if lim == 0 {
				continue
			}
		}
		saved := buf[lim]
		buf[lim] = 0 // sentinel stops whitespace skipping
		i := 0
		for {
			i = skipWs(buf, i)
			if i >= lim {
				break
			}
			if first {
				i = l.parseRates(buf, i)
				first = false
			} else {
				i = l.parseTx(buf, i)
			}
		}
		buf[lim] = saved
		n = copy(buf, buf[lim:n])
		if eof {
			break
		}
	}

	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	var line []byte
	line = append(line, "counted "...)
	line = strconv.AppendInt(line, l.counted, 10)
	line = append(line, "\nnet "...)
	line = strconv.AppendInt(line, l.net, 10)
	line = append(line, '\n')

	names := make([]string, 0, len(l.channels))
	for k := range l.channels {
		names = append(names, k)
	}
	slices.Sort(names)
	for _, k := range names {
		cs := l.channels[k]
		line = append(line, "channel "...)
		line = append(line, k...)
		line = append(line, ' ')
		line = strconv.AppendInt(line, cs.count, 10)
		line = append(line, ' ')
		line = strconv.AppendInt(line, cs.sum, 10)
		line = append(line, '\n')
	}

	type accTotal struct {
		id  string
		sum int64
	}
	accs := make([]accTotal, 0, len(l.accounts))
	for k, v := range l.accounts {
		accs = append(accs, accTotal{k, *v})
	}
	slices.SortFunc(accs, func(a, b accTotal) int {
		if a.sum != b.sum {
			if a.sum > b.sum {
				return -1
			}
			return 1
		}
		if a.id < b.id {
			return -1
		}
		if a.id > b.id {
			return 1
		}
		return 0
	})
	for _, a := range accs[:min(10, len(accs))] {
		line = append(line, "account "...)
		line = append(line, a.id...)
		line = append(line, ' ')
		line = strconv.AppendInt(line, a.sum, 10)
		line = append(line, '\n')
	}
	w.Write(line)
}
