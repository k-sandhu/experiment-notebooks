package main

import (
	"math/bits"
	"os"
	"strconv"
	"strings"
)

type parser struct {
	d []byte
	p int
}

func (ps *parser) nextInt() int {
	d := ps.d
	p := ps.p
	n := len(d)
	for p < n && d[p] <= ' ' {
		p++
	}
	if p >= n {
		ps.p = p
		return 0
	}
	neg := false
	if d[p] == '-' {
		neg = true
		p++
	}
	v := 0
	for p < n && d[p] >= '0' && d[p] <= '9' {
		v = v*10 + int(d[p]-'0')
		p++
	}
	ps.p = p
	if neg {
		return -v
	}
	return v
}

func main() {
	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}
	ps := &parser{d: data}
	N := ps.nextInt()
	M := ps.nextInt()
	Q := ps.nextInt()
	if N < 0 {
		N = 0
	}
	if M < 0 {
		M = 0
	}
	if Q < 0 {
		Q = 0
	}

	eu := make([]int32, M)
	ev := make([]int32, M)
	ew := make([]int32, M)
	deg := make([]int32, N)
	mStored := 0
	wmax := 0
	for i := 0; i < M; i++ {
		u := ps.nextInt()
		v := ps.nextInt()
		w := ps.nextInt()
		if u == v {
			continue
		}
		if u < 0 || u >= N || v < 0 || v >= N {
			continue
		}
		eu[mStored] = int32(u)
		ev[mStored] = int32(v)
		ew[mStored] = int32(w)
		mStored++
		deg[u]++
		deg[v]++
		if w > wmax {
			wmax = w
		}
	}
	sources := make([]int, Q)
	for i := 0; i < Q; i++ {
		sources[i] = ps.nextInt()
	}
	data = nil

	off := make([]int32, N+1)
	for i := 0; i < N; i++ {
		off[i+1] = off[i] + deg[i]
	}
	E := int(off[N])
	adjTo := make([]int32, E)
	adjW := make([]int32, E)
	cursor := make([]int32, N)
	copy(cursor, off[:N])
	for i := 0; i < mStored; i++ {
		u := eu[i]
		v := ev[i]
		w := ew[i]
		a := cursor[u]
		cursor[u]++
		adjTo[a] = v
		adjW[a] = w
		b := cursor[v]
		cursor[v]++
		adjTo[b] = u
		adjW[b] = w
	}
	eu, ev, ew, deg, cursor = nil, nil, nil, nil, nil

	B := 1
	if wmax > 0 {
		B = wmax + 1
	}
	WORDS := (B + 63) >> 6
	dist := make([]int64, N)
	head := make([]int32, B)
	bitsArr := make([]uint64, WORDS)
	capInit := N * 2
	if capInit < 1024 {
		capInit = 1024
	}
	eNode := make([]int32, capInit)
	eNext := make([]int32, capInit)
	const INF = int64(4e18)

	var out strings.Builder
	out.Grow(Q * 48)
	doneSrc := make([]int, 0, Q)
	doneLine := make([]string, 0, Q)

	for qi := 0; qi < Q; qi++ {
		s := sources[qi]
		dup := false
		for k, ds := range doneSrc {
			if ds == s {
				out.WriteString(doneLine[k])
				dup = true
				break
			}
		}
		if dup {
			continue
		}
		var R, total, far int64
		farNode := s

		if s >= 0 && s < N {
			for i := range dist {
				dist[i] = INF
			}
			for i := range head {
				head[i] = -1
			}
			for i := range bitsArr {
				bitsArr[i] = 0
			}
			poolSize := 0
			nonEmpty := 0
			dist[s] = 0
			{
				if poolSize == len(eNode) {
					nc := len(eNode) * 2
					nn := make([]int32, nc)
					copy(nn, eNode)
					eNode = nn
					nx := make([]int32, nc)
					copy(nx, eNext)
					eNext = nx
				}
				idx := poolSize
				poolSize++
				eNode[idx] = int32(s)
				eNext[idx] = head[0]
				if head[0] == -1 {
					bitsArr[0] |= 1
					nonEmpty++
				}
				head[0] = int32(idx)
			}
			curBucket := 0
			var curDist int64
			for {
				if head[curBucket] == -1 {
					if nonEmpty == 0 {
						break
					}
					wi := curBucket >> 6
					bi := curBucket & 63
					posB := -1
					var w uint64
					if bi < 63 {
						w = bitsArr[wi] & (^uint64(0) << uint(bi+1))
					}
					if w != 0 {
						posB = (wi << 6) + bits.TrailingZeros64(w)
					} else {
						for step := 1; step <= WORDS; step++ {
							idxw := wi + step
							if idxw >= WORDS {
								idxw -= WORDS
							}
							ww := bitsArr[idxw]
							if ww != 0 {
								posB = (idxw << 6) + bits.TrailingZeros64(ww)
								break
							}
						}
					}
					if posB < 0 {
						break
					}
					delta := posB - curBucket
					if delta <= 0 {
						delta += B
					}
					curDist += int64(delta)
					curBucket = posB
				}
				eidx := head[curBucket]
				u := int(eNode[eidx])
				nxt := eNext[eidx]
				head[curBucket] = nxt
				if nxt == -1 {
					bitsArr[curBucket>>6] &^= uint64(1) << uint(curBucket&63)
					nonEmpty--
				}
				if dist[u] != curDist {
					continue
				}
				R++
				total += curDist
				if curDist > far {
					far = curDist
					farNode = u
				} else if curDist == far && u < farNode {
					farNode = u
				}
				begin := int(off[u])
				end := int(off[u+1])
				for ei := begin; ei < end; ei++ {
					to := int(adjTo[ei])
					wgt := int(adjW[ei])
					nd := curDist + int64(wgt)
					if nd < dist[to] {
						dist[to] = nd
						b := curBucket + wgt
						if b >= B {
							b -= B
						}
						if poolSize == len(eNode) {
							nc := len(eNode) * 2
							nn := make([]int32, nc)
							copy(nn, eNode)
							eNode = nn
							nx := make([]int32, nc)
							copy(nx, eNext)
							eNext = nx
						}
						idx := poolSize
						poolSize++
						eNode[idx] = int32(to)
						h := head[b]
						eNext[idx] = h
						if h == -1 {
							bitsArr[b>>6] |= uint64(1) << uint(b&63)
							nonEmpty++
						}
						head[b] = int32(idx)
					}
				}
			}
		}
		var lb strings.Builder
		lb.WriteString(strconv.Itoa(s))
		lb.WriteByte(' ')
		lb.WriteString(strconv.FormatInt(R, 10))
		lb.WriteByte(' ')
		lb.WriteString(strconv.FormatInt(total, 10))
		lb.WriteByte(' ')
		lb.WriteString(strconv.FormatInt(far, 10))
		lb.WriteByte(' ')
		lb.WriteString(strconv.Itoa(farNode))
		lb.WriteByte('\n')
		line := lb.String()
		out.WriteString(line)
		doneSrc = append(doneSrc, s)
		doneLine = append(doneLine, line)
	}
	os.Stdout.WriteString(out.String())
}
