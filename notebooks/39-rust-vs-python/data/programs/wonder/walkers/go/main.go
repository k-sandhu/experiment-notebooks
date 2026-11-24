package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
)

type partial struct {
	spread, bumps, returns int64
	bestD, bestJ           int64
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	workers := 1
	if len(os.Args) >= 3 {
		if v, err := strconv.Atoi(os.Args[2]); err == nil {
			workers = v
		}
	}
	if workers < 1 {
		workers = 1
	}
	if workers > 32 {
		workers = 32
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	fields := strings.Fields(string(data))
	if len(fields) < 4 {
		os.Exit(1)
	}
	J, _ := strconv.ParseInt(fields[0], 10, 64)
	L, _ := strconv.ParseInt(fields[1], 10, 64)
	B64, _ := strconv.ParseInt(fields[2], 10, 64)
	B := int32(B64)
	seed, _ := strconv.ParseUint(fields[3], 10, 64)

	if J <= 0 {
		fmt.Print("spread 0\nbumps 0\nreturns 0\nfarthest 0 0\n")
		return
	}
	if int64(workers) > J {
		workers = int(J)
	}
	parts := make([]partial, workers)
	dx := [4]int32{1, -1, 0, 0}
	dy := [4]int32{0, 0, 1, -1}
	run := func(start, end int64, out *partial) {
		var spread, bumps, returns int64
		bestD := int64(-1)
		var bestJ int64 = start
		for j := start; j < end; j++ {
			state := seed + uint64(j)
			var x, y int32
			var b, r int64
			for i := int64(0); i < L; i++ {
				state += 0x9E3779B97F4A7C15
				z := state
				z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
				z = (z ^ (z >> 27)) * 0x94D049BB133111EB
				rr := z ^ (z >> 31)
				d := rr >> 62
				nx := x + dx[d]
				ny := y + dy[d]
				if nx > B || nx < -B || ny > B || ny < -B {
					b++
				} else {
					x, y = nx, ny
					if x == 0 && y == 0 {
						r++
					}
				}
			}
			bumps += b
			returns += r
			spread += int64(x)*int64(x) + int64(y)*int64(y)
			ax := int64(x)
			if ax < 0 {
				ax = -ax
			}
			ay := int64(y)
			if ay < 0 {
				ay = -ay
			}
			dist := ax + ay
			if dist > bestD {
				bestD = dist
				bestJ = j
			}
		}
		out.spread, out.bumps, out.returns = spread, bumps, returns
		out.bestD, out.bestJ = bestD, bestJ
	}

	if workers == 1 {
		run(0, J, &parts[0])
	} else {
		var wg sync.WaitGroup
		base := J / int64(workers)
		rem := J % int64(workers)
		var s int64
		for w := 0; w < workers; w++ {
			cnt := base
			if int64(w) < rem {
				cnt++
			}
			st, en := s, s+cnt
			s = en
			if w == workers-1 {
				run(st, en, &parts[w])
			} else {
				wg.Add(1)
				go func(st, en int64, idx int) {
					defer wg.Done()
					run(st, en, &parts[idx])
				}(st, en, w)
			}
		}
		wg.Wait()
	}
	var spread, bumps, returns int64
	bestD := int64(-1)
	var bestJ int64
	for i := range parts {
		spread += parts[i].spread
		bumps += parts[i].bumps
		returns += parts[i].returns
		if parts[i].bestD > bestD {
			bestD, bestJ = parts[i].bestD, parts[i].bestJ
		}
	}
	if bestD < 0 {
		bestD = 0
	}
	fmt.Printf("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n", spread, bumps, returns, bestJ, bestD)
}
