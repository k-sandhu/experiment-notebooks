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
	walker   uint64
	distance int64
}

func readUint(data []byte, pos *int) uint64 {
	i := *pos
	for i < len(data) && data[i] <= ' ' {
		i++
	}
	var n uint64
	for i < len(data) && data[i] >= '0' && data[i] <= '9' {
		n = n*10 + uint64(data[i]-'0')
		i++
	}
	*pos = i
	return n
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	pos := 0
	walkers := readUint(data, &pos)
	steps := readUint(data, &pos)
	bound := readUint(data, &pos)
	seed := readUint(data, &pos)

	workers, _ := strconv.Atoi(os.Args[2])
	runtime.GOMAXPROCS(workers)

	results := make([]result, workers)
	stride := uint64(workers)
	twiceBound := bound << 1

	var wg sync.WaitGroup
	wg.Add(workers)

	for worker := 0; worker < workers; worker++ {
		go func(worker int) {
			total := result{distance: -1}

			for j := uint64(worker); j < walkers; j += stride {
				state := seed + j
				var x, y int64
				var bumps, returns int64

				for remaining := steps; remaining != 0; remaining-- {
					state += 0x9E3779B97F4A7C15
					z := state
					z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
					z = (z ^ (z >> 27)) * 0x94D049BB133111EB
					z ^= z >> 31

					axisMask := -int64(z >> 63)
					step := int64(1) - int64((z>>61)&2)
					nx := x + (step &^ axisMask)
					ny := y + (step & axisMask)

					if uint64(nx)+bound > twiceBound ||
						uint64(ny)+bound > twiceBound {
						bumps++
						continue
					}

					x, y = nx, ny
					if x|y == 0 {
						returns++
					}
				}

				total.spread += x*x + y*y
				total.bumps += bumps
				total.returns += returns

				if x < 0 {
					x = -x
				}
				if y < 0 {
					y = -y
				}
				distance := x + y
				if distance > total.distance {
					total.distance = distance
					total.walker = j
				}
			}

			results[worker] = total
			wg.Done()
		}(worker)
	}

	wg.Wait()

	answer := result{distance: -1}
	for _, r := range results {
		answer.spread += r.spread
		answer.bumps += r.bumps
		answer.returns += r.returns
		if r.distance > answer.distance ||
			(r.distance == answer.distance && r.walker < answer.walker) {
			answer.distance = r.distance
			answer.walker = r.walker
		}
	}

	fmt.Printf("spread %d\nbumps %d\nreturns %d\nfarthest %d %d\n",
		answer.spread, answer.bumps, answer.returns,
		answer.walker, answer.distance)
}
