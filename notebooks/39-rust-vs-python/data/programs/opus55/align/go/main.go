// Weighted edit distance for many pairs.
//
// With Q[j] = sum of column (insert) costs of C[1..j], the kernels store E[i][j] = D[i][j] - Q[j]:
//   E[i][j] = min(E[i-1][j] + rc, E[i-1][j-1] + adj[j], E[i][j-1]),  adj[j] = M[r][C_j] - cc[C_j]
// so the loop-carried dependency is a single min instead of add+min.
package main

import (
	"os"
	"strconv"
)

func dp32(R []byte, m int, rc *[26]int32, adjFor *[26][]int32, row []int32) int32 {
	row = row[:m+1]
	for j := range row {
		row[j] = 0
	}
	i := 0
	// Two rows per pass: two independent running-min chains and half the row traffic.
	for ; i+1 < len(R); i += 2 {
		d1, d2 := rc[R[i]], rc[R[i+1]]
		adj1 := adjFor[R[i]][:len(row)]
		adj2 := adjFor[R[i+1]][:len(row)]
		diag1 := row[0]
		left1 := diag1 + d1
		left2 := left1 + d2
		row[0] = left2
		for j := 1; j < len(row); j++ {
			up := row[j]
			v1 := min(up+d1, diag1+adj1[j], left1)
			v2 := min(v1+d2, left1+adj2[j], left2)
			row[j] = v2
			diag1 = up
			left1 = v1
			left2 = v2
		}
	}
	if i < len(R) {
		d := rc[R[i]]
		adj := adjFor[R[i]][:len(row)]
		diag := row[0]
		left := diag + d
		row[0] = left
		for j := 1; j < len(row); j++ {
			up := row[j]
			v := min(up+d, diag+adj[j], left)
			row[j] = v
			left = v
			diag = up
		}
	}
	return row[m]
}

func dp64(R []byte, m int, rc *[26]int32, adjFor *[26][]int32) int64 {
	row := make([]int64, m+1)
	for _, a := range R {
		d := int64(rc[a])
		adj := adjFor[a][:len(row)]
		diag := row[0]
		left := diag + d
		row[0] = left
		for j := 1; j < len(row); j++ {
			up := row[j]
			v := min(up+d, diag+int64(adj[j]), left)
			row[j] = v
			left = v
			diag = up
		}
	}
	return row[m]
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	p := 0
	n := len(data)

	var idx [256]int8
	for i := range idx {
		idx[i] = -1
	}
	A := 0
	for p < n && data[p] >= 'A' && data[p] <= 'Z' {
		idx[data[p]] = int8(A)
		A++
		p++
	}
	readInt := func() int64 {
		for p < n && (data[p] < '0' || data[p] > '9') {
			p++
		}
		var v int64
		for p < n && data[p] >= '0' && data[p] <= '9' {
			v = v*10 + int64(data[p]-'0')
			p++
		}
		return v
	}
	readWord := func(w []byte) []byte {
		for p < n && (data[p] < 'A' || data[p] > 'Z') {
			p++
		}
		w = w[:0]
		for p < n && data[p] >= 'A' && data[p] <= 'Z' {
			w = append(w, byte(idx[data[p]]))
			p++
		}
		return w
	}

	var insC, delC [26]int32
	var subM, subT [26][26]int32
	for i := 0; i < A; i++ {
		insC[i] = int32(readInt())
	}
	for i := 0; i < A; i++ {
		delC[i] = int32(readInt())
	}
	for i := 0; i < A; i++ {
		for j := 0; j < A; j++ {
			v := int32(readInt())
			subM[i][j] = v
			subT[j][i] = v
		}
	}
	P := int(readInt())

	var sBuf, tBuf []byte
	var adjStore, row []int32
	var adjFor [26][]int32
	out := make([]byte, 0, P*12+32)
	var total int64

	for k := 0; k < P; k++ {
		sBuf = readWord(sBuf)
		tBuf = readWord(tBuf)
		// Put the longer string on the inner (column) axis: transposing swaps insert/delete
		// and transposes the substitution table, leaving D[n][m] unchanged.
		R, C := sBuf, tBuf
		rc, cc, M := &delC, &insC, &subM
		if len(sBuf) > len(tBuf) {
			R, C = tBuf, sBuf
			rc, cc, M = &insC, &delC, &subT
		}
		m := len(C)

		var used [26]bool
		nUsed := 0
		for _, a := range R {
			if !used[a] {
				used[a] = true
				nUsed++
			}
		}
		stride := m + 1
		if cap(adjStore) < stride*nUsed {
			adjStore = make([]int32, stride*nUsed)
		}
		adjStore = adjStore[:stride*nUsed]
		var Q int64
		for _, c := range C {
			Q += int64(cc[c])
		}
		slot := 0
		for a := 0; a < A; a++ {
			if !used[a] {
				adjFor[a] = nil
				continue
			}
			r := adjStore[slot*stride : (slot+1)*stride]
			slot++
			Ma := &M[a]
			r[0] = 0
			rr := r[1:]
			for j, c := range C {
				rr[j] = Ma[c] - cc[c]
			}
			adjFor[a] = r
		}

		var cost int64
		if int64(len(R)+m+4)*1000 < 1<<30 {
			if cap(row) < m+1 {
				row = make([]int32, m+1)
			}
			cost = int64(dp32(R, m, rc, &adjFor, row)) + Q
		} else {
			cost = dp64(R, m, rc, &adjFor) + Q
		}
		total += cost
		out = strconv.AppendInt(out, cost, 10)
		out = append(out, '\n')
	}
	out = append(out, "total "...)
	out = strconv.AppendInt(out, total, 10)
	out = append(out, '\n')
	os.Stdout.Write(out)
}
