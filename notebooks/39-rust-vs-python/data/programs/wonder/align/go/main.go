package main

import (
	"os"
	"strconv"
	"strings"
)

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	N := len(data)
	pos := 0

	charIdx := make([]int, 256)
	for i := range charIdx {
		charIdx[i] = -1
	}
	A := 0
	for pos < N && data[pos] != '\n' {
		c := data[pos]
		pos++
		if c >= 'A' && c <= 'Z' {
			charIdx[c] = A
			A++
		}
	}
	if pos < N {
		pos++
	}

	skipWs := func() {
		for pos < N {
			c := data[pos]
			if c == ' ' || c == '\n' || c == '\r' || c == '\t' {
				pos++
			} else {
				break
			}
		}
	}
	parseInt := func() int {
		skipWs()
		v := 0
		for pos < N && data[pos] >= '0' && data[pos] <= '9' {
			v = v*10 + int(data[pos]-'0')
			pos++
		}
		return v
	}

	ins := make([]int32, A)
	del := make([]int32, A)
	sub := make([]int32, A*A)
	for i := 0; i < A; i++ {
		ins[i] = int32(parseInt())
	}
	for i := 0; i < A; i++ {
		del[i] = int32(parseInt())
	}
	for i := 0; i < A*A; i++ {
		sub[i] = int32(parseInt())
	}
	P := parseInt()

	strs := make([][]uint8, 2*P)
	maxLen := 0
	for k := 0; k < 2*P; k++ {
		skipWs()
		start := pos
		for pos < N {
			c := data[pos]
			if c == ' ' || c == '\n' || c == '\r' || c == '\t' {
				break
			}
			pos++
		}
		length := pos - start
		s := make([]uint8, length)
		for i := 0; i < length; i++ {
			s[i] = uint8(charIdx[data[start+i]])
		}
		if length > maxLen {
			maxLen = length
		}
		strs[k] = s
	}

	prev := make([]int32, maxLen+1)
	cur := make([]int32, maxLen+1)
	insT := make([]int32, maxLen)

	var out strings.Builder
	out.Grow(P * 12)
	var total int64

	for p := 0; p < P; p++ {
		s := strs[2*p]
		t := strs[2*p+1]
		n := len(s)
		m := len(t)
		for j := 0; j < m; j++ {
			insT[j] = ins[t[j]]
		}
		prev[0] = 0
		for j := 0; j < m; j++ {
			prev[j+1] = prev[j] + insT[j]
		}
		for i := 0; i < n; i++ {
			si := s[i]
			dcost := del[si]
			subBase := int(si) * A
			diag := prev[0]
			left := diag + dcost
			cur[0] = left
			for j := 0; j < m; j++ {
				up := prev[j+1]
				a := up + dcost
				b := left + insT[j]
				c := diag + sub[subBase+int(t[j])]
				v := a
				if b < v {
					v = b
				}
				if c < v {
					v = c
				}
				diag = up
				left = v
				cur[j+1] = v
			}
			prev, cur = cur, prev
		}
		ans := prev[m]
		total += int64(ans)
		out.WriteString(strconv.Itoa(int(ans)))
		out.WriteByte('\n')
	}
	out.WriteString("total ")
	out.WriteString(strconv.FormatInt(total, 10))
	out.WriteByte('\n')
	os.Stdout.WriteString(out.String())
}
