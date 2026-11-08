package main

// Ledger: fast single-pass JSON Lines aggregator.
// Hand-rolled byte scanner over the whole input (no DOM), plain maps with
// string keys created only for the few fields we need.

import (
	"bufio"
	"os"
	"sort"
	"strconv"
)

var data []byte
var i, n int

var sStart, sEnd int
var sEsc bool

type chAgg struct {
	count, net int64
}

func main() {
	data, _ = os.ReadFile(os.Args[1])
	n = len(data)

	rates := make(map[string]int64)
	channels := make(map[string]*chAgg)
	accounts := make(map[string]int64)

	// ---- first line: rates ----
	skipWs()
	i++ // '{'
	for {
		skipWs()
		scanString()
		ks, ke, kesc := sStart, sEnd, sEsc
		skipWs()
		i++ // ':'
		skipWs()
		if !kesc && ke-ks == 5 && eqBytes(ks, ke, "rates") {
			i++ // '{'
			for {
				skipWs()
				if data[i] == '}' {
					i++
					break
				}
				scanString()
				cur := strValue()
				skipWs()
				i++ // ':'
				skipWs()
				var r int64
				for data[i] >= '0' && data[i] <= '9' {
					r = r*10 + int64(data[i]-'0')
					i++
				}
				rates[cur] = r
				skipWs()
				if data[i] == ',' {
					i++
				}
			}
		} else {
			skipValue()
		}
		skipWs()
		if data[i] == ',' {
			i++
			continue
		}
		i++
		break
	}

	// ---- transactions ----
	var totalCount, totalNet int64

	for {
		skipWs()
		if i >= n {
			break
		}
		i++ // '{'

		var typeCode int // 1 credit, 2 debit, 3 refund, 4 void
		testTag := false
		var hund int64
		var currency, account, channel string

	inner:
		for {
			skipWs()
			scanString()
			ks, ke, kesc := sStart, sEnd, sEsc
			klen := ke - ks
			skipWs()
			i++ // ':'
			skipWs()
			if !kesc {
				c0 := byte(0)
				if klen > 0 {
					c0 = data[ks]
				}
				switch {
				case klen == 4 && c0 == 't' && eqBytes(ks, ke, "type"):
					scanString()
					typeCode = typeCodeVal()
				case klen == 6 && eqBytes(ks, ke, "amount"):
					scanString()
					hund = parseAmount(sStart, sEnd, sEsc)
				case klen == 8 && eqBytes(ks, ke, "currency"):
					scanString()
					currency = strValue()
				case klen == 7 && eqBytes(ks, ke, "account"):
					scanString()
					account = strValue()
				case klen == 4 && c0 == 't' && eqBytes(ks, ke, "tags"):
					testTag = parseTags()
				case klen == 4 && c0 == 'm' && eqBytes(ks, ke, "meta"):
					channel = parseMeta()
				default:
					skipValue()
				}
			} else {
				// escaped key: decode and compare (rare)
				switch string(decodeInto(ks, ke)) {
				case "type":
					scanString()
					typeCode = typeCodeVal()
				case "amount":
					scanString()
					hund = parseAmount(sStart, sEnd, sEsc)
				case "currency":
					scanString()
					currency = strValue()
				case "account":
					scanString()
					account = strValue()
				case "tags":
					testTag = parseTags()
				case "meta":
					channel = parseMeta()
				default:
					skipValue()
				}
			}
			skipWs()
			if data[i] == ',' {
				i++
				continue inner
			}
			i++ // '}'
			break inner
		}

		if typeCode == 4 || testTag {
			continue
		}
		rate, ok := rates[currency]
		if !ok {
			continue
		}
		usd := (hund * rate) / 1000000
		v := usd
		if typeCode == 2 {
			v = -usd
		}

		totalCount++
		totalNet += v

		if c, ok := channels[channel]; ok {
			c.count++
			c.net += v
		} else {
			channels[channel] = &chAgg{count: 1, net: v}
		}
		accounts[account] += v
	}

	// ---- output ----
	w := bufio.NewWriterSize(os.Stdout, 1<<20)
	buf := make([]byte, 0, 256)

	buf = append(buf, "counted "...)
	buf = strconv.AppendInt(buf, totalCount, 10)
	buf = append(buf, '\n')
	buf = append(buf, "net "...)
	buf = strconv.AppendInt(buf, totalNet, 10)
	buf = append(buf, '\n')

	type chRow struct {
		name string
		a    *chAgg
	}
	chRows := make([]chRow, 0, len(channels))
	for k, v := range channels {
		chRows = append(chRows, chRow{k, v})
	}
	sort.Slice(chRows, func(a, b int) bool { return chRows[a].name < chRows[b].name })
	for _, r := range chRows {
		buf = append(buf, "channel "...)
		buf = append(buf, r.name...)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, r.a.count, 10)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, r.a.net, 10)
		buf = append(buf, '\n')
		w.Write(buf)
		buf = buf[:0]
	}

	type accRow struct {
		name string
		net  int64
	}
	accRows := make([]accRow, 0, len(accounts))
	for k, v := range accounts {
		accRows = append(accRows, accRow{k, v})
	}
	sort.Slice(accRows, func(a, b int) bool {
		if accRows[a].net != accRows[b].net {
			return accRows[a].net > accRows[b].net
		}
		return accRows[a].name < accRows[b].name
	})
	lim := len(accRows)
	if lim > 10 {
		lim = 10
	}
	for k := 0; k < lim; k++ {
		buf = append(buf, "account "...)
		buf = append(buf, accRows[k].name...)
		buf = append(buf, ' ')
		buf = strconv.AppendInt(buf, accRows[k].net, 10)
		buf = append(buf, '\n')
		w.Write(buf)
		buf = buf[:0]
	}
	w.Flush()
}

// ---- scanner helpers ----

func skipWs() {
	for i < n {
		c := data[i]
		if c == ' ' || c == '\t' || c == '\r' || c == '\n' {
			i++
		} else {
			break
		}
	}
}

func skipString() { // i at opening quote; leaves i past closing quote
	i++
	for {
		c := data[i]
		if c == '\\' {
			i += 2 // hex digits after \u contain no '"' or '\\'
			continue
		}
		if c == '"' {
			i++
			return
		}
		i++
	}
}

func scanString() { // i at opening quote; leaves i past closing quote
	i++
	sStart = i
	sEsc = false
	for {
		c := data[i]
		if c == '\\' {
			sEsc = true
			i += 2
			continue
		}
		if c == '"' {
			sEnd = i
			i++
			return
		}
		i++
	}
}

func skipValue() {
	c := data[i]
	if c == '"' {
		skipString()
		return
	}
	if c == '{' || c == '[' {
		depth := 0
		for i < n {
			d := data[i]
			if d == '"' {
				skipString()
				continue
			}
			if d == '{' || d == '[' {
				depth++
			} else if d == '}' || d == ']' {
				depth--
				if depth == 0 {
					i++
					return
				}
			}
			i++
		}
		return
	}
	for i < n {
		d := data[i]
		if d == ',' || d == '}' || d == ']' || d == ' ' || d == '\t' || d == '\r' || d == '\n' {
			return
		}
		i++
	}
}

func eqBytes(a, b int, lit string) bool {
	if b-a != len(lit) {
		return false
	}
	for j := 0; j < len(lit); j++ {
		if data[a+j] != lit[j] {
			return false
		}
	}
	return true
}

// value string at sStart..sEnd (sEsc set) as a Go string
func strValue() string {
	if !sEsc {
		return string(data[sStart:sEnd])
	}
	return string(decodeInto(sStart, sEnd))
}

func hex4(at int) int {
	v := 0
	for k := 0; k < 4; k++ {
		c := data[at+k]
		v <<= 4
		if c <= '9' {
			v += int(c - '0')
		} else if c <= 'F' {
			v += int(c-'A') + 10
		} else {
			v += int(c-'a') + 10
		}
	}
	return v
}

func decodeInto(from, to int) []byte {
	out := make([]byte, 0, to-from)
	j := from
	for j < to {
		c := data[j]
		if c != '\\' {
			out = append(out, c)
			j++
			continue
		}
		e := data[j+1]
		j += 2
		switch e {
		case '"':
			out = append(out, '"')
		case '\\':
			out = append(out, '\\')
		case '/':
			out = append(out, '/')
		case 'b':
			out = append(out, '\b')
		case 'f':
			out = append(out, '\f')
		case 'n':
			out = append(out, '\n')
		case 'r':
			out = append(out, '\r')
		case 't':
			out = append(out, '\t')
		case 'u':
			cp := hex4(j)
			j += 4
			if cp >= 0xD800 && cp <= 0xDBFF && j+1 < to && data[j] == '\\' && data[j+1] == 'u' {
				lo := hex4(j + 2)
				if lo >= 0xDC00 && lo <= 0xDFFF {
					cp = 0x10000 + (cp-0xD800)<<10 + (lo - 0xDC00)
					j += 6
				}
			}
			switch {
			case cp < 0x80:
				out = append(out, byte(cp))
			case cp < 0x800:
				out = append(out, byte(0xC0|cp>>6), byte(0x80|cp&0x3F))
			case cp < 0x10000:
				out = append(out, byte(0xE0|cp>>12), byte(0x80|(cp>>6)&0x3F), byte(0x80|cp&0x3F))
			default:
				out = append(out, byte(0xF0|cp>>18), byte(0x80|(cp>>12)&0x3F), byte(0x80|(cp>>6)&0x3F), byte(0x80|cp&0x3F))
			}
		default:
			out = append(out, e)
		}
	}
	return out
}

func decodedEq(lit string) bool {
	return string(decodeInto(sStart, sEnd)) == lit
}

func parseAmount(from, to int, esc bool) int64 {
	if esc {
		b := decodeInto(from, to)
		return parseAmountDigits(b, 0, len(b))
	}
	return parseAmountDigits(data, from, to)
}

func parseAmountDigits(b []byte, from, to int) int64 {
	var ip int64
	j := from
	for j < to && b[j] >= '0' && b[j] <= '9' {
		ip = ip*10 + int64(b[j]-'0')
		j++
	}
	var frac int64
	fd := 0
	if j < to && b[j] == '.' {
		j++
		for j < to && fd < 2 && b[j] >= '0' && b[j] <= '9' {
			frac = frac*10 + int64(b[j]-'0')
			fd++
			j++
		}
	}
	for fd < 2 {
		frac *= 10
		fd++
	}
	return ip*100 + frac
}

func parseTags() bool {
	i++ // '['
	test := false
	for {
		skipWs()
		if data[i] == ']' {
			i++
			return test
		}
		if data[i] == '"' {
			scanString()
			if !test {
				test = sEsc && decodedEq("test") || !sEsc && sEnd-sStart == 4 && eqBytes(sStart, sEnd, "test")
			}
		} else {
			skipValue()
		}
		skipWs()
		if data[i] == ',' {
			i++
		}
	}
}

func parseMeta() string {
	i++ // '{'
	var channel string
	for {
		skipWs()
		if data[i] == '}' {
			i++
			return channel
		}
		scanString()
		ks, ke, kesc := sStart, sEnd, sEsc
		skipWs()
		i++ // ':'
		skipWs()
		isChannel := kesc && string(decodeInto(ks, ke)) == "channel" ||
			!kesc && ke-ks == 7 && eqBytes(ks, ke, "channel")
		if isChannel {
			scanString()
			channel = strValue()
		} else {
			skipValue()
		}
		skipWs()
		if data[i] == ',' {
			i++
		}
	}
}

func typeCodeVal() int {
	if !sEsc {
		l := sEnd - sStart
		switch {
		case l == 6 && eqBytes(sStart, sEnd, "credit"):
			return 1
		case l == 5 && eqBytes(sStart, sEnd, "debit"):
			return 2
		case l == 6 && eqBytes(sStart, sEnd, "refund"):
			return 3
		case l == 4 && eqBytes(sStart, sEnd, "void"):
			return 4
		}
		return 0
	}
	switch string(decodeInto(sStart, sEnd)) {
	case "credit":
		return 1
	case "debit":
		return 2
	case "refund":
		return 3
	case "void":
		return 4
	}
	return 0
}
