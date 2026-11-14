package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
)

type parser struct {
	data string
	pos  int
}

func (p *parser) next() string {
	for p.pos < len(p.data) && p.data[p.pos] <= ' ' {
		p.pos++
	}
	start := p.pos
	for p.pos < len(p.data) && p.data[p.pos] > ' ' {
		p.pos++
	}
	return p.data[start:p.pos]
}

func (p *parser) integer() int {
	v, _ := strconv.Atoi(p.next())
	return v
}

func (p *parser) number() float64 {
	v, _ := strconv.ParseFloat(p.next(), 64)
	return v
}

type mass struct {
	x, v, m float64
	k, r, c float64
	f       float64
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	p := parser{data: string(data)}
	n := p.integer()
	steps := p.integer()
	dt := p.number()
	circumference := p.number()

	masses := make([]mass, n)
	for i := range masses {
		a := &masses[i]
		a.x = p.number()
		a.v = p.number()
		a.m = p.number()
		a.k = p.number()
		a.r = p.number()
		a.c = p.number()
	}

	first := &masses[0]
	for step := 0; step < steps; step++ {
		left := first
		for i := 1; i < n; i++ {
			right := &masses[i]
			stretch := (right.x - left.x) - left.r
			left.f = float64(left.k * stretch)
			left = right
		}
		stretch := ((first.x + circumference) - left.x) - left.r
		left.f = float64(left.k * stretch)

		previousForce := left.f
		for i := range masses {
			a := &masses[i]
			force := (a.f - previousForce) - float64(a.c*a.v)
			previousForce = a.f
			a.v = a.v + float64(dt*(force/a.m))
			a.x = a.x + float64(dt*a.v)
		}
	}

	var kinetic, potential, position float64
	fastest := 0
	maxSpeed := math.Abs(first.v)

	for i := range masses {
		a := &masses[i]
		energy := float64(float64(float64(0.5*a.m)*a.v) * a.v)
		kinetic += energy
		position += a.x

		speed := math.Abs(a.v)
		if speed > maxSpeed {
			maxSpeed = speed
			fastest = i
		}
	}

	left := first
	for i := 1; i < n; i++ {
		right := &masses[i]
		stretch := (right.x - left.x) - left.r
		energy := float64(float64(float64(0.5*left.k)*stretch) * stretch)
		potential += energy
		left = right
	}
	stretch := ((first.x + circumference) - left.x) - left.r
	energy := float64(float64(float64(0.5*left.k)*stretch) * stretch)
	potential += energy

	fmt.Printf(
		"kinetic %.16e\npotential %.16e\nposition %.16e\nfastest %d\n",
		kinetic, potential, position, fastest,
	)
}
