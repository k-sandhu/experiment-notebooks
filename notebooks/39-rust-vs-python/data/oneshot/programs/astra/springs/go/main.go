package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
)

type scanner struct {
	data []byte
	pos  int
}

func (s *scanner) next() string {
	for s.pos < len(s.data) && s.data[s.pos] <= ' ' {
		s.pos++
	}
	start := s.pos
	for s.pos < len(s.data) && s.data[s.pos] > ' ' {
		s.pos++
	}
	return string(s.data[start:s.pos])
}

func (s *scanner) integer() int {
	v, _ := strconv.Atoi(s.next())
	return v
}

func (s *scanner) number() float64 {
	v, _ := strconv.ParseFloat(s.next(), 64)
	return v
}

type mass struct {
	x, v, m, k, r, c, f float64
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	in := scanner{data: data}
	n := in.integer()
	steps := in.integer()
	dt := in.number()
	circumference := in.number()

	masses := make([]mass, n)
	for i := range masses {
		p := &masses[i]
		p.x = in.number()
		p.v = in.number()
		p.m = in.number()
		p.k = in.number()
		p.r = in.number()
		p.c = in.number()
	}

	last := n - 1
	for step := 0; step < steps; step++ {
		for i := 0; i < last; i++ {
			p := &masses[i]
			stretch := (masses[i+1].x - p.x) - p.r
			p.f = float64(p.k * stretch)
		}

		p := &masses[last]
		stretch := ((masses[0].x + circumference) - p.x) - p.r
		p.f = float64(p.k * stretch)

		previousForce := p.f
		for i := range masses {
			p := &masses[i]
			force := (p.f - previousForce) - float64(p.c*p.v)
			previousForce = p.f

			velocity := p.v + float64(dt*(force/p.m))
			p.v = velocity
			p.x = p.x + float64(dt*velocity)
		}
	}

	var kinetic, potential, position float64
	fastest := 0
	maxSpeed := math.Abs(masses[0].v)

	for i := range masses {
		p := &masses[i]

		energy := ((0.5 * p.m) * p.v) * p.v
		kinetic += float64(energy)
		position += p.x

		var stretch float64
		if i < last {
			stretch = (masses[i+1].x - p.x) - p.r
		} else {
			stretch = ((masses[0].x + circumference) - p.x) - p.r
		}
		energy = ((0.5 * p.k) * stretch) * stretch
		potential += float64(energy)

		speed := math.Abs(p.v)
		if speed > maxSpeed {
			maxSpeed = speed
			fastest = i
		}
	}

	fmt.Printf(
		"kinetic %.16e\npotential %.16e\nposition %.16e\nfastest %d\n",
		kinetic, potential, position, fastest,
	)
}
