package main

import (
	"bufio"
	"os"
	"sort"
	"strconv"
	"unicode/utf8"
)

const (
	kindNone  = 0
	kindPlus  = 1
	kindMinus = 2
	kindVoid  = 3
)

type txn struct {
	kind    uint8
	test    bool
	hund    int64
	rate    int64
	account []byte
	channel []byte
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

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<20), 1<<27)

	var rates map[string]int64
	haveRates := false
	var counted, net int64
	chIndex := make(map[string]int)
	var chNames []string
	var chCount, chNet []int64
	accIndex := make(map[string]int)
	var accNames []string
	var accNet []int64
	var t txn

	for sc.Scan() {
		line := sc.Bytes()
		if len(line) == 0 {
			continue
		}
		if !haveRates {
			rates = parseRates(line)
			haveRates = true
			continue
		}
		parseTxn(line, rates, &t)
		if t.kind == kindNone || t.kind == kindVoid || t.test {
			continue
		}
		usd := t.hund * t.rate / 1000000
		if t.kind == kindMinus {
			usd = -usd
		}
		counted++
		net += usd

		ci, ok := chIndex[string(t.channel)]
		if !ok {
			name := string(t.channel)
			ci = len(chNames)
			chIndex[name] = ci
			chNames = append(chNames, name)
			chCount = append(chCount, 0)
			chNet = append(chNet, 0)
		}
		chCount[ci]++
		chNet[ci] += usd

		ai, ok := accIndex[string(t.account)]
		if !ok {
			name := string(t.account)
			ai = len(accNames)
			accIndex[name] = ai
			accNames = append(accNames, name)
			accNet = append(accNet, 0)
		}
		accNet[ai] += usd
	}

	order := make([]int, len(chNames))
	for i := range order {
		order[i] = i
	}
	sort.Slice(order, func(a, b int) bool {
		return chNames[order[a]] < chNames[order[b]]
	})

	better := func(a, b int) bool {
		if accNet[a] != accNet[b] {
			return accNet[a] > accNet[b]
		}
		return accNames[a] < accNames[b]
	}
	top := make([]int, 0, 10)
	for j := range accNet {
		if len(top) == 10 && !better(j, top[9]) {
			continue
		}
		if len(top) < 10 {
			top = append(top, j)
		} else {
			top[9] = j
		}
		for k := len(top) - 1; k > 0 && better(top[k], top[k-1]); k-- {
			top[k], top[k-1] = top[k-1], top[k]
		}
	}

	out := make([]byte, 0, 1<<12)
	out = append(out, "counted "...)
	out = strconv.AppendInt(out, counted, 10)
	out = append(out, '\n')
	out = append(out, "net "...)
	out = strconv.AppendInt(out, net, 10)
	out = append(out, '\n')
	for _, ci := range order {
		out = append(out, "channel "...)
		out = append(out, chNames[ci]...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, chCount[ci], 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, chNet[ci], 10)
		out = append(out, '\n')
	}
	for _, ai := range top {
		out = append(out, "account "...)
		out = append(out, accNames[ai]...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, accNet[ai], 10)
		out = append(out, '\n')
	}
	os.Stdout.Write(out)
}

func skipWS(b []byte, i int) int {
	for i < len(b) {
		switch b[i] {
		case ' ', '\t', '\r', '\n':
			i++
		default:
			return i
		}
	}
	return i
}

// skipString expects b[i] == '"' and returns the index just past the closing quote.
func skipString(b []byte, i int) int {
	i++
	for i < len(b) {
		c := b[i]
		if c == '"' {
			return i + 1
		}
		if c == '\\' {
			i += 2
			continue
		}
		i++
	}
	return len(b)
}

// skipValue skips one JSON value starting at b[i] and returns the index after it.
func skipValue(b []byte, i int) int {
	depth := 0
	for i < len(b) {
		switch b[i] {
		case '"':
			i = skipString(b, i)
			if depth == 0 {
				return i
			}
			continue
		case '{', '[':
			depth++
		case '}', ']':
			if depth == 0 {
				return i
			}
			depth--
			if depth == 0 {
				return i + 1
			}
		case ',', ' ', '\t', '\r', '\n':
			if depth == 0 {
				return i
			}
		}
		i++
	}
	return i
}

func skipAny(b []byte, i int) int {
	ni := skipValue(b, i)
	if ni <= i {
		ni = i + 1
	}
	return ni
}

func hex4(b []byte, i int) int {
	if i+4 > len(b) {
		return 0
	}
	v := 0
	for k := 0; k < 4; k++ {
		c := b[i+k]
		var d int
		switch {
		case c >= '0' && c <= '9':
			d = int(c - '0')
		case c >= 'a' && c <= 'f':
			d = int(c-'a') + 10
		case c >= 'A' && c <= 'F':
			d = int(c-'A') + 10
		}
		v = v<<4 | d
	}
	return v
}

// parseString expects b[i] == '"'. It returns the decoded contents and the index
// after the closing quote. Escape-free strings alias b; decoded strings are fresh.
func parseString(b []byte, i int) ([]byte, int) {
	i++
	start := i
	for i < len(b) {
		c := b[i]
		if c == '"' {
			return b[start:i], i + 1
		}
		if c == '\\' {
			break
		}
		i++
	}
	if i >= len(b) {
		return b[start:], len(b)
	}
	out := make([]byte, 0, i-start+16)
	out = append(out, b[start:i]...)
	for i < len(b) {
		c := b[i]
		if c == '"' {
			return out, i + 1
		}
		if c != '\\' || i+1 >= len(b) {
			out = append(out, c)
			i++
			continue
		}
		i++
		e := b[i]
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
			r := hex4(b, i+1)
			i += 4
			if r >= 0xD800 && r < 0xDC00 && i+6 < len(b) && b[i+1] == '\\' && b[i+2] == 'u' {
				r2 := hex4(b, i+3)
				if r2 >= 0xDC00 && r2 < 0xE000 {
					r = 0x10000 + (r-0xD800)<<10 + (r2 - 0xDC00)
					i += 6
				}
			}
			out = utf8.AppendRune(out, rune(r))
		default:
			out = append(out, e)
		}
		i++
	}
	return out, i
}

func parseHundredths(s []byte) int64 {
	var v int64
	i := 0
	for i < len(s) && s[i] >= '0' && s[i] <= '9' {
		v = v*10 + int64(s[i]-'0')
		i++
	}
	v *= 100
	if i < len(s) && s[i] == '.' {
		i++
		if i < len(s) && s[i] >= '0' && s[i] <= '9' {
			v += int64(s[i]-'0') * 10
			i++
			if i < len(s) && s[i] >= '0' && s[i] <= '9' {
				v += int64(s[i] - '0')
			}
		}
	}
	return v
}

func parseRates(b []byte) map[string]int64 {
	rates := make(map[string]int64)
	i := skipWS(b, 0)
	if i >= len(b) || b[i] != '{' {
		return rates
	}
	i++
	for {
		i = skipWS(b, i)
		if i >= len(b) || b[i] == '}' {
			break
		}
		if b[i] == ',' {
			i++
			continue
		}
		if b[i] != '"' {
			break
		}
		var key []byte
		key, i = parseString(b, i)
		i = skipWS(b, i)
		if i < len(b) && b[i] == ':' {
			i++
		}
		i = skipWS(b, i)
		if i >= len(b) {
			break
		}
		if string(key) != "rates" || b[i] != '{' {
			i = skipAny(b, i)
			continue
		}
		i++
		for {
			i = skipWS(b, i)
			if i >= len(b) || b[i] == '}' {
				break
			}
			if b[i] == ',' {
				i++
				continue
			}
			if b[i] != '"' {
				break
			}
			var cur []byte
			cur, i = parseString(b, i)
			i = skipWS(b, i)
			if i < len(b) && b[i] == ':' {
				i++
			}
			i = skipWS(b, i)
			if i >= len(b) {
				break
			}
			if b[i] >= '0' && b[i] <= '9' {
				var v int64
				for i < len(b) && b[i] >= '0' && b[i] <= '9' {
					v = v*10 + int64(b[i]-'0')
					i++
				}
				rates[string(cur)] = v
			} else {
				i = skipAny(b, i)
			}
		}
		i++
	}
	return rates
}

func parseTxn(b []byte, rates map[string]int64, t *txn) {
	*t = txn{}
	i := skipWS(b, 0)
	if i >= len(b) || b[i] != '{' {
		return
	}
	i++
	for {
		i = skipWS(b, i)
		if i >= len(b) || b[i] == '}' {
			break
		}
		if b[i] == ',' {
			i++
			continue
		}
		if b[i] != '"' {
			break
		}
		var key []byte
		key, i = parseString(b, i)
		i = skipWS(b, i)
		if i < len(b) && b[i] == ':' {
			i++
		}
		i = skipWS(b, i)
		if i >= len(b) {
			break
		}
		switch string(key) {
		case "type":
			if b[i] == '"' {
				var s []byte
				s, i = parseString(b, i)
				switch string(s) {
				case "credit", "refund":
					t.kind = kindPlus
				case "debit":
					t.kind = kindMinus
				case "void":
					t.kind = kindVoid
				}
			} else {
				i = skipAny(b, i)
			}
		case "account":
			if b[i] == '"' {
				t.account, i = parseString(b, i)
			} else {
				i = skipAny(b, i)
			}
		case "amount":
			if b[i] == '"' {
				var s []byte
				s, i = parseString(b, i)
				t.hund = parseHundredths(s)
			} else {
				end := skipAny(b, i)
				t.hund = parseHundredths(b[i:end])
				i = end
			}
		case "currency":
			if b[i] == '"' {
				var s []byte
				s, i = parseString(b, i)
				t.rate = rates[string(s)]
			} else {
				i = skipAny(b, i)
			}
		case "tags":
			if b[i] != '[' {
				i = skipAny(b, i)
				break
			}
			i++
			for {
				i = skipWS(b, i)
				if i >= len(b) {
					break
				}
				c := b[i]
				if c == ']' {
					i++
					break
				}
				if c == ',' {
					i++
					continue
				}
				if c == '"' {
					var s []byte
					s, i = parseString(b, i)
					if string(s) == "test" {
						t.test = true
					}
				} else {
					i = skipAny(b, i)
				}
			}
		case "meta":
			if b[i] != '{' {
				i = skipAny(b, i)
				break
			}
			i++
			for {
				i = skipWS(b, i)
				if i >= len(b) || b[i] == '}' {
					break
				}
				if b[i] == ',' {
					i++
					continue
				}
				if b[i] != '"' {
					break
				}
				var mk []byte
				mk, i = parseString(b, i)
				i = skipWS(b, i)
				if i < len(b) && b[i] == ':' {
					i++
				}
				i = skipWS(b, i)
				if i >= len(b) {
					break
				}
				if b[i] == '"' && string(mk) == "channel" {
					t.channel, i = parseString(b, i)
				} else {
					i = skipAny(b, i)
				}
			}
			i++
		default:
			i = skipAny(b, i)
		}
	}
}
