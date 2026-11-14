// Counts adjacent word pairs within sentences and prints the 20 most frequent ones (see SPEC.md).
//
// One pass over the whole input: letters form words, which are looked up in an open-addressing
// vocabulary table; each pair of neighbouring words is counted in an open-addressing table of
// 12-byte slots, which avoids the overhead of a generic map. Ranking uses integer word ranks.
package main

import (
	"fmt"
	"os"
	"slices"
	"strconv"
	"strings"
)

// Byte classes.
const (
	separator   = 0
	letter      = 1
	sentenceEnd = 2
)

var classOf [256]uint8

func init() {
	for c := 'A'; c <= 'Z'; c++ {
		classOf[c] = letter
		classOf[c+32] = letter
	}
	classOf['.'] = sentenceEnd
	classOf['!'] = sentenceEnd
	classOf['?'] = sentenceEnd
}

const (
	fnvOffset = 0x811C9DC5
	fnvPrime  = 0x01000193
	noWord    = ^uint32(0)
	top       = 20
)

func mixPair(a, b uint32) uint32 {
	h := (a * 0x9E3779B1) ^ b
	h ^= h >> 16
	h *= 0x85EBCA6B
	h ^= h >> 13
	return h
}

// Maps lower-cased words to dense ids in first-seen order.
type vocab struct {
	table  []uint32 // id + 1, 0 = empty
	mask   uint32
	hashes []uint32
	words  []string
}

func newVocab() *vocab {
	const slots = 1 << 16
	return &vocab{table: make([]uint32, slots), mask: slots - 1}
}

// find returns the id of the word p (letters in either case); h is the FNV-1a hash of its lower-case form.
func (v *vocab) find(p []byte, h uint32) uint32 {
	idx := h & v.mask
	for {
		e := v.table[idx]
		if e == 0 {
			break
		}
		id := e - 1
		if v.hashes[id] == h && equalFolded(v.words[id], p) {
			return id
		}
		idx = (idx + 1) & v.mask
	}
	id := uint32(len(v.words))
	lower := make([]byte, len(p))
	for j, c := range p {
		lower[j] = c | 0x20
	}
	v.words = append(v.words, string(lower))
	v.hashes = append(v.hashes, h)
	v.table[idx] = id + 1
	if len(v.words)*2 > len(v.table) {
		v.grow()
	}
	return id
}

func equalFolded(w string, p []byte) bool {
	if len(w) != len(p) {
		return false
	}
	for j := range p {
		if w[j] != p[j]|0x20 {
			return false
		}
	}
	return true
}

func (v *vocab) grow() {
	bigger := make([]uint32, len(v.table)*2)
	m := uint32(len(bigger) - 1)
	for id, h := range v.hashes {
		idx := h & m
		for bigger[idx] != 0 {
			idx = (idx + 1) & m
		}
		bigger[idx] = uint32(id + 1)
	}
	v.table = bigger
	v.mask = m
}

// slot holds one ordered pair; c == 0 marks an empty slot.
type slot struct {
	a, b, c uint32
}

// pairCounter counts ordered pairs of word ids.
type pairCounter struct {
	slots    []slot
	mask     uint32
	distinct uint64
}

func newPairCounter() *pairCounter {
	const slots = 1 << 20
	return &pairCounter{slots: make([]slot, slots), mask: slots - 1}
}

func (pc *pairCounter) add(a, b uint32) {
	idx := mixPair(a, b) & pc.mask
	for {
		s := &pc.slots[idx]
		if s.c == 0 {
			s.a, s.b, s.c = a, b, 1
			pc.distinct++
			if pc.distinct*4 > uint64(len(pc.slots))*3 {
				pc.grow()
			}
			return
		}
		if s.a == a && s.b == b {
			s.c++
			return
		}
		idx = (idx + 1) & pc.mask
	}
}

func (pc *pairCounter) grow() {
	bigger := make([]slot, len(pc.slots)*2)
	m := uint32(len(bigger) - 1)
	for _, s := range pc.slots {
		if s.c == 0 {
			continue
		}
		idx := mixPair(s.a, s.b) & m
		for bigger[idx].c != 0 {
			idx = (idx + 1) & m
		}
		bigger[idx] = s
	}
	pc.slots = bigger
	pc.mask = m
}

// better reports whether x ranks before y: higher count, then earlier first word, then earlier second word.
func better(x, y slot, rank []uint32) bool {
	if x.c != y.c {
		return x.c > y.c
	}
	if rank[x.a] != rank[y.a] {
		return rank[x.a] < rank[y.a]
	}
	return rank[x.b] < rank[y.b]
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: solution INPUT_PATH")
		os.Exit(2)
	}
	buf, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	vb := newVocab()
	pc := newPairCounter()
	var words, total uint64
	prev := noWord
	n := len(buf)
	for i := 0; i < n; {
		cls := classOf[buf[i]]
		if cls == letter {
			start := i
			h := uint32(fnvOffset)
			for ; i < n && classOf[buf[i]] == letter; i++ {
				h = (h ^ uint32(buf[i]|0x20)) * fnvPrime
			}
			id := vb.find(buf[start:i], h)
			words++
			if prev != noWord {
				pc.add(prev, id)
				total++
			}
			prev = id
		} else {
			if cls == sentenceEnd {
				prev = noWord
			}
			i++
		}
	}

	// Rank words by byte order so ties can be broken with integer comparisons.
	nv := len(vb.words)
	order := make([]uint32, nv)
	for k := range order {
		order[k] = uint32(k)
	}
	slices.SortFunc(order, func(x, y uint32) int {
		return strings.Compare(vb.words[x], vb.words[y])
	})
	rank := make([]uint32, nv)
	for r, id := range order {
		rank[id] = uint32(r)
	}

	var best [top + 1]slot
	size := 0
	for _, s := range pc.slots {
		if s.c == 0 {
			continue
		}
		j := size
		best[j] = s
		if size == top && !better(best[top], best[top-1], rank) {
			continue
		}
		if size < top {
			size++
		}
		for ; j > 0 && better(best[j], best[j-1], rank); j-- {
			best[j], best[j-1] = best[j-1], best[j]
		}
	}

	var sb strings.Builder
	sb.WriteString("words " + strconv.FormatUint(words, 10) + "\n")
	sb.WriteString("pairs " + strconv.FormatUint(total, 10) + "\n")
	sb.WriteString("distinct " + strconv.FormatUint(pc.distinct, 10) + "\n")
	for _, e := range best[:size] {
		sb.WriteString(strconv.FormatUint(uint64(e.c), 10) + " " + vb.words[e.a] + " " + vb.words[e.b] + "\n")
	}
	os.Stdout.WriteString(sb.String())
}
