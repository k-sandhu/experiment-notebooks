package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	fields := strings.Fields(string(data))
	pos := 0

	next := func() string {
		s := fields[pos]
		pos++
		return s
	}
	nextInt := func() int {
		s := fields[pos]
		pos++
		v := 0
		neg := false
		for i := 0; i < len(s); i++ {
			if s[i] == '-' { neg = true; continue }
			v = v*10 + int(s[i]-'0')
		}
		if neg { v = -v }
		return v
	}

	alphabet := next()
	A := len(alphabet)

	charIndex := [26]int{}
	for i := range charIndex { charIndex[i] = -1 }
	for i := 0; i < A; i++ { charIndex[alphabet[i]-'A'] = i }

	ins := make([]int, A)
	del := make([]int, A)
	for i := 0; i < A; i++ { ins[i] = nextInt() }
	for i := 0; i < A; i++ { del[i] = nextInt() }
	sub := make([][]int, A)
	for i := 0; i < A; i++ {
		sub[i] = make([]int, A)
		for j := 0; j < A; j++ { sub[i][j] = nextInt() }
	}

	P := nextInt()

	var prev, cur []int
	sIdx := make([]int, 0)
	tIdx := make([]int, 0)
	insT := make([]int, 0)

	total := 0
	out := bufio.NewWriter(os.Stdout)

	for pair := 0; pair < P; pair++ {
		s := next()
		t := next()
		n := len(s)
		m := len(t)

		if cap(sIdx) < n { sIdx = make([]int, n) }
		sIdx = sIdx[:n]
		for i := 0; i < n; i++ { sIdx[i] = charIndex[s[i]-'A'] }
		if cap(tIdx) < m { tIdx = make([]int, m) }
		tIdx = tIdx[:m]
		if cap(insT) < m { insT = make([]int, m) }
		insT = insT[:m]
		for j := 0; j < m; j++ {
			tIdx[j] = charIndex[t[j]-'A']
			insT[j] = ins[tIdx[j]]
		}

		if len(prev) < m+1 {
			prev = make([]int, m+1)
			cur = make([]int, m+1)
		}
		prev = prev[:m+1]
		cur = cur[:m+1]

		prev[0] = 0
		for j := 1; j <= m; j++ { prev[j] = prev[j-1] + insT[j-1] }

		for i := 1; i <= n; i++ {
			si := sIdx[i-1]
			delSi := del[si]
			subRow := sub[si]
			cur[0] = prev[0] + delSi
			for j := 1; j <= m; j++ {
				tj := tIdx[j-1]
				up := prev[j] + delSi
				left := cur[j-1] + insT[j-1]
				diag := prev[j-1] + subRow[tj]
				best := up
				if left < best { best = left }
				if diag < best { best = diag }
				cur[j] = best
			}
			prev, cur = cur, prev
		}

		cost := prev[m]
		total += cost
		fmt.Fprintln(out, cost)
	}
	fmt.Fprintln(out, "total", total)
	out.Flush()
}
