package main

import (
	"os"
	"strconv"
)

func main() {
	if len(os.Args) < 2 {
		return
	}
	buf, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	pos := 0
	n := len(buf)
	readInt := func() int {
		for pos < n && buf[pos] <= ' ' {
			pos++
		}
		x := 0
		for pos < n && buf[pos] >= '0' && buf[pos] <= '9' {
			x = x*10 + int(buf[pos]-'0')
			pos++
		}
		return x
	}

	H := readInt()
	W := readInt()
	S := readInt()
	for pos < n && buf[pos] != '\n' {
		pos++
	}
	if pos < n {
		pos++
	}

	W2 := W + 2
	total := (H + 2) * W2
	cur := make([]int32, total)
	nxt := make([]int32, total)
	kind := make([]uint8, total) // 0 wall, 1 open, 2 source
	open := make([]int32, 0, H*W)

	for r := 0; r < H; r++ {
		rowStart := pos
		base := (r+1)*W2 + 1
		for c := 0; c < W; c++ {
			ch := buf[rowStart+c]
			idx := base + c
			if ch == '.' {
				kind[idx] = 1
				open = append(open, int32(idx))
			} else if ch >= '1' && ch <= '9' {
				kind[idx] = 2
				v := int32(ch-'0') * 1000
				cur[idx] = v
				nxt[idx] = v
			}
		}
		pos += W
		for pos < n && buf[pos] != '\n' {
			pos++
		}
		if pos < n {
			pos++
		}
	}

	nOpen := len(open)
	coef := make([]uint8, nOpen)
	for j := 0; j < nOpen; j++ {
		i := int(open[j])
		var a, b, l, r uint8
		if kind[i-W2] != 0 {
			a = 1
		}
		if kind[i+W2] != 0 {
			b = 1
		}
		if kind[i-1] != 0 {
			l = 1
		}
		if kind[i+1] != 0 {
			r = 1
		}
		coef[j] = 4 + (1 - a) + (1 - b) + (1 - l) + (1 - r)
	}

	c := cur
	nn := nxt
	for s := 0; s < S; s++ {
		for j := 0; j < nOpen; j++ {
			i := int(open[j])
			nn[i] = (int32(coef[j])*c[i] +
				c[i-W2] + c[i+W2] + c[i-1] + c[i+1]) >> 3
		}
		c, nn = nn, c
	}

	var sum int64
	var chk int64
	maxv := int32(-1)
	bestR, bestC := 0, 0
	for j := 0; j < nOpen; j++ {
		i := int(open[j])
		v := c[i]
		r := i/W2 - 1
		col := i%W2 - 1
		sum += int64(v)
		chk += int64(v) * (int64(r)*int64(W) + int64(col) + 1)
		if v > maxv {
			maxv = v
			bestR = r
			bestC = col
		}
	}

	out := make([]byte, 0, 96)
	out = append(out, "sum "...)
	out = strconv.AppendInt(out, sum, 10)
	out = append(out, '\n')
	out = append(out, "max "...)
	out = strconv.AppendInt(out, int64(maxv), 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(bestR), 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(bestC), 10)
	out = append(out, '\n')
	out = append(out, "checksum "...)
	out = strconv.AppendInt(out, chk, 10)
	out = append(out, '\n')
	os.Stdout.Write(out)
}
