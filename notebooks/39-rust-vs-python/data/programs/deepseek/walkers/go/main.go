package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
)

const (
	gamma uint64 = 0x9E3779B97F4A7C15
	c1    uint64 = 0xBF58476D1CE4E5B9
	c2    uint64 = 0x94D049BB133111EB
)

type stat struct {
	spread  uint64
	bumps   uint64
	returns uint64
	x, y    int64
}

func b2i(b bool) int64 {
	if b {
		return 1
	}
	return 0
}

func runWalker2(s0, s1 uint64, steps uint64, b int64, o0, o1 *stat) {
	x0, y0 := int64(0), int64(0)
	x1, y1 := int64(0), int64(0)
	var b0, r0, b1, r1 uint64
	nb := -b

	for k := uint64(0); k < steps; k++ {
		s0 += gamma
		z0 := s0
		z0 = (z0 ^ (z0 >> 30)) * c1
		z0 = (z0 ^ (z0 >> 27)) * c2
		z0 ^= z0 >> 31

		s1 += gamma
		z1 := s1
		z1 = (z1 ^ (z1 >> 30)) * c1
		z1 = (z1 ^ (z1 >> 27)) * c2
		z1 ^= z1 >> 31

		d0 := z0 >> 62
		nx0 := x0 + ((1-2*int64(d0&1)) & -int64((d0&2)>>1))
		ny0 := y0 + ((1-2*int64(d0&1)) &^ -int64((d0&2)>>1))
		ox0 := b2i(nx0 > b) - b2i(nx0 < nb)
		oy0 := b2i(ny0 > b) - b2i(ny0 < nb)
		nx0 -= ox0
		ny0 -= oy0
		b0 += uint64(b2i((ox0 | oy0) != 0))
		r0 += uint64(b2i((nx0 | ny0) == 0))
		x0, y0 = nx0, ny0

		d1 := z1 >> 62
		nx1 := x1 + ((1-2*int64(d1&1)) & -int64((d1&2)>>1))
		ny1 := y1 + ((1-2*int64(d1&1)) &^ -int64((d1&2)>>1))
		ox1 := b2i(nx1 > b) - b2i(nx1 < nb)
		oy1 := b2i(ny1 > b) - b2i(ny1 < nb)
		nx1 -= ox1
		ny1 -= oy1
		b1 += uint64(b2i((ox1 | oy1) != 0))
		r1 += uint64(b2i((nx1 | ny1) == 0))
		x1, y1 = nx1, ny1
	}

	o0.spread = uint64(x0*x0 + y0*y0)
	o0.bumps = b0
	o0.returns = r0
	o0.x, o0.y = x0, y0
	o1.spread = uint64(x1*x1 + y1*y1)
	o1.bumps = b1
	o1.returns = r1
	o1.x, o1.y = x1, y1
}

func runWalker(state uint64, steps uint64, b int64, out *stat) {
	x, y := int64(0), int64(0)
	var bumps, returns uint64
	nb := -b

	for k := uint64(0); k < steps; k++ {
		state += gamma
		z := state
		z = (z ^ (z >> 30)) * c1
		z = (z ^ (z >> 27)) * c2
		z ^= z >> 31

		d := z >> 62
		dir := 1 - 2*int64(d&1)
		mx := -int64((d & 2) >> 1)
		nx := x + (dir & mx)
		ny := y + (dir &^ mx)
		ox := b2i(nx > b) - b2i(nx < nb)
		oy := b2i(ny > b) - b2i(ny < nb)
		nx -= ox
		ny -= oy
		bumps += uint64(b2i((ox | oy) != 0))
		returns += uint64(b2i((nx | ny) == 0))
		x, y = nx, ny
	}

	out.spread = uint64(x*x + y*y)
	out.bumps = bumps
	out.returns = returns
	out.x = x
	out.y = y
}

func runRange(seed uint64, steps uint64, b int64, j0, j1 int, stats []stat) {
	j := j0
	for ; j+1 < j1; j += 2 {
		runWalker2(seed+uint64(j), seed+uint64(j+1), steps, b, &stats[j], &stats[j+1])
	}
	if j < j1 {
		runWalker(seed+uint64(j), steps, b, &stats[j])
	}
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	fields := strings.Fields(string(data))
	J, _ := strconv.Atoi(fields[0])
	L, _ := strconv.ParseUint(fields[1], 10, 64)
	B, _ := strconv.ParseInt(fields[2], 10, 64)
	seed, _ := strconv.ParseUint(fields[3], 10, 64)

	workers, _ := strconv.Atoi(strings.TrimSpace(os.Args[2]))
	if workers < 1 {
		workers = 1
	}
	if workers > J {
		workers = J
	}
	if workers < 1 {
		workers = 1
	}

	stats := make([]stat, J)

	if J > 0 {
		if workers == 1 {
			runRange(seed, L, B, 0, J, stats)
		} else {
			var wg sync.WaitGroup
			base := J / workers
			rem := J % workers
			start := 0
			for t := 0; t < workers; t++ {
				cnt := base
				if t < rem {
					cnt++
				}
				s, e := start, start+cnt
				start = e
				wg.Add(1)
				go func(s, e int) {
					defer wg.Done()
					runRange(seed, L, B, s, e, stats)
				}(s, e)
			}
			wg.Wait()
		}
	}

	var totalSpread, totalBumps, totalReturns uint64
	bestDist := int64(0)
	bestJ := 0
	for j := 0; j < J; j++ {
		s := &stats[j]
		totalSpread += s.spread
		totalBumps += s.bumps
		totalReturns += s.returns
		ax, ay := s.x, s.y
		if ax < 0 {
			ax = -ax
		}
		if ay < 0 {
			ay = -ay
		}
		d := ax + ay
		if d > bestDist {
			bestDist = d
			bestJ = j
		}
	}

	fmt.Printf("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n",
		totalSpread, totalBumps, totalReturns, bestJ, bestDist)
}
