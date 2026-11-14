#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <numeric>
#include <string_view>
#include <utility>
#include <vector>

class WordTable {
    struct Entry {
        std::uint64_t hash = 0;
        std::size_t idPlusOne = 0;
    };

    std::vector<Entry> table_;
    std::size_t mask_;

    static std::uint64_t mix(std::uint64_t x) {
        x ^= x >> 30;
        x *= UINT64_C(0xbf58476d1ce4e5b9);
        x ^= x >> 27;
        x *= UINT64_C(0x94d049bb133111eb);
        return x ^ (x >> 31);
    }

    void grow() {
        std::vector<Entry> next(table_.size() * 2);
        const std::size_t nextMask = next.size() - 1;

        for (const Entry& entry : table_) {
            if (entry.idPlusOne != 0) {
                std::size_t index =
                    static_cast<std::size_t>(entry.hash) & nextMask;
                while (next[index].idPlusOne != 0) {
                    index = (index + 1) & nextMask;
                }
                next[index] = entry;
            }
        }

        table_.swap(next);
        mask_ = nextMask;
    }

public:
    std::vector<std::string_view> words;

    WordTable() : table_(65536), mask_(65535) {
        words.reserve(65536);
    }

    std::uint32_t intern(const char* data, std::size_t length,
                         std::uint64_t hash) {
        hash = mix(hash);
        const std::string_view word(data, length);
        std::size_t index = static_cast<std::size_t>(hash) & mask_;

        while (table_[index].idPlusOne != 0) {
            const Entry& entry = table_[index];
            if (entry.hash == hash &&
                words[entry.idPlusOne - 1] == word) {
                return static_cast<std::uint32_t>(entry.idPlusOne - 1);
            }
            index = (index + 1) & mask_;
        }

        if ((words.size() + 1) * 10 >= table_.size() * 7) {
            grow();
            index = static_cast<std::size_t>(hash) & mask_;
            while (table_[index].idPlusOne != 0) {
                index = (index + 1) & mask_;
            }
        }

        const std::uint32_t id =
            static_cast<std::uint32_t>(words.size());
        words.push_back(word);
        table_[index] = Entry{hash, words.size()};
        return id;
    }

    void releaseTable() {
        std::vector<Entry>().swap(table_);
    }
};

template<class Key>
struct Result {
    std::uint64_t count;
    Key key;
};

template<class Key>
struct Better {
    bool operator()(const Result<Key>& a, const Result<Key>& b) const {
        if (a.count != b.count) {
            return a.count > b.count;
        }
        return a.key < b.key;
    }
};

template<class Key>
void summarize(Key* keys, std::size_t size, unsigned wordBits,
               std::uint64_t totalWords,
               const std::vector<std::string_view>& words,
               const std::vector<std::uint32_t>& lexicalOrder) {
    std::unique_ptr<Key[]> scratch;
    Key* sorted = keys;

    if (size < 4096) {
        std::sort(keys, keys + size);
    } else {
        scratch.reset(new Key[size]);
        Key* source = keys;
        Key* destination = scratch.get();

        constexpr unsigned radixBits = 11;
        constexpr std::size_t maxBuckets = std::size_t{1} << radixBits;
        std::array<std::size_t, maxBuckets> positions;
        const unsigned keyBits = wordBits * 2;

        for (unsigned shift = 0; shift < keyBits; shift += radixBits) {
            const unsigned width =
                (std::min)(radixBits, keyBits - shift);
            const std::size_t bucketCount = std::size_t{1} << width;
            const Key bucketMask = static_cast<Key>(bucketCount - 1);

            std::fill_n(positions.begin(), bucketCount, std::size_t{0});

            for (std::size_t i = 0; i < size; ++i) {
                ++positions[static_cast<std::size_t>(
                    (source[i] >> shift) & bucketMask)];
            }

            std::size_t offset = 0;
            for (std::size_t bucket = 0; bucket < bucketCount; ++bucket) {
                const std::size_t count = positions[bucket];
                positions[bucket] = offset;
                offset += count;
            }

            for (std::size_t i = 0; i < size; ++i) {
                const Key key = source[i];
                const std::size_t bucket = static_cast<std::size_t>(
                    (key >> shift) & bucketMask);
                destination[positions[bucket]++] = key;
            }

            std::swap(source, destination);
        }

        sorted = source;
    }

    std::array<Result<Key>, 20> best;
    std::size_t bestSize = 0;
    std::uint64_t distinct = 0;
    const Better<Key> better;

    std::size_t begin = 0;
    while (begin < size) {
        const Key key = sorted[begin];
        std::size_t end = begin + 1;
        while (end < size && sorted[end] == key) {
            ++end;
        }

        const std::uint64_t count =
            static_cast<std::uint64_t>(end - begin);
        ++distinct;

        if (bestSize < best.size()) {
            best[bestSize++] = Result<Key>{count, key};
            std::push_heap(best.begin(), best.begin() + bestSize, better);
        } else if (count > best[0].count) {
            // Keys arrive in lexical order, so later equal-count keys lose.
            std::pop_heap(best.begin(), best.end(), better);
            best.back() = Result<Key>{count, key};
            std::push_heap(best.begin(), best.end(), better);
        }

        begin = end;
    }

    std::sort(best.begin(), best.begin() + bestSize, better);

    std::cout << "words " << totalWords << '\n'
              << "pairs " << static_cast<std::uint64_t>(size) << '\n'
              << "distinct " << distinct << '\n';

    const std::uint64_t wordMask =
        (UINT64_C(1) << wordBits) - 1;

    for (std::size_t i = 0; i < bestSize; ++i) {
        const std::uint64_t key = static_cast<std::uint64_t>(best[i].key);
        const std::size_t first =
            static_cast<std::size_t>(key >> wordBits);
        const std::size_t second =
            static_cast<std::size_t>(key & wordMask);

        std::cout << best[i].count << ' '
                  << words[lexicalOrder[first]] << ' '
                  << words[lexicalOrder[second]] << '\n';
    }
}

int main(int argc, char* argv[]) {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    if (argc < 2) {
        return 0;
    }

    std::ifstream file(argv[1], std::ios::binary | std::ios::ate);
    if (!file) {
        return 0;
    }

    const std::streamoff fileSize = file.tellg();
    if (fileSize < 0) {
        return 0;
    }

    const std::size_t size = static_cast<std::size_t>(fileSize);
    if (size == 0) {
        std::cout << "words 0\npairs 0\ndistinct 0\n";
        return 0;
    }

    std::unique_ptr<char[]> input(new char[size]);
    file.seekg(0, std::ios::beg);
    if (!file.read(input.get(), static_cast<std::streamsize>(size))) {
        return 0;
    }
    file.close();

    WordTable dictionary;
    std::vector<std::uint64_t> pairs;
    pairs.reserve(size / 5 + 1);

    std::uint64_t totalWords = 0;
    std::uint32_t previous = 0;
    bool havePrevious = false;
    std::size_t position = 0;

    while (position < size) {
        const unsigned char character =
            static_cast<unsigned char>(input[position]);
        unsigned lower = static_cast<unsigned>(character) | 32u;

        if (lower - static_cast<unsigned>('a') < 26u) {
            const std::size_t start = position;
            std::uint64_t hash = UINT64_C(14695981039346656037);

            do {
                input[position] = static_cast<char>(lower);
                hash ^= static_cast<std::uint64_t>(lower);
                hash *= UINT64_C(1099511628211);
                ++position;

                if (position == size) {
                    break;
                }

                lower = static_cast<unsigned>(
                    static_cast<unsigned char>(input[position])) | 32u;
            } while (lower - static_cast<unsigned>('a') < 26u);

            const std::uint32_t current = dictionary.intern(
                input.get() + start, position - start, hash);
            ++totalWords;

            if (havePrevious) {
                pairs.push_back(
                    (static_cast<std::uint64_t>(previous) << 32) |
                    static_cast<std::uint64_t>(current));
            }

            previous = current;
            havePrevious = true;
        } else {
            if (character == '.' || character == '!' || character == '?') {
                havePrevious = false;
            }
            ++position;
        }
    }

    if (pairs.empty()) {
        std::cout << "words " << totalWords
                  << "\npairs 0\ndistinct 0\n";
        return 0;
    }

    dictionary.releaseTable();

    const std::size_t vocabularySize = dictionary.words.size();
    std::vector<std::uint32_t> lexicalOrder(vocabularySize);
    std::iota(lexicalOrder.begin(), lexicalOrder.end(), std::uint32_t{0});

    std::sort(lexicalOrder.begin(), lexicalOrder.end(),
              [&dictionary](std::uint32_t a, std::uint32_t b) {
                  return dictionary.words[a] < dictionary.words[b];
              });

    std::vector<std::uint32_t> rank(vocabularySize);
    for (std::size_t i = 0; i < vocabularySize; ++i) {
        rank[lexicalOrder[i]] = static_cast<std::uint32_t>(i);
    }

    unsigned wordBits = 1;
    while ((UINT64_C(1) << wordBits) < vocabularySize) {
        ++wordBits;
    }

    const std::size_t pairCount = pairs.size();

    if (wordBits <= 16) {
        std::unique_ptr<std::uint32_t[]> keys(
            new std::uint32_t[pairCount]);

        for (std::size_t i = 0; i < pairCount; ++i) {
            const std::uint64_t pair = pairs[i];
            const std::uint32_t first =
                rank[static_cast<std::uint32_t>(pair >> 32)];
            const std::uint32_t second =
                rank[static_cast<std::uint32_t>(pair)];

            keys[i] = (first << wordBits) | second;
        }

        std::vector<std::uint64_t>().swap(pairs);
        std::vector<std::uint32_t>().swap(rank);

        summarize(keys.get(), pairCount, wordBits, totalWords,
                  dictionary.words, lexicalOrder);
    } else {
        for (std::uint64_t& pair : pairs) {
            const std::uint32_t first =
                rank[static_cast<std::uint32_t>(pair >> 32)];
            const std::uint32_t second =
                rank[static_cast<std::uint32_t>(pair)];

            pair = (static_cast<std::uint64_t>(first) << wordBits) |
                   static_cast<std::uint64_t>(second);
        }

        std::vector<std::uint32_t>().swap(rank);

        summarize(pairs.data(), pairCount, wordBits, totalWords,
                  dictionary.words, lexicalOrder);
    }

    return 0;
}
