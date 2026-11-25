package main

import (
	"fmt"
	"os"
)

func readInt(data []byte, pos int) (int, int) {
	for pos < len(data) && data[pos] <= 32 {
		pos++
	}
	sign := 1
	if pos < len(data) && data[pos] == 45 { // '-'
		sign = -1
		pos++
	}
	v := 0
	for pos < len(data) && data[pos] > 32 {
		v = v*10 + int(data[pos]-48)
		pos++
	}
	return sign * v, pos
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	pos := 0

	H, pos := readInt(data, pos)
	W, pos := readInt(data, pos)
	S, pos := readInt(data, pos)

	N := H * W
	grid := make([]byte, N)
	gi := 0
	for gi < N {
		b := data[pos]
		pos++
		if b > 32 {
			grid[gi] = b
			gi++
		}
	}

	cur := make([]int, N)
	nxt := make([]int, N)
	self := make([]int, 0, N)
	up := make([]int, 0, N)
	down := make([]int, 0, N)
	left := make([]int, 0, N)
	right := make([]int, 0, N)

	for r := 0; r < H; r++ {
		base := r * W
		for c := 0; c < W; c++ {
			i := base + c
			b := grid[i]
			if b == 46 { // '.'
				self = append(self, i)
				if r > 0 && grid[i-W] != 35 {
					up = append(up, i-W)
				} else {
					up = append(up, i)
				}
				if r+1 < H && grid[i+W] != 35 {
					down = append(down, i+W)
				} else {
					down = append(down, i)
				}
				if c > 0 && grid[i-1] != 35 {
					left = append(left, i-1)
				} else {
					left = append(left, i)
				}
				if c+1 < W && grid[i+1] != 35 {
					right = append(right, i+1)
				} else {
					right = append(right, i)
				}
			} else if b >= 49 && b <= 57 { // '1'..'9'
				v := 1000 * int(b-48)
				cur[i] = v
				nxt[i] = v
			}
		}
	}

	count := len(self)
	for step := 0; step < S; step++ {
		for k := 0; k < count; k++ {
			i := self[k]
			v := cur[i]
			s := 4*v + cur[up[k]] + cur[down[k]] + cur[left[k]] + cur[right[k]]
			nxt[i] = s >> 3 // all values non-negative
		}
		cur, nxt = nxt, cur
	}

	var total int64
	var checksum int64
	bestV := -1
	bestR := 0
	bestC := 0
	for k := 0; k < count; k++ {
		i := self[k]
		v := cur[i]
		total += int64(v)
		if v > bestV {
			bestV = v
			bestR = i / W
			bestC = i % W
		}
		checksum += int64(v) * int64(i+1)
	}

	fmt.Fprintf(os.Stdout, "sum %d\nmax %d %d %d\nchecksum %d\n",
		total, bestV, bestR, bestC, checksum)
}
