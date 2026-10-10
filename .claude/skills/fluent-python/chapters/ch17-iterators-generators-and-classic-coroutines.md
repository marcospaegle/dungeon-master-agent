# Chapter 17: Iterators, Generators, and Classic Coroutines

## Core Idea
The Iterator pattern is built into Python (`iter()`, `next()`, `StopIteration`), so you never hand-code it: a generator function is a factory of iterators. Generators produce data for iteration; classic coroutines (same machinery, used with `.send()`) consume data. Don't mix the two uses.

## Frameworks Introduced
- **The iter() resolution order**: "Whenever Python needs to iterate over an object x, it automatically calls iter(x)."
  - When to use: understanding/debugging why something is (or isn't) iterable.
  - How: (1) if `__iter__` exists, call it for an iterator; (2) else if `__getitem__` exists, build an iterator fetching indexes 0,1,2... until `IndexError`; (3) else `TypeError: 'C' object is not iterable`.
  - Why it works / failure mode: sequences are iterable via the legacy `__getitem__` path, but `isinstance(x, abc.Iterable)` only checks `__iter__`. The most accurate iterability test is `iter(x)` + `except TypeError`.
- **Iterable vs Iterator contract**: iterables have `__iter__` that builds a *new* iterator each call; iterators implement `__next__` and `__iter__` returning `self`. "Iterators are also iterable, but iterables are not iterators."
  - When to use: designing any collection/stream class.
  - How: collection class defines `__iter__` (best as generator function); never add `__next__` to the collection itself.
  - Why it works / failure mode: multiple independent traversals need independent iterator state. Making the iterable its own iterator is an anti-pattern (Alex Martelli).
- **Sentence evolution (5 takes)**: sequence protocol -> classic Iterator class -> generator function -> lazy generator (`re.finditer`) -> generator expression.
  - When to use: as the refactoring ladder for any "class whose only job is to iterate".
  - How: replace hand-written iterator class with `yield`; replace eager list (`findall`) with lazy source (`finditer`); collapse to genexp if it fits in a line or two.
- **Eager vs lazy**: Iterator interface is lazy by design: `next()` yields one item at a time. Lazy postpones producing values to the last possible moment (saves memory/CPU).
- **Baby-steps recursion with yield from** (tree traversal): grow `tree()` level by level (0, 1, 2, 3), spot the nested-for pattern, replace nested loop with recursive `yield from`, then merge helper into one function with a `level=0` parameter.
- **Generic variance for Generator**: `Generator[YieldType, SendType, ReturnType]`. YieldType and ReturnType are "output" -> covariant; SendType is "input" -> contravariant.

## Key Concepts
- **iterable**: any object from which `iter()` can get an iterator (`__iter__`, or `__getitem__` with 0-based ints).
- **iterator**: any object implementing `__next__` (and `__iter__` returning self); exhausted iterators keep raising `StopIteration` and cannot be reset: call `iter()` on the original iterable.
- **generator function**: any function with `yield` in its body; calling it returns a generator object (it is a "generator factory"). Generators *yield* values; functions *return* them.
- **generator**: an iterator built by the Python compiler (generator function or generator expression); `type(g())` and `type(genexpr)` are both `generator`.
- **sentinel (2-arg iter)**: `iter(callable, sentinel)` calls the callable with no args until it returns the sentinel, then raises `StopIteration`.
- **delegating generator / subgenerator / client**: with `yield from`, the delegator pauses; sub-values pass directly to the client; subgenerator's `return x` becomes the value of the `yield from` expression.
- **classic coroutine**: a generator used as a data consumer via `.send()`; must be "primed" with `next()` or `.send(None)`.
- **GeneratorExit**: raised at the suspended `yield` by `.close()`; if not handled it ends the coroutine silently; later `.send()` raises `StopIteration`.
- **StopIteration.value**: how a generator's `return x` is smuggled to the caller (PEP 342 hack); `yield from` extracts it automatically.
- **combinatorics generators**: `product`, `combinations`, `combinations_with_replacement`, `permutations`.

## Mental Models
- Use a generator function as `__iter__` whenever a class exists "just to produce items"; it replaces the whole Iterator class.
- Think of `yield from sub()` as an automatic `for x in sub(): yield x` plus a pipe for sent values and the return value.
- Think of a generator-as-coroutine like a tuple-as-record vs tuple-as-list: same object, different use; hint it differently (`Iterator[float]` vs `Generator[Event, float, int]`).
- Use a generator expression for one-liners; "if the generator expression spans more than a couple of lines, I prefer to code a generator function."
- Think of stdlib generator functions as composable Lego: they take iterables and return generators, so chain them.

## Anti-patterns
- **Iterable that is its own iterator (`__next__` on the collection)**: breaks multiple traversals; "a common antipattern".
- **Hand-coding SentenceIterator**: bookkeeping for state that `yield` gives free; only didactic.
- **`list(itertools.count())` / sorted / reducers on infinite iterators**: never terminates; bound with `islice`/`takewhile`.
- **Mixing generator and coroutine concepts** (Beazley: "Coroutines are not related to iteration").
- **Accumulating floats by repeated `+=`** (`aritprog_v3` using `count`): error accumulates; compute `begin + step * index` instead.
- **Calling `.send()` on an iterator-style generator**, or driving coroutines by hand (`.throw()`, `.send()`) outside a framework.
- **Explicit isinstance(Iterable) check right before iterating**: just iterate and let `TypeError` surface, or catch it.

## Code Examples
```python
class Sentence:
    def __init__(self, text):
        self.text = text
    def __iter__(self):
        for match in RE_WORD.finditer(self.text):
            yield match.group()
```
- **What it demonstrates**: lazy iterable via generator function; no iterator class, no word list.

```python
def aritprog_gen(begin, step, end=None):
    result = type(begin + step)(begin)
    forever = end is None
    index = 0
    while forever or result < end:
        yield result
        index += 1
        result = begin + step * index
```
- **What it demonstrates**: type coercion via `type(begin + step)`; avoiding float drift.

```python
def tree(cls, level=0):
    yield cls.__name__, level
    for sub_cls in cls.__subclasses__():
        yield from tree(sub_cls, level+1)
```
- **What it demonstrates**: recursive generator with implicit base case (empty `__subclasses__()` -> loop body not run).

```python
def averager() -> Generator[float, float, None]:
    total = 0.0
    count = 0
    average = 0.0
    while True:
        term = yield average
        total += term
        count += 1
        average = total/count
```
- **What it demonstrates**: coroutine keeps state in locals (no closure/attributes); prime with `next(coro)`, then `.send(10)`.

```python
try:
    coro_avg.send(STOP)
except StopIteration as exc:
    result = exc.value      # Result(count=3, average=15.5)
```
- **What it demonstrates**: retrieving a coroutine's `return` value.

```python
d6_iter = iter(d6, 1)                 # callable + sentinel
read64 = partial(f.read, 64)
for block in iter(read64, b''): ...   # block reader
```

## Reference Tables
Generator functions in stdlib (grouped by behavior):

| Group | Functions |
|---|---|
| Filtering | `compress(it, sel)`, `dropwhile`, `filter`, `filterfalse`, `islice`, `takewhile` |
| Mapping | `accumulate(it,[func])`, `enumerate(it,start)`, `map`, `starmap(func, it)` |
| Merging | `chain`, `chain.from_iterable`, `product(*its, repeat=)`, `zip(strict=)` (3.10), `zip_longest(fillvalue=)` |
| Expanding | `combinations`, `combinations_with_replacement`, `count(start,step)`, `cycle`, `pairwise` (3.10), `permutations`, `repeat(item,[times])` |
| Rearranging | `groupby(it,key)` (input must be sorted/clustered by key), `reversed(seq)` (sequences only), `tee(it,n)` |
| Reducing (consume whole iterable) | `all` (short-circuits; `all([])` True), `any` (short-circuits; `any([])` False), `max/min(key=,default=)`, `functools.reduce`, `sum` (`math.fsum` for floats) |

| Type hint | Meaning |
|---|---|
| `Iterable[T]` (`collections.abc`) | parameter that you iterate |
| `Iterator[T]` | = `Generator[T, None, None]`; for generator functions used as iterators |
| `Generator[Y, S, R]` | classic coroutine: yields Y, receives S via `.send()`, returns R |

Variance: YieldType/ReturnType covariant (output); SendType contravariant (input).

## Worked Example
Running average coroutine: `coro_avg = averager(); next(coro_avg)` -> 0.0 (priming runs to first `yield`); `.send(10)` -> 10.0; `.send(30)` -> 20.0; `.send(5)` -> 15.0; `.close()` raises GeneratorExit at the yield; further `.send()` -> `StopIteration`. Variant `averager2` yields `None`, breaks on a `Sentinel` instance (`STOP`), and `return Result(count, average)`; a delegating `compute()` does `res = yield from averager2(True)` and gets the Result without touching `StopIteration`.

## Key Takeaways
1. Python obtains iterators from iterables; `iter(x)` falls back to `__getitem__`; a proper iterable creates a new independent iterator per `iter()` call.
2. Write `__iter__` as a generator function (or return a genexp); avoid classic Iterator classes.
3. Prefer lazy sources (`finditer`, `islice`, `takewhile`) over eager lists; know the stdlib generators before writing your own.
4. `yield from` delegates to subgenerators, passes values through, and captures the return value; ideal for recursive traversal.
5. A generator "yields", a function "returns"; `return x` in a generator ends with `StopIteration(x)`.
6. Classic coroutines work but are cumbersome and superseded by native coroutines (`async`/`await`); `yield from` is the precursor of `await`.
7. Annotate iterator generators as `Iterator[T]`; reserve `Generator[Y,S,R]` for coroutines.

## Connects To
- **Ch 1**: sequences iterable via the data model; `__getitem__` protocol.
- **Ch 13**: `Iterable` goose typing and `__subclasshook__`.
- **Ch 15**: variance rules of thumb (covariant output, contravariant input).
- **Ch 18**: `@contextmanager` is a different use of `yield` in generators.
- **Ch 19/21**: classic coroutines lead to native coroutines/asyncio.
