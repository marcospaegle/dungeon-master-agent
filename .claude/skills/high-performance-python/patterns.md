# Patterns

## Profile-Hypothesis-Change-Verify loop
**When to use**: any optimization.
**How**: write hypothesis → coarse timing → cProfile → line_profiler/memory_profiler → change one thing → rerun tests + profile.
**Trade-offs**: profilers add 2–100× overhead; confirm wins with unprofiled timeit.

## No-op @profile decorator
**When to use**: tests run code decorated for line_profiler/memory_profiler.
**How**: define `profile` as pass-through if not in namespace (Ch 2 code).
**Trade-offs**: remove when done; harmless otherwise.

## Timing decorator
**When to use**: quick function timing without a profiler.
**How**: `@timefn` with `functools.wraps` and `time.time()`.
**Trade-offs**: coarse, overhead noticeable at millions of calls.

## Sort once + bisect
**When to use**: repeated lookups/nearest-value on ordered data.
**How**: `sorted()`/Timsort, then `bisect_left`, `insort` to insert.
**Trade-offs**: O(log n) vs dict O(1) but no O(n) conversion and no unique-key restriction.

## Set/dict for membership and dedup
**When to use**: uniqueness, lookup by key.
**How**: `set.add`, `in`, `dict[key]`.
**Trade-offs**: more memory; needs hashable keys with good hash.

## Content-based `__hash__`/`__eq__`
**When to use**: value-equal objects as keys.
**How**: `hash((self.x, self.y))` plus matching `__eq__`.
**Trade-offs**: keys must be effectively immutable; bad hash = O(n) lookups.

## Shed overallocation
**When to use**: millions of small lists held in RAM.
**How**: `list(comprehension)` or `tuple(...)` after building.
**Trade-offs**: tuple is immutable; copy costs time once.

## Generator pipeline
**When to use**: streaming/larger-than-RAM data, early termination.
**How**: chain generator functions; consume with `islice`/loops; use `groupby`, `filterfalse`, `takewhile`.
**Trade-offs**: single pass; recompute if reused; `groupby` groups only sequential keys.

## Generator expression aggregation
**When to use**: counting/summing filtered data.
**How**: `sum(1 for n in gen if cond)` instead of `len([...])`.
**Trade-offs**: none significant.

## Rolling window
**When to use**: moving statistics over a stream.
**How**: tuple window with `window[1:] + (item,)`, or `deque` with `popleft()`.
**Trade-offs**: deque mutates in place; copying negates gain.

## Stable benchmarking
**When to use**: before comparing timings.
**How**: disable Turbo Boost, AC power, no background tasks, many repeats, reboot to confirm.
**Trade-offs**: setup effort.
