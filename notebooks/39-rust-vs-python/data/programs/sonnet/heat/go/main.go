package main

import (
	"fmt"
	"os"
)

func step(a, b, c, m []int32, lo, hi, w2 int) {
	b = b[:len(a)]
	c = c[:len(a)]
	m = m[:len(a)]
	for i := lo; i < hi; i++ {
		b[i] = (c[i]*a[i] + ((a[i-1] + a[i+1] + a[i-w2] + a[i+w2]) & m[i])) >> 3
	}
}

func main() {
	buf, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	p := 0
	readInt := func() int {
		for p < len(buf) && (buf[p] < '0' || buf[p] > '9') {
			p++
		}
		v := 0
		for p < len(buf) && buf[p] >= '0' && buf[p] <= '9' {
			v = v*10 + int(buf[p]-'0')
			p++
		}
		return v
	}
	H, W, S := readInt(), readInt(), readInt()
	w2 := W + 2
	n := w2 * (H + 2)
	a := make([]int32, n)
	b := make([]int32, n)
	c := make([]int32, n)
	m := make([]int32, n)
	open := make([]bool, n)
	wall := make([]int32, n)
	for i := range c {
		c[i] = 8
		wall[i] = 1
	}
	for r := 0; r < H; r++ {
		for p < len(buf) && buf[p] != '.' && buf[p] != '#' && (buf[p] < '1' || buf[p] > '9') {
			p++
		}
		for col := 0; col < W; col++ {
			ch := buf[p]
			p++
			idx := (r+1)*w2 + col + 1
			if ch == '.' {
				open[idx] = true
				wall[idx] = 0
				m[idx] = -1
			} else if ch != '#' {
				a[idx] = int32(1000 * int(ch-'0'))
				wall[idx] = 0
			}
		}
	}
	for r := 1; r <= H; r++ {
		for col := 1; col <= W; col++ {
			idx := r*w2 + col
			if open[idx] {
				c[idx] = 4 + wall[idx-1] + wall[idx+1] + wall[idx-w2] + wall[idx+w2]
			}
		}
	}
	copy(b, a)
	lo, hi := w2+1, (H+1)*w2-1
	for s := 0; s < S; s++ {
		step(a, b, c, m, lo, hi, w2)
		a, b = b, a
	}
	var sum, best, br, bc, chk int64
	best = -1
	for r := 0; r < H; r++ {
		for col := 0; col < W; col++ {
			idx := (r+1)*w2 + col + 1
			if !open[idx] {
				continue
			}
			v := int64(a[idx])
			sum += v
			if v > best {
				best = v
				br = int64(r)
				bc = int64(col)
			}
			chk += v * (int64(r)*int64(W) + int64(col) + 1)
		}
	}
	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n", sum, best, br, bc, chk)
}
