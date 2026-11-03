package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
)

var dxs = [4]int32{1, -1, 0, 0}
var dys = [4]int32{0, 0, 1, -1}

func walk(seed uint64, j int, L int64, B int32, res []int64) {
	state := seed + uint64(j)
	var x, y int32
	var bumps, returns int64
	span := uint32(2 * B)
	for i := int64(0); i < L; i++ {
		state += 0x9E3779B97F4A7C15
		z := state
		z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
		z = (z ^ (z >> 27)) * 0x94D049BB133111EB
		d := z >> 62
		nx := x + dxs[d]
		ny := y + dys[d]
		if uint32(nx+B) > span || uint32(ny+B) > span {
			bumps++
		} else {
			x, y = nx, ny
			if x|y == 0 {
				returns++
			}
		}
	}
	ax, ay := x, y
	if ax < 0 {
		ax = -ax
	}
	if ay < 0 {
		ay = -ay
	}
	res[j*4] = int64(x)*int64(x) + int64(y)*int64(y)
	res[j*4+1] = bumps
	res[j*4+2] = returns
	res[j*4+3] = int64(ax + ay)
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	p := strings.Fields(string(data))
	J, _ := strconv.Atoi(p[0])
	L, _ := strconv.ParseInt(p[1], 10, 64)
	B, _ := strconv.Atoi(p[2])
	seed, _ := strconv.ParseUint(p[3], 10, 64)
	W, _ := strconv.Atoi(os.Args[2])
	if W < 1 {
		W = 1
	}
	if W > J {
		W = J
	}
	res := make([]int64, J*4)
	var wg sync.WaitGroup
	for w := 0; w < W; w++ {
		wg.Add(1)
		go func(w int) {
			defer wg.Done()
			for j := w; j < J; j += W {
				walk(seed, j, L, int32(B), res)
			}
		}(w)
	}
	wg.Wait()
	var spread, bumps, returns, bestD int64 = 0, 0, 0, -1
	bestJ := 0
	for j := 0; j < J; j++ {
		spread += res[j*4]
		bumps += res[j*4+1]
		returns += res[j*4+2]
		if res[j*4+3] > bestD {
			bestD = res[j*4+3]
			bestJ = j
		}
	}
	fmt.Printf("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n", spread, bumps, returns, bestJ, bestD)
}
