package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	fields := strings.Fields(string(data))
	H, _ := strconv.Atoi(fields[0])
	W, _ := strconv.Atoi(fields[1])
	S, _ := strconv.Atoi(fields[2])

	N0 := H * W
	grid := make([]byte, N0)
	for r := 0; r < H; r++ {
		copy(grid[r*W:(r+1)*W], fields[3+r])
	}

	// Assign compact ids: open cells first (row-major), then sources.
	id := make([]int32, N0)
	gidx := make([]int32, 0, N0)
	m := int32(0)
	for g := 0; g < N0; g++ {
		if grid[g] == '.' {
			id[g] = m
			m++
			gidx = append(gidx, int32(g))
		} else {
			id[g] = -1
		}
	}
	M := int(m)

	var srcVals []uint32
	for g := 0; g < N0; g++ {
		c := grid[g]
		if c >= '1' && c <= '9' {
			id[g] = m
			m++
			srcVals = append(srcVals, uint32(c-'0')*1000)
		}
	}
	N := int(m)

	cur := make([]uint32, N)
	nxt := make([]uint32, N)
	for k, v := range srcVals {
		cur[M+k] = v
		nxt[M+k] = v
	}

	// For each open cell, the index of each neighbour's value source.
	// Open or source neighbours point to their id; walls/outside point to self.
	nb := make([][4]int32, M)
	for i, g32 := range gidx {
		g := int(g32)
		r := g / W
		c := g - r*W
		self := int32(i)
		up, dn, lf, rt := self, self, self, self
		if r > 0 && id[g-W] >= 0 {
			up = id[g-W]
		}
		if r < H-1 && id[g+W] >= 0 {
			dn = id[g+W]
		}
		if c > 0 && id[g-1] >= 0 {
			lf = id[g-1]
		}
		if c < W-1 && id[g+1] >= 0 {
			rt = id[g+1]
		}
		nb[i] = [4]int32{up, dn, lf, rt}
	}

	// Simulation. Values never exceed 9000, so uint32 is safe; /8 on
	// non-negative values is a shift.
	for s := 0; s < S; s++ {
		for i := range nb {
			n := nb[i]
			sum := 4*cur[i] + cur[n[0]] + cur[n[1]] + cur[n[2]] + cur[n[3]]
			nxt[i] = sum >> 3
		}
		cur, nxt = nxt, cur
	}

	var T, K int64
	bestV := int64(-1)
	bestR, bestC := 0, 0
	for i := 0; i < M; i++ {
		v := int64(cur[i])
		T += v
		g := int64(gidx[i])
		K += v * (g + 1)
		if v > bestV {
			bestV = v
			bestR = int(g) / W
			bestC = int(g) % W
		}
	}

	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n", T, bestV, bestR, bestC, K)
}
