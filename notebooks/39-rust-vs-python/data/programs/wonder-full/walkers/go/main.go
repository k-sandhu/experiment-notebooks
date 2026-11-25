package main

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
	"sync"
)

const gold = uint64(0x9E3779B97F4A7C15)
const c1 = uint64(0xBF58476D1CE4E5B9)
const c2 = uint64(0x94D049BB133111EB)

var dx = [4]int32{1, -1, 0, 0}
var dy = [4]int32{0, 0, 1, -1}

type partial struct {
	spread, bumps, returns, farIdx, farDist int64
	_                                       [24]byte
}

func dir(state uint64) uint64 {
	z := state
	z = (z ^ (z >> 30)) * c1
	z = (z ^ (z >> 27)) * c2
	return z >> 62
}

func runRange(begin, end, L int64, B int32, seed uint64, out *partial) {
	var spread, bumps, returns int64
	farIdx := begin
	farDist := int64(-1)
	// Coordinates offset by +B into unsigned [0, 2B]; one compare per axis.
	ub := uint32(B) * 2
	org := uint32(B)
	L4 := L &^ 3
	for j := begin; j < end; j++ {
		state := seed + uint64(j)
		ux, uy := org, org
		var b, r int64
		i := int64(0)
		for ; i < L4; i += 4 {
			s0 := state + gold
			s1 := s0 + gold
			s2 := s1 + gold
			s3 := s2 + gold
			state = s3
			d0 := dir(s0)
			d1 := dir(s1)
			d2 := dir(s2)
			d3 := dir(s3)
			{
				nx, ny := ux+uint32(dx[d0]), uy+uint32(dy[d0])
				if nx > ub || ny > ub {
					b++
				} else {
					ux, uy = nx, ny
					if ux == org && uy == org {
						r++
					}
				}
			}
			{
				nx, ny := ux+uint32(dx[d1]), uy+uint32(dy[d1])
				if nx > ub || ny > ub {
					b++
				} else {
					ux, uy = nx, ny
					if ux == org && uy == org {
						r++
					}
				}
			}
			{
				nx, ny := ux+uint32(dx[d2]), uy+uint32(dy[d2])
				if nx > ub || ny > ub {
					b++
				} else {
					ux, uy = nx, ny
					if ux == org && uy == org {
						r++
					}
				}
			}
			{
				nx, ny := ux+uint32(dx[d3]), uy+uint32(dy[d3])
				if nx > ub || ny > ub {
					b++
				} else {
					ux, uy = nx, ny
					if ux == org && uy == org {
						r++
					}
				}
			}
		}
		for ; i < L; i++ {
			state += gold
			d := dir(state)
			nx, ny := ux+uint32(dx[d]), uy+uint32(dy[d])
			if nx > ub || ny > ub {
				b++
			} else {
				ux, uy = nx, ny
				if ux == org && uy == org {
					r++
				}
			}
		}
		bumps += b
		returns += r
		x := int64(ux) - int64(B)
		y := int64(uy) - int64(B)
		spread += x*x + y*y
		ax := x
		if ax < 0 {
			ax = -ax
		}
		ay := int64(y)
		if ay < 0 {
			ay = -ay
		}
		dist := ax + ay
		if dist > farDist {
			farDist = dist
			farIdx = j
		}
	}
	out.spread, out.bumps, out.returns, out.farIdx, out.farDist = spread, bumps, returns, farIdx, farDist
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	var vals [4]uint64
	idx, p := 0, 0
	for idx < 4 && p < len(data) {
		for p < len(data) && (data[p] < '0' || data[p] > '9') {
			p++
		}
		if p >= len(data) {
			break
		}
		var v uint64
		for p < len(data) && data[p] >= '0' && data[p] <= '9' {
			v = v*10 + uint64(data[p]-'0')
			p++
		}
		vals[idx] = v
		idx++
	}
	J, L := int64(vals[0]), int64(vals[1])
	var B int32
	if vals[2] > 2147483647 {
		B = 2147483647
	} else {
		B = int32(vals[2])
	}
	seed := vals[3]

	workers := runtime.NumCPU()
	if len(os.Args) >= 3 {
		if w, e := strconv.Atoi(os.Args[2]); e == nil {
			workers = w
		}
	}
	if workers < 1 {
		workers = 1
	}
	if workers > 32 {
		workers = 32
	}
	if J > 0 && int64(workers) > J {
		workers = int(J)
	}
	if workers < 1 {
		workers = 1
	}

	if J <= 0 {
		fmt.Print("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n")
		return
	}
	parts := make([]partial, workers)
	type rng struct{ a, b int64 }
	ranges := make([]rng, workers)
	base, rem := J/int64(workers), J%int64(workers)
	start := int64(0)
	for w := 0; w < workers; w++ {
		cnt := base
		if int64(w) < rem {
			cnt++
		}
		ranges[w] = rng{start, start + cnt}
		start += cnt
	}
	if workers == 1 {
		runRange(ranges[0].a, ranges[0].b, L, B, seed, &parts[0])
	} else {
		var wg sync.WaitGroup
		for w := 1; w < workers; w++ {
			wg.Add(1)
			go func(w int) {
				defer wg.Done()
				runRange(ranges[w].a, ranges[w].b, L, B, seed, &parts[w])
			}(w)
		}
		runRange(ranges[0].a, ranges[0].b, L, B, seed, &parts[0])
		wg.Wait()
	}
	var spread, bumps, returns, farIdx int64
	farDist := int64(-1)
	for i := range parts {
		pt := &parts[i]
		spread += pt.spread
		bumps += pt.bumps
		returns += pt.returns
		if pt.farDist > farDist {
			farDist = pt.farDist
			farIdx = pt.farIdx
		}
	}
	if farDist < 0 {
		farDist = 0
	}
	// Single buffered write.
	os.Stdout.WriteString(fmt.Sprintf("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n", spread, bumps, returns, farIdx, farDist))
}
