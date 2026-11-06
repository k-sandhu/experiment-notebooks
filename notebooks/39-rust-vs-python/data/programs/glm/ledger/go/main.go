// Ledger: sum JSON-lines transactions with exact integer currency conversion.
// Single pass over the raw bytes; only the needed fields are extracted.
package main

import (
	"bytes"
	"os"
	"sort"
	"strconv"
	"unsafe"
)

const micro = 1000000

type channelAgg struct {
	count int64
	net   int64
}

var (
	data      []byte
	rates     = make(map[string]int64, 16)
	channels  = make(map[string]*channelAgg, 16)
	accounts  = make(map[string]int64, 4096)
	arena     []byte // backing store for decoded (escaped) keys
	arenaOff  int
	scratch   = make([]byte, 0, 256) // reused decode buffer
)

// intern copies a decoded key into stable storage (fixed chunks, never moves).
func intern(b []byte) string {
	if len(arena)-arenaOff < len(b) {
		n := len(b)
		if n < 4096 {
			n = 4096
		}
		arena = append(arena, make([]byte, n)...)
	}
	dst := arena[arenaOff : arenaOff+len(b)]
	copy(dst, b)
	arenaOff += len(b)
	return unsafe.String(&dst[0], len(dst))
}

func isWS(c byte) bool {
	return c == ' ' || c == '\t' || c == '\r' || c == '\n'
}

func skipWS(i int) int {
	for i < len(data) && isWS(data[i]) {
		i++
	}
	return i
}

// parseString starts at '"'; returns content [s,e) and index after '"'.
func parseString(i int) (s, e, next int, esc bool) {
	i++
	s = i
	for i < len(data) {
		c := data[i]
		if c == '"' {
			return s, i, i + 1, esc
		}
		if c == '\\' {
			esc = true
			i++
			if i < len(data) && data[i] == 'u' {
				i += 4
			}
		}
		i++
	}
	return s, i, i, esc
}

func skipValue(i int) int {
	if i < len(data) && data[i] == '"' {
		_, _, next, _ := parseString(i)
		return next
	}
	if i < len(data) && (data[i] == '{' || data[i] == '[') {
		depth := 0
		for i < len(data) {
			c := data[i]
			if c == '"' {
				_, _, next, _ := parseString(i)
				i = next
				continue
			}
			if c == '{' || c == '[' {
				depth++
			} else if c == '}' || c == ']' {
				depth--
				if depth == 0 {
					return i + 1
				}
			}
			i++
		}
		return i
	}
	for i < len(data) {
		c := data[i]
		if c == ',' || c == '}' || c == ']' {
			break
		}
		i++
	}
	return i
}

func decodeString(s, e int) []byte {
	scratch = scratch[:0]
	for i := s; i < e; i++ {
		c := data[i]
		if c != '\\' {
			scratch = append(scratch, c)
			continue
		}
		i++
		switch data[i] {
		case '"':
			scratch = append(scratch, '"')
		case '\\':
			scratch = append(scratch, '\\')
		case '/':
			scratch = append(scratch, '/')
		case 'b':
			scratch = append(scratch, '\b')
		case 'f':
			scratch = append(scratch, '\f')
		case 'n':
			scratch = append(scratch, '\n')
		case 'r':
			scratch = append(scratch, '\r')
		case 't':
			scratch = append(scratch, '\t')
		case 'u':
			cp := hex4(i + 1)
			i += 4
			if cp >= 0xD800 && cp <= 0xDBFF && i+2 < e && data[i+1] == '\\' && data[i+2] == 'u' {
				lo := hex4(i + 3)
				if lo >= 0xDC00 && lo <= 0xDFFF {
					cp = 0x10000 + (cp-0xD800)<<10 + (lo - 0xDC00)
					i += 6
				}
			}
			scratch = appendRune(scratch, cp)
		default:
			scratch = append(scratch, data[i])
		}
	}
	return scratch
}

func hex4(i int) uint32 {
	var v uint32
	for k := 0; k < 4; k++ {
		c := data[i+k]
		v <<= 4
		switch {
		case c >= '0' && c <= '9':
			v |= uint32(c - '0')
		case c >= 'a' && c <= 'f':
			v |= uint32(c-'a') + 10
		case c >= 'A' && c <= 'F':
			v |= uint32(c-'A') + 10
		}
	}
	return v
}

func appendRune(b []byte, cp uint32) []byte {
	switch {
	case cp < 0x80:
		return append(b, byte(cp))
	case cp < 0x800:
		return append(b, byte(0xC0|cp>>6), byte(0x80|cp&0x3F))
	case cp < 0x10000:
		return append(b, byte(0xE0|cp>>12), byte(0x80|(cp>>6)&0x3F), byte(0x80|cp&0x3F))
	default:
		return append(b, byte(0xF0|cp>>18), byte(0x80|(cp>>12)&0x3F), byte(0x80|(cp>>6)&0x3F), byte(0x80|cp&0x3F))
	}
}

// strEq compares a string value (raw slice, maybe escaped) to an ASCII literal.
func strEq(s, e int, esc bool, lit string) bool {
	if !esc {
		return e-s == len(lit) && string(data[s:e]) == lit
	}
	d := decodeString(s, e)
	return string(d) == lit
}

// parseAmount converts "12", "12.5" or "12.05" to integer hundredths.
func parseAmount(s, e int) int64 {
	var whole int64
	i := s
	for i < e && data[i] >= '0' && data[i] <= '9' {
		whole = whole*10 + int64(data[i]-'0')
		i++
	}
	var frac int64
	if i < e && data[i] == '.' {
		i++
		frac = int64(data[i]-'0') * 10
		i++
		if i < e {
			frac += int64(data[i] - '0')
		}
	}
	return whole*100 + frac
}

func asKey(s, e int, esc bool) string {
	if !esc {
		return unsafe.String(&data[s], e-s)
	}
	return intern(decodeString(s, e))
}

func loadRates(i int) {
	i = skipWS(i)
	if i >= len(data) || data[i] != '{' {
		return
	}
	i++
	for {
		i = skipWS(i)
		if i >= len(data) || data[i] == '}' {
			break
		}
		if data[i] == ',' {
			i++
			continue
		}
		ks, ke, knext, kesc := parseString(i)
		i = skipWS(knext)
		i++ // ':'
		i = skipWS(i)
		if strEq(ks, ke, kesc, "rates") {
			i = skipWS(i)
			i++ // '{'
			for {
				i = skipWS(i)
				if i >= len(data) || data[i] == '}' {
					break
				}
				if data[i] == ',' {
					i++
					continue
				}
				cs, ce, cnext, cesc := parseString(i)
				i = skipWS(cnext)
				i++ // ':'
				i = skipWS(i)
				neg := false
				if data[i] == '-' {
					neg = true
					i++
				}
				var rate int64
				for i < len(data) && data[i] >= '0' && data[i] <= '9' {
					rate = rate*10 + int64(data[i]-'0')
					i++
				}
				if neg {
					rate = -rate
				}
				rates[asKey(cs, ce, cesc)] = rate
			}
			i++ // '}'
		} else {
			i = skipValue(i)
		}
	}
}

type accAgg struct {
	name string
	net  int64
}

// better reports whether a ranks ahead of b (net desc, then name asc).
func better(a, b accAgg) bool {
	if a.net != b.net {
		return a.net > b.net
	}
	return a.name < b.name
}

func main() {
	var err error
	data, err = os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}

	// First line: rates.
	i := skipWS(0)
	if eol := indexByte(i, '\n'); eol >= 0 {
		loadRates(i)
		i = eol + 1
	}

	var totalCount, totalNet int64
	for i < len(data) {
		q := skipWS(i)
		eol := indexByte(i, '\n')
		if eol < 0 {
			eol = len(data)
		}
		if q < eol && data[q] == '{' {
			q++
			var sign int64
			var rate int64
			hasRate := false
			var amount int64
			accS, accE, accEsc := -1, 0, false
			chanS, chanE, chanEsc := -1, 0, false
			isTest := false
			for {
				q = skipWS(q)
				if q >= len(data) || data[q] == '}' {
					q++
					break
				}
				if data[q] == ',' {
					q++
					continue
				}
				ks, ke, knext, kesc := parseString(q)
				q = skipWS(knext)
				q++ // ':'
				q = skipWS(q)
				if !kesc {
					kl := ke - ks
					k0 := byte(0)
					if kl > 0 {
						k0 = data[ks]
					}
					switch {
					case k0 == 't' && kl == 4 && string(data[ks:ke]) == "type":
						vs, ve, vnext, vesc := parseString(q)
						q = vnext
						if strEq(vs, ve, vesc, "credit") || strEq(vs, ve, vesc, "refund") {
							sign = 1
						} else if strEq(vs, ve, vesc, "debit") {
							sign = -1
						}
						continue
					case k0 == 'a' && kl == 6 && string(data[ks:ke]) == "amount":
						vs, ve, vnext, _ := parseString(q)
						q = vnext
						amount = parseAmount(vs, ve)
						continue
					case k0 == 'c' && kl == 8 && string(data[ks:ke]) == "currency":
						vs, ve, vnext, vesc := parseString(q)
						q = vnext
						rate, hasRate = rates[asKey(vs, ve, vesc)]
						continue
					case k0 == 'a' && kl == 7 && string(data[ks:ke]) == "account":
						vs, ve, vnext, vesc := parseString(q)
						q = vnext
						accS, accE, accEsc = vs, ve, vesc
						continue
					case k0 == 't' && kl == 4 && string(data[ks:ke]) == "tags":
						q++ // '['
						for {
							q = skipWS(q)
							if q >= len(data) || data[q] == ']' {
								q++
								break
							}
							if data[q] == ',' {
								q++
								continue
							}
							if data[q] == '"' {
								vs, ve, vnext, vesc := parseString(q)
								q = vnext
								if !isTest && strEq(vs, ve, vesc, "test") {
									isTest = true
								}
							} else {
								q = skipValue(q)
							}
						}
						continue
					case k0 == 'm' && kl == 4 && string(data[ks:ke]) == "meta":
						q++ // '{'
						for {
							q = skipWS(q)
							if q >= len(data) || data[q] == '}' {
								q++
								break
							}
							if data[q] == ',' {
								q++
								continue
							}
							mks, mke, mknext, mkesc := parseString(q)
							q = skipWS(mknext)
							q++ // ':'
							q = skipWS(q)
							if strEq(mks, mke, mkesc, "channel") {
								vs, ve, vnext, vesc := parseString(q)
								q = vnext
								chanS, chanE, chanEsc = vs, ve, vesc
							} else {
								q = skipValue(q)
							}
						}
						continue
					}
				}
				q = skipValue(q)
			}
			if sign != 0 && !isTest && hasRate && accS >= 0 && chanS >= 0 {
				val := sign * ((amount * rate) / micro)
				totalCount++
				totalNet += val
				ck := asKey(chanS, chanE, chanEsc)
				if ca, ok := channels[ck]; ok {
					ca.count++
					ca.net += val
				} else {
					channels[ck] = &channelAgg{1, val}
				}
				ak := asKey(accS, accE, accEsc)
				accounts[ak] += val
			}
		}
		i = eol + 1
	}

	out := make([]byte, 0, 4096)
	out = append(out, "counted "...)
	out = strconv.AppendInt(out, totalCount, 10)
	out = append(out, "\nnet "...)
	out = strconv.AppendInt(out, totalNet, 10)
	out = append(out, '\n')

	// Channel lines sorted by name ascending (byte order).
	type chanRow struct {
		name string
		agg  *channelAgg
	}
	rows := make([]chanRow, 0, len(channels))
	for k, v := range channels {
		rows = append(rows, chanRow{k, v})
	}
	sort.Slice(rows, func(a, b int) bool { return rows[a].name < rows[b].name })
	for _, r := range rows {
		out = append(out, "channel "...)
		out = append(out, r.name...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, r.agg.count, 10)
		out = append(out, ' ')
		out = strconv.AppendInt(out, r.agg.net, 10)
		out = append(out, '\n')
	}

	// Top 10 accounts by net desc, then id asc: keep the 10 best while scanning.
	best := make([]accAgg, 0, 10)
	for k, v := range accounts {
		cand := accAgg{k, v}
		if len(best) < 10 {
			best = append(best, cand)
			continue
		}
		// find the worst entry
		worst := 0
		for j := 1; j < len(best); j++ {
			if better(best[worst], best[j]) { // best[j] ranks below best[worst]
				worst = j
			}
		}
		if better(cand, best[worst]) {
			best[worst] = cand
		}
	}
	sort.Slice(best, func(a, b int) bool { return better(best[a], best[b]) })
	for _, a := range best {
		out = append(out, "account "...)
		out = append(out, a.name...)
		out = append(out, ' ')
		out = strconv.AppendInt(out, a.net, 10)
		out = append(out, '\n')
	}

	os.Stdout.Write(out)
}

func indexByte(from int, c byte) int {
	if r := bytes.IndexByte(data[from:], c); r >= 0 {
		return from + r
	}
	return -1
}
