package main

import (
	"os"
	"strconv"
)

func main() {
	b, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	p := 0
	skipWs := func() {
		for p < len(b) && b[p] <= ' ' {
			p++
		}
	}
	nextInt := func() int {
		skipWs()
		v := 0
		for p < len(b) && b[p] >= '0' && b[p] <= '9' {
			v = v*10 + int(b[p]-'0')
			p++
		}
		return v
	}
	skipWs()
	var code [256]int32
	A := 0
	for p < len(b) && b[p] > ' ' {
		code[b[p]] = int32(A)
		A++
		p++
	}
	ins := make([]int32, A)
	del := make([]int32, A)
	sub := make([]int32, A*A+1)
	for i := 0; i < A; i++ {
		ins[i] = int32(nextInt())
	}
	for i := 0; i < A; i++ {
		del[i] = int32(nextInt())
	}
	for i := 0; i < A*A; i++ {
		sub[i] = int32(nextInt())
	}
	P := nextInt()

	var prev, cur, tc, insT []int32
	out := make([]byte, 0, P*8+32)
	var total int64
	for q := 0; q < P; q++ {
		skipWs()
		s := p
		for p < len(b) && b[p] > ' ' {
			p++
		}
		n := p - s
		skipWs()
		t := p
		for p < len(b) && b[p] > ' ' {
			p++
		}
		m := p - t
		if len(tc) < m+1 {
			prev = make([]int32, m+1)
			cur = make([]int32, m+1)
			tc = make([]int32, m+1)
			insT = make([]int32, m+1)
		}
		for j := 1; j <= m; j++ {
			c := code[b[t+j-1]]
			tc[j] = c
			insT[j] = ins[c]
		}
		pv, cu := prev[:m+1], cur[:m+1]
		tcs := tc[:m+1]
		its := insT[:m+1]
		pv[0] = 0
		for j := 1; j <= m; j++ {
			pv[j] = pv[j-1] + its[j]
		}
		for i := 1; i <= n; i++ {
			a := int(code[b[s+i-1]])
			d := del[a]
			sr := sub[a*A : a*A+A]
			left := pv[0] + d
			cu[0] = left
			cu = cu[:m+1]
			pv = pv[:m+1]
			for j := 1; j < len(cu); j++ {
				v := pv[j] + d
				w := pv[j-1] + sr[tcs[j]]
				if w < v {
					v = w
				}
				l := left + its[j]
				if l < v {
					v = l
				}
				left = v
				cu[j] = v
			}
			pv, cu = cu, pv
		}
		r := int64(pv[m])
		total += r
		out = strconv.AppendInt(out, r, 10)
		out = append(out, '\n')
	}
	out = append(out, "total "...)
	out = strconv.AppendInt(out, total, 10)
	out = append(out, '\n')
	os.Stdout.Write(out)
}
