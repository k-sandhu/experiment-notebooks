package main

import (
	"bytes"
	"os"
	"strconv"
)

func nextTok(data []byte, pos int) ([]byte, int) {
	n := len(data)
	for pos < n && data[pos] <= ' ' {
		pos++
	}
	start := pos
	for pos < n && data[pos] > ' ' {
		pos++
	}
	return data[start:pos], pos
}

func atoi(b []byte) int {
	v := 0
	neg := false
	for _, c := range b {
		if c == '-' {
			neg = true
		} else if c >= '0' && c <= '9' {
			v = v*10 + int(c-'0')
		}
	}
	if neg {
		v = -v
	}
	return v
}

// twoRows advances the normalised DP row R by two rows of s at once.
// R[j] holds G[i-1][j] on entry and G[i+1][j] on exit, where
// G[i][j] = D[i][j] - sum(ins of t[1..j]) - sum(del of s[1..i]).
func twoRows(R, wa, wb []int32) {
	n := len(R)
	wa = wa[:n]
	wb = wb[:n]
	var up, c1, c2 int32
	for j := 1; j < n; j++ {
		u := R[j]
		x := min(u, up+wa[j])
		g := min(c1, x)
		y := min(g, c1+wb[j])
		c2 = min(c2, y)
		R[j] = c2
		up = u
		c1 = g
	}
}

func oneRow(R, wa []int32) {
	n := len(R)
	wa = wa[:n]
	var up, c int32
	for j := 1; j < n; j++ {
		u := R[j]
		c = min(c, min(u, up+wa[j]))
		R[j] = c
		up = u
	}
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}

	var tok []byte
	pos := 0
	tok, pos = nextTok(data, pos)

	var idx [256]uint8
	A := 0
	for _, c := range tok {
		if c >= 'A' && c <= 'Z' && A < 26 {
			idx[c] = uint8(A)
			A++
		}
	}

	var ins, del [256]int32
	for i := 0; i < A; i++ {
		tok, pos = nextTok(data, pos)
		ins[i] = int32(atoi(tok))
	}
	for i := 0; i < A; i++ {
		tok, pos = nextTok(data, pos)
		del[i] = int32(atoi(tok))
	}
	// W[c][k] = sub[c][k] - ins[k] - del[c]
	var W [26][32]int32
	for i := 0; i < A; i++ {
		for j := 0; j < A; j++ {
			tok, pos = nextTok(data, pos)
			W[i][j] = int32(atoi(tok)) - ins[j] - del[i]
		}
	}

	tok, pos = nextTok(data, pos)
	P := atoi(tok)

	out := make([]byte, 0, P*12+64)
	var total int64

	var row []int32
	var profBuf []int32
	var tIdx, sIdx []uint8
	var profs [32][]int32

	for p := 0; p < P; p++ {
		var s, t []byte
		s, pos = nextTok(data, pos)
		t, pos = nextTok(data, pos)
		if len(s) == 0 || len(t) == 0 {
			break
		}
		var cost int64
		if !bytes.Equal(s, t) {
			n := len(s)
			m := len(t)
			w := m + 1

			if cap(tIdx) < m {
				tIdx = make([]uint8, m+m/2)
			}
			if cap(sIdx) < n {
				sIdx = make([]uint8, n+n/2)
			}
			ti := tIdx[:m]
			si := sIdx[:n]

			var base int64
			for j, c := range t {
				k := idx[c]
				ti[j] = k
				base += int64(ins[k])
			}
			var present [256]bool
			for i, c := range s {
				k := idx[c]
				si[i] = k
				base += int64(del[k])
				present[k] = true
			}

			if len(row) < w {
				row = make([]int32, w+w/2)
			}
			if len(profBuf) < A*w {
				profBuf = make([]int32, A*(w+w/2))
			}

			for c := 0; c < A; c++ {
				if !present[c] {
					continue
				}
				pr := profBuf[c*w : c*w+w]
				wr := &W[c]
				pr[0] = 0
				dst := pr[1:][:len(ti)]
				for j, k := range ti {
					dst[j] = wr[k&31]
				}
				profs[c] = pr
			}

			R := row[:w]
			clear(R)
			i := 0
			for ; i+1 < n; i += 2 {
				twoRows(R, profs[si[i]&31], profs[si[i+1]&31])
			}
			if i < n {
				oneRow(R, profs[si[i]&31])
			}
			cost = base + int64(R[m])
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
