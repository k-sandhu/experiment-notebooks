package main

import (
	"os"
	"strconv"
)

func isWall(ch byte) bool {
	return ch != '.' && !(ch >= '1' && ch <= '9')
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	pos := 0
	readInt := func() int {
		for pos < len(data) && (data[pos] < '0' || data[pos] > '9') {
			pos++
		}
		v := 0
		for pos < len(data) && data[pos] >= '0' && data[pos] <= '9' {
			v = v*10 + int(data[pos]-'0')
			pos++
		}
		return v
	}
	H := readInt()
	W := readInt()
	S := readInt()
	if H <= 0 || W <= 0 {
		os.Stdout.WriteString("sum 0\nmax 0 0 0\nchecksum 0\n")
		return
	}

	grid := make([]byte, H*W)
	for i := range grid {
		grid[i] = '#'
	}
	for r := 0; r < H; r++ {
		for pos < len(data) && (data[pos] == '\n' || data[pos] == '\r' || data[pos] == ' ' || data[pos] == '\t') {
			pos++
		}
		end := pos + W
		if end > len(data) {
			end = len(data)
		}
		n := copy(grid[r*W:(r+1)*W], data[pos:end])
		pos += n
	}

	// 4 cells per uint64, 16-bit lanes. Each row has WW words plus one zero pad word.
	WW := (W + 3) / 4
	ST := WW + 1
	cur := make([]uint64, (H+2)*ST)
	nxt := make([]uint64, (H+2)*ST)
	m1 := make([]uint64, H*WW)
	m2 := make([]uint64, H*WW)
	mo := make([]uint64, H*WW)

	for r := 0; r < H; r++ {
		row := grid[r*W : (r+1)*W]
		for c := 0; c < W; c++ {
			ch := row[c]
			sh := uint(c&3) * 16
			if ch == '.' {
				cnt := 0
				if r == 0 || isWall(grid[(r-1)*W+c]) {
					cnt++
				}
				if r == H-1 || isWall(grid[(r+1)*W+c]) {
					cnt++
				}
				if c == 0 || isWall(row[c-1]) {
					cnt++
				}
				if c == W-1 || isWall(row[c+1]) {
					cnt++
				}
				if cnt < 4 {
					idx := r*WW + c>>2
					mo[idx] |= uint64(0xFFFF) << sh
					if cnt&1 != 0 {
						m1[idx] |= uint64(0xFFFF) << sh
					}
					if cnt&2 != 0 {
						m2[idx] |= uint64(0xFFFF) << sh
					}
				}
			} else if ch >= '1' && ch <= '9' {
				cur[(r+1)*ST+c>>2] |= (uint64(ch-'0') * 1000) << sh
			}
		}
	}

	const maskQ = 0x3FFF3FFF3FFF3FFF
	const maskH = 0x7FFF7FFF7FFF7FFF

	for step := 0; step < S; step++ {
		var diff uint64
		for r := 0; r < H; r++ {
			base := (r + 1) * ST
			o := nxt[base : base+WW]
			n := len(o)
			c := cur[base : base+WW+1]
			c = c[:n+1]
			u := cur[base-ST : base-ST+WW]
			u = u[:n]
			d := cur[base+ST : base+ST+WW]
			d = d[:n]
			mb := r * WW
			k1 := m1[mb : mb+WW]
			k1 = k1[:n]
			k2 := m2[mb : mb+WW]
			k2 = k2[:n]
			ko := mo[mb : mb+WW]
			ko = ko[:n]
			var prev uint64
			a := c[0]
			for j := 0; j < n; j++ {
				nx := c[j+1]
				l := a<<16 | prev>>48
				rr := a>>16 | nx<<48
				s := u[j] + d[j] + l + rr + (a & k1[j]) + ((a & k2[j]) << 1)
				q := (s >> 2) & maskQ
				comp := ((a + q) >> 1) & maskH
				x := (a ^ comp) & ko[j]
				o[j] = a ^ x
				diff |= x
				prev = a
				a = nx
			}
		}
		cur, nxt = nxt, cur
		if diff == 0 {
			break
		}
	}

	var sum, checksum int64
	var maxV int64 = -1
	maxR, maxC := 0, 0
	for r := 0; r < H; r++ {
		row := grid[r*W : (r+1)*W]
		base := (r + 1) * ST
		for c := 0; c < W; c++ {
			if row[c] != '.' {
				continue
			}
			v := int64((cur[base+c>>2] >> (uint(c&3) * 16)) & 0xFFFF)
			sum += v
			if v > maxV {
				maxV = v
				maxR = r
				maxC = c
			}
			checksum += v * int64(r*W+c+1)
		}
	}
	if maxV < 0 {
		maxV = 0
	}

	out := make([]byte, 0, 128)
	out = append(out, "sum "...)
	out = strconv.AppendInt(out, sum, 10)
	out = append(out, "\nmax "...)
	out = strconv.AppendInt(out, maxV, 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(maxR), 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(maxC), 10)
	out = append(out, "\nchecksum "...)
	out = strconv.AppendInt(out, checksum, 10)
	out = append(out, '\n')
	os.Stdout.Write(out)
}
