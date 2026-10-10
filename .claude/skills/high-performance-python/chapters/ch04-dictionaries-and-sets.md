# Chapter 4: Dictionaries and Sets

## Core Idea
Dicts and sets use open-addressing hash tables to give O(1) insert/lookup on unordered keyed data, at the cost of memory and dependence on the hash function's quality (entropy).

## Frameworks Introduced
- **Hash table mechanics**: `index = hash(key) & mask`; on collision, probe with a perturbed sequence using higher hash bits (`i = (i*5 + perturb + 1) & mask`, `perturb >>= 5`); empty bucket = miss.
- **Sizing rules**: always < 2/3 full (3/5 for sets), size a power of two, min 8; resize ~3× on growth to the next power of two; sets switch to 2× growth after 50,000 elements. Resizing happens only on insert (so popping many items then inserting can shrink it).
- **Dict storage trick**: key/value pairs appended to a compact array; the table stores only indices (30–95% memory saving; insertion order guaranteed since 3.7).
- **Hash function design**: hashing is only as fast as the key's `__hash__`; define `__hash__` and `__eq__` together from the object's contents (e.g. `hash((self.x, self.y))`).
- **Entropy of a hash**: more evenly distributed hash values = fewer collisions; ideal hash = max entropy. Know the mask size (e.g. 5,000 keys → 16,384 buckets → last 14 bits matter).

## Key Concepts
- **Hashable**: has `__hash__` and `__eq__`; lists aren't (mutable).
- **Mask**: `size - 1` in binary; truncates the hash to table size.
- **Deletion**: leaves a sentinel (not NULL) so probe chains still work; slots reclaimed at resize.
- **Load factor**: how full/well-distributed the table is.
- **Amortized O(1)**: occasional expensive resize averages out.
- **SipHash 1-3**: hash for non-int types; int hash = the int itself.
- Default object hash = `id()` (memory address), so equal-content instances are distinct unless you override.

## Mental Models
- Use a set for "unique/membership"; use a dict when you need a value attached to a key.
- Worst case (all keys collide) degrades to O(n), no better than a list.
- A non-O(1) key hash makes the whole dict non-O(1).

## Anti-patterns
- **List-based uniqueness checking** (O(n log n)/quadratic): 1.3 s vs 2.32 ms for sets on 10,000 names (560×; 4,300× at 100,000).
- **Weak custom hash** (e.g. first letter only → 26 buckets; constant `return 42`): 54× slower lookups, slower than a list.
- **Default identity hash when you need value equality** (`Point(1,1)` twice in a set).
- **Assuming namespace-scoping benchmarks still hold**: the authors dropped this section because CPython changes erased the differences.

## Code Examples
```python
class Point:
    def __init__(self, x, y): self.x, self.y = x, y
    def __hash__(self): return hash((self.x, self.y))
    def __eq__(self, other): return self.x == other.x and self.y == other.y
```
```python
def twoletter_hash(key):  # perfect hash for 676 two-letter keys
    offset = ord('a')
    k1, k2 = key
    return (ord(k2) - offset) + 26 * (ord(k1) - offset)
```
- **What they demonstrate**: content-based hashing built on tuple hash; a problem-specific zero-collision hash.

## Reference Tables
| Property | dict | set |
|---|---|---|
| Max load | 2/3 | 3/5 |
| Min size | 8 | 8 |
| Growth | ~3× → power of 2 | 2× after 50,000 elements |
| Insert/lookup | O(1) amortized | O(1) amortized |
| Stores values | yes (indices into entries array) | no |

Hash timings (1M lookups, 676 keys): bad hash 10.16 s, good hash 0.187 s, list 8.96 s.

## Worked Example
Cities hashed by first letter (`ord(self[0])`) in a size-8 table: Rome (82 & 7 = 2) and Barcelona (66 & 7 = 2) collide; Barcelona probes further. Deleting Rome writes a sentinel so a lookup of Barcelona keeps probing. With 500 cities only 26 distinct hashes exist (~19 per hash; ~38 for 1,000), so lookups need up to dozens of probes; fix by hashing more of the string (the default).

## Key Takeaways
1. Dict/set lookup is O(1) only with a good, cheap hash.
2. Override `__hash__` and `__eq__` together using immutable content.
3. Tables are always ≥1/3 empty; budget memory accordingly.
4. Prefer sets for dedup/membership; swapping a list for a set can give 100–1000× gains.
5. Encode performance assumptions in tests since CPython internals shift.

## Connects To
- **Ch 3**: lists/tuples and bisect as the ordered alternative.
- **Ch 5**: iterating dicts/sets and `iter()`.
- **Ch 2**: use timeit to confirm hash quality effects.
