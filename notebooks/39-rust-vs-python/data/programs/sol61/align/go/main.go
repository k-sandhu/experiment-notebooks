package main

import (
	"bytes"
	"os"
	"strconv"
)

type input struct {
	data []byte
	pos  int
}

func (in *input) token() []byte {
	for in.pos < len(in.data) && in.data[in.pos] <= ' ' {
		in.pos++
	}
	start := in.pos
	for in.pos < len(in.data) && in.data[in.pos] > ' ' {
		in.pos++
	}
	return in.data[start:in.pos]
}

func (in *input) number() int {
	value := 0
	for _, c := range in.token() {
		value = value*10 + int(c-'0')
	}
	return value
}

type alignment struct {
	ins, del         [2][26]int32
	sub              [2][26][26]int32
	profile          [26][]int32
	insertion, row32 []int32
	row64            []int64
}

func (a *alignment) cost(s, t []byte) int64 {
	if bytes.Equal(s, t) {
		return 0
	}
	direction := 0
	if len(s) < len(t) {
		s, t = t, s
		direction = 1
	}
	m := len(t)
	if len(a.insertion) < m {
		a.insertion = make([]int32, m)
	}
	insertion := a.insertion[:m]
	deletion, insert := &a.del[direction], &a.ins[direction]
	var bound int64
	var used uint32
	for _, c := range s {
		letter := c - 'A'
		bound += int64(deletion[letter])
		used |= 1 << letter
	}
	for j, c := range t {
		insertion[j] = insert[c-'A']
		bound += int64(insertion[j])
	}
	if bound == 0 {
		return 0
	}
	for c := 0; c < 26; c++ {
		if used&(1<<c) == 0 {
			continue
		}
		if len(a.profile[c]) < m {
			a.profile[c] = make([]int32, m)
		}
		costs, table := a.profile[c][:m], &a.sub[direction][c]
		for j, letter := range t {
			costs[j] = table[letter-'A']
		}
	}
	// Leave headroom for an individual cost before taking the minimum.
	if bound <= 2147483647-1000 {
		return int64(a.evaluate32(s, m, deletion))
	}
	return a.evaluate64(s, m, deletion)
}

func (a *alignment) evaluate32(s []byte, m int, deletion *[26]int32) int32 {
	if len(a.row32) < m {
		a.row32 = make([]int32, m)
	}
	row, insert := a.row32[:m], a.insertion[:m]
	var prefix int32
	for j, value := range insert {
		prefix += value
		row[j] = prefix
	}
	var boundary int32
	for _, c := range s {
		d := deletion[c-'A']
		costs := a.profile[c-'A'][:m]
		diagonal := boundary
		boundary += d
		left := boundary
		for j, above := range row {
			left = min(above+d, left+insert[j], diagonal+costs[j])
			row[j] = left
			diagonal = above
		}
	}
	return row[m-1]
}

func (a *alignment) evaluate64(s []byte, m int, deletion *[26]int32) int64 {
	if len(a.row64) < m {
		a.row64 = make([]int64, m)
	}
	row, insert := a.row64[:m], a.insertion[:m]
	var prefix int64
	for j, value := range insert {
		prefix += int64(value)
		row[j] = prefix
	}
	var boundary int64
	for _, c := range s {
		d := int64(deletion[c-'A'])
		costs := a.profile[c-'A'][:m]
		diagonal := boundary
		boundary += d
		left := boundary
		for j, above := range row {
			left = min(above+d, left+int64(insert[j]), diagonal+int64(costs[j]))
			row[j] = left
			diagonal = above
		}
	}
	return row[m-1]
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	in := input{data: data}
	alphabet := in.token()
	var solver alignment
	for _, c := range alphabet {
		solver.ins[0][c-'A'] = int32(in.number())
	}
	for _, c := range alphabet {
		solver.del[0][c-'A'] = int32(in.number())
	}
	for _, c := range alphabet {
		for _, d := range alphabet {
			solver.sub[0][c-'A'][d-'A'] = int32(in.number())
		}
	}
	for c := 0; c < 26; c++ {
		solver.ins[1][c] = solver.del[0][c]
		solver.del[1][c] = solver.ins[0][c]
		for d := 0; d < 26; d++ {
			solver.sub[1][c][d] = solver.sub[0][d][c]
		}
	}
	pairs := in.number()
	var total int64
	output := make([]byte, 0, 4096)
	for p := 0; p < pairs; p++ {
		s, t := in.token(), in.token()
		result := solver.cost(s, t)
		total += result
		output = strconv.AppendInt(output, result, 10)
		output = append(output, '\n')
	}
	output = append(output, "total "...)
	output = strconv.AppendInt(output, total, 10)
	output = append(output, '\n')
	os.Stdout.Write(output)
}
