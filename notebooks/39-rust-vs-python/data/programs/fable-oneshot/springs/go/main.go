package main

import (
	"math"
	"os"
	"strconv"
)

type mass struct {
	x, v, m, k, r, c float64
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	pos := 0
	next := func() string {
		for pos < len(data) && data[pos] <= ' ' {
			pos++
		}
		st := pos
		for pos < len(data) && data[pos] > ' ' {
			pos++
		}
		return string(data[st:pos])
	}
	nextF := func() float64 {
		f, _ := strconv.ParseFloat(next(), 64)
		return f
	}

	n, _ := strconv.Atoi(next())
	steps, _ := strconv.Atoi(next())
	dt := nextF()
	P := nextF()
	if n < 1 {
		os.Exit(1)
	}

	parts := make([]mass, n)
	for i := 0; i < n; i++ {
		p := &parts[i]
		p.x = nextF()
		p.v = nextF()
		p.m = nextF()
		p.k = nextF()
		p.r = nextF()
		p.c = nextF()
	}

	ps := parts[:n]
	last := &ps[n-1]
	for step := 0; step < steps; step++ {
		xi := ps[0].x
		flast := float64(last.k * (((xi + P) - last.x) - last.r))
		fprev := flast
		for i := 1; i < len(ps); i++ {
			q := &ps[i]
			p := &ps[i-1]
			xn := q.x
			fi := float64(p.k * ((xn - xi) - p.r))
			pv := p.v
			F := (fi - fprev) - float64(p.c*pv)
			nv := pv + float64(dt*(F/p.m))
			p.v = nv
			p.x = xi + float64(dt*nv)
			fprev = fi
			xi = xn
		}
		pv := last.v
		F := (flast - fprev) - float64(last.c*pv)
		nv := pv + float64(dt*(F/last.m))
		last.v = nv
		last.x = xi + float64(dt*nv)
	}

	var K, U, X float64
	bestIdx := 0
	best := math.Abs(ps[0].v)
	for i := 0; i < n; i++ {
		p := &ps[i]
		K += float64(float64(float64(0.5*p.m)*p.v) * p.v)
		var s float64
		if i < n-1 {
			s = (ps[i+1].x - p.x) - p.r
		} else {
			s = ((ps[0].x + P) - p.x) - p.r
		}
		U += float64(float64(float64(0.5*p.k)*s) * s)
		X += p.x
		a := math.Abs(p.v)
		if a > best {
			best = a
			bestIdx = i
		}
	}

	out := make([]byte, 0, 256)
	out = append(out, "kinetic "...)
	out = strconv.AppendFloat(out, K, 'e', 16, 64)
	out = append(out, "\npotential "...)
	out = strconv.AppendFloat(out, U, 'e', 16, 64)
	out = append(out, "\nposition "...)
	out = strconv.AppendFloat(out, X, 'e', 16, 64)
	out = append(out, "\nfastest "...)
	out = strconv.AppendInt(out, int64(bestIdx), 10)
	out = append(out, '\n')
	os.Stdout.Write(out)
}
