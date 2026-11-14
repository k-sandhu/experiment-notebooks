package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

type cell struct {
	i, a, b, c, d int32
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	f := strings.Fields(string(data))
	H, _ := strconv.Atoi(f[0])
	W, _ := strconv.Atoi(f[1])
	S, _ := strconv.Atoi(f[2])
	rows := f[3 : 3+H]

	n := H * W
	cur := make([]int32, n)
	nxt := make([]int32, n)
	open := make([]bool, n)
	cells := make([]cell, 0, n)

	for r := 0; r < H; r++ {
		row := rows[r]
		for c := 0; c < W; c++ {
			ch := row[c]
			i := r*W + c
			if ch == '#' {
				continue
			}
			open[i] = true
			if ch >= '1' && ch <= '9' {
				v := int32(ch-'0') * 1000
				cur[i] = v
				nxt[i] = v
			}
		}
	}
	for r := 0; r < H; r++ {
		row := rows[r]
		for c := 0; c < W; c++ {
			ch := row[c]
			if ch == '#' || (ch >= '1' && ch <= '9') {
				continue
			}
			i := r*W + c
			cl := cell{i: int32(i), a: int32(i), b: int32(i), c: int32(i), d: int32(i)}
			if r > 0 && open[i-W] {
				cl.a = int32(i - W)
			}
			if r < H-1 && open[i+W] {
				cl.b = int32(i + W)
			}
			if c > 0 && open[i-1] {
				cl.c = int32(i - 1)
			}
			if c < W-1 && open[i+1] {
				cl.d = int32(i + 1)
			}
			cells = append(cells, cl)
		}
	}

	for s := 0; s < S; s++ {
		cu := cur
		nx := nxt
		for k := range cells {
			cl := &cells[k]
			nx[cl.i] = (4*cu[cl.i] + cu[cl.a] + cu[cl.b] + cu[cl.c] + cu[cl.d]) >> 3
		}
		cur, nxt = nxt, cur
	}

	var sum, chk int64
	var best int32 = -1
	bestR, bestC := 0, 0
	for r := 0; r < H; r++ {
		for c := 0; c < W; c++ {
			i := r*W + c
			if !open[i] {
				continue
			}
			v := cur[i]
			sum += int64(v)
			chk += int64(v) * int64(i+1)
			if v > best {
				best = v
				bestR, bestC = r, c
			}
		}
	}
	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n", sum, best, bestR, bestC, chk)
}
