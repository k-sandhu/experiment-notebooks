// Weighted alignment cost (see SPEC.md).
//
// The input file is read in one call and parsed in place. The DP keeps one row of int64 costs,
// updated in place, with the diagonal and left values held in locals. Substitution rows are
// [256]int64 arrays indexed by a letter code (a uint8), so the hot lookup has no bounds check.
// Scratch slices are reused across pairs and only grow.
package main

import (
	"fmt"
	"os"
	"strconv"
)

// parser walks the input bytes; tokens are whitespace-separated runs.
type parser struct {
	data []byte
	pos  int
}

// token returns the next whitespace-separated run of bytes.
func (p *parser) token() []byte {
	d := p.data
	i := p.pos
	for i < len(d) && d[i] <= ' ' {
		i++
	}
	start := i
	for i < len(d) && d[i] > ' ' {
		i++
	}
	p.pos = i
	return d[start:i]
}

func (p *parser) number() int64 {
	var v int64
	for _, c := range p.token() {
		v = v*10 + int64(c-'0')
	}
	return v
}

// alignCost returns D[n][m] for the pair. s and t hold letter codes; tIns[k] is the insertion
// cost of t[k]. row must hold len(t)+1 values.
func alignCost(s, t []uint8, tIns []int64, del []int64, sub [][256]int64, row []int64) int64 {
	m := len(t)
	row = row[:m+1]
	cells := row[1 : m+1 : m+1] // cells[k] is D[i][k+1]
	insK := tIns[:m]

	row[0] = 0
	for j := 1; j <= m; j++ {
		row[j] = row[j-1] + insK[j-1]
	}

	for _, si := range s {
		d := del[si]
		subRow := &sub[si]

		diag := row[0]
		row[0] += d
		left := row[0]
		for k, tk := range t {
			up := cells[k]
			v := min(min(up+d, diag+subRow[tk]), left+insK[k])
			cells[k] = v
			left = v
			diag = up
		}
	}
	return row[m]
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: solution INPUT_PATH")
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	p := &parser{data: data}

	alphabet := p.token()
	a := len(alphabet)
	var code [256]uint8
	for i, c := range alphabet {
		code[c] = uint8(i)
	}

	ins := make([]int64, a)
	del := make([]int64, a)
	sub := make([][256]int64, a)
	for i := range ins {
		ins[i] = p.number()
	}
	for i := range del {
		del[i] = p.number()
	}
	for i := 0; i < a; i++ {
		for j := 0; j < a; j++ {
			sub[i][j] = p.number()
		}
	}

	pairs := p.number()

	var s, t []uint8
	var tIns, row []int64
	out := make([]byte, 0, 16*int(pairs)+32)
	var total int64

	for k := int64(0); k < pairs; k++ {
		sTok := p.token()
		tTok := p.token()
		n, m := len(sTok), len(tTok)

		if cap(s) < n {
			s = make([]uint8, n)
		}
		if cap(t) < m {
			t = make([]uint8, m)
			tIns = make([]int64, m)
		}
		if cap(row) < m+1 {
			row = make([]int64, m+1)
		}
		s = s[:n]
		t = t[:m]
		tIns = tIns[:m]
		for i, c := range sTok {
			s[i] = code[c]
		}
		for j, c := range tTok {
			t[j] = code[c]
			tIns[j] = ins[t[j]]
		}

		cost := alignCost(s, t, tIns, del, sub, row)
		total += cost
		out = strconv.AppendInt(out, cost, 10)
		out = append(out, '\n')
	}

	out = append(out, "total "...)
	out = strconv.AppendInt(out, total, 10)
	out = append(out, '\n')
	if _, err := os.Stdout.Write(out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
