# Chapter 2: Profiling to Find Bottlenecks

## Core Idea
Never optimize on intuition: form a hypothesis, profile with the least-detailed tool that answers it, change one thing, and keep tests green. Aim for "fast enough" and "lean enough", not maximal.

## Frameworks Introduced
- **Escalating profiling ladder** (cheapest/coarsest → most detailed): print/`time.time()`/decorator → `timeit`/`%timeit` → `/usr/bin/time -p` → `cProfile` (+SnakeViz) → `line_profiler` → `memory_profiler`/`mprof` → Scalene → py-spy (live processes) → VizTracer → `dis` / Specialist.
  - When to use: start coarse to find *which function*, then drill to *which line*.
- **Hypothesis-driven optimization**: state an easily testable hypothesis, change *only* that (never two things at once), gather enough evidence. Annotate printed code with predictions to calibrate intuition.
- **Stable benchmarking setup**: disable Turbo Boost/SpeedStep override, AC power, kill background tools (Dropbox/backups), run many times, optionally run level 1, reboot and rerun.
- **No-op `@profile` decorator**: lets pytest run code that is decorated for line_profiler/memory_profiler.

## Key Concepts
- **Profiling overhead**: 10–100× slowdowns typical; Julia example 5.8s plain → 13s cProfile → 31s line_profiler → hours memory_profiler.
- **timeit**: disables GC; `-n` loops, `-r` repeats; timeit.py reports *min*, IPython `%timeit` reports mean±std — don't mix.
- **`/usr/bin/time -p`**: real (wall), user, sys; `--verbose` adds Maximum resident set size and Major page faults.
- **cProfile**: function-level; `-s cumulative`; `-o file.stats` + `pstats` (`print_callers`/`print_callees`).
- **line_profiler**: `kernprof -l -v`; `@profile`; `% Time` column is key.
- **memory_profiler**: use "Mem usage" column (Increment buggy); `mprof run`/`mprof plot`; `profile.timestamp()` labels; `%memit`; `--pdb-mmem`.
- **Scalene**: CPU+memory+GPU, <20% overhead, no code changes; native vs Python vs system time.
- **py-spy**: sampling, attaches to running PID (`sudo env "PATH=$PATH" py-spy top --pid`), `py-spy record -o profile.svg -- python x.py`; (py-spy only to 3.11 at time of writing).
- **VizTracer**: time-based call stack; "Circular buffer is full" → `--min_duration`, `--ignore_c_function`, `--max_stack_depth`.
- **Specialist** (3.11+): green = specialised, orange = partial, red = adaptive; `abs(z) < 2.0` more specialised than `< 2`.

## Mental Models
- Use cProfile for the map, line_profiler for the street view.
- A "line of Python" is many bytecodes; fewer bytecodes with built-ins usually wins (but verify).
- Profiling a line can change its cost: splitting a compound `while` made runtime 31s → 63s.
- RAM growth per line is not the object's true size (GC and allocator headroom); read the trend over several lines.

## Anti-patterns
- **Optimizing without profiling** ("you will get it wrong").
- **Profiling inside a large app** (side effects, threads, I/O skew results): isolate the code first.
- **Disabling unit tests while optimizing** (author lost a day to a "speedup" that broke the algorithm).
- **Leaving print timing in code**; **mixing timeit and %timeit numbers**.
- **Trusting one run** (Turbo Boost gave 3.3s vs 5.6s).

## Code Examples
```python
from functools import wraps
def timefn(fn):
    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        print(f"@timefn: {fn.__name__} took {t2 - t1} seconds")
        return result
    return measure_time
```
```python
# no-op @profile so pytest works without line_profiler/memory_profiler
if 'line_profiler' not in dir() and 'profile' not in dir():
    def profile(func):
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        return inner
```
```bash
python -m cProfile -o profile.stats julia1_nopil.py
kernprof -l -v julia1_lineprofiler.py
python -m memory_profiler julia1_memoryprofiler.py   # or: mprof run / mprof plot
scalene julia1_memoryprofiler.py
sudo env "PATH=$PATH" py-spy top --pid <PID>
viztracer --min_duration 0.1 script.py && vizviewer results.json
```
- **What they demonstrate**: the minimum instrumentation for each tool; the decorator keeps tests runnable.

## Reference Tables
| Tool | Level | Overhead | Needs code change |
|---|---|---|---|
| timeit/%timeit | statement | none | no |
| `/usr/bin/time` | process | none | no |
| cProfile | function | ~2–3× | no |
| line_profiler | line | ~6× | `@profile` |
| memory_profiler | line | 10–100× | `@profile` |
| mprof | time-sampled | low | no |
| Scalene | line CPU+mem | <20% | no |
| py-spy | sampled, live | ~none | no (needs sudo) |
| VizTracer | call timeline | high (filter) | no |

## Worked Example
Julia set (1000×1000, maxiter 300): 34,219,980 `abs` calls (~10% of worst case 300M). line_profiler: `while abs(z) < 2 and n < maxiter` = 44.7% of time. Hypothesis: swapping to `n < maxiter and abs(z) < 2` is faster (`n < maxiter` costs ~21ns vs `abs(z) < 2` ~67ns via `%timeit`, short-circuits 1 in 301). Under line_profiler overhead no clear gain at x=1000; at x=5000 it was 143s vs 142s → slightly faster, modest. Memory: removing the `zs`/`cs` lists and building complex coords in-loop cut peak RAM 140MB → 60MB. `fn_expressive` (loop) 45.6ms vs `fn_terse` (`sum(range)`) 16.4ms; `dis` shows 17 vs 7 bytecode lines.

## Key Takeaways
1. Hypothesize, then measure; change one thing at a time.
2. Start with cProfile (+SnakeViz) to find the function, then line_profiler for the line.
3. Use memory_profiler/Scalene for RAM; use mprof timelines to explain to colleagues.
4. Use py-spy to inspect a live production process without changes.
5. Keep unit tests and coverage.py running after every optimization; use the no-op `@profile`.
6. Fewer bytecodes via built-ins is a rule of thumb, not a law.
7. Put the cheapest test first in `and` chains when it short-circuits often.
8. Encode performance assumptions as tests; CPython changes can invalidate old conclusions.

## Connects To
- **Ch 1**: why Python code is slow (bytecode/dynamic dispatch).
- **Ch 3–5**: choosing data structures after profiling identifies the hot spot.
- **Ch 6–7 (not yet released)**: perf stat, compiling with Cython.
