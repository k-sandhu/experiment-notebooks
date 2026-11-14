package main

import (
	"os"
	"strconv"
)

var data []byte
var pos, dlen int

func skipWs() {
	p := pos
	n := dlen
	for p < n && data[p] <= ' ' {
		p++
	}
	pos = p
}

func nextInt() int {
	p := pos
	n := dlen
	for p < n && data[p] <= ' ' {
		p++
	}
	v := 0
	for p < n {
		c := data[p]
		if c < '0' || c > '9' {
			break
		}
		v = v*10 + int(c-'0')
		p++
	}
	pos = p
	return v
}

func main() {
	data, _ = os.ReadFile(os.Args[1])
	dlen = len(data)

	skipWs()
	abStart := pos
	for pos < dlen && data[pos] > ' ' {
		pos++
	}
	A := pos - abStart
	var mp [256]byte
	for i := 0; i < A; i++ {
		mp[data[abStart+i]] = byte(i)
	}

	ins := make([]int, A)
	delc := make([]int, A)
	sub := make([]int, A*A)
	for i := 0; i < A; i++ {
		ins[i] = nextInt()
	}
	for i := 0; i < A; i++ {
		delc[i] = nextInt()
	}
	for i := 0; i < A*A; i++ {
		sub[i] = nextInt()
	}

	P := nextInt()

	s := make([]byte, 0, 1024)
	t := make([]byte, 0, 1024)
	tins := make([]int, 1024)
	row := make([]int, 1024)

	out := make([]byte, 0, 8192)
	total := int64(0)

	for q := 0; q < P; q++ {
		skipWs()
		s = s[:0]
		for pos < dlen && data[pos] > ' ' {
			s = append(s, mp[data[pos]])
			pos++
		}
		skipWs()
		t = t[:0]
		for pos < dlen && data[pos] > ' ' {
			t = append(t, mp[data[pos]])
			pos++
		}

		n := len(s)
		m := len(t)

		same := n == m
		if same {
			for i := 0; i < n; i++ {
				if s[i] != t[i] {
					same = false
					break
				}
			}
		}
		if same {
			out = append(out, '0', '\n')
			continue
		}

		if len(tins) < m {
			tins = make([]int, m*2+1)
		}
		if len(row) < m+1 {
			row = make([]int, (m+1)*2)
		}
		r := row[:m+1]
		ti := tins[:m]

		for j := 0; j < m; j++ {
			ti[j] = ins[t[j]]
		}
		r[0] = 0
		for j := 1; j <= m; j++ {
			r[j] = r[j-1] + ti[j-1]
		}

		for i := 0; i < n; i++ {
			si := int(s[i])
			dc := delc[si]
			srow := sub[si*A : si*A+A]

			diag := r[0]
			left := diag + dc
			r[0] = left

			for j := 1; j <= m; j++ {
				up := r[j]
				a := up + dc
				b := diag + srow[t[j-1]]
				x := left + ti[j-1]
				mn := min(a, b, x)
				diag = up
				r[j] = mn
				left = mn
			}
		}

		cost := r[m]
		total += int64(cost)
		out = strconv.AppendInt(out, int64(cost), 10)
		out = append(out, '\n')
	}

	out = append(out, "total "...)
	out = strconv.AppendInt(out, total, 10)
	out = append(out, '\n')

	os.Stdout.Write(out)
}
