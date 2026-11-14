package main

import (
	"math/bits"
	"os"
	"runtime"
	"runtime/debug"
	"strconv"
)

type parser struct {
	data []byte
	pos  int
}

func (p *parser) nextInt() int {
	for p.data[p.pos] <= ' ' {
		p.pos++
	}
	v := 0
	for {
		c := p.data[p.pos]
		if c < '0' || c > '9' {
			break
		}
		v = v*10 + int(c-'0')
		p.pos++
	}
	return v
}

type road struct {
	u, v int
	w    uint64
}

type result struct {
	reachable int
	total     int64
	far       int64
	node      int
}

func shortest(
	source int,
	offsets []int,
	edges []uint64,
	dist []int64,
	next, prev []int,
) result {
	for i := range dist {
		dist[i] = -1
	}

	var heads [1024]int
	for i := range heads {
		heads[i] = -1
	}
	var occupied [16]uint64
	var groups uint64

	dist[source] = 0
	next[source] = -1
	prev[source] = -1
	heads[0] = source
	occupied[0] = 1
	groups = 1

	pending := 1
	bucket := 0
	answer := result{node: source}

	for pending != 0 {
		if heads[bucket] < 0 {
			word := bucket >> 6
			mask := occupied[word] & (^uint64(0) << uint(bucket&63))
			if mask == 0 {
				available := groups & (^uint64(0) << uint(word+1))
				if available == 0 {
					available = groups
				}
				word = bits.TrailingZeros64(available)
				mask = occupied[word]
			}
			bucket = word*64 + bits.TrailingZeros64(mask)
		}

		u := heads[bucket]
		h := next[u]
		heads[bucket] = h
		if h >= 0 {
			prev[h] = -1
		} else {
			word := bucket >> 6
			occupied[word] &^= uint64(1) << uint(bucket&63)
			if occupied[word] == 0 {
				groups &^= uint64(1) << uint(word)
			}
		}
		pending--

		d := dist[u]
		answer.reachable++
		answer.total += d
		if d > answer.far {
			answer.far = d
			answer.node = u
		} else if d == answer.far && u < answer.node {
			answer.node = u
		}

		for _, edge := range edges[offsets[u]:offsets[u+1]] {
			v := int(edge >> 10)
			nd := d + int64(edge&1023)
			old := dist[v]

			if old >= 0 {
				if nd >= old {
					continue
				}

				oldBucket := int(old & 1023)
				p := prev[v]
				n := next[v]
				if p >= 0 {
					next[p] = n
				} else {
					heads[oldBucket] = n
					if n < 0 {
						word := oldBucket >> 6
						occupied[word] &^= uint64(1) << uint(oldBucket&63)
						if occupied[word] == 0 {
							groups &^= uint64(1) << uint(word)
						}
					}
				}
				if n >= 0 {
					prev[n] = p
				}
			} else {
				pending++
			}

			dist[v] = nd
			newBucket := int(nd & 1023)
			h = heads[newBucket]
			next[v] = h
			prev[v] = -1
			if h >= 0 {
				prev[h] = v
			} else {
				word := newBucket >> 6
				occupied[word] |= uint64(1) << uint(newBucket&63)
				groups |= uint64(1) << uint(word)
			}
			heads[newBucket] = v
		}
	}

	return answer
}

func main() {
	runtime.GOMAXPROCS(1)
	debug.SetGCPercent(-1)

	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	data = append(data, '\n')
	p := parser{data: data}

	n := p.nextInt()
	m := p.nextInt()
	q := p.nextInt()

	offsets := make([]int, n+1)
	roads := make([]road, m)
	for i := range roads {
		u := p.nextInt()
		v := p.nextInt()
		w := p.nextInt()
		roads[i] = road{u: u, v: v, w: uint64(w)}
		offsets[u+1]++
		offsets[v+1]++
	}

	sources := make([]int, q)
	for i := range sources {
		sources[i] = p.nextInt()
	}

	for i := 1; i <= n; i++ {
		offsets[i] += offsets[i-1]
	}

	edges := make([]uint64, offsets[n])
	for _, e := range roads {
		edges[offsets[e.u]] = uint64(e.v)<<10 | e.w
		offsets[e.u]++
		edges[offsets[e.v]] = uint64(e.u)<<10 | e.w
		offsets[e.v]++
	}
	for i := n; i > 0; i-- {
		offsets[i] = offsets[i-1]
	}
	offsets[0] = 0

	dist := make([]int64, n)
	next := make([]int, n)
	prev := make([]int, n)

	cache := make(map[int]result, q)
	output := make([]byte, 0, q*64)

	for _, source := range sources {
		answer, found := cache[source]
		if !found {
			answer = shortest(source, offsets, edges, dist, next, prev)
			cache[source] = answer
		}

		output = strconv.AppendInt(output, int64(source), 10)
		output = append(output, ' ')
		output = strconv.AppendInt(output, int64(answer.reachable), 10)
		output = append(output, ' ')
		output = strconv.AppendInt(output, answer.total, 10)
		output = append(output, ' ')
		output = strconv.AppendInt(output, answer.far, 10)
		output = append(output, ' ')
		output = strconv.AppendInt(output, int64(answer.node), 10)
		output = append(output, '\n')
	}

	for len(output) > 0 {
		written, err := os.Stdout.Write(output)
		if err != nil || written == 0 {
			return
		}
		output = output[written:]
	}
}
