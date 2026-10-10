# Chapter 5: Iterators and Generators

## Core Idea
Generators lazily produce one value at a time, trading random access for near-zero memory and early termination. Organize code as generate → transform pipelines, and process datasets larger than RAM.

## Frameworks Introduced
- **For loop deconstruction**: `iter(obj)` then repeated `next()` until `StopIteration`; a generator is already its own iterator.
- **Generate-then-transform separation**: generator functions create data; ordinary functions consume it. Makes transforms reusable and series-agnostic (e.g. `num_odd_under_5000(gen)`).
- **Chained generator pipeline**: `read_data` → `groupby_day` → `filter_anomalous_groups` → `islice(first 5)`; only enough data is read to satisfy the consumer.
- **CPU vs memory trade-off**: precomputed lists win if values are reused; generators win when single-pass/online and RAM-bound.
- **itertools toolkit**: `islice` (slice infinite generators), `chain`, `takewhile`, `cycle`, `groupby` (sequential groups only), `filterfalse`; see docs recipes.

## Key Concepts
- **Lazy evaluation**: compute only on `next()`.
- **Single-pass / online algorithm**: only the current value is available; no length, no re-reading.
- **Generator comprehension**: `( ... )` vs list comp `[ ... ]`; `sum(1 for n in gen if ...)` replaces `len([...])`.
- **Built-ins that are lazy**: `range`, `map`, `zip`, `filter`, `reversed`, `enumerate`.
- **`yield from`** delegates to a sub-iterator.
- **Welford's online algorithm**: one-pass mean/skew/kurtosis (further memory savings).
- **deque**: O(1) appends/pops at both ends for rolling windows (but mutates in place).

## Mental Models
- Use a generator when each element's result depends only on its value (or a small window).
- Wrapping a generator in `list` for `len` defeats its purpose (98 MB wasted).
- Fibonacci generator can be infinite; take what you need with `islice`/`takewhile`.

## Anti-patterns
- **`len([n for n in gen if ...])`**: builds a throwaway list; use `sum(1 for ...)`.
- **Over-using itertools into un-Pythonic one-liners** (`fibonacci_succinct`); prefer the readable `fibonacci_transform` loop.
- **Generators when you need multiple passes**: they recompute.
- **Yielding a deque directly** (shared mutable view) vs copying to tuple (loses the benefit).

## Code Examples
```python
def fibonacci():
    i, j = 0, 1
    while True:
        yield i
        i, j = j, i + j
```
```python
from itertools import groupby, filterfalse, islice
def groupby_day(iterable):
    key = lambda row: row.date.day
    for day, data_group in groupby(iterable, key):
        yield list(data_group)

def filter_anomalous_groups(data):
    yield from filterfalse(is_normal, data)

anomalies = islice(filter_anomalous_groups(groupby_day(read_data(f))), 5)
```
- **What they demonstrate**: infinite series as a function; a lazy multi-stage pipeline with early stop.

## Reference Tables
| Case | Approach |
|---|---|
| 100,000 Fibonacci, list | 227 ms, +418 MB |
| 100,000 Fibonacci, generator | 81.9 ms (2.7× faster), ~0 MB |
| 100M Fibonacci list | ~3.1 GB (may be unrunnable) |

## Worked Example
Anomaly detection over 631,152,000 per-second points (20 years): read lines lazily, group by day, keep days failing `scipy.stats.normaltest` (p < 1e-3), and `islice` the first five. Changing from daily chunks to a 3,600-point rolling window only swaps `groupby_day` for `groupby_window` (`window = window[1:] + (item,)` per step), with the memory bound visible as the window size.

## Key Takeaways
1. Generators cut memory from O(n) to O(1) and often time too.
2. Separate producing data from transforming it.
3. Design algorithms to be online/single-pass to use generators.
4. Use generator expressions for aggregation, not list comps.
5. Iterator-shaped code ports easily to multiprocessing/clusters (`map`-like APIs).

## Connects To
- **Ch 3**: lists' overallocation and append costs avoided.
- **Ch 4**: iteration over dict keys/sets.
- **Ch 9–10 (not yet released)**: parallel map over iterators.
