package main

import (
	"os"
	"strconv"
)

func main() {
	buf, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	rd := len(buf)
	p := 0

	nextInt := func() int {
		for p < rd && (buf[p] < '0' || buf[p] > '9') {
			p++
		}
		v := 0
		for p < rd && buf[p] >= '0' && buf[p] <= '9' {
			v = v*10 + int(buf[p]-'0')
			p++
		}
		return v
	}

	H := nextInt()
	W := nextInt()
	S := nextInt()
	n := H * W

	cur := make([]int32, n)
	nxt := make([]int32, n)
	wall := make([]bool, n)
	openList := make([]int32, 0, n)

	for p < rd && buf[p] != '\n' {
		p++
	}
	if p < rd {
		p++
	}

	for r := 0; r < H; r++ {
		for c := 0; c < W; c++ {
			ch := buf[p]
			p++
			i := r*W + c
			if ch == '#' {
				wall[i] = true
			} else if ch >= '1' && ch <= '9' {
				cur[i] = int32(ch-'0') * 1000
			} else {
				openList = append(openList, int32(i))
			}
		}
		for p < rd && buf[p] != '\n' {
			p++
		}
		if p < rd {
			p++
		}
	}

	copy(nxt, cur) // sources keep their fixed value in the swap buffer

	m := len(openList)
	iup := make([]int32, n)
	idown := make([]int32, n)
	ileft := make([]int32, n)
	iright := make([]int32, n)
	for k := 0; k < m; k++ {
		i := int(openList[k])
		r, c := i/W, i%W
		if r > 0 && !wall[i-W] {
			iup[i] = int32(i - W)
		} else {
			iup[i] = int32(i)
		}
		if r+1 < H && !wall[i+W] {
			idown[i] = int32(i + W)
		} else {
			idown[i] = int32(i)
		}
		if c > 0 && !wall[i-1] {
			ileft[i] = int32(i - 1)
		} else {
			ileft[i] = int32(i)
		}
		if c+1 < W && !wall[i+1] {
			iright[i] = int32(i + 1)
		} else {
			iright[i] = int32(i)
		}
	}

	for s := 0; s < S; s++ {
		for k := 0; k < m; k++ {
			i := openList[k]
			v := cur[i]
			nxt[i] = (4*v + cur[iup[i]] + cur[idown[i]] + cur[ileft[i]] + cur[iright[i]]) >> 3
		}
		cur, nxt = nxt, cur
	}

	sum := int64(0)
	chk := int64(0)
	mx := int32(-1)
	mi := int32(0)
	for k := 0; k < m; k++ {
		i := openList[k]
		v := cur[i]
		sum += int64(v)
		chk += int64(v) * int64(i+1)
		if v > mx {
			mx = v
			mi = i
		}
	}

	out := make([]byte, 0, 96)
	out = append(out, "sum "...)
	out = strconv.AppendInt(out, sum, 10)
	out = append(out, "\nmax "...)
	out = strconv.AppendInt(out, int64(mx), 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(mi/int32(W)), 10)
	out = append(out, ' ')
	out = strconv.AppendInt(out, int64(mi%int32(W)), 10)
	out = append(out, "\nchecksum "...)
	out = strconv.AppendInt(out, chk, 10)
	out = append(out, '\n')
	os.Stdout.Write(out)
}
