package main

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
	"strings"
	"sync"
)

type result struct {
	spread, bumps, returns, walker, distance int64
}

func simulate(first, end, steps, bound int64, seed uint64) result {
	r := result{distance: -1}
	for j := first; j < end; j++ {
		state := seed + uint64(j)
		var x, y, bumps, returns int64
		for k := int64(0); k < steps; k++ {
			state += 0x9E3779B97F4A7C15
			z := state
			z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
			z = (z ^ (z >> 27)) * 0x94D049BB133111EB
			// The final xor does not change the top two bits.
			d := int64(z >> 62)
			axis := d >> 1
			delta := 1 - 2*(d&1)
			position := x
			if axis != 0 {
				position = y
			}
			wall := bound
			if delta < 0 {
				wall = -bound
			}
			blocked := position == wall
			move := delta
			if blocked {
				bumps++
				move = 0
			}
			x += move & (axis - 1)
			y += move & -axis
			if (x | y) == 0 {
				returns++
			}
		}
		r.spread += x*x + y*y
		r.bumps += bumps
		r.returns += returns
		distance := x
		if distance < 0 {
			distance = -distance
		}
		if y < 0 {
			distance -= y
		} else {
			distance += y
		}
		if distance > r.distance {
			r.distance = distance
			r.walker = j
		}
	}
	return r
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	fields := strings.Fields(string(data))
	walkers, _ := strconv.ParseInt(fields[0], 10, 64)
	steps, _ := strconv.ParseInt(fields[1], 10, 64)
	bound, _ := strconv.ParseInt(fields[2], 10, 64)
	seed, _ := strconv.ParseUint(fields[3], 10, 64)
	workers, _ := strconv.Atoi(os.Args[2])
	runtime.GOMAXPROCS(workers)
	results := make([]result, workers)
	q, remainder := walkers/int64(workers), walkers%int64(workers)
	var pending sync.WaitGroup
	pending.Add(workers - 1)
	run := func(w int) {
		index := int64(w)
		before := index
		if before > remainder {
			before = remainder
		}
		first := q*index + before
		end := first + q
		if index < remainder {
			end++
		}
		results[w] = simulate(first, end, steps, bound, seed)
	}
	for w := 1; w < workers; w++ {
		go func(index int) {
			run(index)
			pending.Done()
		}(w)
	}
	run(0)
	pending.Wait()
	total := result{distance: -1}
	for _, r := range results {
		total.spread += r.spread
		total.bumps += r.bumps
		total.returns += r.returns
		if r.distance > total.distance || (r.distance == total.distance && r.walker < total.walker) {
			total.distance = r.distance
			total.walker = r.walker
		}
	}
	if total.distance < 0 {
		total.distance = 0
	}
	fmt.Printf("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n",
		total.spread, total.bumps, total.returns, total.walker, total.distance)
}
