# Chapter 12: Special Methods for Sequences

## Core Idea
A user-defined immutable flat sequence needs only `__len__` and `__getitem__` (protocol/duck typing), but a well-behaved one also handles slices, safe `repr`, dynamic attributes, aggregate hashing, and formatting. Build it by composition (an internal `array`) and delegation.

## Frameworks Introduced
- **Protocol (informal interface) / duck typing**: "a protocol is an informal interface, defined only in documentation and not in code." The sequence protocol = `__len__` + `__getitem__`; any class providing them with standard semantics is a sequence regardless of base class. Partial implementation is legitimate (iteration needs only `__getitem__`).
  - Dynamic protocol (traditional, informal) vs **static protocol** (`typing.Protocol`, PEP 544; implementations must provide all methods).
  - Data Model advice: emulate a built-in only "to the degree that it makes sense".
- **Slice-aware `__getitem__`**: if `key` is a `slice`, build a new instance of `type(self)` from a slice of the internal sequence; else `operator.index(key)` and return the item.
  - Why: every built-in sequence returns its own type when sliced.
- **`__getattr__` + `__setattr__` pair**: `__getattr__` is only a fallback when normal lookup fails (instance, class, bases). Providing virtual attributes (`v.x`) without blocking assignment creates inconsistency (`v.x = 10` creates a real instance attribute that shadows). So when you implement `__getattr__`, usually implement `__setattr__` too.
- **Aggregate hash via map-reduce**: `functools.reduce(operator.xor, (hash(x) for x in self), 0)`; map = hash each component lazily, reduce = xor.
  - Always supply the initializer (identity of the operation: 0 for `+ | ^`, 1 for `* &`).
- **Efficient `__eq__`**: check lengths first, then `all(a == b for a, b in zip(self, other))`; avoids building two tuples.
- **Extended format mini-language**: new code `'h'` for hyperspherical coordinates `<r, phi1, phi2, ...>`; chosen to avoid built-in format codes.

## Key Concepts
- **`slice(start, stop, step)`**: object passed to `__getitem__` for `a:b:c`; `s[1:4:2, 9]` passes a tuple (commas make a tuple, possibly of slices).
- **`slice.indices(len)`**: returns normalized non-negative `(start, stop, stride)` for a sequence of that length, clipped like built-ins; use when you cannot delegate to an underlying sequence.
- **`operator.index()`**: calls `__index__` (PEP 357); unlike `int()`, `operator.index(3.14)` raises `TypeError`.
- **`reprlib.repr()`**: length-limited safe repr (marks cut with `...`).
- **`__match_args__`**: doubles as the names of virtual attributes (`('x','y','z','t')`).
- **`zip`**: parallel iteration, lazy, stops silently at the shortest; `itertools.zip_longest(fillvalue=...)`; `zip(..., strict=True)` (3.10, PEP 618) raises `ValueError` on length mismatch.
- **`functools.reduce`**: aka fold/accumulate/aggregate/inject; `sum`, `any`, `all` cover the most common uses.
- **`math.hypot(*self)`**: N-dimensional norm since 3.8.

## Mental Models
- "Don't check whether it is-a duck: check whether it quacks-like-a duck" (Martelli).
- Use composition: store components in `array('d', ...)`, delegate `__len__`, `__iter__`, `__getitem__`.
- Sequence constructors take one iterable argument (like built-ins), not `*args`.
- `__repr__` must never raise; its job is debugging. `__format__` targets end users and may show everything.
- Keep `__eq__` and `__hash__` adjacent in source.

## Anti-patterns
- **`Vector(*args)` constructor**: breaks sequence-constructor convention.
- **Delegating slicing to the internal array blindly**: returns `array`, not `Vector`.
- **Overusing `isinstance`**: justified for slice vs index; for the index case use `operator.index` instead of `isinstance(key, int)`.
- **Implementing `__getattr__` without `__setattr__`**: inconsistent state after assignment.
- **Using `__slots__` just to forbid attributes**: use `__setattr__`; `__slots__` is for memory.
- **`__eq__` via `tuple(self) == tuple(other)` on large vectors**: copies everything.
- **`reduce` without initializer**: `TypeError` on empty input.
- **Relying on `zip` with unequal lengths**: silent truncation; check `len` or use `strict=True`.
- **Subclassing `Vector2d` for `Vector`**: incompatible constructors; want standalone sequence example.
- **`reduce(operator.add, ...)` instead of `sum`** (Pythonic Sum soapbox: `sum(sub[1] for sub in my_list)` beats reduce/lambda).

## Code Examples
```python
def __len__(self):
    return len(self._components)

def __getitem__(self, key):
    if isinstance(key, slice):
        cls = type(self)
        return cls(self._components[key])
    index = operator.index(key)
    return self._components[index]
```
- **What it demonstrates**: slice returns same type; ints validated with `__index__`.

```python
__match_args__ = ('x', 'y', 'z', 't')

def __getattr__(self, name):
    cls = type(self)
    try:
        pos = cls.__match_args__.index(name)
    except ValueError:
        pos = -1
    if 0 <= pos < len(self._components):
        return self._components[pos]
    msg = f'{cls.__name__!r} object has no attribute {name!r}'
    raise AttributeError(msg)

def __setattr__(self, name, value):
    cls = type(self)
    if len(name) == 1:
        if name in cls.__match_args__:
            error = 'readonly attribute {attr_name!r}'
        elif name.islower():
            error = "can't set attributes 'a' to 'z' in {cls_name!r}"
        else:
            error = ''
        if error:
            msg = error.format(cls_name=cls.__name__, attr_name=name)
            raise AttributeError(msg)
    super().__setattr__(name, value)
```
- **What it demonstrates**: virtual read-only attributes and the matching setter guard.

```python
def __repr__(self):
    components = reprlib.repr(self._components)
    components = components[components.find('['):-1]
    return f'Vector({components})'

def __eq__(self, other):
    return (len(self) == len(other) and
            all(a == b for a, b in zip(self, other)))

def __hash__(self):
    hashes = (hash(x) for x in self)
    return functools.reduce(operator.xor, hashes, 0)

def angle(self, n):
    r = math.hypot(*self[n:])
    a = math.atan2(r, self[n-1])
    if (n == len(self) - 1) and (self[-1] < 0):
        return math.pi * 2 - a
    else:
        return a

def angles(self):
    return (self.angle(n) for n in range(1, len(self)))

def __format__(self, fmt_spec=''):
    if fmt_spec.endswith('h'):  # hyperspherical coordinates
        fmt_spec = fmt_spec[:-1]
        coords = itertools.chain([abs(self)], self.angles())
        outer_fmt = '<{}>'
    else:
        coords = self
        outer_fmt = '({})'
    components = (format(c, fmt_spec) for c in coords)
    return outer_fmt.format(', '.join(components))
```
- **What it demonstrates**: safe repr, efficient eq, map-reduce hash, spherical format. (Note: book listing needs `import itertools`.)

```python
>>> functools.reduce(operator.xor, range(6))   # 1
>>> list(zip(*[(1, 2, 3), (4, 5, 6)]))          # transpose: [(1, 4), (2, 5), (3, 6)]
```

## Reference Tables
| `s[...]` syntax | `__getitem__` receives |
|---|---|
| `s[1]` | `1` |
| `s[1:4]` | `slice(1, 4, None)` |
| `s[1:4:2]` | `slice(1, 4, 2)` |
| `s[1:4:2, 9]` | `(slice(1, 4, 2), 9)` |
| `s[1:4:2, 7:9]` | `(slice(1, 4, 2), slice(7, 9, None))` |

| Format-code namespace | Letters |
|---|---|
| int | `bcdoxXn` |
| float | `eEfFgGn%` |
| str | `s` |
| Vector2d custom | `p` (polar) |
| Vector custom | `h` (hyperspherical) |

| reduce initializer | operations |
|---|---|
| 0 | `+`, `\|`, `^` |
| 1 | `*`, `&` |

Examples: `slice(None, 10, 2).indices(5)` -> `(0, 5, 2)`; `slice(-3, None, None).indices(5)` -> `(2, 5, 1)`.

## Worked Example
Evolving `Vector` through five takes: (1) iterable constructor, `array` storage, `reprlib` repr, Vector2d-compatible; (2) `__len__` + slice-aware `__getitem__` (`v7[1:4]` -> `Vector([1.0, 2.0, 3.0])`, `v7[1,2]` -> `TypeError`); (3) `__getattr__`/`__setattr__` for `x,y,z,t` after seeing `v.x = 10` silently shadow; (4) xor-reduce hash and `zip`/`all` eq; (5) `__format__` with `h`. Final `format(Vector([-1,-1,-1,-1]), 'h')` -> `'<2.0, 2.0943951023931957, 2.186276035465284, 3.9269908169872414>'`.

## Key Takeaways
1. Implementing `__len__` and `__getitem__` makes a sequence by duck typing; no inheritance needed.
2. Slicing: handle `slice` explicitly and return the same class; use `operator.index` for scalar keys.
3. `__getattr__` is a fallback; pair it with `__setattr__` to prevent shadowing bugs.
4. Hash with lazy map + `reduce(xor, ..., 0)`; compare with length check + `all(zip)`.
5. `repr` must be bounded and never raise (`reprlib`).
6. Custom format codes must avoid built-in codes.
7. Prefer `sum`/`any`/`all` over `reduce` where they fit.

## Connects To
- **Ch 1/11**: `Vector2d`, special methods, `__format__`, hash/eq rules.
- **Ch 2/3**: sequences, slicing, `array`, hashing.
- **Ch 13**: protocols, ABCs, static vs dynamic protocols.
- **Ch 16**: operator overloading for `Vector`, `==` vs tuple issue.
- **Ch 17**: generators used in `angles`/`__format__`.
