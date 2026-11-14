package main

import (
	"os"
	"strconv"
	"strings"
)

var data []byte
var pos int

func nextd() float64 {
	for pos < len(data) {
		b := data[pos]
		if b == ' ' || b == '\n' || b == '\r' || b == '\t' {
			pos++
		} else {
			break
		}
	}
	start := pos
	for pos < len(data) {
		b := data[pos]
		if b == ' ' || b == '\n' || b == '\r' || b == '\t' {
			break
		}
		pos++
	}
	v, _ := strconv.ParseFloat(string(data[start:pos]), 64)
	return v
}

func main() {
	data, _ = os.ReadFile(os.Args[1])
	n := int(nextd())
	s := int(nextd())
	dt := nextd()
	P := nextd()

	x := make([]float64, n)
	v := make([]float64, n)
	m := make([]float64, n)
	k := make([]float64, n)
	r := make([]float64, n)
	c := make([]float64, n)
	f := make([]float64, n)
	for i := 0; i < n; i++ {
		x[i] = nextd()
		v[i] = nextd()
		m[i] = nextd()
		k[i] = nextd()
		r[i] = nextd()
		c[i] = nextd()
	}

	for step := 0; step < s; step++ {
		for i := 0; i < n-1; i++ {
			f[i] = k[i] * ((x[i+1] - x[i]) - r[i])
		}
		f[n-1] = k[n-1] * (((x[0] + P) - x[n-1]) - r[n-1])

		{
			F := (f[0] - f[n-1]) - (c[0] * v[0])
			nv := v[0] + dt*(F/m[0])
			x[0] = x[0] + dt*nv
			v[0] = nv
		}
		for i := 1; i < n; i++ {
			F := (f[i] - f[i-1]) - (c[i] * v[i])
			nv := v[i] + dt*(F/m[i])
			x[i] = x[i] + dt*nv
			v[i] = nv
		}
	}

	var K, U, X float64
	J := 0
	best := 0.0
	for i := 0; i < n; i++ {
		K += ((0.5 * m[i]) * v[i]) * v[i]
		X += x[i]
		av := v[i]
		if av < 0 {
			av = -av
		}
		if av > best {
			best = av
			J = i
		}
	}
	for i := 0; i < n-1; i++ {
		sp := (x[i+1] - x[i]) - r[i]
		U += ((0.5 * k[i]) * sp) * sp
	}
	{
		sp := ((x[0] + P) - x[n-1]) - r[n-1]
		U += ((0.5 * k[n-1]) * sp) * sp
	}

	var b strings.Builder
	b.Grow(200)
	b.WriteString("kinetic ")
	b.WriteString(strconv.FormatFloat(K, 'e', 17, 64))
	b.WriteString("\npotential ")
	b.WriteString(strconv.FormatFloat(U, 'e', 17, 64))
	b.WriteString("\nposition ")
	b.WriteString(strconv.FormatFloat(X, 'e', 17, 64))
	b.WriteString("\nfastest ")
	b.WriteString(strconv.Itoa(J))
	b.WriteString("\n")
	os.Stdout.WriteString(b.String())
}
