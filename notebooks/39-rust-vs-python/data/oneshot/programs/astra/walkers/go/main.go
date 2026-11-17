package main

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
	"sync"
)

type result struct {
	spread   int64
	bumps    int64
	returns  int64
	walker   int64
	distance int64
}

func simulate(first, stride, walkers, steps int64, bound, seed uint64) result {
	out := result{distance: -1}
	width := bound << 1

	for j := first; j < walkers; j += stride {
		state := seed + uint64(j)
		position := [2]int64{}
		var bumps, returns int64

		for remaining := steps; remaining > 0; remaining-- {
			state += 0x9E3779B97F4A7C15
			z := state
			z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
			z = (z ^ (z >> 27)) * 0x94D049BB133111EB

			// The final XOR with z >> 31 cannot change the top two bits.
			axis := z >> 63
			delta := int64(1) - int64((z>>62)&1)*2
			next := position[axis] + delta

			if uint64(next)+bound > width {
				bumps++
				continue
			}

			position[axis] = next
			if position[0]|position[1] == 0 {
				returns++
			}
		}

		x, y := position[0], position[1]
		out.spread += x*x + y*y
		out.bumps += bumps
		out.returns += returns

		if x < 0 {
			x = -x
		}
		if y < 0 {
			y = -y
		}
		distance := x + y
		if distance > out.distance {
			out.distance = distance
			out.walker = j
		}
	}

	return out
}

func main() {
	if len(os.Args) != 3 {
		return
	}

	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	workers, err := strconv.Atoi(os.Args[2])
	if err != nil || workers < 1 || workers > 32 {
		return
	}

	offset := 0
	nextUint := func() uint64 {
		for offset < len(data) && data[offset] <= ' ' {
			offset++
		}
		var value uint64
		for offset < len(data) {
			c := data[offset]
			if c < '0' || c > '9' {
				break
			}
			value = value*10 + uint64(c-'0')
			offset++
		}
		return value
	}

	walkers := int64(nextUint())
	steps := int64(nextUint())
	bound := nextUint()
	seed := nextUint()

	// No coordinate can exceed the number of steps in magnitude.
	if bound > uint64(steps) {
		bound = uint64(steps)
	}

	runtime.GOMAXPROCS(workers)
	results := make([]result, workers)
	var wg sync.WaitGroup
	wg.Add(workers)

	for w := 0; w < workers; w++ {
		go func(index int) {
			runtime.LockOSThread()
			defer runtime.UnlockOSThread()
			defer wg.Done()

			results[index] = simulate(
				int64(index), int64(workers),
				walkers, steps, bound, seed,
			)
		}(w)
	}

	wg.Wait()

	total := result{distance: -1}
	for _, r := range results {
		total.spread += r.spread
		total.bumps += r.bumps
		total.returns += r.returns
		if r.distance > total.distance ||
			(r.distance == total.distance && r.walker < total.walker) {
			total.distance = r.distance
			total.walker = r.walker
		}
	}

	fmt.Printf("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n",
		total.spread, total.bumps, total.returns,
		total.walker, total.distance)
}
