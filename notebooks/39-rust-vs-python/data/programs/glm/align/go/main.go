package main

import (
	"os"
	"strconv"
)

var data []byte
var pos int
var tokStart, tokLen int

func isWs(c byte) bool {
	return c == ' ' || c == '\n' || c == '\r' || c == '\t'
}

func skipWs() {
	for pos < len(data) && isWs(data[pos]) {
		pos++
	}
}

func nextInt() int64 {
	skipWs()
	neg := false
	if pos < len(data) && (data[pos] == '-' || data[pos] == '+') {
		neg = data[pos] == '-'
		pos++
	}
	var v int64
	for pos < len(data) && data[pos] >= '0' && data[pos] <= '9' {
		v = v*10 + int64(data[pos]-'0')
		pos++
	}
	if neg {
		return -v
	}
	return v
}

func nextToken() {
	skipWs()
	tokStart = pos
	for pos < len(data) && !isWs(data[pos]) {
		pos++
	}
	tokLen = pos - tokStart
}

var rowBuf = make([]int32, 64)
var tIdxBuf = make([]int32, 64)
var insTBuf = make([]int32, 64)

func solve(sStart, sLen, tStart, tLen int, idx *[256]int16, ins, del, sub []int32) int64 {
	n, m := sLen, tLen
	row := rowBuf
	if len(row) < m+1 {
		row = make([]int32, m+1)
		rowBuf = row
	}
	tIdx, insT := tIdxBuf, insTBuf
	if len(tIdx) < m {
		tIdx = make([]int32, m)
		tIdxBuf = tIdx
		insT = make([]int32, m)
		insTBuf = insT
	}
	for j := 0; j < m; j++ {
		c := idx[data[tStart+j]]
		tIdx[j] = int32(c)
		insT[j] = ins[c]
	}

	_ = row[m]
	row[0] = 0
	for j := 0; j < m; j++ {
		row[j+1] = row[j] + insT[j]
	}

	for i := 0; i < n; i++ {
		si := idx[data[sStart+i]]
		dl := del[si]
		subr := sub[si<<5 : si<<5+26]
		diag := row[0]
		row[0] = diag + dl
		for j := 0; j < m; j++ {
			up := row[j+1]
			v := up + dl
			x := row[j] + insT[j]
			if x < v {
				v = x
			}
			x = diag + subr[tIdx[j]]
			if x < v {
				v = x
			}
			row[j+1] = v
			diag = up
		}
	}
	return int64(row[m])
}

func main() {
	data, _ = os.ReadFile(os.Args[1])
	pos = 0

	nextToken()
	A := tokLen
	var idx [256]int16
	for i := range idx {
		idx[i] = -1
	}
	for i := 0; i < A; i++ {
		idx[data[tokStart+i]] = int16(i)
	}

	ins := make([]int32, A)
	del := make([]int32, A)
	sub := make([]int32, A<<5) // stride 32 rows
	for i := 0; i < A; i++ {
		ins[i] = int32(nextInt())
	}
	for i := 0; i < A; i++ {
		del[i] = int32(nextInt())
	}
	for i := 0; i < A; i++ {
		for j := 0; j < A; j++ {
			sub[(i<<5)+j] = int32(nextInt())
		}
	}

	P := int(nextInt())

	out := make([]byte, 0, P*13+16)
	var total int64
	for q := 0; q < P; q++ {
		nextToken()
		sStart, n := tokStart, tokLen
		nextToken()
		tStart, m := tokStart, tokLen
		cost := solve(sStart, n, tStart, m, &idx, ins, del, sub)
		total += cost
		out = strconv.AppendInt(out, cost, 10)
		out = append(out, '\n')
	}
	out = append(out, "total "...)
	out = strconv.AppendInt(out, total, 10)
	out = append(out, '\n')
	os.Stdout.Write(out)
}
