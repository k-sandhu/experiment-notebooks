package main

import (
	"fmt"
	"os"
	"strconv"
)

type parser struct {
	data []byte
	pos  int
}

func (p *parser) skip() {
	for p.pos < len(p.data) {
		b := p.data[p.pos]
		if b == ' ' || b == '\n' || b == '\r' || b == '\t' {
			p.pos++
		} else {
			break
		}
	}
}

func (p *parser) nextToken() []byte {
	p.skip()
	start := p.pos
	for p.pos < len(p.data) {
		b := p.data[p.pos]
		if b == ' ' || b == '\n' || b == '\r' || b == '\t' {
			break
		}
		p.pos++
	}
	return p.data[start:p.pos]
}

func (p *parser) nextFloat() float64 {
	tok := p.nextToken()
	v, _ := strconv.ParseFloat(string(tok), 64)
	return v
}

func (p *parser) nextInt() int64 {
	tok := p.nextToken()
	var v int64
	for _, b := range tok {
		v = v*10 + int64(b-'0')
	}
	return v
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	p := &parser{data: data}

	n := int(p.nextInt())
	steps := p.nextInt()
	dt := p.nextFloat()
	P := p.nextFloat()

	x := make([]float64, n)
	v := make([]float64, n)
	m := make([]float64, n)
	k := make([]float64, n)
	r := make([]float64, n)
	c := make([]float64, n)
	for i := 0; i < n; i++ {
		x[i] = p.nextFloat()
		v[i] = p.nextFloat()
		m[i] = p.nextFloat()
		k[i] = p.nextFloat()
		r[i] = p.nextFloat()
		c[i] = p.nextFloat()
	}

	last := n - 1
	for t := int64(0); t < steps; t++ {
		x0 := x[0]
		xl := x[last]
		sLast := ((x0 + P) - xl) - r[last]
		fLast := k[last] * sLast
		fprev := fLast

		for i := 0; i < last; i++ {
			s := (x[i+1] - x[i]) - r[i]
			f := k[i] * s
			F := (f - fprev) - c[i]*v[i]
			nv := v[i] + dt*(F/m[i])
			v[i] = nv
			x[i] = x[i] + dt*nv
			fprev = f
		}

		Fl := (fLast - fprev) - c[last]*v[last]
		nvl := v[last] + dt*(Fl/m[last])
		v[last] = nvl
		x[last] = x[last] + dt*nvl
	}

	K := 0.0
	U := 0.0
	X := 0.0
	for i := 0; i < n; i++ {
		K += ((0.5 * m[i]) * v[i]) * v[i]
		X += x[i]
	}
	for i := 0; i < last; i++ {
		s := (x[i+1] - x[i]) - r[i]
		U += ((0.5 * k[i]) * s) * s
	}
	{
		s := ((x[0] + P) - x[last]) - r[last]
		U += ((0.5 * k[last]) * s) * s
	}

	fastest := 0
	best := -1.0
	for i := 0; i < n; i++ {
		a := v[i]
		if a < 0 {
			a = -a
		}
		if a > best {
			best = a
			fastest = i
		}
	}

	fmt.Printf("kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n", K, U, X, fastest)
}
