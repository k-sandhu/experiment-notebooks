package main

import (
	"bufio"
	"bytes"
	"fmt"
	"os"
	"slices"
)

func isDig(c byte) bool { return c >= '0' && c <= '9' }

func isPathCh(c byte) bool {
	return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
		(c >= '0' && c <= '9') || c == '_' || c == '-' || c == '/'
}

func tsOk(b []byte, p int) bool {
	return isDig(b[p]) && isDig(b[p+1]) && isDig(b[p+2]) && isDig(b[p+3]) && b[p+4] == '-' &&
		isDig(b[p+5]) && isDig(b[p+6]) && b[p+7] == '-' &&
		isDig(b[p+8]) && isDig(b[p+9]) && b[p+10] == 'T' &&
		isDig(b[p+11]) && isDig(b[p+12]) && b[p+13] == ':' &&
		isDig(b[p+14]) && isDig(b[p+15]) && b[p+16] == ':' &&
		isDig(b[p+17]) && isDig(b[p+18]) && b[p+19] == '.' &&
		isDig(b[p+20]) && isDig(b[p+21]) && isDig(b[p+22]) && b[p+23] == 'Z'
}

func main() {
	f, err := os.Open(os.Args[1])
	if err != nil {
		return
	}
	defer f.Close()

	m := make(map[string]int32, 1024)
	names := make([]string, 0, 1024)
	lists := make([][]int32, 0, 1024)
	maxes := make([]int32, 0, 1024)
	scratch := make([]byte, 2048)

	var lines, malformed uint64
	var statusCount [10]uint64

	buf := make([]byte, 1<<22)
	used := 0
	eof := false

	for !eof {
		if used == len(buf) {
			nb := make([]byte, used<<1)
			copy(nb, buf)
			buf = nb
		}
		nread, rerr := f.Read(buf[used:])
		if nread > 0 {
			used += nread
		}
		if rerr != nil {
			if used > 0 && buf[used-1] != '\n' {
				if used == len(buf) {
					nb := make([]byte, used<<1)
					copy(nb, buf)
					buf = nb
				}
				buf[used] = '\n'
				used++
			}
			eof = true
		}

		start := 0
		for {
			idx := bytes.IndexByte(buf[start:used], '\n')
			if idx < 0 {
				break
			}
			e := start + idx
			lines++

			ok := true
			statusClass := 0
			var lat int32
			pathStart, pathEnd := 0, 0

			{
				q := start
				end := e

				for {
					if end-q < 25 || !tsOk(buf, q) {
						ok = false
						break
					}
					q += 24
					if buf[q] != ' ' {
						ok = false
						break
					}
					q++
					if q >= end || buf[q] < 'a' || buf[q] > 'z' {
						ok = false
						break
					}
					q++
					for q < end && buf[q] >= 'a' && buf[q] <= 'z' {
						q++
					}
					if q >= end || buf[q] != '-' {
						ok = false
						break
					}
					q++
					if q >= end || !isDig(buf[q]) {
						ok = false
						break
					}
					for q < end && isDig(buf[q]) {
						q++
					}
					if q >= end || buf[q] != ' ' {
						ok = false
						break
					}
					q++

					rem := end - q
					if rem >= 4 && buf[q] == 'G' && buf[q+1] == 'E' && buf[q+2] == 'T' && buf[q+3] == ' ' {
						q += 4
					} else if rem >= 5 && buf[q] == 'P' && buf[q+1] == 'O' && buf[q+2] == 'S' && buf[q+3] == 'T' && buf[q+4] == ' ' {
						q += 5
					} else if rem >= 4 && buf[q] == 'P' && buf[q+1] == 'U' && buf[q+2] == 'T' && buf[q+3] == ' ' {
						q += 4
					} else if rem >= 7 && buf[q] == 'D' && buf[q+1] == 'E' && buf[q+2] == 'L' && buf[q+3] == 'E' && buf[q+4] == 'T' && buf[q+5] == 'E' && buf[q+6] == ' ' {
						q += 7
					} else if rem >= 6 && buf[q] == 'P' && buf[q+1] == 'A' && buf[q+2] == 'T' && buf[q+3] == 'C' && buf[q+4] == 'H' && buf[q+5] == ' ' {
						q += 6
					} else {
						ok = false
						break
					}

					if q >= end || buf[q] != '/' {
						ok = false
						break
					}
					pathStart = q
					for q < end && isPathCh(buf[q]) {
						q++
					}
					pathEnd = q
					if q < end && buf[q] == '?' {
						q++
						for q < end && buf[q] != ' ' {
							q++
						}
					}
					if q >= end || buf[q] != ' ' {
						ok = false
						break
					}
					q++
					if end-q < 4 || !isDig(buf[q]) || !isDig(buf[q+1]) || !isDig(buf[q+2]) || buf[q+3] != ' ' {
						ok = false
						break
					}
					statusClass = int(buf[q] - '0')
					q += 4
					if q >= end || !isDig(buf[q]) {
						ok = false
						break
					}
					for q < end && isDig(buf[q]) {
						q++
					}
					if q >= end || buf[q] != 'B' {
						ok = false
						break
					}
					q++
					if q >= end || buf[q] != ' ' {
						ok = false
						break
					}
					q++
					if q >= end || !isDig(buf[q]) {
						ok = false
						break
					}
					v := int32(0)
					for q < end && isDig(buf[q]) {
						v = v*10 + int32(buf[q]-'0')
						q++
					}
					if q >= end || buf[q] != '.' {
						ok = false
						break
					}
					q++
					if q >= end || !isDig(buf[q]) {
						ok = false
						break
					}
					v = v*10 + int32(buf[q]-'0')
					q++
					if end-q < 3 || buf[q] != 'm' || buf[q+1] != 's' || buf[q+2] != ' ' {
						ok = false
						break
					}
					q += 3
					if q >= end || buf[q] != '"' {
						ok = false
						break
					}
					q++
					for q < end && buf[q] != '"' {
						q++
					}
					if q >= end {
						ok = false
						break
					}
					q++
					if q != end {
						ok = false
						break
					}
					lat = v
					break
				}
			}

			if !ok {
				malformed++
			} else {
				statusCount[statusClass]++
				need := (pathEnd-pathStart)*4 + 4
				if need > len(scratch) {
					scratch = make([]byte, need)
				}
				tlen := 0
				t := pathStart
				for t < pathEnd {
					scratch[tlen] = '/'
					tlen++
					t++
					s := t
					digits := true
					nonempty := false
					for t < pathEnd && buf[t] != '/' {
						if !isDig(buf[t]) {
							digits = false
						}
						nonempty = true
						t++
					}
					if nonempty && digits {
						scratch[tlen] = '{'
						scratch[tlen+1] = 'i'
						scratch[tlen+2] = 'd'
						scratch[tlen+3] = '}'
						tlen += 4
					} else {
						tlen += copy(scratch[tlen:], buf[s:t])
					}
				}
				id, found := m[string(scratch[:tlen])]
				if !found {
					id = int32(len(names))
					key := string(scratch[:tlen])
					m[key] = id
					names = append(names, key)
					lists = append(lists, nil)
					maxes = append(maxes, 0)
				}
				lists[id] = append(lists[id], lat)
				if lat > maxes[id] {
					maxes[id] = lat
				}
			}

			start = e + 1
		}
		if start > 0 {
			copy(buf, buf[start:used])
			used -= start
		}
	}

	out := bufio.NewWriterSize(os.Stdout, 4096)
	fmt.Fprintf(out, "lines %d\n", lines)
	fmt.Fprintf(out, "malformed %d\n", malformed)
	for d := 0; d < 10; d++ {
		if statusCount[d] != 0 {
			fmt.Fprintf(out, "status %dxx %d\n", d, statusCount[d])
		}
	}

	order := make([]int, len(names))
	for i := range order {
		order[i] = i
	}
	slices.SortFunc(order, func(a, b int) int {
		ca, cb := len(lists[a]), len(lists[b])
		if ca != cb {
			return cb - ca
		}
		if names[a] < names[b] {
			return -1
		}
		if names[a] > names[b] {
			return 1
		}
		return 0
	})

	top := len(order)
	if top > 10 {
		top = 10
	}
	for k := 0; k < top; k++ {
		idx := order[k]
		v := lists[idx]
		slices.Sort(v)
		cnt := uint64(len(v))
		i50 := int((50*cnt+99)/100) - 1
		i95 := int((95*cnt+99)/100) - 1
		p50, p95, mx := v[i50], v[i95], v[len(v)-1]
		fmt.Fprintf(out, "path %s %d %d.%d %d.%d %d.%d\n",
			names[idx], cnt, p50/10, p50%10, p95/10, p95%10, mx/10, mx%10)
	}
	out.Flush()
}
