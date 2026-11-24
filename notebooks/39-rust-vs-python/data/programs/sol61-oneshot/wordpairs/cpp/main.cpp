#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <memory>
#include <numeric>
#include <string_view>
#include <vector>

class WordTable {
    struct Slot {
        std::uint64_t hash = 0;
        std::uint32_t idPlusOne = 0;
    };

    std::vector<Slot> slots_;
    std::size_t mask_;
    std::size_t limit_;

    void grow() {
        std::vector<Slot> next(slots_.size() * 2);
        const std::size_t nextMask = next.size() - 1;

        for (const Slot& slot : slots_) {
            if (slot.idPlusOne != 0) {
                std::size_t pos = static_cast<std::size_t>(slot.hash) & nextMask;
                while (next[pos].idPlusOne != 0) {
                    pos = (pos + 1) & nextMask;
                }
                next[pos] = slot;
            }
        }

        slots_.swap(next);
        mask_ = slots_.size() - 1;
        limit_ = slots_.size() * 7 / 10;
    }

public:
    std::vector<std::string_view> words;

    WordTable() : slots_(1024), mask_(1023), limit_(716) {
        words.reserve(4096);
    }

    std::uint32_t intern(const char* data, std::size_t length,
                         std::uint64_t hash) {
        hash ^= hash >> 30;
        hash *= 0xbf58476d1ce4e5b9ULL;
        hash ^= hash >> 27;
        hash *= 0x94d049bb133111ebULL;
        hash ^= hash >> 31;

        std::size_t pos = static_cast<std::size_t>(hash) & mask_;

        for (;;) {
            const Slot& slot = slots_[pos];

            if (slot.idPlusOne == 0) {
                if (words.size() >= limit_) {
                    grow();
                    pos = static_cast<std::size_t>(hash) & mask_;
                    while (slots_[pos].idPlusOne != 0) {
                        pos = (pos + 1) & mask_;
                    }
                }

                const auto id = static_cast<std::uint32_t>(words.size());
                words.emplace_back(data, length);
                slots_[pos].hash = hash;
                slots_[pos].idPlusOne = id + 1;
                return id;
            }

            if (slot.hash == hash) {
                const std::string_view word = words[slot.idPlusOne - 1];
                if (word.size() == length &&
                    std::memcmp(word.data(), data, length) == 0) {
                    return slot.idPlusOne - 1;
                }
            }

            pos = (pos + 1) & mask_;
        }
    }
};

template<class Key>
const Key* radixSort(Key* values, std::size_t size, unsigned usedBits,
                     std::unique_ptr<Key[]>& scratch) {
    if (size < 2) {
        return values;
    }

    constexpr unsigned digitBits = 11;
    constexpr std::size_t bucketCount = 1u << digitBits;
    constexpr Key digitMask = static_cast<Key>(bucketCount - 1);

    scratch.reset(new Key[size]);

    Key* source = values;
    Key* destination = scratch.get();
    std::array<std::size_t, bucketCount> offsets;

    for (unsigned shift = 0; shift < usedBits; shift += digitBits) {
        offsets.fill(0);

        for (std::size_t i = 0; i < size; ++i) {
            ++offsets[static_cast<std::size_t>(
                (source[i] >> shift) & digitMask)];
        }

        std::size_t sum = 0;
        for (std::size_t& offset : offsets) {
            const std::size_t count = offset;
            offset = sum;
            sum += count;
        }

        for (std::size_t i = 0; i < size; ++i) {
            const Key key = source[i];
            const std::size_t bucket =
                static_cast<std::size_t>((key >> shift) & digitMask);
            destination[offsets[bucket]++] = key;
        }

        std::swap(source, destination);
    }

    return source;
}

template<class Key>
void report(Key* keys, std::size_t pairCount, unsigned wordBits,
            std::uint64_t wordCount,
            const std::vector<std::uint32_t>& lexicalOrder,
            const std::vector<std::string_view>& words) {
    std::unique_ptr<Key[]> scratch;
    const Key* sorted = radixSort(keys, pairCount, wordBits * 2, scratch);

    struct Result {
        Key key;
        std::uint64_t count;
    };

    std::array<Result, 20> best;
    std::size_t bestSize = 0;
    std::uint64_t distinct = 0;

    std::size_t i = 0;
    while (i < pairCount) {
        const Key key = sorted[i];
        std::size_t end = i + 1;
        while (end < pairCount && sorted[end] == key) {
            ++end;
        }

        const std::uint64_t count =
            static_cast<std::uint64_t>(end - i);
        ++distinct;

        // Keys are visited in lexical order, so an equal count never
        // displaces an earlier result.
        if (bestSize < best.size() || count > best.back().count) {
            std::size_t position;
            if (bestSize < best.size()) {
                position = bestSize++;
            } else {
                position = best.size() - 1;
            }

            while (position != 0 && best[position - 1].count < count) {
                best[position] = best[position - 1];
                --position;
            }
            best[position] = Result{key, count};
        }

        i = end;
    }

    std::printf("words %llu\npairs %llu\ndistinct %llu\n",
                static_cast<unsigned long long>(wordCount),
                static_cast<unsigned long long>(pairCount),
                static_cast<unsigned long long>(distinct));

    const Key wordMask = (Key{1} << wordBits) - 1;

    for (std::size_t j = 0; j < bestSize; ++j) {
        const auto firstRank =
            static_cast<std::uint32_t>(best[j].key >> wordBits);
        const auto secondRank =
            static_cast<std::uint32_t>(best[j].key & wordMask);

        const std::string_view first = words[lexicalOrder[firstRank]];
        const std::string_view second = words[lexicalOrder[secondRank]];

        std::printf("%llu ",
                    static_cast<unsigned long long>(best[j].count));
        std::fwrite(first.data(), 1, first.size(), stdout);
        std::putchar(' ');
        std::fwrite(second.data(), 1, second.size(), stdout);
        std::putchar('\n');
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        return 0;
    }

    std::FILE* file = std::fopen(argv[1], "rb");
    if (file == nullptr) {
        return 0;
    }

    if (_fseeki64(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        return 0;
    }

    const auto fileLength = _ftelli64(file);
    if (fileLength < 0 || _fseeki64(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        return 0;
    }

    const std::size_t capacity = static_cast<std::size_t>(fileLength);
    std::unique_ptr<char[]> input(new char[capacity + 1]);

    std::size_t size = 0;
    while (size < capacity) {
        const std::size_t amount =
            std::fread(input.get() + size, 1, capacity - size, file);
        if (amount == 0) {
            break;
        }
        size += amount;
    }
    std::fclose(file);
    input[size] = '\0';

    WordTable dictionary;
    std::vector<std::uint64_t> pairs;
    pairs.reserve(size / 5 + 1);

    constexpr std::uint32_t noWord = UINT32_MAX;
    std::uint32_t previous = noWord;
    std::uint64_t wordCount = 0;

    char* current = input.get();
    const char* end = current + size;

    while (current < end) {
        unsigned character =
            static_cast<unsigned char>(*current) | 32u;

        if (character - static_cast<unsigned>('a') <= 25u) {
            const char* start = current;
            std::uint64_t hash = 14695981039346656037ULL;

            do {
                *current = static_cast<char>(character);
                hash = (hash ^ character) * 1099511628211ULL;
                ++current;
                character = static_cast<unsigned char>(*current) | 32u;
            } while (character - static_cast<unsigned>('a') <= 25u);

            const std::uint32_t id = dictionary.intern(
                start, static_cast<std::size_t>(current - start), hash);

            ++wordCount;
            if (previous != noWord) {
                pairs.push_back(
                    (static_cast<std::uint64_t>(previous) << 32) | id);
            }
            previous = id;
        } else {
            if (*current == '.' || *current == '!' || *current == '?') {
                previous = noWord;
            }
            ++current;
        }
    }

    if (pairs.empty()) {
        std::printf("words %llu\npairs 0\ndistinct 0\n",
                    static_cast<unsigned long long>(wordCount));
        return 0;
    }

    const auto& words = dictionary.words;
    std::vector<std::uint32_t> lexicalOrder(words.size());
    std::iota(lexicalOrder.begin(), lexicalOrder.end(), std::uint32_t{0});

    std::sort(lexicalOrder.begin(), lexicalOrder.end(),
              [&words](std::uint32_t a, std::uint32_t b) {
                  return words[a] < words[b];
              });

    std::vector<std::uint32_t> rank(words.size());
    for (std::size_t i = 0; i < lexicalOrder.size(); ++i) {
        rank[lexicalOrder[i]] = static_cast<std::uint32_t>(i);
    }

    const unsigned wordBits = std::max(
        1u, static_cast<unsigned>(
                std::bit_width(static_cast<std::uint32_t>(words.size() - 1))));

    const std::size_t pairCount = pairs.size();

    if (wordBits <= 16) {
        std::unique_ptr<std::uint32_t[]> packed(
            new std::uint32_t[pairCount]);

        for (std::size_t i = 0; i < pairCount; ++i) {
            const std::uint64_t pair = pairs[i];
            const auto first = static_cast<std::uint32_t>(pair >> 32);
            const auto second = static_cast<std::uint32_t>(pair);
            packed[i] = (rank[first] << wordBits) | rank[second];
        }

        std::vector<std::uint64_t>().swap(pairs);

        report(packed.get(), pairCount, wordBits, wordCount,
               lexicalOrder, words);
    } else {
        for (std::uint64_t& pair : pairs) {
            const auto first = static_cast<std::uint32_t>(pair >> 32);
            const auto second = static_cast<std::uint32_t>(pair);
            pair = (static_cast<std::uint64_t>(rank[first]) << wordBits) |
                   rank[second];
        }

        report(pairs.data(), pairCount, wordBits, wordCount,
               lexicalOrder, words);
    }

    return 0;
}
