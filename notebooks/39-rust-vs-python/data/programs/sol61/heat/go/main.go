package main

import (
	"fmt"
	"os"
	"slices"
)

func main() {
	input, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	pos := 0
	number := func() int {
		for input[pos] <= ' ' {
			pos++
		}
		value := 0
		for pos < len(input) && input[pos] >= '0' && input[pos] <= '9' {
			digit := int(input[pos] - '0')
			const limit = int(^uint(0) >> 1)
			if value > (limit-digit)/10 {
				value = limit
			} else {
				value = value*10 + digit
			}
			pos++
		}
		return value
	}
	h, w, steps := number(), number(), number()
	stride := w + 2
	size := (h + 2) * stride
	begin, end := stride, (h+1)*stride
	grid := make([]byte, size)
	for i := range grid {
		grid[i] = '#'
	}
	// Every cell stays in [0, 9000]; widen only the arithmetic, not storage.
	a, b := make([]uint16, size), make([]uint16, size)
	weight := make([]uint8, size)
	openCount := 0
	hasSource := false
	for r := 1; r <= h; r++ {
		for pos < len(input) && input[pos] <= ' ' {
			pos++
		}
		for c := 1; c <= w; c++ {
			i := r*stride + c
			ch := input[pos]
			pos++
			grid[i] = ch
			if ch == '.' {
				openCount++
			}
			if ch >= '1' && ch <= '9' {
				a[i] = uint16(ch-'0') * 1000
				b[i] = a[i]
				hasSource = true
			}
		}
	}
	sparse := openCount < (end-begin)/4
	indexCount := end - begin - openCount
	if sparse {
		indexCount = openCount
	}
	indices := make([]int32, 0, indexCount)
	for i := begin; i < end; i++ {
		if grid[i] == '.' {
			n := uint8(4)
			if grid[i-stride] == '#' {
				n++
			}
			if grid[i+stride] == '#' {
				n++
			}
			if grid[i-1] == '#' {
				n++
			}
			if grid[i+1] == '#' {
				n++
			}
			weight[i] = n
			if sparse {
				indices = append(indices, int32(i))
			}
		} else if !sparse {
			indices = append(indices, int32(i))
		}
	}
	if hasSource {
		for step := 0; step < steps; step++ {
			if sparse {
				for _, index := range indices {
					i := int(index)
					b[i] = uint16((uint32(weight[i])*uint32(a[i]) + uint32(a[i-stride]) + uint32(a[i+stride]) + uint32(a[i-1]) + uint32(a[i+1])) >> 3)
				}
			} else {
				// Equal-length shifted slices let the compiler eliminate bounds checks.
				next := b[begin:end]
				up, down := a[begin-stride:][:len(next)], a[begin+stride:][:len(next)]
				right := a[begin+1:][:len(next)]
				left, center := uint32(a[begin-1]), uint32(a[begin])
				weights := weight[begin:end]
				for i := range next {
					valueRight := uint32(right[i])
					next[i] = uint16((uint32(weights[i])*center + uint32(up[i]) + uint32(down[i]) + left + valueRight) >> 3)
					left, center = center, valueRight
				}
				for _, i := range indices {
					b[i] = a[i]
				}
			}
			stable := step&63 == 63 && slices.Equal(a, b)
			a, b = b, a
			if stable {
				break
			}
		}
	}
	var total, checksum int64
	best, bestR, bestC := -1, 0, 0
	for r := 0; r < h; r++ {
		for c := 0; c < w; c++ {
			i := (r+1)*stride + c + 1
			if grid[i] != '.' {
				continue
			}
			value := int(a[i])
			total += int64(value)
			checksum += int64(value) * (int64(r)*int64(w) + int64(c) + 1)
			if value > best {
				best, bestR, bestC = value, r, c
			}
		}
	}
	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n", total, best, bestR, bestC, checksum)
}
