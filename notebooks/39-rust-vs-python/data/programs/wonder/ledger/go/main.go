package main

import (
	"bytes"
	"fmt"
	"os"
	"sort"
	"unsafe"
)

var b []byte
var p, n int
var arena []byte

// span: we return (start,end,escapedDecodedStart...) Simplify: parseString returns string using unsafe for raw, decoded string for escaped.
func skipWs() {
	for p < n {
		c := b[p]
		if c == ' ' || c == '\t' || c == '\r' || c == '\n' {
			p++
		} else {
			break
		}
	}
}

func hex4(s []byte, off int) uint32 {
	var v uint32
	for i := 0; i < 4; i++ {
		c := s[off+i]
		v <<= 4
		if c >= '0' && c <= '9' {
			v |= uint32(c - '0')
		} else if c >= 'a' && c <= 'f' {
			v |= uint32(c-'a') + 10
		} else if c >= 'A' && c <= 'F' {
			v |= uint32(c-'A') + 10
		}
	}
	return v
}

func decodeSpan(src []byte, s, e int) string {
	out := make([]byte, 0, e-s)
	i := s
	for i < e {
		c := src[i]
		if c != '\\' {
			out = append(out, c)
			i++
			continue
		}
		i++
		if i >= e {
			break
		}
		esc := src[i]
		i++
		switch esc {
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
			cp := hex4(src, i)
			i += 4
			if cp >= 0xD800 && cp <= 0xDBFF && i+1 < e && src[i] == '\\' && src[i+1] == 'u' {
				lo := hex4(src, i+2)
				if lo >= 0xDC00 && lo <= 0xDFFF {
					i += 6
					cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
				}
			}
			out = append(out, string(rune(cp))...)
		default:
			out = append(out, esc)
		}
	}
	return string(out)
}

// parseString returns string view (unsafe, no copy) or decoded string.
func parseString() string {
	p++
	start := p
	i := p
	esc := false
	for i < n {
		c := b[i]
		if c == '"' {
			break
		}
		if c == '\\' {
			esc = true
			i += 2
			continue
		}
		i++
	}
	end := i
	if i < n {
		p = i + 1
	} else {
		p = i
	}
	if !esc {
		if end == start {
			return ""
		}
		return unsafe.String(&b[start], end-start)
	}
	return decodeSpan(b, start, end)
}

func skipString() {
	p++
	for p < n {
		c := b[p]
		if c == '"' {
			p++
			return
		}
		if c == '\\' {
			p += 2
			continue
		}
		p++
	}
}

func skipValue() {
	skipWs()
	if p >= n {
		return
	}
	c := b[p]
	if c == '"' {
		skipString()
		return
	}
	if c == '{' || c == '[' {
		depth := 0
		for p < n {
			ch := b[p]
			if ch == '"' {
				skipString()
				continue
			}
			if ch == '{' || ch == '[' {
				depth++
				p++
				continue
			}
			if ch == '}' || ch == ']' {
				p++
				depth--
				if depth == 0 {
					return
				}
				continue
			}
			p++
		}
		return
	}
	for p < n {
		ch := b[p]
		if ch == ',' || ch == '}' || ch == ']' || ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n' {
			break
		}
		p++
	}
}

func parseIntValue() int64 {
	skipWs()
	neg := false
	if p < n && b[p] == '-' {
		neg = true
		p++
	}
	var v int64
	for p < n && b[p] >= '0' && b[p] <= '9' {
		v = v*10 + int64(b[p]-'0')
		p++
	}
	for p < n {
		c := b[p]
		if (c >= '0' && c <= '9') || c == '.' || c == 'e' || c == 'E' || c == '+' || c == '-' {
			p++
		} else {
			break
		}
	}
	if neg {
		return -v
	}
	return v
}

func parseAmount(s string) int64 {
	// s may be unsafe string referencing b; indexing fine
	var v int64
	i := 0
	L := len(s)
	for i < L && s[i] >= '0' && s[i] <= '9' {
		v = v*10 + int64(s[i]-'0')
		i++
	}
	v *= 100
	if i < L && s[i] == '.' {
		i++
		frac := int64(0)
		dig := 0
		for i < L && s[i] >= '0' && s[i] <= '9' && dig < 2 {
			frac = frac*10 + int64(s[i]-'0')
			i++
			dig++
		}
		if dig == 1 {
			frac *= 10
		}
		v += frac
	}
	return v
}

type rateE struct {
	code string
	rate int64
}
type chanE struct {
	name  string
	count int64
	net   int64
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	b = data
	n = len(b)
	p = 0
	if n == 0 {
		fmt.Print("counted 0\nnet 0\n")
		return
	}
	var rates []rateE
	var chans []*chanE
	chanMap := make(map[string]*chanE, 16)
	accounts := make(map[string]int64, 1<<16)

	skipWs()
	if p < n && b[p] == '{' {
		p++
		for p < n {
			skipWs()
			if p >= n {
				break
			}
			if b[p] == '}' {
				p++
				break
			}
			if b[p] == ',' {
				p++
				continue
			}
			key := parseString()
			skipWs()
			if p < n && b[p] == ':' {
				p++
			}
			if key == "rates" {
				skipWs()
				if p < n && b[p] == '{' {
					p++
					for p < n {
						skipWs()
						if p >= n {
							break
						}
						if b[p] == '}' {
							p++
							break
						}
						if b[p] == ',' {
							p++
							continue
						}
						code := parseString()
						skipWs()
						if p < n && b[p] == ':' {
							p++
						}
						rate := parseIntValue()
						rates = append(rates, rateE{code, rate})
					}
				} else {
					skipValue()
				}
			} else {
				skipValue()
			}
		}
	}

	var counted, totalNet int64
	for {
		for p < n && (b[p] == '\n' || b[p] == '\r' || b[p] == ' ' || b[p] == '\t') {
			p++
		}
		if p >= n {
			break
		}
		if b[p] != '{' {
			for p < n && b[p] != '\n' {
				p++
			}
			continue
		}
		p++
		var account, channel string
		hasAccount, hasChannel := false, false
		var hundredths int64
		var rate int64 = 1000000
		sign := int64(1)
		skip := false
		for p < n {
			skipWs()
			if p >= n {
				break
			}
			c := b[p]
			if c == '}' {
				p++
				break
			}
			if c == ',' {
				p++
				continue
			}
			key := parseString()
			skipWs()
			if p < n && b[p] == ':' {
				p++
			}
			skipWs()
			switch key {
			case "account":
				if p < n && b[p] == '"' {
					account = parseString()
					hasAccount = true
				} else {
					skipValue()
				}
			case "type":
				if p < n && b[p] == '"' {
					v := parseString()
					if v == "void" {
						skip = true
					} else if v == "debit" {
						sign = -1
					} else {
						sign = 1
					}
				} else {
					skipValue()
				}
			case "amount":
				if p < n && b[p] == '"' {
					v := parseString()
					hundredths = parseAmount(v)
				} else {
					skipValue()
				}
			case "currency":
				if p < n && b[p] == '"' {
					v := parseString()
					rate = 0
					for _, r := range rates {
						if r.code == v {
							rate = r.rate
							break
						}
					}
				} else {
					skipValue()
				}
			case "tags":
				skipWs()
				if p < n && b[p] == '[' {
					p++
					for p < n {
						skipWs()
						if p >= n {
							break
						}
						if b[p] == ']' {
							p++
							break
						}
						if b[p] == ',' {
							p++
							continue
						}
						if b[p] == '"' {
							v := parseString()
							if v == "test" {
								skip = true
							}
						} else {
							skipValue()
						}
						if skip {
							break
						}
					}
				} else {
					skipValue()
				}
			case "meta":
				skipWs()
				if p < n && b[p] == '{' {
					p++
					for p < n {
						skipWs()
						if p >= n {
							break
						}
						if b[p] == '}' {
							p++
							break
						}
						if b[p] == ',' {
							p++
							continue
						}
						mk := parseString()
						skipWs()
						if p < n && b[p] == ':' {
							p++
						}
						skipWs()
						if mk == "channel" {
							if p < n && b[p] == '"' {
								channel = parseString()
								hasChannel = true
							} else {
								skipValue()
							}
						} else {
							skipValue()
						}
					}
				} else {
					skipValue()
				}
			default:
				skipValue()
			}
			if skip {
				// skip to end of line
				idx := bytes.IndexByte(b[p:], '\n')
				if idx < 0 {
					p = n
				} else {
					p += idx + 1
				}
				break
			}
		}
		if skip {
			continue
		}
		usd := (hundredths * rate) / 1000000
		signed := sign * usd
		counted++
		totalNet += signed
		if hasChannel {
			ce, ok := chanMap[channel]
			if !ok {
				// Need stable key: if channel came from unsafe string it points into b (stable). If decoded, it's owned. Both fine as map keys (Go stores string header).
				ce = &chanE{name: channel}
				chanMap[channel] = ce
				chans = append(chans, ce)
			}
			ce.count++
			ce.net += signed
		}
		if hasAccount {
			accounts[account] += signed
		}
	}

	sort.Slice(chans, func(i, j int) bool { return chans[i].name < chans[j].name })
	type accE struct {
		id  string
		net int64
	}
	accs := make([]accE, 0, len(accounts))
	for k, v := range accounts {
		accs = append(accs, accE{k, v})
	}
	sort.Slice(accs, func(i, j int) bool {
		if accs[i].net != accs[j].net {
			return accs[i].net > accs[j].net
		}
		return accs[i].id < accs[j].id
	})
	top := 10
	if len(accs) < top {
		top = len(accs)
	}
	var out bytes.Buffer
	out.Grow(8192)
	fmt.Fprintf(&out, "counted %d\nnet %d\n", counted, totalNet)
	for _, c := range chans {
		fmt.Fprintf(&out, "channel %s %d %d\n", c.name, c.count, c.net)
	}
	for i := 0; i < top; i++ {
		fmt.Fprintf(&out, "account %s %d\n", accs[i].id, accs[i].net)
	}
	os.Stdout.Write(out.Bytes())
}
