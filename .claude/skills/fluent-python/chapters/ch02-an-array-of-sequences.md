# Chapter 2: An Array of Sequences

## Core Idea
Python inherits from ABC a uniform sequence interface (iteration, slicing, sorting, concatenation). Choosing the right sequence (container vs flat, mutable vs immutable, list vs tuple vs array vs deque) and mastering comprehensions, unpacking, pattern matching and slicing is the foundation of idiomatic code.

## Frameworks Introduced
- **Two axes of sequence classification**: container vs flat; mutable vs immutable.
  - When to use: to extrapolate what you know about one sequence type to others.
  - How: *Container sequences* (`list`, `tuple`, `collections.deque`) hold references to objects of any type, including nested. *Flat sequences* (`str`, `bytes`, `array.array`) store raw values in their own memory. Mutable: `list`, `bytearray`, `array.array`, `deque`. Immutable: `tuple`, `str`, `bytes`.
  - Why it works: flat sequences are compact (one object holding C values) vs a tuple of floats (tuple + each float object with `ob_refcnt`, `ob_type`, `ob_fval`). Failure mode: container sequences surprise you with mutable items.
- **Tuples have a double life**: records with no field names (position = meaning) vs immutable lists (length fixed, clarity + performance).
  - How: as a record, extract fields via unpacking, never sort it; as an immutable list, check `hash(t)` to assert fixed value.
- **Destructuring with match/case** (3.10): sequence pattern matches if subject is a sequence (not `str`/`bytes`/`bytearray`), same number of items, and each item matches (nested too).
  - How: `case [name, _, _, (lat, lon)] if lon <= 0:` pattern + optional guard; `as` binds a subpart; `str(name)` is a runtime type check; `*_` / `*rest` captures the remainder (once per sequence); `_` is never bound and may repeat; always add `case _:` catch-all.
  - Why: declarative, "shape of the code follows the shape of the data". Failure mode: no catch-all means a silent no-op.
- **Listcomp vs genexp rule**: listcomp builds lists; genexp (parens) feeds any other constructor/loop lazily.
- **Naming slices**: assign `slice(a, b, c)` objects to constants like spreadsheet named ranges.

## Key Concepts
- **listcomp / genexp**: bracket form builds a list; paren form yields items one by one via iterator protocol (saves memory). Single-argument call needs no extra parens.
- **Comprehension scope**: for-variables are local to the comprehension; walrus `:=` targets leak to the enclosing function.
- **Cartesian product**: multiple `for` clauses nest in written order.
- **Iterable unpacking**: parallel assignment, swap `b, a = a, b`, `*rest` (any position, once), `f(*args)`, `[*a, 4]`, `{*a, *b}`, nested `(a, b, (c, d))`.
- **Slice object**: `s[a:b:c]` -> `__getitem__(slice(a, b, c))`; `a[i, j]` -> `__getitem__((i, j))`; `...` is the single `Ellipsis` instance.
- **Half-open ranges**: stop excluded; `s[:x] + s[x:]` splits cleanly, `len == stop - start` (Dijkstra).
- **In-place API convention**: methods that mutate return `None` (`list.sort`, `random.shuffle`), so no cascading.
- **Stable sort / Timsort**: ties keep original order; `key=` is called once per item.
- **memoryview**: shared-memory sequence; `.cast()` reinterprets bytes without copying.
- **deque**: thread-safe double-ended queue, optionally bounded by `maxlen`.

## Mental Models
- Use a listcomp when the goal is "build a new list"; a `for` loop when doing anything else. If a comprehension spans more than two lines, break it up.
- Use a genexp whenever the result feeds `tuple()`, `array()`, `sum()`, or a `for`.
- Use `array.array` for millions of numbers; `deque` for FIFO or "last N seen"; `set` for frequent `in` checks; NumPy for real numeric work.
- Think of `+=` as "maybe in place": `__iadd__` if present, else `a = a + b`.
- Use `key=` instead of comparison functions (one-arg, called once per item, comparison in C).

## Anti-patterns
- **`[[]] * 3` / `[['_'] * 3] * 3`**: three references to the same inner list. Use `[['_'] * 3 for _ in range(3)]`.
- **Listcomp for side effects**: if you don't use the produced list, don't use the syntax.
- **Mutable items inside tuples**: the tuple is only as immutable as its contents; unhashable, can't be dict key.
- **`t[2] += [50, 60]` on a tuple holding a list**: raises `TypeError` yet the list is mutated (augmented assignment is not atomic). Use `t[2].extend(...)`.
- **Repeated `+=` on immutable sequences**: copies each time (exception: `str`, optimized in CPython).
- **`map/filter` + lambda instead of a listcomp**: no speed advantage over listcomp, worse readability.
- **Matching `str` as a sequence in match/case**: str/bytes/bytearray are atomic; wrap with `tuple(s)` if intended.
- **`l[2:5] = 100`**: slice assignment needs an iterable (`[100]`).

## Code Examples
```python
# Cartesian product, order follows nested-for order
>>> tshirts = [(color, size) for color in colors for size in sizes]
# lazy variant, never builds the list
>>> for tshirt in (f'{c} {s}' for c in colors for s in sizes):
...     print(tshirt)
```
- **What it demonstrates**: multiple for clauses; genexp avoids a million-item intermediate list.

```python
def handle_command(self, message):
    match message:
        case ['BEEPER', frequency, times]:
            self.beep(times, frequency)
        case ['NECK', angle]:
            self.rotate_neck(angle)
        case ['LED', ident, intensity]:
            self.leds[ident].set_brightness(ident, intensity)
        case ['LED', ident, red, green, blue]:
            self.leds[ident].set_color(ident, red, green, blue)
        case _:
            raise InvalidCommand(message)
```
- **What it demonstrates**: sequence patterns dispatch on length and literal head; `_` catch-all.

```python
case ['lambda', [*parms], *body] if body:
    return Procedure(parms, body, env)
case ['define', Symbol() as name, value_exp]:
    env[name] = evaluate(value_exp, env)
case ['define', [Symbol() as name, *parms], *body] if body:
    env[name] = Procedure(parms, body, env)
```
- **What it demonstrates**: nested patterns, class pattern `Symbol() as name`, guards; adds validation the if/elif version lacked.

```python
>>> SKU = slice(0, 6)
>>> DESCRIPTION = slice(6, 40)
>>> for item in line_items:
...     print(item[UNIT_PRICE], item[DESCRIPTION])
```
- **What it demonstrates**: named slices for flat-file parsing.

```python
>>> dq = deque(range(10), maxlen=10)
>>> dq.rotate(3)         # n>0: right items go to the left
>>> dq.appendleft(-1)    # full deque drops from opposite end
>>> dq.extendleft([10, 20, 30, 40])  # items end up reversed
```

```python
>>> numbers = array.array('h', [-2, -1, 0, 1, 2])
>>> memv_oct = memoryview(numbers).cast('B')
>>> memv_oct[5] = 4      # numbers -> array('h', [-2, -1, 1024, 1, 2])
```
- **What it demonstrates**: memoryview shares memory; poking a byte edits a 16-bit item.

## Reference Tables
| Need | Use |
|---|---|
| Mutable, mixed, general | `list` |
| Fixed record / immutable list | `tuple` |
| Millions of numbers | `array.array` (typecode `'d'`, `'h'`, `'B'`...; `.tofile/.fromfile` ~60x faster than text) |
| Slice arrays w/o copying | `memoryview` |
| Heavy numerics | NumPy (vectorized, memory-mapped `.npy`) |
| FIFO / bounded recent items | `collections.deque(maxlen=n)` |
| Thread comms (blocks when full) | `queue.Queue/LifoQueue/PriorityQueue/SimpleQueue` |
| Process comms | `multiprocessing.Queue/JoinableQueue` |
| Async tasks | `asyncio.Queue` family |
| Priority queue on a list | `heapq.heappush/heappop` |

Tuple vs list: tuple lacks `append`, `insert`, `remove`, `pop`, `sort`, `reverse`, `extend`, `clear`, `__iadd__`, `__setitem__`, `__delitem__`, `__reversed__` (reversed() still works). Tuple wins: constant built in one bytecode op, `tuple(t)` returns same object, exact allocation, references stored inline (cache friendly).

Sorting: `list.sort()` in place returns `None`; `sorted()` accepts any iterable and returns a new list; both take keyword-only `reverse` and `key`. `array` has no `.sort`: `a = array.array(a.typecode, sorted(a))`.

## Worked Example
Rewriting Norvig's `lis.py` `evaluate`: each `elif exp[0] == 'if': (_, test, consequence, alternative) = exp` becomes `case ['if', test, consequence, alternative]:`. Table: `(quote exp)` -> `['quote', exp]`; `(lambda (parms...) body...)` -> `['lambda', [*parms], *body] if body`; `(define name exp)` -> `['define', Symbol() as name, exp]`. The nested `[*parms]` rejects `['lambda', 'x', ...]` (invalid Scheme); case order between the two `define` forms doesn't matter because no subject matches both; `case _: raise SyntaxError(lispstr(exp))` prevents silent failures.

## Key Takeaways
1. Classify sequences as container/flat and mutable/immutable before choosing.
2. Prefer comprehensions/genexps for building; keep them short.
3. Tuples are records first; unpack instead of indexing; `hash(t)` tests true immutability.
4. Slicing is more than extraction: stride, named slice objects, `Ellipsis`, assignment and `del`.
5. `*` on sequences copies references, so never nest mutable items with `*`; `+=` may or may not be in place.
6. Reach for `array`, `memoryview`, NumPy, `deque` when a list is the wrong tool.
7. Use pattern matching to destructure; always include a catch-all.

## Connects To
- **Ch 1**: the dunders behind sequences.
- **Ch 3**: dict/set (hash-based, not sequences); `{**a, **b}` and PEP 448.
- **Ch 4**: `str`/`bytes`/`bytearray` details; memoryview with bytes.
- **Ch 6**: references, aliasing, the `[[]]*3` bug explained.
- **Ch 12**: implementing slicing/sequence protocol in your own class.
- **Ch 17**: generators behind genexps.
