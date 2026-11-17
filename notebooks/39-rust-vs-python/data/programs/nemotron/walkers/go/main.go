package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
)

const C = 0x9E3779B97F4A7C15
const M1 = 0xBF58476D1CE4E5B9
const M2 = 0x94D049BB133111EB

type result struct {
	spread, bumps, returns, farDist, farIdx uint64
}

// Simulate walkers [start, end) and return partial results.
func runChunk(start, end, L, B, seed uint64) result {
	var r result
	r.farIdx = start
	var b int64 = int64(B)
	for j := start; j < end; j++ {
		state := seed + j // (SEED + j) mod 2^64
		var x, y int64
		var b2, r2 uint64
		for s := L; s != 0; s-- {
			state += C
			z := state
			z ^= z >> 30
			z *= M1
			z ^= z >> 27
			z *= M2
			v := z ^ (z >> 31)
			d := v >> 62
			bumped := false
			switch d {
			case 0:
				if x < b {
					x++
				} else {
					bumped = true
				}
			case 1:
				if x > -b {
					x--
				} else {
					bumped = true
				}
			case 2:
				if y < b {
					y++
				} else {
					bumped = true
				}
			default:
				if y > -b {
					y--
				} else {
					bumped = true
				}
			}
			if bumped {
				b2++
			} else if x == 0 && y == 0 {
				r2++
			}
		}
		r.spread += uint64(x)*uint64(x) + uint64(y)*uint64(y)
		r.bumps += b2
		r.returns += r2
		dist := uint64(abs64(x)) + uint64(abs64(y))
		// Strictly greater keeps the smallest walker index on ties.
		if dist > r.farDist {
			r.farDist = dist
			r.farIdx = j
		}
	}
	return r
}

func abs64(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}

func parseU64(s string) uint64 {
	v, _ := strconv.ParseUint(s, 10, 64)
	return v
}

func main() {
	if len(os.Args) < 3 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	parts := strings.Fields(string(data))
	if len(parts) < 4 {
		os.Exit(1)
	}
	J := parseU64(parts[0])
	L := parseU64(parts[1])
	B := parseU64(parts[2])
	seed := parseU64(parts[3])

	workers := parseU64(os.Args[2])
	if workers < 1 {
		workers = 1
	}
	var nThreads int
	if J == 0 {
		nThreads = 0
	} else if workers < uint64(J) {
		nThreads = int(workers)
	} else {
		nThreads = int(J)
	}

	results := make([]result, nThreads)
	if nThreads > 0 {
		var wg sync.WaitGroup
		chunk := (J + uint64(nThreads) - 1) / uint64(nThreads)
		for i := 0; i < nThreads; i++ {
			start := uint64(i) * chunk
			end := start + chunk
			if end > J {
				end = J
			}
			wg.Add(1)
			go func(i int, start, end uint64) {
				defer wg.Done()
				results[i] = runChunk(start, end, L, B, seed)
			}(i, start, end)
		}
		wg.Wait()
	}

	var spread, bumps, returns, farDist, farIdx uint64
	for i := 0; i < nThreads; i++ {
		r := results[i]
		spread += r.spread
		bumps += r.bumps
		returns += r.returns
		if r.farDist > farDist || (r.farDist == farDist && r.farIdx < farIdx) {
			farDist = r.farDist
			farIdx = r.farIdx
		}
	}

	fmt.Println("spread", spread)
	fmt.Println("bumps", bumps)
	fmt.Println("returns", returns)
	fmt.Println("farthest", farIdx, farDist)
}
