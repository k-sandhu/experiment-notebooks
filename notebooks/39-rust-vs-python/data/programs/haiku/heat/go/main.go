package main

// Heat on a grid (see SPEC.md).
//
// The grid is stored padded with a one-cell border of zeros, row stride W + 2, so every
// neighbour lookup is a plain offset. Walls and border cells always hold 0, so a wall
// neighbour contributes 0 and the "use own old value" rule becomes (8 - valid) * old.

import (
	"fmt"
	"os"
)

// step performs one simulation step over the flat index range [begin, end).
// mask is -1 for open cells and 0 otherwise; fixed holds the constant value of sources.
// The re-slicing gives the compiler equal-length views, so the loop body has no bounds checks.
func step(cur, nxt, mult, mask, fixed []int32, begin, end, stride int) {
	o := nxt[begin:end]
	n := len(o)
	c := cur[begin:end][:n]
	l := cur[begin-1 : end-1][:n]
	r := cur[begin+1 : end+1][:n]
	u := cur[begin-stride : end-stride][:n]
	d := cur[begin+stride : end+stride][:n]
	m := mult[begin:end][:n]
	k := mask[begin:end][:n]
	f := fixed[begin:end][:n]
	for i := range o {
		sum := m[i]*c[i] + l[i] + r[i] + u[i] + d[i]
		o[i] = ((sum >> 3) & k[i]) | f[i]
	}
}

func isCell(ch byte) bool {
	return ch == '.' || ch == '#' || (ch >= '1' && ch <= '9')
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: solution INPUT_PATH")
		os.Exit(2)
	}
	buf, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	p := 0
	readInt := func() int64 {
		for p < len(buf) && (buf[p] < '0' || buf[p] > '9') {
			p++
		}
		var v int64
		for p < len(buf) && buf[p] >= '0' && buf[p] <= '9' {
			v = v*10 + int64(buf[p]-'0')
			p++
		}
		return v
	}
	H := int(readInt())
	W := int(readInt())
	S := readInt()

	P := W + 2
	N := (H + 2) * P
	kind := make([]uint8, N) // 0 = wall or border, 1 = open, 2 = source
	mult := make([]int32, N)
	mask := make([]int32, N)
	fixed := make([]int32, N)

	for r := 1; r <= H; r++ {
		for c := 1; c <= W; c++ {
			for p < len(buf) && !isCell(buf[p]) {
				p++
			}
			if p >= len(buf) {
				break
			}
			ch := buf[p]
			p++
			i := r*P + c
			if ch == '.' {
				kind[i] = 1
			} else if ch != '#' {
				kind[i] = 2
				fixed[i] = int32(1000 * int(ch-'0'))
			}
		}
	}

	for r := 1; r <= H; r++ {
		for c := 1; c <= W; c++ {
			i := r*P + c
			if kind[i] == 1 {
				valid := int32(0)
				for _, j := range [4]int{i - 1, i + 1, i - P, i + P} {
					if kind[j] != 0 {
						valid++
					}
				}
				mult[i] = 8 - valid
				mask[i] = -1
			}
		}
	}

	cur := make([]int32, N)
	nxt := make([]int32, N)
	copy(cur, fixed) // sources start at their fixed value
	copy(nxt, fixed)
	rowsBegin := P
	rowsEnd := (H + 1) * P
	for s := int64(0); s < S; s++ {
		step(cur, nxt, mult, mask, fixed, rowsBegin, rowsEnd, P)
		cur, nxt = nxt, cur
	}

	var total, checksum, bestV int64 = 0, 0, -1
	bestR, bestC := -1, -1
	for r := 0; r < H; r++ {
		for c := 0; c < W; c++ {
			i := (r+1)*P + c + 1
			if kind[i] != 1 {
				continue
			}
			v := int64(cur[i])
			total += v
			if v > bestV {
				bestV = v
				bestR = r
				bestC = c
			}
			checksum += v * int64(r*W+c+1)
		}
	}

	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n", total, bestV, bestR, bestC, checksum)
}
