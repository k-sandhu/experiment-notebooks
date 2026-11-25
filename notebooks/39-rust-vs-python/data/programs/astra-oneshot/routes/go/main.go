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
	data := p.data
	i := p.pos
	for i < len(data) && data[i] <= ' ' {
		i++
	}
	value := 0
	for i < len(data) {
		c := data[i]
		if c < '0' || c > '9' {
			break
		}
		value = value*10 + int(c-'0')
		i++
	}
	p.pos = i
	return value
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

	in := parser{data: data}
	n := in.nextInt()
	m := in.nextInt()
	q := in.nextInt()

	offsets := make([]int, n+1)
	from := make([]int, m)
	to := make([]int, m)
	roadWeights := make([]uint16, m)

	for i := 0; i < m; i++ {
		u := in.nextInt()
		v := in.nextInt()
		w := in.nextInt()
		from[i] = u
		to[i] = v
		roadWeights[i] = uint16(w)
		offsets[u+1]++
		offsets[v+1]++
	}
	for i := 1; i <= n; i++ {
		offsets[i] += offsets[i-1]
	}

	cursor := make([]int, n)
	copy(cursor, offsets[:n])
	neighbors := make([]int, offsets[n])
	weights := make([]uint16, offsets[n])

	for i := 0; i < m; i++ {
		u, v, w := from[i], to[i], roadWeights[i]

		j := cursor[u]
		neighbors[j] = v
		weights[j] = w
		cursor[u]++

		j = cursor[v]
		neighbors[j] = u
		weights[j] = w
		cursor[v]++
	}

	dist := make([]int64, n)
	next := make([]int, n)
	prev := make([]int, n)

	const bucketMask = 1023
	var heads [1024]int
	for i := range heads {
		heads[i] = -1
	}
	var occupied [16]uint64

	output := make([]byte, 0, 256)

	for query := 0; query < q; query++ {
		source := in.nextInt()
		for i := range dist {
			dist[i] = -1
		}

		dist[source] = 0
		next[source] = -1
		prev[source] = -1
		heads[0] = source
		occupied[0] = 1

		summary := uint64(1)
		currentBucket := 0
		reachable := int64(0)
		total := int64(0)
		farthest := int64(0)
		farthestNode := source

		for summary != 0 {
			word := currentBucket >> 6
			available := occupied[word] &
				(^uint64(0) << uint(currentBucket&63))

			if available == 0 {
				later := summary & (^uint64(0) << uint(word+1))
				if later != 0 {
					word = bits.TrailingZeros64(later)
				} else {
					word = bits.TrailingZeros64(summary)
				}
				available = occupied[word]
			}

			bucket := word*64 + bits.TrailingZeros64(available)
			currentBucket = bucket

			u := heads[bucket]
			newHead := next[u]
			heads[bucket] = newHead
			if newHead != -1 {
				prev[newHead] = -1
			} else {
				occupied[word] &^= uint64(1) << uint(bucket&63)
				if occupied[word] == 0 {
					summary &^= uint64(1) << uint(word)
				}
			}

			d := dist[u]
			reachable++
			total += d
			if d > farthest {
				farthest = d
				farthestNode = u
			} else if d == farthest && u < farthestNode {
				farthestNode = u
			}

			for e, end := offsets[u], offsets[u+1]; e < end; e++ {
				v := neighbors[e]
				candidate := d + int64(weights[e])
				old := dist[v]
				if old >= 0 && candidate >= old {
					continue
				}

				if old >= 0 {
					oldBucket := int(old & bucketMask)
					p, nx := prev[v], next[v]
					if p == -1 {
						heads[oldBucket] = nx
					} else {
						next[p] = nx
					}
					if nx != -1 {
						prev[nx] = p
					}
					if heads[oldBucket] == -1 {
						oldWord := oldBucket >> 6
						occupied[oldWord] &^=
							uint64(1) << uint(oldBucket&63)
						if occupied[oldWord] == 0 {
							summary &^= uint64(1) << uint(oldWord)
						}
					}
				}

				dist[v] = candidate
				newBucket := int(candidate & bucketMask)
				h := heads[newBucket]
				prev[v] = -1
				next[v] = h
				if h != -1 {
					prev[h] = v
				} else {
					newWord := newBucket >> 6
					occupied[newWord] |= uint64(1) << uint(newBucket&63)
					summary |= uint64(1) << uint(newWord)
				}
				heads[newBucket] = v
			}
		}

		output = strconv.AppendInt(output, int64(source), 10)
		output = append(output, ' ')
		output = strconv.AppendInt(output, reachable, 10)
		output = append(output, ' ')
		output = strconv.AppendInt(output, total, 10)
		output = append(output, ' ')
		output = strconv.AppendInt(output, farthest, 10)
		output = append(output, ' ')
		output = strconv.AppendInt(output, int64(farthestNode), 10)
		output = append(output, '\n')
	}

	_, _ = os.Stdout.Write(output)
}
