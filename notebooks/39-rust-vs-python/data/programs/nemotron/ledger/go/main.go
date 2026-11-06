package main

import (
	"bytes"
	"os"
	"sort"
)

var file []byte
var pos int
var limit int

func isWS(b byte) bool { return b == ' ' || b == '\t' || b == '\r' || b == '\n' }

var sb bytes.Buffer

func scanString() bool {
	sb.Reset()
	i := pos + 1
	for i < limit {
		c := file[i]
		i++
		if c == '"' { pos = i; return true }
		if c == '\\' {
			if i >= limit { return false }
			e := file[i]
			i++
			switch e {
			case '"': sb.WriteByte('"')
			case '\\': sb.WriteByte('\\')
			case '/': sb.WriteByte('/')
			case 'n': sb.WriteByte('\n')
			case 'r': sb.WriteByte('\r')
			case 't': sb.WriteByte('\t')
			case 'b': sb.WriteByte('\b')
			case 'f': sb.WriteByte('\f')
			case 'u':
				if i+6 >= limit { return false }
				cp := 0
				for k := 0; k < 4; k++ {
					h := file[i]; i++; cp <<= 4
					switch {
					case h >= '0' && h <= '9': cp += int(h - '0')
					case h >= 'a' && h <= 'f': cp += int(h - 'a' + 10)
					case h >= 'A' && h <= 'F': cp += int(h - 'A' + 10)
					default: return false
					}
				}
				if cp >= 0xD800 && cp <= 0xDBFF && i+1 < limit && file[i] == '\\' && file[i+1] == 'u' {
					i += 2
					cp2 := 0
					for k := 0; k < 4; k++ {
						h := file[i]; i++; cp2 <<= 4
						switch {
						case h >= '0' && h <= '9': cp2 += int(h - '0')
						case h >= 'a' && h <= 'f': cp2 += int(h - 'a' + 10)
						case h >= 'A' && h <= 'F': cp2 += int(h - 'A' + 10)
						default: return false
						}
					}
					cp = 0x10000 + ((cp - 0xD800) << 10) + (cp2 - 0xDC00)
				}
				sb.WriteRune(rune(cp))
			default: return false
			}
		} else {
			sb.WriteByte(byte(c))
		}
	}
	return false
}

func skipScalar() {
	for pos < limit {
		b := file[pos]
		if b == ',' || b == '}' || b == ']' || isWS(b) { return }
		pos++
	}
}

const (
	kindRates = iota
	kindCounted
	kindSkipped
	kindBad
)

var acct, typ, amt, cur, chanStr string
var hasTest bool
var usd int64

func parseLine() int {
	i := pos
	for i < limit && isWS(file[i]) { i++ }
	if i >= limit || file[i] != '{' { return kindBad }
	i++
	pos = i

	depth := 1
	var key string
	haveKey := false
	keyDepth := 0

	inRates := false; ratesDepth := 0
	inMeta := false; metaDepth := 0
	inTags := false; tagsDepth := 0

	acct = ""; typ = ""; amt = ""; cur = ""; chanStr = ""
	hasTest = false
	isRates := false

	for pos < limit && depth > 0 {
		c := file[pos]
		if c == '"' {
			if !scanString() { return kindBad }
			for pos < limit && isWS(file[pos]) { pos++ }
			if pos < limit && file[pos] == ':' {
				key = sb.String()
				keyDepth = depth
				haveKey = true
				pos++
				for pos < limit && isWS(file[pos]) { pos++ }
				if pos >= limit { return kindBad }
				nxt := file[pos]
				if nxt == '"' {
					if !scanString() { return kindBad }
					if haveKey {
						if keyDepth == 1 {
							switch key {
							case "account": acct = sb.String()
							case "type": typ = sb.String()
							case "currency": cur = sb.String()
							case "amount": amt = sb.String()
							}
						} else if inMeta && depth == metaDepth && key == "channel" {
							chanStr = sb.String()
						}
					}
					haveKey = false
				} else if nxt == '{' {
					depth++; pos++
					if haveKey && keyDepth == 1 && key == "rates" { inRates = true; ratesDepth = depth; isRates = true } else if haveKey && keyDepth == 1 && key == "meta" { metaDepth = depth; inMeta = true }
					haveKey = false
				} else if nxt == '[' {
					depth++; pos++
					if haveKey && keyDepth == 1 && key == "tags" { inTags = true; tagsDepth = depth }
					haveKey = false
				} else {
					if inRates && depth == ratesDepth && haveKey {
						v := int64(0); any := false
						for pos < limit {
							h := file[pos]
							if h < '0' || h > '9' { break }
							v = v*10 + int64(h-'0'); pos++; any = true
						}
						if !any { return kindBad }
						rates[key] = v
					} else {
						skipScalar()
					}
					haveKey = false
				}
			} else {
				if inTags && depth == tagsDepth && sb.String() == "test" { hasTest = true }
				haveKey = false
			}
		} else if c == '{' || c == '[' {
			depth++; pos++; haveKey = false
		} else if c == '}' || c == ']' {
			depth--; pos++
			if inMeta && depth == metaDepth-1 { inMeta = false }
			if inTags && depth == tagsDepth-1 { inTags = false }
			haveKey = false
		} else {
			pos++
		}
	}

	if isRates { return kindRates }
	if typ == "void" { return kindSkipped }
	if hasTest { return kindSkipped }

	dollars := int64(0); j := 0
	for j < len(amt) && amt[j] >= '0' && amt[j] <= '9' { dollars = dollars*10 + int64(amt[j]-'0'); j++ }
	cents := int64(0)
	if j < len(amt) && amt[j] == '.' {
		j++; nd := 0
		for j < len(amt) && amt[j] >= '0' && amt[j] <= '9' && nd < 2 { cents = cents*10 + int64(amt[j]-'0'); j++; nd++ }
		for nd < 2 { cents *= 10; nd++ }
	}
	hundredths := dollars*100 + cents

	rate, ok := rates[cur]
	if !ok { return kindBad }
	usd = (hundredths * rate) / 1000000
	if typ == "debit" { usd = -usd }
	return kindCounted
}

var rates = map[string]int64{}
var channels = map[string][2]int64{}
var accounts = map[string]int64{}
var totalCount, totalNet int64

func main() {
	var err error
	file, err = os.ReadFile(os.Args[1])
	if err != nil { os.Exit(1) }
	limit = len(file)
	pos = 0

	var out bytes.Buffer
	for pos < limit {
		lineStart := pos
		for pos < limit && file[pos] != '\n' { pos++ }
		end := pos
		ln := end - lineStart
		if ln > 0 {
			curLimit := limit
			limit = end
			pos = lineStart
			k := parseLine()
			limit = curLimit
			pos = end + 1
			if k == kindCounted {
				totalCount++
				totalNet += usd
				c := channels[chanStr]
				c[0]++; c[1] += usd
				channels[chanStr] = c
				accounts[acct] += usd
			}
		} else {
			pos = end + 1
		}
	}

	out.WriteString("counted ")
	out.WriteString(int64ToStr(totalCount))
	out.WriteByte('\n')
	out.WriteString("net ")
	out.WriteString(int64ToStr(totalNet))
	out.WriteByte('\n')

	chNames := make([]string, 0, len(channels))
	for name := range channels { chNames = append(chNames, name) }
	sort.Strings(chNames)
	for _, name := range chNames {
		c := channels[name]
		out.WriteString("channel ")
		out.WriteString(name)
		out.WriteByte(' ')
		out.WriteString(int64ToStr(c[0]))
		out.WriteByte(' ')
		out.WriteString(int64ToStr(c[1]))
		out.WriteByte('\n')
	}

	accts := make([]struct{ k string; v int64 }, 0, len(accounts))
	for k, v := range accounts { accts = append(accts, struct{ k string; v int64 }{k, v}) }
	sort.Slice(accts, func(i, j int) bool {
		if accts[i].v != accts[j].v { return accts[i].v > accts[j].v }
		return accts[i].k < accts[j].k
	})
	lim := 10
	if len(accts) < lim { lim = len(accts) }
	for k := 0; k < lim; k++ {
		out.WriteString("account ")
		out.WriteString(accts[k].k)
		out.WriteByte(' ')
		out.WriteString(int64ToStr(accts[k].v))
		out.WriteByte('\n')
	}

	os.Stdout.Write(out.Bytes())
}

func int64ToStr(v int64) string {
	if v == 0 { return "0" }
	neg := false
	if v < 0 { neg = true; v = -v }
	var buf [20]byte
	i := len(buf)
	for v > 0 { i--; buf[i] = byte('0' + v%10); v /= 10 }
	if neg { i--; buf[i] = '-' }
	return string(buf[i:])
}
