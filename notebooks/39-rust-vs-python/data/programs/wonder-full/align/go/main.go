package main

import (
	"os"
	"strconv"
	"strings"
)

var data []byte
var pos int

func isWs(c byte) bool { return c == ' ' || c == '\n' || c == '\r' || c == '\t' }

func skipWs() {
	for pos < len(data) && isWs(data[pos]) {
		pos++
	}
}

func nextToken() (int, int) {
	skipWs()
	start := pos
	for pos < len(data) && !isWs(data[pos]) {
		pos++
	}
	return start, pos - start
}

func nextInt() int {
	skipWs()
	v := 0
	for pos < len(data) && data[pos] >= '0' && data[pos] <= '9' {
		v = v*10 + int(data[pos]-'0')
		pos++
	}
	return v
}

func main() {
	var err error
	data, err = os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	aStart, A := nextToken()
	var idx [256]int32
	for i := 0; i < A; i++ {
		idx[data[aStart+i]] = int32(i)
	}
	ins := make([]int32, A)
	del := make([]int32, A)
	sub := make([]int32, A*A)
	for i := range ins {
		ins[i] = int32(nextInt())
	}
	for i := range del {
		del[i] = int32(nextInt())
	}
	for i := range sub {
		sub[i] = int32(nextInt())
	}
	P := nextInt()

	var out strings.Builder
	out.Grow(P*8 + 32)
	var total int64
	var sIdx, tIdx []int32
	var prev, curr, colIns, subCols []int32

	for p := 0; p < P; p++ {
		sStart, sLen := nextToken()
		tStart, tLen := nextToken()
		var ans int64
		equal := sLen == tLen
		if equal {
			for i := 0; i < sLen; i++ {
				if data[sStart+i] != data[tStart+i] {
					equal = false
					break
				}
			}
		}
		if equal {
			ans = 0
		} else {
			if cap(sIdx) < sLen {
				sIdx = make([]int32, sLen)
			}
			sIdx = sIdx[:sLen]
			if cap(tIdx) < tLen {
				tIdx = make([]int32, tLen)
			}
			tIdx = tIdx[:tLen]
			for i := 0; i < sLen; i++ {
				sIdx[i] = idx[data[sStart+i]]
			}
			for i := 0; i < tLen; i++ {
				tIdx[i] = idx[data[tStart+i]]
			}

			var rowStr, colStr, rowCost, colCost []int32
			var R, C int
			transposed := false
			if tLen <= sLen {
				rowStr, colStr, R, C = sIdx, tIdx, sLen, tLen
				rowCost, colCost = del, ins
			} else {
				rowStr, colStr, R, C = tIdx, sIdx, tLen, sLen
				rowCost, colCost = ins, del
				transposed = true
			}

			if cap(colIns) < C+1 {
				colIns = make([]int32, C+1)
			}
			colIns = colIns[:C+1]
			for j := 0; j < C; j++ {
				colIns[j+1] = colCost[colStr[j]]
			}

			if cap(subCols) < A*C {
				subCols = make([]int32, A*C)
			}
			subCols = subCols[:A*C]
			if !transposed {
				for a := 0; a < A; a++ {
					base, sbase := a*C, a*A
					for j := 0; j < C; j++ {
						subCols[base+j] = sub[sbase+int(colStr[j])]
					}
				}
			} else {
				for b := 0; b < A; b++ {
					base := b * C
					for j := 0; j < C; j++ {
						subCols[base+j] = sub[int(colStr[j])*A+b]
					}
				}
			}

			if cap(prev) < C+1 {
				prev = make([]int32, C+1)
				curr = make([]int32, C+1)
			}
			prev = prev[:C+1]
			curr = curr[:C+1]
			prev[0] = 0
			for j := 1; j <= C; j++ {
				prev[j] = prev[j-1] + colIns[j]
			}

			for i := 0; i < R; i++ {
				rc := rowStr[i]
				d := rowCost[rc]
				sc := subCols[int(rc)*C : int(rc)*C+C]
				left := prev[0] + d
				curr[0] = left
				diag := prev[0]
				for j := 1; j <= C; j++ {
					up := prev[j]
					best := min(min(diag+sc[j-1], up+d), left+colIns[j])
					curr[j] = best
					diag = up
					left = best
				}
				prev, curr = curr, prev
			}
			ans = int64(prev[C])
		}
		total += ans
		out.WriteString(strconv.FormatInt(ans, 10))
		out.WriteByte('\n')
	}
	out.WriteString("total ")
	out.WriteString(strconv.FormatInt(total, 10))
	out.WriteByte('\n')
	os.Stdout.WriteString(out.String())
}
