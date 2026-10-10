# Chapter 3: Lists and Tuples

## Core Idea
Performance starts with knowing which questions you ask of your data and picking the structure that answers them fast. Lists (dynamic arrays) and tuples (static arrays) give O(1) indexed lookup; unordered search costs O(n), sorted search O(log n).

## Frameworks Introduced
- **Array model**: contiguous "buckets" of pointers; element `i` is at `M + i` → O(1), independent of size and element type.
- **Search ladder**: unsorted → linear search O(n) (what `list.index()` does); sorted → binary search O(log n) via `bisect`; keyed → dict/set O(1) (Ch 4).
  - How: sort once (Timsort: O(n) best, O(n log n) worst), then `bisect`; use `bisect.insort` to keep order; `bisect_left` for nearest value.
- **List vs tuple decision**: tuple = multiple properties of one unchanging thing (phone number parts, polynomial coefficients, a game result); list = growing collection of disparate things. Often a list of tuples.
- **Pick the right structure and stick with it**: conversion cost (e.g. list → dict is O(n)) can negate the lookup gain.

## Key Concepts
- **List overallocation**: `M = (N + (N >> 3) + 6) & ~3` (3.12.2): ~12.5% headroom for large lists, much more for small (1 item → 4, 9 → 16). Happens on append or list comprehension, not literal creation.
- **Tuple freelist**: tuples of size 0–20 cached, up to 2,000 each, avoiding kernel allocation; instantiation can be ~7.6× faster than lists. Other freelists are tiny (gens 80, dicts 80, floats 100, lists 80).
- **Tuple concatenation** is O(n) and always makes a new tuple; no in-place append.
- **Memory**: 1M × 9-int samples: list comprehension 444 MB, `list(...)` copy 396 MB (1.12× smaller), tuple 372 MB (1.19× smaller).
- **Mixed types** add overhead; `array` module / numpy remove it.
- `functools.total_ordering` derives ordering from `__eq__`/`__lt__` at a small cost.

## Mental Models
- Use a tuple when the data becomes static; use `list(list_comp)` / `tuple(...)` to shed overallocation when you will hold many small collections.
- Generic code is slower than code specialized to the problem.

## Anti-patterns
- **Linear search in a loop over an ordered list**: sort + bisect.
- **Converting to dict to do one lookup**: O(n) conversion vs O(log n) bisect.
- **Millions of small comprehension-built lists** in RAM-tight code.
- **Building tuples with repeated `+`**: O(n) each.

## Code Examples
```python
import bisect
def find_closest(haystack, needle):
    i = bisect.bisect_left(haystack, needle)
    if i == len(haystack):
        return i - 1
    elif haystack[i] == needle:
        return i
    elif i > 0:
        j = i - 1
        if haystack[i] - needle > needle - haystack[j]:
            return j
    return i
```
- **What it demonstrates**: nearest-value lookup in a sorted list in O(log n); combine with `bisect.insort`.

## Reference Tables
| Operation | list | tuple |
|---|---|---|
| index `a[i]` | O(1) | O(1) |
| append | amortized O(1) | n/a (concat O(n)) |
| search unsorted | O(n) | O(n) |
| search sorted | O(log n) | O(log n) |
| mutable / resizable | yes | no |
| memory | extra headroom + bookkeeping | exact, cached freelist |

## Worked Example
Many small lists: `sample_comp` (comprehension, overallocated) 444.45 MB; wrap in `list(...)` → 396.45 MB; cast to `tuple` → 372.45 MB, saving ~72 MB for 1,000,000 samples of 9 items. A list of 100,000,000 built by append uses 104,391,068 slots (4.4% waste) vs exactly 100,000,000 for a tuple.

## Key Takeaways
1. Index in O(1); search unsorted in O(n); sorted in O(log n).
2. Sort once + `bisect` beats building a dict for one-off lookups.
3. Overallocation is cheap per list but huge across millions of lists.
4. Tuples are lighter and faster to create; use them for fixed data.
5. Timings in ns scale: `l[5]` ≈ 14 ns regardless of list size.

## Connects To
- **Ch 4**: hash tables fix O(n) search for unordered data.
- **Ch 5**: generators avoid materializing lists.
- **Ch 2**: use `%timeit`/`%memit` to verify.
