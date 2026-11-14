package main

import (
	"os"
	"strconv"
)

type span struct {
	start int
	end   int
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	p := 0
	nextInt := func() int {
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

	h, w, steps := nextInt(), nextInt(), nextInt()
	stride := w + 2
	size := (h + 2) * stride

	current := make([]uint16, size)
	next := make([]uint16, size)
	kind := make([]uint8, size)
	weight := make([]uint8, size)
	hasSource := false

	for r := 0; r < h; r++ {
		for p < len(data) && data[p] <= ' ' {
			p++
		}
		base := (r+1)*stride + 1
		for c := 0; c < w; c++ {
			i := base + c
			ch := data[p+c]
			switch ch {
			case '.':
				kind[i] = 1
			case '#':
			default:
				kind[i] = 2
				value := uint16(ch-'0') * 1000
				current[i] = value
				next[i] = value
				hasSource = true
			}
		}
		p += w
	}

	runs := make([]span, 0, h)
	for r := 0; r < h; r++ {
		base := (r+1)*stride + 1
		end := base + w
		for i := base; i < end; {
			if kind[i] != 1 {
				i++
				continue
			}
			start := i
			for i < end && kind[i] == 1 {
				k := uint8(4)
				if kind[i-stride] == 0 {
					k++
				}
				if kind[i+stride] == 0 {
					k++
				}
				if kind[i-1] == 0 {
					k++
				}
				if kind[i+1] == 0 {
					k++
				}
				weight[i] = k
				i++
			}
			runs = append(runs, span{start: start, end: i})
		}
	}

	if !hasSource {
		steps = 0
	}

	for step := 0; step < steps; step++ {
		for _, run := range runs {
			start, end := run.start, run.end
			center := current[start:end]
			dst := next[start:end]
			up := current[start-stride : end-stride]
			down := current[start+stride : end+stride]
			left := current[start-1 : end-1]
			right := current[start+1 : end+1]
			factor := weight[start:end]

			last := len(center) - 1
			_ = dst[last]
			_ = up[last]
			_ = down[last]
			_ = left[last]
			_ = right[last]
			_ = factor[last]

			for j, old := range center {
				total := uint32(old)*uint32(factor[j]) +
					uint32(up[j]) + uint32(down[j]) +
					uint32(left[j]) + uint32(right[j])
				dst[j] = uint16(total >> 3)
			}
		}
		current, next = next, current
	}

	var sum, checksum int64
	maxValue := -1
	maxRow, maxCol := 0, 0

	for _, run := range runs {
		row := run.start/stride - 1
		col := run.start%stride - 1
		position := int64(row)*int64(w) + int64(col) + 1

		for i := run.start; i < run.end; i++ {
			value := int(current[i])
			sum += int64(value)
			checksum += int64(value) * position
			if value > maxValue {
				maxValue = value
				maxRow = row
				maxCol = col + i - run.start
			}
			position++
		}
	}

	out := make([]byte, 0, 128)
	out = append(out, "sum "...)
	out = strconv.AppendInt(out, sum, 10)
	out = append(out, '\n')
	out = append(out, "max "...)
	out = strconv.AppendInt(out, int64(maxValue), 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(maxRow), 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(maxCol), 10)
	out = append(out, '\n')
	out = append(out, "checksum "...)
	out = strconv.AppendInt(out, checksum, 10)
	out = append(out, '\n')
	_, _ = os.Stdout.Write(out)
}
