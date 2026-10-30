import heapq
import re
import sys
from array import array

import numpy as np


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read().lower()
    ids = {}
    words = []
    sequence = array('I')
    append = sequence.append
    total_words = 0
    for match in re.finditer(rb'[a-z]+|[.!?]', data):
        token = match.group()
        if token[0] < 97:
            append(0)
            continue
        word_id = ids.get(token)
        if word_id is None:
            word_id = len(words) + 1
            ids[token] = word_id
            words.append(token)
        append(word_id)
        total_words += 1
    del data, ids
    seq = np.frombuffer(sequence, dtype=np.uint32)
    left, right = seq[:-1], seq[1:]
    valid = (left != 0) & (right != 0)
    packed = left[valid].astype(np.uint64)
    packed <<= np.uint64(32)
    packed |= right[valid]
    total_pairs = len(packed)
    del left, right, valid, seq, sequence
    pairs, counts = np.unique(packed, return_counts=True)
    del packed
    distinct = len(pairs)
    if distinct:
        threshold = np.partition(counts, max(0, distinct - 20))[max(0, distinct - 20)]
        candidates = np.flatnonzero(counts >= threshold)
        def rank(i):
            pair = int(pairs[i])
            return (-int(counts[i]), words[(pair >> 32) - 1], words[(pair & 0xffffffff) - 1])
        best = heapq.nsmallest(20, candidates, key=rank)
    else:
        best = []
    out = [f'words {total_words}', f'pairs {total_pairs}', f'distinct {distinct}']
    for i in best:
        pair = int(pairs[i])
        out.append(f'{counts[i]} {words[(pair >> 32) - 1].decode("ascii")} {words[(pair & 0xffffffff) - 1].decode("ascii")}')
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
