package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
)

const c1 = 0x9E3779B97F4A7C15
const c2 = 0xBF58476D1CE4E5B9
const c3 = 0x94D049BB133111EB

type result struct {
	spread    uint64
	bumps     uint64
	returns   uint64
	farDist   uint64
	farWalker uint64
}

// SplitMix64 step; all arithmetic wraps modulo 2^64 on uint64.
func next(state uint64) uint64 {
	state += c1
	z := state
	z = (z ^ (z >> 30)) * c2
	z = (z ^ (z >> 27)) * c3
	return z ^ (z >> 31)
}

// advance updates state in place and returns the generated value.
func advance(state *uint64) uint64 {
	*state += c1
	z := *state
	z = (z ^ (z >> 30)) * c2
	z = (z ^ (z >> 27)) * c3
	return z ^ (z >> 31)
}

// Simulate walkers [start, end). The reduction is order-independent, so the
// result does not depend on how walkers are split across goroutines.
func runRange(start, end, L uint64, B int, seed uint64) result {
	var res result
	if start < end {
		res.farWalker = start
	}
	var dx = [4]int{1, -1, 0, 0}
	var dy = [4]int{0, 0, 1, -1}
	for j := start; j < end; j++ {
		state := seed + j
		x, y := 0, 0
		var b, r uint64
		for t := uint64(0); t < L; t++ {
			rnd := advance(&state)
			d := int(rnd >> 62)
			nx := x + dx[d]
			ny := y + dy[d]
			if nx >= -B && nx <= B && ny >= -B && ny <= B {
				x, y = nx, ny
				if x == 0 && y == 0 {
					r++
				}
			} else {
				b++
			}
		}
		res.spread += uint64(x*x + y*y)
		res.bumps += b
		res.returns += r
		dist := uint64(abs(x) + abs(y))
		if dist > res.farDist {
			res.farDist = dist
			res.farWalker = j
		}
	}
	return res
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

func merge(into *result, other result) {
	into.spread += other.spread
	into.bumps += other.bumps
	into.returns += other.returns
	if other.farDist > into.farDist ||
		(other.farDist == into.farDist && other.farWalker < into.farWalker) {
		into.farDist = other.farDist
		into.farWalker = other.farWalker
	}
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, "cannot read", os.Args[1])
		os.Exit(1)
	}
	fields := strings.Fields(string(data))
	J, _ := strconv.ParseUint(fields[0], 10, 64)
	L, _ := strconv.ParseUint(fields[1], 10, 64)
	B, _ := strconv.Atoi(fields[2])
	seed, _ := strconv.ParseUint(fields[3], 10, 64)
	W, _ := strconv.ParseUint(os.Args[2], 10, 64)
	if W < 1 {
		W = 1
	}
	if W > 32 {
		W = 32
	}

	results := make([]result, W)
	var wg sync.WaitGroup
	for i := uint64(0); i < W; i++ {
		start := i * J / W
		end := (i + 1) * J / W
		wg.Add(1)
		go func(i, start, end uint64) {
			defer wg.Done()
			results[i] = runRange(start, end, L, B, seed)
		}(i, start, end)
	}
	wg.Wait()

	total := results[0]
	for i := uint64(1); i < W; i++ {
		merge(&total, results[i])
	}

	fmt.Println("spread", total.spread)
	fmt.Println("bumps", total.bumps)
	fmt.Println("returns", total.returns)
	fmt.Println("farthest", total.farWalker, total.farDist)
}
