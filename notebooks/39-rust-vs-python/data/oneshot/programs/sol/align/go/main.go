package main

import (
	"bytes"
	"os"
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

func (p *parser) integer() int64 {
	for p.pos < len(p.data) && p.data[p.pos] <= ' ' {
		p.pos++
	}
	var value int64
	for p.pos < len(p.data) {
		c := p.data[p.pos]
		if c < '0' || c > '9' {
			break
		}
		value = value*10 + int64(c-'0')
		p.pos++
	}
	return value
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	p := parser{data: data}
	alphabet := p.token()

	var insertion, deletion [256]int64
	var substitution [26][256]int64

	for _, c := range alphabet {
		insertion[c] = p.integer()
	}
	for _, c := range alphabet {
		deletion[c] = p.integer()
	}
	for _, source := range alphabet {
		row := &substitution[source-'A']
		for _, target := range alphabet {
			row[target] = p.integer()
		}
	}

	pairs := int(p.integer())
	output := make([]byte, 0, 4096)
	var dp []int64
	var total int64

	for pair := 0; pair < pairs; pair++ {
		s := p.token()
		t := p.token()

		var cost int64
		if !bytes.Equal(s, t) {
			m := len(t)
			if cap(dp) < m+1 {
				dp = make([]int64, m+1)
			} else {
				dp = dp[:m+1]
			}

			dp[0] = 0
			var prefix int64
			for j, c := range t {
				prefix += insertion[c]
				dp[j+1] = prefix
			}

			cells := dp[1:]
			for _, source := range s {
				row := &substitution[source-'A']
				deleteCost := deletion[source]
				diagonal := dp[0]
				left := diagonal + deleteCost
				dp[0] = left

				for j, target := range t {
					above := cells[j]
					best := min(
						diagonal+row[target],
						above+deleteCost,
						left+insertion[target],
					)
					cells[j] = best
					diagonal = above
					left = best
				}
			}
			cost = dp[m]
		}

		total += cost
		output = strconv.AppendInt(output, cost, 10)
		output = append(output, '\n')
	}

	output = append(output, "total "...)
	output = strconv.AppendInt(output, total, 10)
	output = append(output, '\n')
	_, _ = os.Stdout.Write(output)
}
