package main

import (
	"bytes"
	"os"
	"sort"
	"strconv"
)

type Entry struct {
	key []byte
	lats []int
	mx  int
}

func isDig(c byte) bool { return c-'0' <= 9 }
func isLow(c byte) bool { return c-'a' <= 25 }
func isPathCh(c byte) bool {
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' || c == '/' || c == '-'
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	var total, malformed int64
	var statusCnt [10]int64

	entries := make([]*Entry, 0, 1024)
	index := make(map[string]*Entry, 1024)
	tmp := make([]byte, 0, 256)

	n := len(data)
	pos := 0
	for pos < n {
		lineStart := pos
		var lineEnd int
		if idx := bytes.IndexByte(data[pos:], '\n'); idx >= 0 {
			lineEnd = pos + idx
			pos = lineEnd + 1
		} else {
			lineEnd = n
			pos = n
		}
		total++
		s := data[lineStart:lineEnd]
		ln := len(s)
		ok := true
		statusClass := 0
		latency := 0
		pathStart, pathEnd := 0, 0

		if ln < 25 {
			ok = false
		} else if !(isDig(s[0]) && isDig(s[1]) && isDig(s[2]) && isDig(s[3]) && s[4] == '-' && isDig(s[5]) && isDig(s[6]) && s[7] == '-' && isDig(s[8]) && isDig(s[9]) && s[10] == 'T' && isDig(s[11]) && isDig(s[12]) && s[13] == ':' && isDig(s[14]) && isDig(s[15]) && s[16] == ':' && isDig(s[17]) && isDig(s[18]) && s[19] == '.' && isDig(s[20]) && isDig(s[21]) && isDig(s[22]) && s[23] == 'Z' && s[24] == ' ') {
			ok = false
		} else {
			i := 25
			st := i
			for i < ln && isLow(s[i]) {
				i++
			}
			if i == st {
				ok = false
			} else if i >= ln || s[i] != '-' {
				ok = false
			} else {
				i++
				st = i
				for i < ln && isDig(s[i]) {
					i++
				}
				if i == st || i >= ln || s[i] != ' ' {
					ok = false
				} else {
					i++
					rem := data[lineStart+i : lineEnd]
					switch {
					case bytes.HasPrefix(rem, []byte("GET ")):
						i += 4
					case bytes.HasPrefix(rem, []byte("PUT ")):
						i += 4
					case bytes.HasPrefix(rem, []byte("POST ")):
						i += 5
					case bytes.HasPrefix(rem, []byte("PATCH ")):
						i += 6
					case bytes.HasPrefix(rem, []byte("DELETE ")):
						i += 7
					default:
						ok = false
					}
					if ok {
						if i >= ln || s[i] != '/' {
							ok = false
						} else {
							pathStart = i
							for i < ln && s[i] != ' ' && s[i] != '?' {
								if !isPathCh(s[i]) {
									ok = false
									break
								}
								i++
							}
							if ok {
								pathEnd = i
								if i < ln && s[i] == '?' {
									i++
									for i < ln && s[i] != ' ' {
										i++
									}
								}
								if i >= ln || s[i] != ' ' {
									ok = false
								} else {
									i++
									if i+4 > ln || !isDig(s[i]) || !isDig(s[i+1]) || !isDig(s[i+2]) || s[i+3] != ' ' {
										ok = false
									} else {
										statusClass = int(s[i] - '0')
										i += 4
										st = i
										for i < ln && isDig(s[i]) {
											i++
										}
										if i == st || i >= ln || s[i] != 'B' {
											ok = false
										} else {
											i++
											if i >= ln || s[i] != ' ' {
												ok = false
											} else {
												i++
												st = i
												v := 0
												for i < ln && isDig(s[i]) {
													v = v*10 + int(s[i]-'0')
													i++
												}
												if i == st || i >= ln || s[i] != '.' {
													ok = false
												} else {
													i++
													if i >= ln || !isDig(s[i]) {
														ok = false
													} else {
														v = v*10 + int(s[i]-'0')
														i++
														latency = v
														if i+2 > ln || s[i] != 'm' || s[i+1] != 's' {
															ok = false
														} else {
															i += 2
															if i >= ln || s[i] != ' ' {
																ok = false
															} else {
																i++
																if i >= ln || s[i] != '"' {
																	ok = false
																} else if ln < 1 || s[ln-1] != '"' || i+1 >= ln {
																	ok = false
																} else if bytes.IndexByte(s[i+1:ln-1], '"') >= 0 {
																	ok = false
																}
															}
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
		if !ok {
			malformed++
			continue
		}
		statusCnt[statusClass]++

		// build template
		tmp = tmp[:0]
		p := pathStart
		for {
			segStart := p
			for p < pathEnd && s[p] != '/' {
				p++
			}
			segLen := p - segStart
			allDig := segLen > 0
			if allDig {
				for k := segStart; k < p; k++ {
					if !isDig(s[k]) {
						allDig = false
						break
					}
				}
			}
			if allDig {
				tmp = append(tmp, '{', 'i', 'd', '}')
			} else if segLen > 0 {
				tmp = append(tmp, s[segStart:p]...)
			}
			if p >= pathEnd {
				break
			}
			tmp = append(tmp, '/')
			p++
		}
		if e, found := index[string(tmp)]; found {
			e.lats = append(e.lats, latency)
			if latency > e.mx {
				e.mx = latency
			}
		} else {
			key := make([]byte, len(tmp))
			copy(key, tmp)
			e := &Entry{key: key, lats: make([]int, 0, 16), mx: latency}
			e.lats = append(e.lats, latency)
			entries = append(entries, e)
			index[string(key)] = e
		}
	}

	sort.Slice(entries, func(a, b int) bool {
		ca, cb := len(entries[a].lats), len(entries[b].lats)
		if ca != cb {
			return ca > cb
		}
		return bytes.Compare(entries[a].key, entries[b].key) < 0
	})
	top := len(entries)
	if top > 10 {
		top = 10
	}
	var out bytes.Buffer
	out.Grow(4096)
	out.WriteString("lines ")
	out.WriteString(strconv.FormatInt(total, 10))
	out.WriteByte('\n')
	out.WriteString("malformed ")
	out.WriteString(strconv.FormatInt(malformed, 10))
	out.WriteByte('\n')
	for c := 0; c < 10; c++ {
		if statusCnt[c] > 0 {
			out.WriteString("status ")
			out.WriteByte(byte('0' + c))
			out.WriteString("xx ")
			out.WriteString(strconv.FormatInt(statusCnt[c], 10))
			out.WriteByte('\n')
		}
	}
	writeLat := func(v int) {
		out.WriteString(strconv.Itoa(v / 10))
		out.WriteByte('.')
		out.WriteString(strconv.Itoa(v % 10))
	}
	for ti := 0; ti < top; ti++ {
		e := entries[ti]
		sort.Ints(e.lats)
		nn := int64(len(e.lats))
		r50 := (50*nn + 99) / 100
		r95 := (95*nn + 99) / 100
		out.WriteString("path ")
		out.Write(e.key)
		out.WriteByte(' ')
		out.WriteString(strconv.FormatInt(nn, 10))
		out.WriteByte(' ')
		writeLat(e.lats[r50-1])
		out.WriteByte(' ')
		writeLat(e.lats[r95-1])
		out.WriteByte(' ')
		writeLat(e.mx)
		out.WriteByte('\n')
	}
	os.Stdout.Write(out.Bytes())
}
