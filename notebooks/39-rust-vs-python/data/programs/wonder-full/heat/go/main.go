package main

import (
	"fmt"
	"os"
)

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	pos := 0
	parse := func() int {
		for pos < len(data) && (data[pos] < '0' || data[pos] > '9') {
			pos++
		}
		v := 0
		for pos < len(data) && data[pos] >= '0' && data[pos] <= '9' {
			v = v*10 + int(data[pos]-'0')
			pos++
		}
		return v
	}
	H, W, S := parse(), parse(), parse()
	for pos < len(data) && data[pos] != '\n' {
		pos++
	}
	if pos < len(data) {
		pos++
	}
	N := H * W
	grid := make([]byte, N)
	gi := 0
	for q := pos; q < len(data) && gi < N; q++ {
		c := data[q]
		if c == '.' || c == '#' || (c >= '1' && c <= '9') {
			grid[gi] = c
			gi++
		}
	}

	cur := make([]int32, N)
	nxt := make([]int32, N)
	for i, c := range grid {
		if c >= '1' && c <= '9' {
			v := int32(1000 * int(c-'0'))
			cur[i] = v
			nxt[i] = v
		}
	}

	runs := make([]int, 0, H*4)
	spec := make([]int, 0, 1024)
	openIdx := make([]int, 0, N)
	for r := 0; r < H; r++ {
		runStart := -1
		for c := 0; c < W; c++ {
			i := r*W + c
			if grid[i] != '.' {
				if runStart >= 0 {
					runs = append(runs, runStart, i-runStart)
					runStart = -1
				}
				continue
			}
			openIdx = append(openIdx, i)
			interior := r > 0 && r < H-1 && c > 0 && c < W-1 &&
				grid[i-W] != '#' && grid[i+W] != '#' && grid[i-1] != '#' && grid[i+1] != '#'
			if interior {
				if runStart < 0 {
					runStart = i
				}
			} else {
				if runStart >= 0 {
					runs = append(runs, runStart, i-runStart)
					runStart = -1
				}
				up, dn, lf, rt := i, i, i, i
				if r > 0 && grid[i-W] != '#' {
					up = i - W
				}
				if r < H-1 && grid[i+W] != '#' {
					dn = i + W
				}
				if c > 0 && grid[i-1] != '#' {
					lf = i - 1
				}
				if c < W-1 && grid[i+1] != '#' {
					rt = i + 1
				}
				spec = append(spec, i, up, dn, lf, rt)
			}
		}
		if runStart >= 0 {
			runs = append(runs, runStart, r*W+W-runStart)
		}
	}

	for step := 0; step < S; step++ {
		for ri := 0; ri < len(runs); ri += 2 {
			start, n := runs[ri], runs[ri+1]
			up := cur[start-W : start-W+n]
			mid := cur[start : start+n]
			dn := cur[start+W : start+W+n]
			lf := cur[start-1 : start-1+n]
			rt := cur[start+1 : start+1+n]
			out := nxt[start : start+n]
			for k, v := range mid {
				out[k] = (4*v + up[k] + dn[k] + lf[k] + rt[k]) >> 3
			}
		}
		for si := 0; si < len(spec); si += 5 {
			i := spec[si]
			nxt[i] = (4*cur[i] + cur[spec[si+1]] + cur[spec[si+2]] + cur[spec[si+3]] + cur[spec[si+4]]) >> 3
		}
		cur, nxt = nxt, cur
	}

	var sum, checksum int64
	best := int32(-1)
	bestIdx := 0
	if len(openIdx) > 0 {
		bestIdx = openIdx[0]
	}
	for _, i := range openIdx {
		v := cur[i]
		sum += int64(v)
		checksum += int64(v) * int64(i+1)
		if v > best {
			best = v
			bestIdx = i
		}
	}
	if best < 0 {
		best = 0
	}
	br, bc := 0, 0
	if W > 0 {
		br, bc = bestIdx/W, bestIdx%W
	}
	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n", sum, best, br, bc, checksum)
}
