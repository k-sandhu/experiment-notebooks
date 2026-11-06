package main

import (
	"bufio"
	"os"
	"strconv"
)

var data []byte
var pos int
var dlen int

func readInt() int {
	b := data
	p := pos
	n := dlen
	for p < n && b[p] <= ' ' {
		p++
	}
	x := 0
	for p < n && b[p] >= '0' && b[p] <= '9' {
		x = x*10 + int(b[p]-'0')
		p++
	}
	pos = p
	return x
}

func main() {
	var err error
	data, err = os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	dlen = len(data)

	var mp [256]int
	for i := range mp {
		mp[i] = -1
	}

	p := pos
	for p < dlen && data[p] <= ' ' {
		p++
	}
	astart := p
	for p < dlen && data[p] > ' ' {
		p++
	}
	A := p - astart
	for i := 0; i < A; i++ {
		mp[data[astart+i]] = i
	}
	pos = p

	insC := make([]int32, A)
	delC := make([]int32, A)
	subC := make([]int32, A*A)
	for i := 0; i < A; i++ {
		insC[i] = int32(readInt())
	}
	for i := 0; i < A; i++ {
		delC[i] = int32(readInt())
	}
	for i := 0; i < A*A; i++ {
		subC[i] = int32(readInt())
	}

	P := readInt()
	p = pos

	sIdx := make([]uint8, 0, 4096)
	tIdx := make([]uint8, 0, 4096)
	insT := make([]int32, 0, 4096)
	prev := make([]int32, 4097)
	cur := make([]int32, 4097)

	out := bufio.NewWriterSize(os.Stdout, 1<<16)
	defer out.Flush()

	var total int64

	for q := 0; q < P; q++ {
		for p < dlen && data[p] <= ' ' {
			p++
		}
		s0 := p
		for p < dlen && data[p] > ' ' {
			p++
		}
		n := p - s0
		if cap(sIdx) < n {
			sIdx = make([]uint8, n)
		} else {
			sIdx = sIdx[:n]
		}
		for i := 0; i < n; i++ {
			sIdx[i] = uint8(mp[data[s0+i]])
		}

		for p < dlen && data[p] <= ' ' {
			p++
		}
		t0 := p
		for p < dlen && data[p] > ' ' {
			p++
		}
		m := p - t0
		if cap(tIdx) < m {
			tIdx = make([]uint8, m)
		} else {
			tIdx = tIdx[:m]
		}
		if cap(insT) < m {
			insT = make([]int32, m)
		} else {
			insT = insT[:m]
		}
		if cap(prev) < m+1 {
			prev = make([]int32, m+1)
			cur = make([]int32, m+1)
		} else {
			prev = prev[:m+1]
			cur = cur[:m+1]
		}
		for j := 0; j < m; j++ {
			c := mp[data[t0+j]]
			tIdx[j] = uint8(c)
			insT[j] = insC[c]
		}

		prev[0] = 0
		for j := 1; j <= m; j++ {
			prev[j] = prev[j-1] + insT[j-1]
		}

		pr := prev
		cu := cur

		for i := 1; i <= n; i++ {
			c := int(sIdx[i-1])
			d := delC[c]
			sr := c * A
			v := pr[0] + d
			cu[0] = v
			for j := 1; j <= m; j++ {
				best := pr[j] + d
				x := v + insT[j-1]
				if x < best {
					best = x
				}
				x = pr[j-1] + subC[sr+int(tIdx[j-1])]
				if x < best {
					best = x
				}
				v = best
				cu[j] = best
			}
			pr, cu = cu, pr
		}

		cost := pr[m]
		total += int64(cost)
		out.WriteString(strconv.Itoa(int(cost)))
		out.WriteByte('\n')
	}

	out.WriteString("total ")
	out.WriteString(strconv.FormatInt(total, 10))
	out.WriteByte('\n')
}
