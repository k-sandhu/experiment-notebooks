package main

import (
	"math/bits"
	"os"
	"strconv"
	"strings"
)

func main() {
	if len(os.Args) < 2 {
		return
	}
	buf, err := os.ReadFile(os.Args[1])
	if err != nil || len(buf) == 0 {
		return
	}
	pos := 0
	parse := func() int {
		n := len(buf)
		for pos < n && (buf[pos] < '0' || buf[pos] > '9') {
			pos++
		}
		v := 0
		for pos < n && buf[pos] >= '0' && buf[pos] <= '9' {
			v = v*10 + int(buf[pos]-'0')
			pos++
		}
		return v
	}
	N, M, Q := parse(), parse(), parse()
	eu := make([]int32, M)
	ev := make([]int32, M)
	ew := make([]int32, M)
	deg := make([]int32, N)
	ecnt := 0
	for i := 0; i < M; i++ {
		u, v, w := parse(), parse(), parse()
		if u == v {
			continue
		}
		eu[ecnt], ev[ecnt], ew[ecnt] = int32(u), int32(v), int32(w)
		ecnt++
		deg[u]++
		deg[v]++
	}
	sources := make([]int, Q)
	for i := 0; i < Q; i++ {
		sources[i] = parse()
	}
	buf = nil
	off := make([]int32, N+1)
	for i := 0; i < N; i++ {
		off[i+1] = off[i] + deg[i]
	}
	adj := make([]int32, off[N])
	cur := make([]int32, N)
	copy(cur, off[:N])
	for i := 0; i < ecnt; i++ {
		u, v, w := eu[i], ev[i], ew[i]
		adj[cur[u]] = (v << 10) | w
		cur[u]++
		adj[cur[v]] = (u << 10) | w
		cur[v]++
	}
	eu, ev, ew, deg, cur = nil, nil, nil, nil, nil

	const INF = int32(0x3f3f3f3f)
	dist := make([]int32, N)
	nxt := make([]int32, N)
	prv := make([]int32, N)
	done := make([]bool, N)
	head := make([]int32, 1024)
	words := make([]uint64, 16)

	var sb strings.Builder
	sb.Grow(Q * 40)
	type res struct {
		s    int
		r    int64
		tot  int64
		far  int64
		node int
	}
	cache := make([]res, 0, 64)

	for qi := 0; qi < Q; qi++ {
		s := sources[qi]
		var R, tot, far int64
		farNode := s
		hit := false
		for _, c := range cache {
			if c.s == s {
				R, tot, far, farNode = c.r, c.tot, c.far, c.node
				hit = true
				break
			}
		}
		if !hit {
			for i := range dist {
				dist[i] = INF
			}
			for i := range done {
				done[i] = false
			}
			for i := range head {
				head[i] = -1
			}
			for i := range words {
				words[i] = 0
			}
			dist[s] = 0
			head[0] = int32(s)
			nxt[s] = -1
			prv[s] = -1
			words[0] = 1
			var inq int64 = 1
			curDist := int32(0)
			curB := 0
			R, tot, far = 0, 0, 0
			farNode = s
			for inq > 0 {
				node := head[curB]
				head[curB] = -1
				words[curB>>6] &^= 1 << uint(curB&63)
				for node != -1 {
					nn := nxt[node]
					done[node] = true
					inq--
					R++
					tot += int64(curDist)
					if int64(curDist) > far {
						far = int64(curDist)
						farNode = int(node)
					} else if int64(curDist) == far && int(node) < farNode {
						farNode = int(node)
					}
					a0, a1 := off[node], off[node+1]
					for ai := a0; ai < a1; ai++ {
						pk := adj[ai]
						v := pk >> 10
						if done[v] {
							continue
						}
						nd := curDist + (pk & 1023)
						if nd < dist[v] {
							if dist[v] != INF {
								ob := dist[v] & 1023
								pv, nv := prv[v], nxt[v]
								if pv != -1 {
									nxt[pv] = nv
								} else {
									head[ob] = nv
								}
								if nv != -1 {
									prv[nv] = pv
								}
								if head[ob] == -1 {
									words[ob>>6] &^= 1 << uint(ob&63)
								}
							} else {
								inq++
							}
							dist[v] = nd
							nb := nd & 1023
							oh := head[nb]
							nxt[v] = oh
							prv[v] = -1
							if oh != -1 {
								prv[oh] = v
							} else {
								words[nb>>6] |= 1 << uint(nb&63)
							}
							head[nb] = v
						}
					}
					node = nn
				}
				if inq == 0 {
					break
				}
				wi, bi := curB>>6, curB&63
				nb := -1
				var w0 uint64
				if bi != 63 {
					w0 = words[wi] & (^uint64(0) << uint(bi+1))
				}
				if w0 != 0 {
					nb = (wi << 6) + bits.TrailingZeros64(w0)
				} else {
					for k := 1; k < 16; k++ {
						idx := (wi + k) & 15
						w := words[idx]
						if w != 0 {
							nb = (idx << 6) + bits.TrailingZeros64(w)
							break
						}
					}
					if nb == -1 {
						var low uint64
						if bi == 63 {
							low = ^uint64(0)
						} else {
							low = (uint64(1) << uint(bi+1)) - 1
						}
						if w := words[wi] & low; w != 0 {
							nb = (wi << 6) + bits.TrailingZeros64(w)
						}
					}
				}
				offd := nb - curB
				if offd <= 0 {
					offd += 1024
				}
				curDist += int32(offd)
				curB = nb
			}
			if len(cache) < 64 {
				cache = append(cache, res{s, R, tot, far, farNode})
			}
		}
		sb.WriteString(strconv.Itoa(s))
		sb.WriteByte(' ')
		sb.WriteString(strconv.FormatInt(R, 10))
		sb.WriteByte(' ')
		sb.WriteString(strconv.FormatInt(tot, 10))
		sb.WriteByte(' ')
		sb.WriteString(strconv.FormatInt(far, 10))
		sb.WriteByte(' ')
		sb.WriteString(strconv.Itoa(farNode))
		sb.WriteByte('\n')
	}
	os.Stdout.WriteString(sb.String())
}
