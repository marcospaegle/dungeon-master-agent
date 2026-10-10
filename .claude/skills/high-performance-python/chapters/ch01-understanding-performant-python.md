# Chapter 1: Understanding Performant Python

## Core Idea
High-performance programming is minimizing the cost of moving and transforming bits: understand the real hardware (compute, memory, buses) and how Python's abstractions (VM, GC, dynamic types, GIL) force your bits to move, then bring Python code closer to the ideal. Team velocity matters more than clever speedups.

## Frameworks Introduced
- **Fundamental computer system**: computing units + memory units + the connections (buses) between them. Each has a property: compute = ops/cycle (IPC) × clock; memory = capacity + read/write speed + latency; bus = width × frequency.
  - When to use: reasoning about *why* code is slow before touching it.
  - How: ask where the data lives (disk/RAM/L1-L2), how often it crosses a bus, and whether access is sequential.
- **Idealized computing vs the Python VM**: ideal = send `number` plus many `i` values to the CPU cache once, vectorize (SIMD), return one result. Python = one loop iteration per value, fragmented objects, dynamic dispatch.
- **Make it work → Make it right → Make it fast** (in that order). "Build one to throw away"; add tests/docs before profiling/compiling.
- **Optimize for the team, not the code block**: pick problems that hurt *every day* (1% on a daily pain beats 100x on a yearly one); quantify cost in money/time; start with the simplest solution that teaches you something.

## Key Concepts
- **Amdahl's law**: speedup from more cores is capped by the serial portion.
- **GIL**: one Python instruction at a time per process; escape via `multiprocessing`, numpy/numexpr, Cython/Numba, distributed.
- **Vectorization / SIMD**: one instruction on multiple data per cycle; needs contiguous typed data (numpy), not Python lists.
- **Heavy data**: cost/effort of moving data; keep data where it's needed, move it as little as possible.
- **Memory tiering**: speed and capacity are inversely proportional (disk → RAM → L1/L2).
- **Bus width vs frequency**: width helps sequential/vectorized reads; frequency helps random reads.
- **Hyperthreading / out-of-order execution / multicore**: how CPUs gain speed now that clock and IPC are stagnant (HT up to ~30%).
- **Adaptive specializing interpreter (3.11)**: 10–25% speedups. **Copy-and-patch JIT (3.13)**: stencils from LLVM with "holes" filled at runtime.

## Mental Models
- Use the survey analogy for Amdahl: 100 askers can't beat the 1-minute serial answer time.
- Python is slow because of abstraction (GC fragmentation, no layout control, dynamic types, not compiled, GIL), yet it recoups development speed; libraries (numpy, scikit-learn) wrap C/Fortran so well-used Python can match C.
- Ask "If our system runs faster, will we as a team run slower in the long run?" before introducing Cython-like complexity.

## Anti-patterns
- **Unreviewed, untested prototype shipped to production**: becomes unloved inertia on one developer.
- **Assuming idiomatic-looking code is fast**: `search_fast` vs `search_slow` are both O(n), but not terminating the loop early wastes work.
- **Clever, unreadable code**: prefer longer readable function + docstring + tests.
- **Using `assert` for data validation in notebooks/prod**: raise `ValueError`; use Pandera for dataframes.
- **Copy-paste snippets**: build a library instead.

## Code Examples
```python
def check_prime(number):
    sqrt_number = math.sqrt(number)
    for i in range(2, int(sqrt_number) + 1):
        if (number / i).is_integer():
            return False
    return True
```
- **What it demonstrates**: one loop iteration per `i` in Python; ideal hardware would test `V` values per instruction (not valid Python; numpy provides this).

## Reference Tables
| Memory unit | Traits |
|---|---|
| Spinning disk | persistent, slow, bad on random access, ~20 TB |
| SSD | faster than HDD, ~1 TB |
| RAM | fast, handles random access, ~64 GB |
| L1/L2 cache | extremely fast, tiny (dozens of MB) |

| Python version | Interpreter change |
|---|---|
| 3.11 | adaptive type-specializing interpreter (10–25%) |
| 3.12 | clean-ups + DSL for generating the interpreter |
| 3.13 | hot-spot detector + copy-and-patch JIT |
GIL-free build (PEP 703) expected generally ~2028.

## Worked Example
`search_unknown1` (`any(gen)`) vs `search_unknown2` (`any([list comp])`): the list-comp version builds the whole list before `any` can short-circuit, so it does the unnecessary work the generator avoids. Lesson: you can't tell by reading; profile.

## Key Takeaways
1. Reduce data movement: keep data in cache-friendly, contiguous, typed structures.
2. Cores don't help beyond the serial fraction; in Python use processes, not threads, for CPU-bound work.
3. Order of work: make it work, make it right (tests/docs/Docker/CI), then make it fast.
4. Good practice must-haves: README, tests/ with pytest + coverage, docstrings, source control, black/flake8, isolated envs, CI.
5. JIT in 3.13 won't help numpy/pandas/scipy (already compiled); it helps native numeric Python.
6. Value = impact × frequency; estimate in money.

## Connects To
- **Ch 2**: profiling is how you find the wasted operations.
- **Ch 3–5**: concrete data structures that realize these memory/compute trade-offs.
- **Ch 6–9 (not yet released)**: numpy vectorization, Cython/Numba, multiprocessing.
