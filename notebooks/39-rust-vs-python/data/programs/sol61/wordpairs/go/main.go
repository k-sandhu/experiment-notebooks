package main

import (
	"bufio"
	"fmt"
	"os"
	"slices"
	"sort"
)

// Pointer-free arrays avoid per-pair allocations and GC scanning.
type pairList struct {
	narrow []uint32
	wide   []uint64
}

func (t *pairList) add(a, b uint32) {
	if t.wide == nil && (a > 65535 || b > 65535) {
		t.wide = make([]uint64, len(t.narrow), cap(t.narrow))
		for i, key := range t.narrow {
			t.wide[i] = uint64(key>>16)<<32 | uint64(key&65535)
		}
		t.narrow = nil
	}
	if t.wide != nil {
		t.wide = append(t.wide, uint64(a)<<32|uint64(b))
	} else {
		t.narrow = append(t.narrow, a<<16|b)
	}
}

func radixSort[T ~uint32 | ~uint64](keys []T) []T {
	if len(keys) < 2048 {
		slices.Sort(keys)
		return keys
	}
	var variation T
	first := keys[0]
	for _, key := range keys {
		variation |= key ^ first
	}
	if variation == 0 {
		return keys
	}
	scratch := make([]T, len(keys))
	for shift := uint(0); shift < 64 && variation>>shift != 0; shift += 11 {
		if (variation>>shift)&2047 == 0 {
			continue
		}
		var offsets [2048]int
		for _, key := range keys {
			offsets[(key>>shift)&2047]++
		}
		total := 0
		for j, count := range offsets {
			offsets[j] = total
			total += count
		}
		for _, key := range keys {
			digit := (key >> shift) & 2047
			scratch[offsets[digit]] = key
			offsets[digit]++
		}
		keys, scratch = scratch, keys
	}
	return keys
}

type entry struct{ key, count uint64 }

func better(a, b entry, rank []int) bool {
	if a.count != b.count {
		return a.count > b.count
	}
	af, bf := rank[uint32(a.key>>32)], rank[uint32(b.key>>32)]
	if af != bf {
		return af < bf
	}
	return rank[uint32(a.key)] < rank[uint32(b.key)]
}

func scanPairs[T ~uint32 | ~uint64](keys []T, bits uint, mask uint64, rank []int) ([]entry, uint64) {
	keys = radixSort(keys)
	top := make([]entry, 0, 20)
	var distinct uint64
	for i := 0; i < len(keys); {
		start, key := i, keys[i]
		i++
		for i < len(keys) && keys[i] == key {
			i++
		}
		distinct++
		e := entry{(uint64(key)>>bits)<<32 | (uint64(key) & mask), uint64(i - start)}
		if len(top) == 20 && !better(e, top[19], rank) {
			continue
		}
		p := len(top)
		if p < 20 {
			top = append(top, e)
		} else {
			p = 19
		}
		for p > 0 && better(e, top[p-1], rank) {
			top[p] = top[p-1]
			p--
		}
		top[p] = e
	}
	return top, distinct
}

func main() {
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	vocabulary := make(map[string]uint32)
	words := []string{""}
	pairs := pairList{narrow: make([]uint32, 0, len(data)/6)}
	var wordCount, pairCount uint64
	var previous uint32
	for i := 0; i < len(data); {
		c := data[i] | 32
		if c >= 'a' && c <= 'z' {
			start := i
			for {
				data[i] = c
				i++
				if i == len(data) {
					break
				}
				c = data[i] | 32
				if c < 'a' || c > 'z' {
					break
				}
			}
			// Go elides the byte-slice-to-string allocation for map lookups.
			id := vocabulary[string(data[start:i])]
			if id == 0 {
				word := string(data[start:i])
				id = uint32(len(words))
				vocabulary[word] = id
				words = append(words, word)
			}
			wordCount++
			if previous != 0 {
				pairs.add(previous, id)
				pairCount++
			}
			previous = id
		} else {
			raw := data[i]
			i++
			if raw == '.' || raw == '!' || raw == '?' {
				previous = 0
			}
		}
	}
	order := make([]int, len(words)-1)
	for i := range order {
		order[i] = i + 1
	}
	sort.Slice(order, func(i, j int) bool { return words[order[i]] < words[order[j]] })
	rank := make([]int, len(words))
	for i, id := range order {
		rank[id] = i
	}
	var top []entry
	var distinct uint64
	if pairs.wide != nil {
		top, distinct = scanPairs(pairs.wide, 32, 0xffffffff, rank)
	} else {
		top, distinct = scanPairs(pairs.narrow, 16, 65535, rank)
	}
	output := bufio.NewWriter(os.Stdout)
	fmt.Fprintf(output, "words %d\npairs %d\ndistinct %d\n", wordCount, pairCount, distinct)
	for _, e := range top {
		fmt.Fprintf(output, "%d %s %s\n", e.count, words[uint32(e.key>>32)], words[uint32(e.key)])
	}
	if err := output.Flush(); err != nil {
		panic(err)
	}
}
