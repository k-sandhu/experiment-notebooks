package main

import (
	"bufio"
	"fmt"
	"os"
	"runtime"
	"sort"
)

type pairEntry struct {
	key   uint64
	count uint64
}

type pairTable struct {
	entries []pairEntry
	used    int
	limit   int
}

func hashPair(x uint64) uint64 {
	x ^= x >> 30
	x *= 0xbf58476d1ce4e5b9
	x ^= x >> 27
	x *= 0x94d049bb133111eb
	return x ^ (x >> 31)
}

func (t *pairTable) grow() {
	newEntries := make([]pairEntry, len(t.entries)*2)
	mask := uint64(len(newEntries) - 1)

	for i := range t.entries {
		e := t.entries[i]
		if e.key == 0 {
			continue
		}
		p := hashPair(e.key) & mask
		for newEntries[p].key != 0 {
			p = (p + 1) & mask
		}
		newEntries[p] = e
	}

	t.entries = newEntries
	t.limit = len(newEntries) - len(newEntries)/4
}

func (t *pairTable) add(key uint64) {
	mask := uint64(len(t.entries) - 1)
	p := hashPair(key) & mask

	for {
		e := &t.entries[p]
		if e.key == key {
			e.count++
			return
		}
		if e.key == 0 {
			if t.used == t.limit {
				t.grow()
				mask = uint64(len(t.entries) - 1)
				p = hashPair(key) & mask
				continue
			}
			e.key = key
			e.count = 1
			t.used++
			return
		}
		p = (p + 1) & mask
	}
}

type result struct {
	key   uint64
	count uint64
	order uint64
}

func better(a, b result) bool {
	return a.count > b.count ||
		(a.count == b.count && a.order < b.order)
}

func main() {
	runtime.GOMAXPROCS(1)

	if len(os.Args) < 2 {
		return
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return
	}

	dictionary := make(map[string]uint32, 65536)
	words := make([]string, 1, 65536)

	table := pairTable{
		entries: make([]pairEntry, 1<<16),
		limit:   (1 << 16) * 3 / 4,
	}

	var wordCount, pairCount uint64
	var previous uint32

	for i := 0; i < len(data); {
		c := data[i]
		lower := c | 0x20
		if lower < 'a' || lower > 'z' {
			if c == '.' || c == '!' || c == '?' {
				previous = 0
			}
			i++
			continue
		}

		start := i
		for {
			data[i] = lower
			i++
			if i == len(data) {
				break
			}
			lower = data[i] | 0x20
			if lower < 'a' || lower > 'z' {
				break
			}
		}

		wordCount++
		id := dictionary[string(data[start:i])]
		if id == 0 {
			word := string(data[start:i])
			id = uint32(len(words))
			dictionary[word] = id
			words = append(words, word)
		}

		if previous != 0 {
			key := uint64(previous)<<32 | uint64(id)
			table.add(key)
			pairCount++
		}
		previous = id
	}

	out := bufio.NewWriterSize(os.Stdout, 65536)
	fmt.Fprintf(out, "words %d\npairs %d\ndistinct %d\n",
		wordCount, pairCount, table.used)

	if table.used == 0 {
		out.Flush()
		return
	}

	sortedIDs := make([]uint32, len(words)-1)
	for i := range sortedIDs {
		sortedIDs[i] = uint32(i + 1)
	}
	sort.Slice(sortedIDs, func(i, j int) bool {
		return words[sortedIDs[i]] < words[sortedIDs[j]]
	})

	ranks := make([]uint32, len(words))
	for rank, id := range sortedIDs {
		ranks[id] = uint32(rank)
	}

	var top [20]result
	topCount := 0

	for i := range table.entries {
		e := table.entries[i]
		if e.key == 0 {
			continue
		}
		if topCount == len(top) && e.count < top[len(top)-1].count {
			continue
		}

		first := uint32(e.key >> 32)
		second := uint32(e.key)
		candidate := result{
			key:   e.key,
			count: e.count,
			order: uint64(ranks[first])<<32 | uint64(ranks[second]),
		}

		if topCount == len(top) && !better(candidate, top[len(top)-1]) {
			continue
		}

		position := topCount
		if topCount < len(top) {
			topCount++
		} else {
			position = len(top) - 1
		}

		for position > 0 && better(candidate, top[position-1]) {
			top[position] = top[position-1]
			position--
		}
		top[position] = candidate
	}

	for i := 0; i < topCount; i++ {
		e := top[i]
		first := uint32(e.key >> 32)
		second := uint32(e.key)
		fmt.Fprintf(out, "%d %s %s\n", e.count, words[first], words[second])
	}
	out.Flush()
}
