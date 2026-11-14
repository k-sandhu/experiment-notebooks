package main

import (
	"bufio"
	"bytes"
	"io"
	"os"
	"sort"
	"strconv"
	"unicode/utf8"
)

var rates = map[string]int64{}

var accMap = map[string]int{}
var accNames []string
var accSums []int64

var chMap = map[string]int{}
var chNames []string
var chCounts []int64
var chSums []int64

var totalCount int64
var totalNet int64

func skipWS(b []byte, i int) int {
	for i < len(b) {
		c := b[i]
		if c == ' ' || c == '\t' || c == '\n' || c == '\r' {
			i++
		} else {
			break
		}
	}
	return i
}

func hex4(b []byte) rune {
	var r rune
	for k := 0; k < 4; k++ {
		var c byte
		if k < len(b) {
			c = b[k]
		}
		var d rune
		switch {
		case c >= '0' && c <= '9':
			d = rune(c - '0')
		case c >= 'a' && c <= 'f':
			d = rune(c-'a') + 10
		case c >= 'A' && c <= 'F':
			d = rune(c-'A') + 10
		}
		r = r<<4 | d
	}
	return r
}

func unescape(raw []byte) []byte {
	out := make([]byte, 0, len(raw))
	n := len(raw)
	for i := 0; i < n; i++ {
		c := raw[i]
		if c != '\\' {
			out = append(out, c)
			continue
		}
		i++
		if i >= n {
			break
		}
		switch raw[i] {
		case 'b':
			out = append(out, 8)
		case 'f':
			out = append(out, 12)
		case 'n':
			out = append(out, '\n')
		case 'r':
			out = append(out, '\r')
		case 't':
			out = append(out, '\t')
		case 'u':
			r := hex4(raw[i+1:])
			i += 4
			if r >= 0xD800 && r < 0xDC00 && i+6 < n+0 && raw[i+1] == '\\' && raw[i+2] == 'u' {
				lo := hex4(raw[i+3:])
				if lo >= 0xDC00 && lo < 0xE000 {
					r = 0x10000 + (r-0xD800)<<10 + (lo - 0xDC00)
					i += 6
				}
			}
			out = utf8.AppendRune(out, r)
		default:
			out = append(out, raw[i])
		}
	}
	return out
}

// parseStr: b[i] must be '"'. Returns the decoded content and index after closing quote.
func parseStr(b []byte, i int) ([]byte, int) {
	s := i + 1
	if s > len(b) {
		return nil, len(b)
	}
	q := bytes.IndexByte(b[s:], '"')
	if q >= 0 && bytes.IndexByte(b[s:s+q], '\\') < 0 {
		return b[s : s+q], s + q + 1
	}
	j := s
	for j < len(b) {
		c := b[j]
		if c == '"' {
			return unescape(b[s:j]), j + 1
		}
		if c == '\\' {
			j += 2
			continue
		}
		j++
	}
	return nil, len(b)
}

func skipString(b []byte, i int) int {
	s := i + 1
	if s > len(b) {
		return len(b)
	}
	q := bytes.IndexByte(b[s:], '"')
	if q >= 0 && bytes.IndexByte(b[s:s+q], '\\') < 0 {
		return s + q + 1
	}
	j := s
	for j < len(b) {
		c := b[j]
		if c == '"' {
			return j + 1
		}
		if c == '\\' {
			j += 2
			continue
		}
		j++
	}
	return len(b)
}

func skipValue(b []byte, i int) int {
	if i >= len(b) {
		return i
	}
	switch b[i] {
	case '"':
		return skipString(b, i)
	case '{', '[':
		depth := 0
		j := i
		for j < len(b) {
			switch b[j] {
			case '"':
				j = skipString(b, j)
				continue
			case '{', '[':
				depth++
			case '}', ']':
				depth--
				if depth == 0 {
					return j + 1
				}
			}
			j++
		}
		return j
	default:
		for i < len(b) {
			c := b[i]
			if c == ',' || c == '}' || c == ']' || c == ' ' || c == '\t' || c == '\r' || c == '\n' {
				break
			}
			i++
		}
		return i
	}
}

func parseTags(b []byte, i int, test *bool) int {
	if i >= len(b) || b[i] != '[' {
		return skipValue(b, i)
	}
	i++
	for {
		i = skipWS(b, i)
		if i >= len(b) {
			return i
		}
		c := b[i]
		if c == ']' {
			return i + 1
		}
		if c == ',' {
			i++
			continue
		}
		if c == '"' {
			var s []byte
			s, i = parseStr(b, i)
			if string(s) == "test" {
				*test = true
			}
		} else {
			i = skipValue(b, i)
		}
	}
}

func parseMeta(b []byte, i int, channel *[]byte) int {
	if i >= len(b) || b[i] != '{' {
		return skipValue(b, i)
	}
	i++
	for {
		i = skipWS(b, i)
		if i >= len(b) {
			return i
		}
		c := b[i]
		if c == '}' {
			return i + 1
		}
		if c == ',' {
			i++
			continue
		}
		if c != '"' {
			return skipValue(b, i)
		}
		var key []byte
		key, i = parseStr(b, i)
		i = skipWS(b, i)
		if i < len(b) && b[i] == ':' {
			i++
		}
		i = skipWS(b, i)
		if string(key) == "channel" && i < len(b) && b[i] == '"' {
			*channel, i = parseStr(b, i)
		} else {
			i = skipValue(b, i)
		}
	}
}

func parseRates(b []byte) {
	i := skipWS(b, 0)
	if i >= len(b) || b[i] != '{' {
		return
	}
	i++
	for {
		i = skipWS(b, i)
		if i >= len(b) {
			return
		}
		c := b[i]
		if c == '}' {
			return
		}
		if c == ',' {
			i++
			continue
		}
		if c != '"' {
			return
		}
		var key []byte
		key, i = parseStr(b, i)
		i = skipWS(b, i)
		if i < len(b) && b[i] == ':' {
			i++
		}
		i = skipWS(b, i)
		if string(key) == "rates" && i < len(b) && b[i] == '{' {
			i++
			for {
				i = skipWS(b, i)
				if i >= len(b) {
					return
				}
				c := b[i]
				if c == '}' {
					i++
					break
				}
				if c == ',' {
					i++
					continue
				}
				if c != '"' {
					return
				}
				var cur []byte
				cur, i = parseStr(b, i)
				i = skipWS(b, i)
				if i < len(b) && b[i] == ':' {
					i++
				}
				i = skipWS(b, i)
				var v int64
				for i < len(b) && b[i] >= '0' && b[i] <= '9' {
					v = v*10 + int64(b[i]-'0')
					i++
				}
				rates[string(cur)] = v
			}
		} else {
			i = skipValue(b, i)
		}
	}
}

func parseLine(b []byte) {
	n := len(b)
	i := skipWS(b, 0)
	if i >= n || b[i] != '{' {
		return
	}
	i++
	var account, channel, typ, cur, amt []byte
	test := false
	for {
		i = skipWS(b, i)
		if i >= n {
			break
		}
		c := b[i]
		if c == '}' {
			break
		}
		if c == ',' {
			i++
			continue
		}
		if c != '"' {
			break
		}
		var key []byte
		key, i = parseStr(b, i)
		i = skipWS(b, i)
		if i < n && b[i] == ':' {
			i++
		}
		i = skipWS(b, i)
		if i >= n {
			break
		}
		switch string(key) {
		case "account":
			if b[i] == '"' {
				account, i = parseStr(b, i)
			} else {
				i = skipValue(b, i)
			}
		case "type":
			if b[i] == '"' {
				typ, i = parseStr(b, i)
			} else {
				i = skipValue(b, i)
			}
		case "amount":
			if b[i] == '"' {
				amt, i = parseStr(b, i)
			} else {
				i = skipValue(b, i)
			}
		case "currency":
			if b[i] == '"' {
				cur, i = parseStr(b, i)
			} else {
				i = skipValue(b, i)
			}
		case "tags":
			i = parseTags(b, i, &test)
		case "meta":
			i = parseMeta(b, i, &channel)
		default:
			i = skipValue(b, i)
		}
	}
	if test {
		return
	}
	ts := string(typ)
	if ts == "void" {
		return
	}
	// amount to hundredths
	var h int64
	k := 0
	for k < len(amt) && amt[k] >= '0' && amt[k] <= '9' {
		h = h*10 + int64(amt[k]-'0')
		k++
	}
	h *= 100
	if k < len(amt) && amt[k] == '.' {
		k++
		if k < len(amt) && amt[k] >= '0' && amt[k] <= '9' {
			h += int64(amt[k]-'0') * 10
			k++
			if k < len(amt) && amt[k] >= '0' && amt[k] <= '9' {
				h += int64(amt[k] - '0')
			}
		}
	}
	usd := h * rates[string(cur)] / 1000000
	if ts == "debit" {
		usd = -usd
	}
	totalCount++
	totalNet += usd

	ai, ok := accMap[string(account)]
	if !ok {
		s := string(account)
		ai = len(accSums)
		accMap[s] = ai
		accNames = append(accNames, s)
		accSums = append(accSums, 0)
	}
	accSums[ai] += usd

	ci, ok := chMap[string(channel)]
	if !ok {
		s := string(channel)
		ci = len(chNames)
		chMap[s] = ci
		chNames = append(chNames, s)
		chCounts = append(chCounts, 0)
		chSums = append(chSums, 0)
	}
	chCounts[ci]++
	chSums[ci] += usd
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Stderr.WriteString(err.Error() + "\n")
		os.Exit(1)
	}
	defer f.Close()

	buf := make([]byte, 1<<22)
	n := 0
	first := true
	eof := false
	handle := func(line []byte) {
		if len(line) > 0 && line[len(line)-1] == '\r' {
			line = line[:len(line)-1]
		}
		if skipWS(line, 0) >= len(line) {
			return
		}
		if first {
			first = false
			parseRates(line)
			return
		}
		parseLine(line)
	}
	for !eof {
		if n == len(buf) {
			nb := make([]byte, len(buf)*2)
			copy(nb, buf[:n])
			buf = nb
		}
		m, err := f.Read(buf[n:])
		n += m
		if err != nil {
			if err == io.EOF {
				eof = true
			} else {
				eof = true
			}
		}
		pos := 0
		for pos < n {
			idx := bytes.IndexByte(buf[pos:n], '\n')
			if idx < 0 {
				break
			}
			handle(buf[pos : pos+idx])
			pos += idx + 1
		}
		if pos > 0 {
			copy(buf, buf[pos:n])
			n -= pos
		}
	}
	if n > 0 {
		handle(buf[:n])
	}

	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	w.WriteString("counted " + strconv.FormatInt(totalCount, 10) + "\n")
	w.WriteString("net " + strconv.FormatInt(totalNet, 10) + "\n")

	cidx := make([]int, len(chNames))
	for i := range cidx {
		cidx[i] = i
	}
	sort.Slice(cidx, func(a, b int) bool { return chNames[cidx[a]] < chNames[cidx[b]] })
	for _, i := range cidx {
		w.WriteString("channel " + chNames[i] + " " + strconv.FormatInt(chCounts[i], 10) + " " + strconv.FormatInt(chSums[i], 10) + "\n")
	}

	aidx := make([]int, len(accNames))
	for i := range aidx {
		aidx[i] = i
	}
	sort.Slice(aidx, func(a, b int) bool {
		x, y := aidx[a], aidx[b]
		if accSums[x] != accSums[y] {
			return accSums[x] > accSums[y]
		}
		return accNames[x] < accNames[y]
	})
	if len(aidx) > 10 {
		aidx = aidx[:10]
	}
	for _, i := range aidx {
		w.WriteString("account " + accNames[i] + " " + strconv.FormatInt(accSums[i], 10) + "\n")
	}
}
