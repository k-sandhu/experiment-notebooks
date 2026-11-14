package main

import (
	"fmt"
	"os"
	"runtime"
)

type span struct {
	start int
	end   int
}

func readInt(data []byte, pos *int) int {
	i := *pos
	for data[i] <= ' ' {
		i++
	}
	n := 0
	for i < len(data) && data[i] >= '0' && data[i] <= '9' {
		n = n*10 + int(data[i]-'0')
		i++
	}
	*pos = i
	return n
}

func main() {
	runtime.GOMAXPROCS(1)

	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	pos := 0
	h := readInt(data, &pos)
	w := readInt(data, &pos)
	steps := readInt(data, &pos)

	stride := w + 2
	size := (h + 2) * stride

	current := make([]int32, size)
	next := make([]int32, size)
	kind := make([]byte, size)
	coefficient := make([]byte, size)
	hasSource := false

	for r := 0; r < h; r++ {
		for pos < len(data) && data[pos] <= ' ' {
			pos++
		}
		base := (r+1)*stride + 1
		for c := 0; c < w; c++ {
			ch := data[pos+c]
			p := base + c
			switch ch {
			case '.':
				kind[p] = 1
			case '#':
			default:
				kind[p] = 2
				v := int32(ch-'0') * 1000
				current[p] = v
				next[p] = v
				hasSource = true
			}
		}
		pos += w
	}

	spans := make([]span, 0, h)
	for r := 0; r < h; r++ {
		base := (r+1)*stride + 1
		start := -1
		for c := 0; c < w; c++ {
			p := base + c
			if kind[p] != 1 {
				if start >= 0 {
					spans = append(spans, span{start, p})
					start = -1
				}
				continue
			}

			if start < 0 {
				start = p
			}

			k := byte(4)
			if kind[p-stride] == 0 {
				k++
			}
			if kind[p+stride] == 0 {
				k++
			}
			if kind[p-1] == 0 {
				k++
			}
			if kind[p+1] == 0 {
				k++
			}
			coefficient[p] = k
		}
		if start >= 0 {
			spans = append(spans, span{start, base + w})
		}
	}

	if hasSource {
		for step := 0; step < steps; step++ {
			for _, run := range spans {
				lo, hi := run.start, run.end
				center := current[lo:hi]
				up := current[lo-stride : hi-stride]
				down := current[lo+stride : hi+stride]
				left := current[lo-1 : hi-1]
				right := current[lo+1 : hi+1]
				weights := coefficient[lo:hi]
				out := next[lo:hi]

				last := len(center) - 1
				_ = up[last]
				_ = down[last]
				_ = left[last]
				_ = right[last]
				_ = weights[last]
				_ = out[last]

				for i, v := range center {
					out[i] = (v*int32(weights[i]) +
						up[i] + down[i] + left[i] + right[i]) >> 3
				}
			}
			current, next = next, current
		}
	}

	var sum, checksum int64
	maxValue := int32(-1)
	maxPosition := 0

	for _, run := range spans {
		row := run.start/stride - 1
		col := run.start%stride - 1
		index := int64(row)*int64(w) + int64(col) + 1

		for p := run.start; p < run.end; p++ {
			v := current[p]
			sum += int64(v)
			checksum += int64(v) * index
			index++

			if v > maxValue {
				maxValue = v
				maxPosition = p
			}
		}
	}

	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n",
		sum,
		maxValue,
		maxPosition/stride-1,
		maxPosition%stride-1,
		checksum,
	)
}
