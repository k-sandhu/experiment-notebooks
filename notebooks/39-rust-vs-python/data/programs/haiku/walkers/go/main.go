// Random walkers: J independent SplitMix64-driven walks inside a box, spread over WORKERS goroutines.
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
)

// SplitMix64 increment. uint64 arithmetic wraps on overflow.
const gamma uint64 = 0x9E3779B97F4A7C15

// Totals for one contiguous range of walkers.
type partial struct {
	spread    uint64
	bumps     int64
	returns   int64
	farDist   int64
	farWalker int64
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: solution INPUT_PATH [WORKERS]")
		os.Exit(2)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fields := strings.Fields(string(data))
	walkers, _ := strconv.ParseInt(fields[0], 10, 64)
	steps, _ := strconv.ParseInt(fields[1], 10, 64)
	box, _ := strconv.ParseInt(fields[2], 10, 64)
	seed, _ := strconv.ParseUint(fields[3], 10, 64)

	workers := 1
	if len(os.Args) >= 3 {
		if w, err := strconv.Atoi(os.Args[2]); err == nil {
			workers = w
		}
	}
	workers = max(1, min(workers, int(max(walkers, 1))))

	// Worker w handles the contiguous walkers [first, last).
	parts := make([]partial, workers)
	var wg sync.WaitGroup
	for w := range workers {
		first := walkers * int64(w) / int64(workers)
		last := walkers * int64(w+1) / int64(workers)
		wg.Add(1)
		go func() {
			defer wg.Done()
			parts[w] = walkRange(seed, steps, box, first, last)
		}()
	}
	wg.Wait()

	// Parts are in walker order, so the first part holding the maximum also holds the smallest index.
	total := partial{farDist: -1}
	for _, part := range parts {
		total.spread += part.spread
		total.bumps += part.bumps
		total.returns += part.returns
		if part.farDist > total.farDist {
			total.farDist = part.farDist
			total.farWalker = part.farWalker
		}
	}
	if total.farDist < 0 {
		total.farDist = 0
	}

	fmt.Fprintf(os.Stdout, "spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n",
		total.spread, total.bumps, total.returns, total.farWalker, total.farDist)
}

func walkRange(seed uint64, steps, box, first, last int64) partial {
	acc := partial{farDist: -1}
	for j := first; j < last; j++ {
		walkOne(seed, steps, box, j, &acc)
	}
	return acc
}

// Runs walker j to the end of its steps and folds its result into acc.
// The direction is computed arithmetically rather than with a switch, so the
// unpredictable random choice never causes a branch misprediction.
func walkOne(seed uint64, steps, box, j int64, acc *partial) {
	state := seed + uint64(j)
	var x, y, bumps, returns int64
	for i := int64(0); i < steps; i++ {
		state += gamma
		z := state
		z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
		z = (z ^ (z >> 27)) * 0x94D049BB133111EB
		// z ^ (z >> 31) has the same top two bits as z, so the final mix is skipped.
		d := z >> 62
		isY := int64(d >> 1)
		sign := 1 - 2*int64(d&1)
		nx := x + sign*(1-isY)
		ny := y + sign*isY
		if nx < -box || nx > box || ny < -box || ny > box {
			bumps++
		} else {
			x, y = nx, ny
			if (x | y) == 0 {
				returns++
			}
		}
	}
	dist := abs(x) + abs(y)
	acc.spread += uint64(x*x + y*y)
	acc.bumps += bumps
	acc.returns += returns
	// Walkers are visited in increasing order, so a strict comparison keeps the smallest index on a tie.
	if dist > acc.farDist {
		acc.farDist = dist
		acc.farWalker = j
	}
}

func abs(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}
