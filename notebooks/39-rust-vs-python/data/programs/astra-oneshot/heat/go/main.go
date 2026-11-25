package main

import (
	"fmt"
	"os"
	"runtime"
)

func main() {
	runtime.GOMAXPROCS(1)

	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	p := 0
	readInt := func() int {
		for p < len(data) && data[p] <= ' ' {
			p++
		}
		v := 0
		for p < len(data) && data[p] >= '0' && data[p] <= '9' {
			v = v*10 + int(data[p]-'0')
			p++
		}
		return v
	}

	h, w, steps := readInt(), readInt(), readInt()
	grid := make([]byte, h*w)
	openCount, sourceCount, firstOpen := 0, 0, -1

	for r := 0; r < h; r++ {
		for p < len(data) && data[p] <= ' ' {
			p++
		}
		row := grid[r*w : (r+1)*w]
		copy(row, data[p:p+w])
		p += w

		for c, ch := range row {
			if ch == '.' {
				openCount++
				if firstOpen < 0 {
					firstOpen = r*w + c
				}
			} else if ch != '#' {
				sourceCount++
			}
		}
	}

	if steps == 0 || sourceCount == 0 {
		fmt.Printf("sum 0\nmax 0 %d %d\nchecksum 0\n", firstOpen/w, firstOpen%w)
		return
	}

	// Open cells occupy the first openCount entries; sources follow.
	ids := make([]int, len(grid))
	current := make([]uint32, openCount+sourceCount)
	next := make([]uint32, len(current))
	openID, sourceID := 0, openCount

	for pos, ch := range grid {
		switch ch {
		case '#':
			ids[pos] = -1
		case '.':
			ids[pos] = openID
			openID++
		default:
			ids[pos] = sourceID
			value := uint32(ch-'0') * 1000
			current[sourceID] = value
			next[sourceID] = value
			sourceID++
		}
	}

	// Reflecting boundaries are represented by a reference to the cell itself.
	neighbors := make([][4]int, openCount)
	for r := 0; r < h; r++ {
		base := r * w
		for c := 0; c < w; c++ {
			pos := base + c
			if grid[pos] != '.' {
				continue
			}

			id := ids[pos]
			n := [4]int{id, id, id, id}
			if r > 0 && ids[pos-w] >= 0 {
				n[0] = ids[pos-w]
			}
			if r+1 < h && ids[pos+w] >= 0 {
				n[1] = ids[pos+w]
			}
			if c > 0 && ids[pos-1] >= 0 {
				n[2] = ids[pos-1]
			}
			if c+1 < w && ids[pos+1] >= 0 {
				n[3] = ids[pos+1]
			}
			neighbors[id] = n
		}
	}

	for step := 0; step < steps; step++ {
		oldOpen := current[:openCount]
		newOpen := next[:openCount]
		for i, n := range neighbors {
			newOpen[i] = (4*oldOpen[i] +
				current[n[0]] + current[n[1]] +
				current[n[2]] + current[n[3]]) >> 3
		}
		current, next = next, current
	}

	var total, checksum int64
	var maximum uint32
	bestPos := firstOpen
	id := 0

	for pos, ch := range grid {
		if ch != '.' {
			continue
		}
		value := current[id]
		id++
		total += int64(value)
		checksum += int64(value) * int64(pos+1)
		if value > maximum {
			maximum = value
			bestPos = pos
		}
	}

	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n",
		total, maximum, bestPos/w, bestPos%w, checksum)
}
