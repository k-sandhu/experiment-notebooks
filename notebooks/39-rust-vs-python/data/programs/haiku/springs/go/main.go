// Springs on a ring: explicit time stepping of N masses joined by N springs (see SPEC.md).
//
// Each step runs in two passes over flat float64 slices. The arithmetic keeps the spec's
// operation order, so the results match the reference bit for bit, apart from summation order
// in the final sums.
package main

import (
	"bytes"
	"fmt"
	"math"
	"os"
	"strconv"
)

type ring struct {
	n             int
	steps         int64
	dt            float64
	circumference float64
	x, v, m       []float64
	k, r, c       []float64
	f             []float64 // spring forces for the current step
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: solution INPUT_PATH")
		os.Exit(1)
	}
	rg, err := readRing(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	n := rg.n

	for s := int64(0); s < rg.steps; s++ {
		rg.step()
	}

	p := rg.circumference
	x, v, m, k, r := rg.x, rg.v, rg.m, rg.k, rg.r

	kinetic := 0.0
	for i := 0; i < n; i++ {
		kinetic += ((0.5 * m[i]) * v[i]) * v[i]
	}

	potential := 0.0
	for i := 0; i+1 < n; i++ {
		s := (x[i+1] - x[i]) - r[i]
		potential += ((0.5 * k[i]) * s) * s
	}
	sLast := ((x[0] + p) - x[n-1]) - r[n-1]
	potential += ((0.5 * k[n-1]) * sLast) * sLast

	position := 0.0
	for i := 0; i < n; i++ {
		position += x[i]
	}

	fastest := 0
	for i := 1; i < n; i++ {
		if math.Abs(v[i]) > math.Abs(v[fastest]) {
			fastest = i
		}
	}

	fmt.Printf("kinetic %.16e\n", kinetic)
	fmt.Printf("potential %.16e\n", potential)
	fmt.Printf("position %.16e\n", position)
	fmt.Printf("fastest %d\n", fastest)
}

// One time step (SPEC.md, "One time step").
func (rg *ring) step() {
	n := rg.n
	p := rg.circumference
	dt := rg.dt
	x, v, m := rg.x[:n], rg.v[:n], rg.m[:n]
	k, r, c, f := rg.k[:n], rg.r[:n], rg.c[:n], rg.f[:n]

	// Pass 1: spring forces from the old positions. Spring n-1 wraps around to mass 0.
	for i := 0; i+1 < n; i++ {
		f[i] = k[i] * ((x[i+1] - x[i]) - r[i])
	}
	f[n-1] = k[n-1] * (((x[0] + p) - x[n-1]) - r[n-1])

	// Pass 2: velocity from the forces (old velocity), then position from the new velocity.
	// Mass 0 uses the force of spring n-1 as its left neighbour.
	v[0] = v[0] + dt*(((f[0]-f[n-1])-(c[0]*v[0]))/m[0])
	for i := 1; i < n; i++ {
		v[i] = v[i] + dt*(((f[i]-f[i-1])-(c[i]*v[i]))/m[i])
	}
	for i := range x {
		x[i] = x[i] + dt*v[i]
	}
}

func readRing(path string) (*ring, error) {
	text, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	tokens := bytes.Fields(text)
	next := func() (float64, error) {
		if len(tokens) == 0 {
			return 0, fmt.Errorf("input ends early")
		}
		tok := tokens[0]
		tokens = tokens[1:]
		return strconv.ParseFloat(string(tok), 64)
	}

	nTok, err := next()
	if err != nil {
		return nil, err
	}
	stepsTok, err := next()
	if err != nil {
		return nil, err
	}
	dt, err := next()
	if err != nil {
		return nil, err
	}
	p, err := next()
	if err != nil {
		return nil, err
	}
	n := int(nTok)
	rg := &ring{
		n: n, steps: int64(stepsTok), dt: dt, circumference: p,
		x: make([]float64, n), v: make([]float64, n), m: make([]float64, n),
		k: make([]float64, n), r: make([]float64, n), c: make([]float64, n),
		f: make([]float64, n),
	}
	columns := [][]float64{rg.x, rg.v, rg.m, rg.k, rg.r, rg.c}
	for i := 0; i < n; i++ {
		for _, column := range columns {
			val, err := next()
			if err != nil {
				return nil, err
			}
			column[i] = val
		}
	}
	return rg, nil
}
