package main

import (
	"fmt"
	"os"
)

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	at := 0
	number := func() int {
		for data[at] <= ' ' {
			at++
		}
		n := 0
		for at < len(data) && data[at] > ' ' {
			n = n*10 + int(data[at]-'0')
			at++
		}
		return n
	}
	h, w, steps := number(), number(), number()
	stride := w + 2
	size := (h + 2) * stride
	a, b, coeff := make([]int32, size), make([]int32, size), make([]int32, size)
	cells := make([]int, 0, h*w)
	for r := 0; r < h; r++ {
		for data[at] <= ' ' {
			at++
		}
		for c := 0; c < w; c++ {
			ch := data[at]
			at++
			p := (r+1)*stride + c + 1
			if ch == '.' {
				cells = append(cells, p)
				coeff[p] = 4
			} else if ch != '#' {
				a[p] = int32(ch-'0') * 1000
				b[p] = a[p]
			}
			if ch != '#' {
				coeff[p] |= 16
			}
		}
	}
	for _, p := range cells {
		n := int32(0)
		if coeff[p-stride] != 0 {
			n++
		}
		if coeff[p+stride] != 0 {
			n++
		}
		if coeff[p-1] != 0 {
			n++
		}
		if coeff[p+1] != 0 {
			n++
		}
		coeff[p] = 8 - n
	}
	for s := 0; s < steps; s++ {
		for _, p := range cells {
			b[p] = (coeff[p]*a[p] + a[p-stride] + a[p+stride] + a[p-1] + a[p+1]) >> 3
		}
		a, b = b, a
	}
	var sum, checksum int64
	best, pos := int32(-1), 0
	for _, p := range cells {
		v := a[p]
		r, c := p/stride-1, p%stride-1
		sum += int64(v)
		checksum += int64(v) * (int64(r)*int64(w) + int64(c) + 1)
		if v > best {
			best = v
			pos = p
		}
	}
	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n", sum, best, pos/stride-1, pos%stride-1, checksum)
}
