package main

import (
	"bytes"
	"os"
	"runtime"
	"strconv"
)

type parser struct {
	data []byte
	pos  int
}

func (p *parser) token() []byte {
	for p.pos < len(p.data) && p.data[p.pos] <= ' ' {
		p.pos++
	}
	start := p.pos
	for p.pos < len(p.data) && p.data[p.pos] > ' ' {
		p.pos++
	}
	return p.data[start:p.pos]
}

func (p *parser) number() int {
	for p.pos < len(p.data) && p.data[p.pos] <= ' ' {
		p.pos++
	}
	value := 0
	for p.pos < len(p.data) {
		c := p.data[p.pos]
		if c < '0' || c > '9' {
			break
		}
		value = value*10 + int(c-'0')
		p.pos++
	}
	return value
}

type column struct {
	value  int64
	insert int64
	letter byte
}

func main() {
	runtime.GOMAXPROCS(1)
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	p := parser{data: data}
	alphabet := p.token()

	var index [256]uint8
	var insertion, deletion [256]int64
	var forward, reverse [26][256]int64

	for i, c := range alphabet {
		index[c] = uint8(i)
	}
	for _, c := range alphabet {
		insertion[c] = int64(p.number())
	}
	for _, c := range alphabet {
		deletion[c] = int64(p.number())
	}
	for i, source := range alphabet {
		for j, target := range alphabet {
			cost := int64(p.number())
			forward[i][target] = cost
			reverse[j][source] = cost
		}
	}

	pairs := p.number()
	var columns []column
	output := make([]byte, 0, 4096)
	var total int64

	for pair := 0; pair < pairs; pair++ {
		s := p.token()
		t := p.token()

		if bytes.Equal(s, t) {
			output = append(output, '0', '\n')
			continue
		}

		ins := &insertion
		del := &deletion
		sub := &forward

		if len(t) > len(s) {
			s, t = t, s
			ins, del = del, ins
			sub = &reverse
		}

		if cap(columns) < len(t) {
			columns = make([]column, len(t))
		} else {
			columns = columns[:len(t)]
		}

		var initial int64
		for j, c := range t {
			cost := ins[c]
			initial += cost
			columns[j] = column{
				value:  initial,
				insert: cost,
				letter: c,
			}
		}

		var first int64
		for _, c := range s {
			deleteCost := del[c]
			subRow := &sub[index[c]]
			diagonal := first
			first += deleteCost
			left := first

			for j := range columns {
				cell := &columns[j]
				above := cell.value
				best := min(
					above+deleteCost,
					left+cell.insert,
					diagonal+subRow[cell.letter],
				)
				cell.value = best
				diagonal = above
				left = best
			}
		}

		cost := columns[len(columns)-1].value
		total += cost
		output = strconv.AppendInt(output, cost, 10)
		output = append(output, '\n')
	}

	output = append(output, "total "...)
	output = strconv.AppendInt(output, total, 10)
	output = append(output, '\n')
	_, _ = os.Stdout.Write(output)
}
