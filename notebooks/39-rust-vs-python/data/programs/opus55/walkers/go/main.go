package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
)

const (
	gamma = 0x9E3779B97F4A7C15
	mul1  = 0xBF58476D1CE4E5B9
	mul2  = 0x94D049BB133111EB

	// Runs shorter than this are not worth a trip through the unchecked loop.
	minFastRun = 4
	maxFastRun = 1 << 30
)

var (
	dxTable = [4]int64{1, -1, 0, 0}
	dyTable = [4]int64{0, 0, 1, -1}
	// The same moves packed as dx + dy<<32, so one add moves both coordinates.
	packedMoves = [4]uint64{1, 1<<64 - 1, 1 << 32, 1<<64 - 1<<32}
)

type walkResult struct {
	x, y, bumps, returns int64
}

// direction returns the top two bits of the next SplitMix64 output.
// The final z ^ (z >> 31) never changes them.
func direction(s uint64) uint64 {
	a := (s ^ (s >> 30)) * mul1
	b := (a ^ (a >> 27)) * mul2
	return b >> 62
}

func abs(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}

func walk(s uint64, steps, bound int64) walkResult {
	span := uint64(2 * bound)
	var x, y, bumps, returns int64
	left := steps
	for left > 0 {
		ax, ay := abs(x), abs(y)
		// Within `run` steps the walker can neither reach a wall nor the origin,
		// so those steps need no checks at all.
		run := min(bound-max(ax, ay), ax+ay-1)
		if run >= minFastRun {
			// Capping the run keeps the packed x displacement inside the low 32 bits.
			run = min(run, left, maxFastRun)
			left -= run
			var moved uint64
			for i := int64(0); i < run; i++ {
				s += gamma
				moved += packedMoves[direction(s)]
			}
			dx := int64(int32(moved))
			x += dx
			y += int64(moved-uint64(dx)) >> 32
			continue
		}
		// Checked steps near a wall or the origin, until the walker is clear again.
		end := max(left-minFastRun, 0)
		for ; left > end; left-- {
			s += gamma
			d := direction(s)
			nx, ny := x+dxTable[d], y+dyTable[d]
			if uint64(nx+bound) <= span && uint64(ny+bound) <= span {
				x, y = nx, ny
				if x|y == 0 {
					returns++
				}
			} else {
				bumps++
			}
		}
	}
	return walkResult{x, y, bumps, returns}
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fields := strings.Fields(string(data))
	walkers, _ := strconv.ParseInt(fields[0], 10, 64)
	steps, _ := strconv.ParseInt(fields[1], 10, 64)
	bound, _ := strconv.ParseInt(fields[2], 10, 64)
	seed, _ := strconv.ParseUint(fields[3], 10, 64)
	workers := int64(1)
	if len(os.Args) > 2 {
		workers, _ = strconv.ParseInt(os.Args[2], 10, 64)
	}
	workers = max(workers, 1)

	// A walker never gets farther than `steps` from the origin, so a larger box behaves the same.
	bound = min(bound, steps)

	results := make([]walkResult, max(walkers, 0))
	threads := min(workers, walkers)
	var wg sync.WaitGroup
	for t := int64(0); t < threads; t++ {
		from, to := walkers*t/threads, walkers*(t+1)/threads
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := from; j < to; j++ {
				results[j] = walk(seed+uint64(j), steps, bound)
			}
		}()
	}
	wg.Wait()

	var spread, bumps, returns, bestJ int64
	bestD := int64(-1)
	for j, r := range results {
		spread += r.x*r.x + r.y*r.y
		bumps += r.bumps
		returns += r.returns
		if d := abs(r.x) + abs(r.y); d > bestD {
			bestD, bestJ = d, int64(j)
		}
	}
	bestD = max(bestD, 0)
	w := bufio.NewWriter(os.Stdout)
	fmt.Fprintf(w, "spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n", spread, bumps, returns, bestJ, bestD)
	w.Flush()
}
