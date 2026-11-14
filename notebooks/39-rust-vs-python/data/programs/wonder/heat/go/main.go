package main

import (
	"fmt"
	"os"
)

func main() {
	buf, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	n := len(buf)
	p := 0
	var hdr [3]int
	for k := 0; k < 3; k++ {
		for p < n && (buf[p] < '0' || buf[p] > '9') {
			p++
		}
		v := 0
		for p < n && buf[p] >= '0' && buf[p] <= '9' {
			v = v*10 + int(buf[p]-'0')
			p++
		}
		hdr[k] = v
	}
	H, W, S := hdr[0], hdr[1], hdr[2]
	for p < n && buf[p] != '\n' {
		p++
	}
	if p < n {
		p++
	}
	N := H * W
	cur := make([]int32, N)
	nxt := make([]int32, N)
	kind := make([]byte, N)
	for r := 0; r < H; r++ {
		for p < n && (buf[p] == '\r' || buf[p] == '\n') {
			p++
		}
		for c := 0; c < W; c++ {
			var ch byte = '.'
			if p < n {
				ch = buf[p]
				p++
			}
			i := r*W + c
			if ch == '#' {
				kind[i] = 0
			} else if ch == '.' {
				kind[i] = 1
			} else {
				kind[i] = 2
				v := int32(int(ch-'0') * 1000)
				cur[i] = v
				nxt[i] = v
			}
		}
	}
	buf = nil
	openIdx := make([]int32, 0, N)
	runStart := make([]int32, 0, 1024)
	runLen := make([]int32, 0, 1024)
	eIdx := make([]int32, 0, 4096)
	eU := make([]int32, 0, 4096)
	eD := make([]int32, 0, 4096)
	eL := make([]int32, 0, 4096)
	eR := make([]int32, 0, 4096)
	for r := 0; r < H; r++ {
		c := 0
		for c < W {
			i := r*W + c
			if kind[i] != 1 {
				c++
				continue
			}
			fast := r > 0 && r+1 < H && c > 0 && c+1 < W && kind[i-W] != 0 && kind[i+W] != 0 && kind[i-1] != 0 && kind[i+1] != 0
			if fast {
				start := i
				length := 0
				for c < W {
					j := r*W + c
					if kind[j] != 1 {
						break
					}
					if !(r > 0 && r+1 < H && c > 0 && c+1 < W && kind[j-W] != 0 && kind[j+W] != 0 && kind[j-1] != 0 && kind[j+1] != 0) {
						break
					}
					openIdx = append(openIdx, int32(j))
					length++
					c++
				}
				runStart = append(runStart, int32(start))
				runLen = append(runLen, int32(length))
			} else {
				openIdx = append(openIdx, int32(i))
				eIdx = append(eIdx, int32(i))
				up := i
				if r > 0 && kind[i-W] != 0 {
					up = i - W
				}
				dn := i
				if r+1 < H && kind[i+W] != 0 {
					dn = i + W
				}
				lf := i
				if c > 0 && kind[i-1] != 0 {
					lf = i - 1
				}
				rt := i
				if c+1 < W && kind[i+1] != 0 {
					rt = i + 1
				}
				eU = append(eU, int32(up))
				eD = append(eD, int32(dn))
				eL = append(eL, int32(lf))
				eR = append(eR, int32(rt))
				c++
			}
		}
	}
	kind = nil
	nRuns := len(runStart)
	nEdge := len(eIdx)
	w32 := int32(W)
	for step := 0; step < S; step++ {
		for ri := 0; ri < nRuns; ri++ {
			start := int(runStart[ri])
			length := int(runLen[ri])
			for k := 0; k < length; k++ {
				i := start + k
				old := cur[i]
				nxt[i] = ((old << 2) + cur[i-int(w32)] + cur[i+int(w32)] + cur[i-1] + cur[i+1]) >> 3
			}
		}
		for k := 0; k < nEdge; k++ {
			i := int(eIdx[k])
			old := cur[i]
			nxt[i] = ((old << 2) + cur[eU[k]] + cur[eD[k]] + cur[eL[k]] + cur[eR[k]]) >> 3
		}
		cur, nxt = nxt, cur
	}
	var sum int64
	var checksum int64
	best := int32(-1)
	bestIdx := 0
	if len(openIdx) > 0 {
		bestIdx = int(openIdx[0])
	}
	for _, ii := range openIdx {
		i := int(ii)
		v := cur[i]
		sum += int64(v)
		checksum += int64(v) * int64(i+1)
		if v > best {
			best = v
			bestIdx = i
		}
	}
	br, bc := 0, 0
	if W != 0 {
		br = bestIdx / W
		bc = bestIdx % W
	}
	fmt.Printf("sum %d\nmax %d %d %d\nchecksum %d\n", sum, best, br, bc, checksum)
}
