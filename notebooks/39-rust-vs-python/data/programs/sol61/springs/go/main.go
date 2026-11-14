package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
)

type input struct {
	data string
	at   int
}

func (in *input) token() string {
	for in.at < len(in.data) && in.data[in.at] <= ' ' {
		in.at++
	}
	start := in.at
	for in.at < len(in.data) && in.data[in.at] > ' ' {
		in.at++
	}
	return in.data[start:in.at]
}

func (in *input) number() float64 {
	x, _ := strconv.ParseFloat(in.token(), 64)
	return x
}

func simulate(n, steps int, dt, p float64, x, v, m, k, r, c []float64) {
	last := n - 1
	// These checks let the compiler remove bounds checks from the hot loop.
	_ = x[last]
	_ = v[last]
	_ = m[last]
	_ = k[last]
	_ = r[last]
	_ = c[last]
	for step := 0; step < steps; step++ {
		current := x[0]
		lastForce := float64(k[last] * (((current + p) - x[last]) - r[last]))
		previousForce := lastForce
		// Carry the old position and spring force forward before overwriting x.
		for i := 0; i < last; i++ {
			next := x[i+1]
			force := float64(k[i] * ((next - current) - r[i]))
			// Explicit conversions also prohibit Go's optional FMA contraction.
			damping := float64(c[i] * v[i])
			net := (force - previousForce) - damping
			velocity := v[i] + float64(dt*(net/m[i]))
			v[i] = velocity
			x[i] = current + float64(dt*velocity)
			current = next
			previousForce = force
		}
		damping := float64(c[last] * v[last])
		net := (lastForce - previousForce) - damping
		velocity := v[last] + float64(dt*(net/m[last]))
		v[last] = velocity
		x[last] = current + float64(dt*velocity)
	}
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	in := input{data: string(data)}
	n, _ := strconv.Atoi(in.token())
	steps, _ := strconv.Atoi(in.token())
	dt, p := in.number(), in.number()
	storage := make([]float64, 6*n)
	x, v, m := storage[:n:n], storage[n:2*n:2*n], storage[2*n:3*n:3*n]
	k, r, c := storage[3*n:4*n:4*n], storage[4*n:5*n:5*n], storage[5*n:6*n:6*n]
	for i := 0; i < n; i++ {
		x[i], v[i], m[i] = in.number(), in.number(), in.number()
		k[i], r[i], c[i] = in.number(), in.number(), in.number()
	}
	simulate(n, steps, dt, p, x, v, m, k, r, c)
	kinetic, potential, position := 0.0, 0.0, 0.0
	fastest, speed := 0, math.Abs(v[0])
	for i := 0; i < n; i++ {
		kinetic += ((0.5 * m[i]) * v[i]) * v[i]
		var stretch float64
		if i+1 < n {
			stretch = (x[i+1] - x[i]) - r[i]
		} else {
			stretch = ((x[0] + p) - x[i]) - r[i]
		}
		potential += ((0.5 * k[i]) * stretch) * stretch
		position += x[i]
		if math.Abs(v[i]) > speed {
			fastest, speed = i, math.Abs(v[i])
		}
	}
	fmt.Printf("kinetic %.17g\npotential %.17g\nposition %.17g\nfastest %d\n",
		kinetic, potential, position, fastest)
}
