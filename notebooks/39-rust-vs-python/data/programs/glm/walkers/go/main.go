package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
)

type result struct {
	spread, bumps, rets, bestD, bestJ int64
}

var dxTab = [4]int64{1, -1, 0, 0}
var dyTab = [4]int64{0, 0, 1, -1}

func splitmix64(state *uint64) uint64 {
	*state += 0x9E3779B97F4A7C15
	z := *state
	z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
	z = (z ^ (z >> 27)) * 0x94D049BB133111EB
	return z ^ (z >> 31)
}

func walkRange(j0, j1 int64, seed uint64, L, B int64, r *result) {
	var spread, bumps, rets, bestD, bestJ int64
	bestJ = -1
	bestD = -1
	negB := -B
	for j := j0; j < j1; j++ {
		state := seed + uint64(j)
		var x, y int64
		for s := int64(0); s < L; s++ {
			d := splitmix64(&state) >> 62
			nx, ny := x+dxTab[d], y+dyTab[d]
			if nx > B || nx < negB || ny > B || ny < negB {
				bumps++
			} else {
				x, y = nx, ny
				if x == 0 && y == 0 {
					rets++
				}
			}
		}
		spread += x*x + y*y
		D := x
		if D < 0 {
			D = -D
		}
		if y < 0 {
			D -= y
		} else {
			D += y
		}
		if D > bestD {
			bestD = D
			bestJ = j
		}
	}
	r.spread, r.bumps, r.rets, r.bestD, r.bestJ = spread, bumps, rets, bestD, bestJ
}

func main() {
	if len(os.Args) < 3 {
		os.Exit(1)
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	var J, L, B int64
	var seed uint64
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<16), 1<<16)
	if !sc.Scan() {
		os.Exit(1)
	}
	fields := strings.Fields(sc.Text())
	if len(fields) < 4 {
		os.Exit(1)
	}
	J, _ = strconv.ParseInt(fields[0], 10, 64)
	L, _ = strconv.ParseInt(fields[1], 10, 64)
	B, _ = strconv.ParseInt(fields[2], 10, 64)
	seed, _ = strconv.ParseUint(fields[3], 10, 64)
	f.Close()

	workers, _ := strconv.Atoi(os.Args[2])
	if workers < 1 {
		workers = 1
	}
	if int64(workers) > J {
		workers = int(J)
	}
	chunk := (J + int64(workers) - 1) / int64(workers)
	results := make([]result, workers)
	var wg sync.WaitGroup
	for w := 0; w < workers; w++ {
		j0 := int64(w) * chunk
		j1 := j0 + chunk
		if j1 > J {
			j1 = J
		}
		if j0 >= j1 {
			break
		}
		wg.Add(1)
		go func(w int, j0, j1 int64) {
			defer wg.Done()
			walkRange(j0, j1, seed, L, B, &results[w])
		}(w, j0, j1)
	}
	wg.Wait()

	var spread, bumps, rets, bestD, bestJ int64
	bestJ = -1
	bestD = -1
	for w := 0; w < workers; w++ {
		r := &results[w]
		spread += r.spread
		bumps += r.bumps
		rets += r.rets
		if r.bestJ >= 0 && (bestJ < 0 || r.bestD > bestD) {
			bestD, bestJ = r.bestD, r.bestJ
		}
	}

	out := bufio.NewWriter(os.Stdout)
	fmt.Fprintf(out, "spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n", spread, bumps, rets, bestJ, bestD)
	out.Flush()
}
