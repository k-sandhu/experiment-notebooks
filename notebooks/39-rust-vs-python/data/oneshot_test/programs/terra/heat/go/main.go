package main

import (
	"bufio"
	"fmt"
	"os"
)

type cell struct {
	pos, up, down, left, right int32
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	offset := 0
	nextInt := func() int {
		for offset < len(data) && data[offset] <= ' ' {
			offset++
		}
		n := 0
		for offset < len(data) && data[offset] >= '0' && data[offset] <= '9' {
			n = n*10 + int(data[offset]-'0')
			offset++
		}
		return n
	}

	h, w, steps := nextInt(), nextInt(), nextInt()
	stride := w + 2
	size := (h + 2) * stride

	grid := make([]byte, size)
	for i := range grid {
		grid[i] = '#'
	}

	a := make([]int32, size)
	b := make([]int32, size)

	for r := 0; r < h; r++ {
		for offset < len(data) && data[offset] <= ' ' {
			offset++
		}
		base := (r+1)*stride + 1
		for c := 0; c < w; c++ {
			ch := data[offset+c]
			p := base + c
			grid[p] = ch
			if ch >= '1' && ch <= '9' {
				v := int32(ch-'0') * 1000
				a[p], b[p] = v, v
			}
		}
		offset += w
	}

	cells := make([]cell, 0, h*w)
	for r := 0; r < h; r++ {
		base := (r+1)*stride + 1
		for c := 0; c < w; c++ {
			p := base + c
			if grid[p] != '.' {
				continue
			}

			up, down := p-stride, p+stride
			left, right := p-1, p+1
			if grid[up] == '#' {
				up = p
			}
			if grid[down] == '#' {
				down = p
			}
			if grid[left] == '#' {
				left = p
			}
			if grid[right] == '#' {
				right = p
			}

			cells = append(cells, cell{
				int32(p), int32(up), int32(down), int32(left), int32(right),
			})
		}
	}

	for step := 0; step < steps; step++ {
		var changed int32
		for _, c := range cells {
			old := a[c.pos]
			v := (4*old + a[c.up] + a[c.down] + a[c.left] + a[c.right]) >> 3
			b[c.pos] = v
			changed |= old ^ v
		}
		a, b = b, a
		if changed == 0 {
			break
		}
	}

	var sum, checksum int64
	var maxValue int32 = -1
	maxRow, maxCol := 0, 0

	for _, c := range cells {
		p := int(c.pos)
		r := p/stride - 1
		col := p%stride - 1
		v := a[p]
		sum += int64(v)
		checksum += int64(v) * (int64(r)*int64(w) + int64(col) + 1)
		if v > maxValue {
			maxValue = v
			maxRow, maxCol = r, col
		}
	}

	out := bufio.NewWriter(os.Stdout)
	fmt.Fprintf(out, "sum %d\nmax %d %d %d\nchecksum %d\n",
		sum, maxValue, maxRow, maxCol, checksum)
	out.Flush()
}
