package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
)

const (
	gamma = 0x9E3779B97F4A7C15
	mulA  = 0xBF58476D1CE4E5B9
	mulB  = 0x94D049BB133111EB
)

// Packed deltas: low 32 bits carry dx, high 32 bits carry dy (mod 2^64).
var packTab = [4]uint64{1, 0xFFFFFFFFFFFFFFFF, 0x0000000100000000, 0xFFFFFFFF00000000}
var dxTab = [4]int64{1, -1, 0, 0}
var dyTab = [4]int64{0, 0, 1, -1}

func walk(seed uint64, L, B int64) (x, y, bumps, returns int64) {
	s := seed
	rem := L
	for rem > 0 {
		ax := x
		if ax < 0 {
			ax = -ax
		}
		ay := y
		if ay < 0 {
			ay = -ay
		}
		mx := ax
		if ay > mx {
			mx = ay
		}
		// k steps during which neither a bump nor a return is possible.
		k := B - mx
		if q := ax + ay - 1; q < k {
			k = q
		}
		if k > rem {
			k = rem
		}
		if k < 8 {
			c := rem
			if c > 8 {
				c = 8
			}
			rem -= c
			for ; c > 0; c-- {
				s += gamma
				z := s
				z = (z ^ (z >> 30)) * mulA
				z = (z ^ (z >> 27)) * mulB
				d := (z >> 62) & 3
				nx := x + dxTab[d]
				ny := y + dyTab[d]
				if nx > B || nx < -B || ny > B || ny < -B {
					bumps++
				} else {
					x, y = nx, ny
					if nx|ny == 0 {
						returns++
					}
				}
			}
			continue
		}
		if k > 1<<30 {
			k = 1 << 30
		}
		rem -= k
		var acc uint64
		n := k
		for ; n >= 4; n -= 4 {
			z0 := s + gamma
			z1 := z0 + gamma
			z2 := z1 + gamma
			z3 := z2 + gamma
			s = z3
			z0 = (z0 ^ (z0 >> 30)) * mulA
			z1 = (z1 ^ (z1 >> 30)) * mulA
			z2 = (z2 ^ (z2 >> 30)) * mulA
			z3 = (z3 ^ (z3 >> 30)) * mulA
			z0 = (z0 ^ (z0 >> 27)) * mulB
			z1 = (z1 ^ (z1 >> 27)) * mulB
			z2 = (z2 ^ (z2 >> 27)) * mulB
			z3 = (z3 ^ (z3 >> 27)) * mulB
			acc += packTab[(z0>>62)&3]
			acc += packTab[(z1>>62)&3]
			acc += packTab[(z2>>62)&3]
			acc += packTab[(z3>>62)&3]
		}
		for ; n > 0; n-- {
			s += gamma
			z := s
			z = (z ^ (z >> 30)) * mulA
			z = (z ^ (z >> 27)) * mulB
			acc += packTab[(z>>62)&3]
		}
		dx := int64(int32(uint32(acc)))
		dy := int64(int32(uint32((acc - uint64(dx)) >> 32)))
		x += dx
		y += dy
	}
	return
}

type result struct {
	spread, bumps, returns int64
	bestD, bestJ           int64
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	f := strings.Fields(string(data))
	if len(f) < 4 {
		os.Exit(1)
	}
	J, _ := strconv.ParseInt(f[0], 10, 64)
	L, _ := strconv.ParseInt(f[1], 10, 64)
	bu, errB := strconv.ParseUint(f[2], 10, 64)
	if errB != nil || bu > 1<<62 {
		bu = 1 << 62
	}
	B := int64(bu)
	seed, _ := strconv.ParseUint(f[3], 10, 64)

	workers := 1
	if len(os.Args) >= 3 {
		if w, e := strconv.Atoi(strings.TrimSpace(os.Args[2])); e == nil && w >= 1 {
			workers = w
		}
	}
	if workers > 64 {
		workers = 64
	}
	if int64(workers) > J {
		workers = int(J)
	}
	if workers < 1 {
		workers = 1
	}

	blk := J / (int64(workers) * 16)
	if blk < 1 {
		blk = 1
	}

	results := make([]result, workers)
	var next atomic.Int64
	var wg sync.WaitGroup

	run := func(w int) {
		var spread, bumps, returns int64
		bestD := int64(-1)
		bestJ := int64(0)
		for {
			start := next.Add(blk) - blk
			if start >= J {
				break
			}
			end := start + blk
			if end > J {
				end = J
			}
			for j := start; j < end; j++ {
				x, y, b, r := walk(seed+uint64(j), L, B)
				spread += x*x + y*y
				bumps += b
				returns += r
				if x < 0 {
					x = -x
				}
				if y < 0 {
					y = -y
				}
				d := x + y
				if d > bestD || (d == bestD && j < bestJ) {
					bestD = d
					bestJ = j
				}
			}
		}
		results[w] = result{spread, bumps, returns, bestD, bestJ}
	}

	if workers == 1 {
		run(0)
	} else {
		wg.Add(workers)
		for w := 0; w < workers; w++ {
			go func(w int) {
				defer wg.Done()
				run(w)
			}(w)
		}
		wg.Wait()
	}

	var spread, bumps, returns int64
	bestD := int64(-1)
	bestJ := int64(0)
	for i := range results {
		r := &results[i]
		spread += r.spread
		bumps += r.bumps
		returns += r.returns
		if r.bestD > bestD || (r.bestD == bestD && r.bestD >= 0 && r.bestJ < bestJ) {
			bestD = r.bestD
			bestJ = r.bestJ
		}
	}
	if bestD < 0 {
		bestD = 0
		bestJ = 0
	}

	out := make([]byte, 0, 128)
	out = append(out, "spread "...)
	out = strconv.AppendInt(out, spread, 10)
	out = append(out, "\nbumps "...)
	out = strconv.AppendInt(out, bumps, 10)
	out = append(out, "\nreturns "...)
	out = strconv.AppendInt(out, returns, 10)
	out = append(out, "\nfarthest "...)
	out = strconv.AppendInt(out, bestJ, 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, bestD, 10)
	out = append(out, '\n')
	if _, err := os.Stdout.Write(out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
