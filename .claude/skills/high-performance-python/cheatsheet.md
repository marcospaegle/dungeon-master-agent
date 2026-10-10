# Cheatsheet

## Decision rules
| When | Do | Because |
|---|---|---|
| Code is slow/RAM-heavy | Profile first, with a stated hypothesis | intuition is usually wrong |
| Don't know which function | cProfile + SnakeViz | map before street view |
| Know the function | line_profiler (`kernprof -l -v`) | per-line % time |
| RAM too high | memory_profiler/`mprof`, Scalene | trend over lines, not one line |
| Live prod process | py-spy `top`/`record` | sampling, no code changes |
| Need call timeline | VizTracer with `--min_duration` | avoid circular buffer overflow |
| Unsorted data, many lookups | set/dict | O(1) vs O(n) |
| Sorted data, one-off lookups | bisect | avoids O(n) dict build |
| Fixed data | tuple | lighter, freelist, faster |
| Growing data | list | amortized O(1) append |
| Millions of small lists | `tuple()`/`list()` copy | drop overallocation |
| Big/streaming data, single pass | generator | O(1) memory |
| Data reused many times | list/precompute | generator recomputes |
| CPU-bound parallel in Python | processes, not threads | GIL |
| Optimizing | keep tests + coverage running | speedups can be bugs |
| Custom key class | `__hash__`+`__eq__` on contents | default is `id()` |

## Thresholds & numbers
- Profiler overhead: cProfile ~2–3×, line_profiler ~6×, memory_profiler 10–100×, Scalene <20%.
- List growth: ~12.5% headroom `(N + (N>>3) + 6) & ~3`; small lists far more.
- Dict < 2/3 full (set < 3/5), power-of-2 size, min 8, resize ~3×.
- Tuple freelist: sizes 0–20 × 2,000.
- Hyperthreading ≤ ~30%; Python 3.11 specialisation 10–25%.
- Timing reference: list index ≈ 14 ns; `abs(z)<2` ≈ 67 ns vs `n<maxiter` ≈ 21 ns.

## Tells & smells
- `len([x for ...])` → use `sum(1 for ...)`.
- Hand-written loop where a built-in exists (`sum(range)` 2.8× faster) → check bytecode count.
- Custom `__hash__` returning few distinct values → collision chains.
- Same set of results across threads yields no speedup → GIL.
- `NameError: profile` under pytest → add no-op decorator.
- Timings differ run to run → Turbo Boost/background load.
- "Circular buffer is full" → filter VizTracer.

## Order of work
Make it work → make it right (tests, docs, Docker, CI) → make it fast (profile, compile, parallelize).
