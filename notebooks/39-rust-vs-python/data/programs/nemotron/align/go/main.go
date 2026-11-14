package main

import (
	"fmt"
	"os"
)

var (
	data []byte
	pos  int
	lenD int
)

func skipWs() {
	for pos < lenD && data[pos] <= 32 {
		pos++
	}
}

func nextInt() int {
	skipWs()
	x := 0
	for pos < lenD && data[pos] > 32 {
		x = x*10 + int(data[pos]-'0')
		pos++
	}
	return x
}

func readTokenIdx(idx *[256]int) []int {
	skipWs()
	start := pos
	for pos < lenD && data[pos] > 32 {
		pos++
	}
	a := make([]int, pos-start)
	for i := start; i < pos; i++ {
		a[i-start] = idx[data[i]]
	}
	return a
}

func main() {
	data, _ = os.ReadFile(os.Args[1])
	lenD = len(data)

	skipWs()
	alphaStart := pos
	for pos < lenD && data[pos] > 32 {
		pos++
	}
	A := pos - alphaStart

	var idx [256]int
	for i := range idx {
		idx[i] = -1
	}
	for i := 0; i < A; i++ {
		idx[data[alphaStart+i]] = i
	}

	ins := make([]int, A)
	del := make([]int, A)
	sub := make([]int, A*A)
	for i := 0; i < A; i++ {
		ins[i] = nextInt()
	}
	for i := 0; i < A; i++ {
		del[i] = nextInt()
	}
	for i := 0; i < A*A; i++ {
		sub[i] = nextInt()
	}

	P := nextInt()

	var prev, cur []int
	var total int64

	for pair := 0; pair < P; pair++ {
		s := readTokenIdx(&idx)
		t := readTokenIdx(&idx)
		n := len(s)
		m := len(t)

		if len(prev) < m+1 {
			prev = make([]int, m+1)
			cur = make([]int, m+1)
		}

		prev[0] = 0
		for j := 1; j <= m; j++ {
			prev[j] = prev[j-1] + ins[t[j-1]]
		}

		for i := 0; i < n; i++ {
			si := s[i]
			d := del[si]
			base := si * A
			cur[0] = prev[0] + d
			diag := prev[0]
			for j := 1; j <= m; j++ {
				tj := t[j-1]
				best := prev[j] + d
				v := cur[j-1] + ins[tj]
				if v < best {
					best = v
				}
				v = diag + sub[base+tj]
				if v < best {
					best = v
				}
				cur[j] = best
				diag = prev[j]
			}
			prev, cur = cur, prev
		}

		cost := int64(prev[m])
		total += cost
		fmt.Println(cost)
	}
	fmt.Println("total", total)
}
