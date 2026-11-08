// Word pairs benchmark - Go 1.27, standard library only.
// Single pass: lowercase words in place, intern them to ids, emit packed
// (prevId, curId) pairs within sentences, radix-sort the packed pairs, count
// runs, keep the top 20 by (count desc, word1 asc, word2 asc).
package main

import (
	"bufio"
	"fmt"
	"os"
)

func isLetter(c byte) bool {
	c |= 0x20
	return c >= 'a' && c <= 'z'
}

// Open-addressing map from lowercase word to a dense id.
// Lookup compares against the input buffer directly, so only distinct words
// become Go strings.
type wordMap struct {
	keys    []string
	hashes  []uint32
	ids     []int
	mask    int
	occupied int
	growAt  int
	words   []string // id -> word
}

func newWordMap(cap int) *wordMap {
	return &wordMap{
		keys:    make([]string, cap),
		hashes:  make([]uint32, cap),
		ids:     make([]int, cap),
		mask:    cap - 1,
		growAt:  int(float64(cap) * 0.75),
		words:   make([]string, 0, cap),
	}
}

func (m *wordMap) grow() {
	oldKeys, oldHashes, oldIds := m.keys, m.hashes, m.ids
	newCap := len(oldKeys) * 2
	m.keys = make([]string, newCap)
	m.hashes = make([]uint32, newCap)
	m.ids = make([]int, newCap)
	m.mask = newCap - 1
	m.growAt = int(float64(newCap) * 0.75)
	for i := 0; i < len(oldKeys); i++ {
		k := oldKeys[i]
		if k != "" {
			h := oldHashes[i] & uint32(m.mask)
			pos := int(h)
			for m.keys[pos] != "" {
				pos = (pos + 1) & m.mask
			}
			m.keys[pos] = k
			m.hashes[pos] = oldHashes[i]
			m.ids[pos] = oldIds[i]
		}
	}
}

func hashBytes(data []byte, start, len int) uint32 {
	h := uint32(2166136261)
	for i := 0; i < len; i++ {
		h = h*16777619 ^ uint32(data[start+i])
	}
	return h
}

func equalsBytes(k string, data []byte, start, length int) bool {
	if len(k) != length {
		return false
	}
	for i := 0; i < length; i++ {
		if k[i] != data[start+i] {
			return false
		}
	}
	return true
}

func (m *wordMap) getOrPut(data []byte, start, length int, hash uint32) int {
	pos := int(hash & uint32(m.mask))
	for {
		k := m.keys[pos]
		if k == "" {
			s := string(data[start : start+length])
			m.keys[pos] = s
			m.hashes[pos] = hash
			id := m.occupied
			m.ids[pos] = id
			m.words = append(m.words, s)
			m.occupied++
			if m.occupied >= m.growAt {
				m.grow()
			}
			return id
		}
		if m.hashes[pos] == hash && equalsBytes(k, data, start, length) {
			return m.ids[pos]
		}
		pos = (pos + 1) & m.mask
	}
}

// LSD radix sort over 4 x 8-bit passes. Because there is an even number of
// passes, the sorted data ends up in the caller's slice.
func radixSort(a []uint64) {
	n := len(a)
	if n < 2 {
		return
	}
	tmp := make([]uint64, n)
	var count [256]int
	src, dst := a, tmp
	for shift := uint(0); shift < 64; shift += 8 {
		for i := range count {
			count[i] = 0
		}
		for _, v := range src {
			count[(v>>shift)&0xFF]++
		}
		total := 0
		for i := 0; i < 256; i++ {
			c := count[i]
			count[i] = total
			total += c
		}
		for _, v := range src {
			b := int((v >> shift) & 0xFF)
			dst[count[b]] = v
			count[b]++
		}
		src, dst = dst, src
	}
}

// Top-20 bookkeeping, ordered best-first.
var bestCount [20]uint64
var bestW1 [20]int
var bestW2 [20]int
var bestn int
var wordsRef *[]string // points at wordMap.words so appends stay visible

func better(c1 uint64, a1, b1 int, c2 uint64, a2, b2 int) bool {
	words := *wordsRef
	if c1 != c2 {
		return c1 > c2
	}
	if words[a1] != words[a2] {
		return words[a1] < words[a2]
	}
	return words[b1] < words[b2]
}

func consider(count uint64, w1, w2 int) {
	if bestn < 20 {
		pos := bestn
		for pos > 0 && better(count, w1, w2, bestCount[pos-1], bestW1[pos-1], bestW2[pos-1]) {
			bestCount[pos] = bestCount[pos-1]
			bestW1[pos] = bestW1[pos-1]
			bestW2[pos] = bestW2[pos-1]
			pos--
		}
		bestCount[pos] = count
		bestW1[pos] = w1
		bestW2[pos] = w2
		bestn++
	} else if better(count, w1, w2, bestCount[19], bestW1[19], bestW2[19]) {
		c, a, b := count, w1, w2
		pos := 19
		for pos > 0 && better(c, a, b, bestCount[pos-1], bestW1[pos-1], bestW2[pos-1]) {
			bestCount[pos] = bestCount[pos-1]
			bestW1[pos] = bestW1[pos-1]
			bestW2[pos] = bestW2[pos-1]
			pos--
		}
		bestCount[pos] = c
		bestW1[pos] = a
		bestW2[pos] = b
	}
}

func main() {
	if len(os.Args) < 2 {
		os.Exit(1)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		os.Exit(1)
	}
	n := len(data)
	m := newWordMap(1 << 14)
	wordsRef = &m.words
	pairs := make([]uint64, 0, 1<<20)
	prevId := 0
	havePrev := false
	var wordTotal, pairTotal uint64

	i := 0
	for i < n {
		for i < n {
			c := data[i]
			if isLetter(c) {
				break
			}
			if c == '.' || c == '!' || c == '?' {
				havePrev = false
			}
			i++
		}
		if i >= n {
			break
		}
		start := i
		h := uint32(2166136261)
		for i < n {
			c := data[i]
			if !isLetter(c) {
				break
			}
			if c >= 'A' && c <= 'Z' {
				c += 0x20 // lowercase in place
				data[i] = c
			}
			h = h*16777619 ^ uint32(c)
			i++
		}
		length := i - start
		id := m.getOrPut(data, start, length, h)
		wordTotal++
		if havePrev {
			pairTotal++
			pairs = append(pairs, uint64(prevId)<<32|uint64(id))
		}
		prevId = id
		havePrev = true
	}

	radixSort(pairs)

	k := 0
	var distinct uint64
	for k < len(pairs) {
		j := k + 1
		for j < len(pairs) && pairs[j] == pairs[k] {
			j++
		}
		consider(uint64(j-k), int(pairs[k]>>32), int(pairs[k]&0xFFFFFFFF))
		distinct++
		k = j
	}

	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	fmt.Fprintf(out, "words %d\npairs %d\ndistinct %d\n", wordTotal, pairTotal, distinct)
	words := *wordsRef
	for t := 0; t < bestn; t++ {
		fmt.Fprintf(out, "%d %s %s\n", bestCount[t], words[bestW1[t]], words[bestW2[t]])
	}
}
