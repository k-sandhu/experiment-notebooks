package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
)

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	t := strings.Fields(string(data))
	p := 0
	next := func() float64 {
		v, _ := strconv.ParseFloat(t[p], 64)
		p++
		return v
	}
	n := int(next())
	steps := int(next())
	dt := next()
	P := next()
	x := make([]float64, n)
	v := make([]float64, n)
	m := make([]float64, n)
	k := make([]float64, n)
	r := make([]float64, n)
	c := make([]float64, n)
	for i := 0; i < n; i++ {
		x[i] = next()
		v[i] = next()
		m[i] = next()
		k[i] = next()
		r[i] = next()
		c[i] = next()
	}
	n1 := n - 1
	for s := 0; s < steps; s++ {
		flast := k[n1] * (((x[0] + P) - x[n1]) - r[n1])
		fprev := flast
		xs := x[:n]
		vs := v[:n]
		ms := m[:n]
		ks := k[:n]
		rs := r[:n]
		cs := c[:n]
		for i := 0; i < n1; i++ {
			f := ks[i] * ((xs[i+1] - xs[i]) - rs[i])
			F := (f - fprev) - (cs[i] * vs[i])
			nv := vs[i] + dt*(F/ms[i])
			vs[i] = nv
			xs[i] = xs[i] + dt*nv
			fprev = f
		}
		F := (flast - fprev) - (c[n1] * v[n1])
		nv := v[n1] + dt*(F/m[n1])
		v[n1] = nv
		x[n1] = x[n1] + dt*nv
	}
	var kin, pot, pos float64
	best := -1.0
	bi := 0
	for i := 0; i < n; i++ {
		kin += ((0.5 * m[i]) * v[i]) * v[i]
		var st float64
		if i < n1 {
			st = (x[i+1] - x[i]) - r[i]
		} else {
			st = ((x[0] + P) - x[n1]) - r[n1]
		}
		pot += ((0.5 * k[i]) * st) * st
		pos += x[i]
		a := math.Abs(v[i])
		if a > best {
			best = a
			bi = i
		}
	}
	fmt.Printf("kinetic %.12e\npotential %.12e\nposition %.12e\nfastest %d\n", kin, pot, pos, bi)
}
