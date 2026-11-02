import heapq
import re
import sys


def main():
    with open(sys.argv[1], 'rb') as f:
        data = f.read().lower()
    shift = len(data).bit_length()
    mask = (1 << shift) - 1
    ids = {}
    words = []
    counts = {}
    previous = -1
    total_words = total_pairs = 0
    for match in re.finditer(rb'[a-z]+|[.!?]', data):
        token = match.group()
        if token[0] < 97:
            previous = -1
            continue
        word_id = ids.get(token)
        if word_id is None:
            word_id = len(words)
            ids[token] = word_id
            words.append(token)
        total_words += 1
        if previous >= 0:
            pair = (previous << shift) | word_id
            counts[pair] = counts.get(pair, 0) + 1
            total_pairs += 1
        previous = word_id
    best = heapq.nsmallest(20, counts.items(),
                           key=lambda item: (-item[1], words[item[0] >> shift], words[item[0] & mask]))
    out = [f'words {total_words}', f'pairs {total_pairs}', f'distinct {len(counts)}']
    out.extend(f'{count} {words[pair >> shift].decode("ascii")} {words[pair & mask].decode("ascii")}'
               for pair, count in best)
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
