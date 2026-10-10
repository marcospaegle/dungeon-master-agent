---
name: high-performance-python
description: "Knowledge base from \"High Performance Python, 3rd Edition (Early Release)\" by Micha Gorelick and Ian Ozsvald. Use when applying their frameworks for profiling (cProfile, line_profiler, memory_profiler, Scalene, py-spy), lists/tuples vs dicts/sets, hashing, generators and iterators, GIL/JIT, Python optimization, studying the book, or referencing its concepts."
---

<!-- argument-hint: [topic, framework name, or chapter number] -->

# High Performance Python, 3rd Edition (Early Release, 2024-07-26)
**Authors**: Micha Gorelick, Ian Ozsvald | **Pages**: ~226 | **Chapters available**: 5 of 12 | **Generated**: 2026-10-10

> **Coverage note**: the source is an *Early Release*. Only Ch 1–5 exist (Understanding Performant Python, Profiling, Lists & Tuples, Dicts & Sets, Iterators & Generators). Planned Ch 6–12 (Matrix/Vector with numpy, Compiling to C, Asynchronous I/O, multiprocessing, Clusters & Job Queues, Using Less RAM, Lessons from the Field) were unavailable and are NOT covered; the text contains "[Link to Come]" placeholders. Don't invent their content from this skill.

## How to Use This Skill

- **Without arguments** — load core frameworks below
- **With a topic** — ask about `bisect`, `line_profiler`, `hash collisions`; I read the relevant chapter
- **With chapter** — ask for `ch02`
- **Browse** — ask "what chapters do you have?"

When a topic isn't in Core Frameworks, I read the chapter file before answering.

---

## Core Frameworks & Mental Models

**Rule 0: measure, don't guess.** Form a hypothesis, profile, change *one* thing, re-run tests and profile. "You will get it wrong" on intuition. Aim for "fast enough" and "lean enough".

**Make it work → Make it right → Make it fast.** Prototype (build one to throw away), then tests/docs/README/Dockerfile/CI, then profile and compile/parallelize using the test suite as a safety net. Readability beats cleverness. Optimize for team velocity; ask "if the system runs faster, will the team run slower?" Value = impact × frequency (1% on a daily pain > 100x on a yearly one); price it in money.

**Escalating profiling ladder** (start coarse):
1. print / `time.time()` / `@timefn` decorator, `timeit`, `%timeit`, `/usr/bin/time -p` (real/user/sys, max RSS, page faults)
2. `cProfile` (`-s cumulative`, `-o stats`, `pstats`) + SnakeViz → *which function*
3. `line_profiler` (`kernprof -l -v`, `@profile`) → *which line*
4. `memory_profiler` / `mprof` / `%memit`; Scalene (CPU+RAM+GPU, <20% overhead)
5. `py-spy` for a live process (`top`, `record`); VizTracer for a time-based call stack
6. `dis` bytecode and Specialist (3.11+ specialisation colours)
Use stable benchmarking: disable Turbo Boost, AC power, no background tasks, repeat, reboot-confirm. Use the **no-op `@profile` decorator** so pytest still runs. Never mix `timeit.py` (min) and `%timeit` (mean±std) numbers.

**Hardware model.** Compute + memory (disk → RAM → L1/L2: faster = smaller) + buses. Optimize which data is where, its layout (sequential beats random), and how often it moves ("heavy data"). Python's abstractions (GC fragmentation, dynamic types, not compiled, GIL) block vectorization and cache use; escape with numpy, Cython/Numba, multiprocessing. Amdahl: serial fraction caps speedup. Python 3.11 specialising interpreter (10–25%), 3.13 copy-and-patch JIT (won't help numpy/pandas), PEP 703 GIL-free ~2028.

**Lists vs tuples.** Both O(1) index. Lists are dynamic arrays with overallocation `(N + (N>>3) + 6) & ~3`; tuples are static, exact-size, with a freelist (size 0–20 × 2,000; up to ~7.6× faster to create). Use tuples for fixed multi-property things, lists for growing collections. Shed overallocation via `tuple()`/`list(...)` when holding millions of small collections (1M×9 ints: 444 MB → 372 MB).

**Search ladder.** Unsorted: linear O(n). Sorted: Timsort once + `bisect` O(log n) (`insort`, nearest value via `bisect_left`). Keyed: set/dict O(1). Don't convert to a dict just for one lookup (O(n) build). Pick the right structure and stick with it.

**Dicts and sets.** Open-addressing hash table; `hash & mask`, perturbed probing, deletion sentinels, < 2/3 full (set 3/5), power-of-2 size, resize on insert only. Values live in a compact entries array (insertion order since 3.7). Speed depends on hash entropy: override `__hash__` and `__eq__` together from immutable contents (`hash((x, y))`); a poor hash gave 54× slower lookups, worse than a list. Set vs list for dedup: 560× faster at 10k, 4,300× at 100k.

**Iterators and generators.** `for` = `iter()` + `next()` until `StopIteration`. Generators are lazy, O(1) memory, enable early termination; best for online/single-pass algorithms. Separate generating from transforming; chain stages (`groupby`, `filterfalse`, `takewhile`, `islice`, `chain`, `cycle`). Use `sum(1 for ...)` not `len([...])`. Precompute (list) if data is reused; generators recompute. Readable loops beat itertools one-liners.

---

## Chapter Index

| # | Title | Key Frameworks |
|---|-------|----------------|
| [ch01](chapters/ch01-understanding-performant-python.md) | Understanding Performant Python | hardware model, Amdahl/GIL, vectorization, make it work/right/fast, team-first, JIT/GIL future |
| [ch02](chapters/ch02-profiling-to-find-bottlenecks.md) | Profiling to Find Bottlenecks | profiling ladder, hypothesis loop, cProfile/line_profiler/memory_profiler/Scalene/py-spy/VizTracer, dis/Specialist, no-op @profile |
| [ch03](chapters/ch03-lists-and-tuples.md) | Lists and Tuples | array model, overallocation, bisect, list vs tuple, freelist |
| [ch04](chapters/ch04-dictionaries-and-sets.md) | Dictionaries and Sets | hash table, probing, sizing rules, entropy, custom hash |
| [ch05](chapters/ch05-iterators-and-generators.md) | Iterators and Generators | lazy evaluation, generate/transform split, itertools, pipelines |

## Topic Index

- **Amdahl's law** → ch01
- **bisect / binary search** → ch03
- **bytecode / dis / Specialist** → ch02
- **cProfile / SnakeViz** → ch02
- **deque / rolling window** → ch05
- **GIL** → ch01
- **hash collisions / entropy / `__hash__`** → ch04
- **hashing, dict/set resizing** → ch04
- **itertools** → ch05
- **JIT / PEP 703** → ch01
- **line_profiler / kernprof** → ch02
- **list overallocation** → ch03
- **memory_profiler / mprof / %memit** → ch02, ch03, ch05
- **py-spy / Scalene / VizTracer** → ch02
- **team practices / testing / Docker / notebooks** → ch01
- **timeit / benchmarking setup / Turbo Boost** → ch02
- **tuple freelist** → ch03
- **vectorization / SIMD** → ch01
- **generators / lazy evaluation** → ch05

## Supporting Files

- [glossary.md](glossary.md) — key terms with definitions
- [patterns.md](patterns.md) — techniques and patterns
- [cheatsheet.md](cheatsheet.md) — decision rules, thresholds, smells

---

## Scope & Limits

This skill covers only the five released chapters of the Early Release. Compiling (Cython/Numba), numpy, asyncio, multiprocessing, clusters, and RAM-reduction chapters are not included. Version-specific numbers (CPython 3.12) may change; re-measure.
