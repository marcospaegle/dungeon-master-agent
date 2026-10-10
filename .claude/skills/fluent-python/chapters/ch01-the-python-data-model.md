# Chapter 1: The Python Data Model

## Core Idea
The Python Data Model is the API through which your objects plug into the language's own constructs (len, iteration, operators, with, etc.). You implement special (dunder) methods; the interpreter, not you, calls them. This is the iceberg beneath everything "Pythonic".

## Frameworks Introduced
- **Data Model as a framework**: "a description of Python as a framework" that formalizes interfaces of sequences, functions, iterators, coroutines, classes, context managers.
  - When to use: whenever you want a user-defined class to behave like a built-in (collection, number, context manager, callable).
  - How: (1) pick the language construct to support; (2) implement its special method(s); (3) call via the built-in/operator (`len(x)`, `x[k]`, `a + b`), never `x.__len__()`.
  - Why it works: users don't memorize arbitrary method names, and you inherit the standard library (`random.choice`, `reversed`, `sorted`) for free. Failure mode: calling dunders directly, or inventing `__names__` outside documented use ("subject to breakage without warning").
- **Special-method delegation by composition**: implement `__len__`/`__getitem__` by delegating to an inner `list`.
  - How: wrap `self._cards`; slicing, iteration, `in`, `reversed` all come for free.
- **Collection ABC trio**: `Collection` = `Iterable` (`__iter__`) + `Sized` (`__len__`) + `Container` (`__contains__`); specialized into `Sequence`, `Mapping`, `Set`.
  - How: no inheritance required; implementing the method satisfies the interface.

## Key Concepts
- **Special / dunder / magic method**: method with leading and trailing double underscores, invoked by the interpreter in response to syntax. "Dunder-getitem".
- **Metaobject protocol**: an API for core language constructs; synonym for "object model". Python's is fully documented, so "muggles" can emulate built-in behavior (unlike Go's magic `[]`/`range`).
- **`__repr__` vs `__str__`**: repr is unambiguous, ideally source-like, for debugging/logging; str is end-user display. `object.__str__` falls back to `__repr__`.
- **`!r` conversion**: in f-strings, uses `repr` of the field (`f'Vector({self.x!r}, {self.y!r})'`).
- **Truthiness**: `bool(x)` calls `__bool__`; if absent, `__len__() == 0` is falsy; otherwise truthy.
- **Reversed operators / augmented assignment**: `__radd__` used when left operand can't handle it; `__iadd__` for `+=` (Ch16).
- **Implicit calls**: `for x in y` calls `iter(y)` -> `__iter__` or falls back to `__getitem__`; `in` falls back to sequential scan if no `__contains__`.
- **`PyVarObject.ob_size`**: why `len()` on built-ins is fast; it reads a C field, no method call.
- **Infix operators create new objects**: `+`/`*` must not mutate operands.

## Mental Models
- Think of the interpreter as the caller and of yourself as a plugin author: "you should be implementing special methods more often than invoking them."
- Use the built-in (`len`, `iter`, `str`, `repr`) instead of the dunder: it is faster for built-ins and may add services.
- Think of `len`/`abs` as unary operators, which explains their functional look ("practicality beats purity").
- Only `__init__` is commonly called directly (to invoke the superclass initializer).

## Anti-patterns
- **Calling `obj.__len__()` directly**: bypasses built-in fast path and extra services.
- **Implementing only `__str__`** (toString habit): implement `__repr__` first; if only one, choose `__repr__`.
- **Mutating operands in `__add__`/`__mul__`**: infix operators must return new objects.
- **Unguarded `__bool__` returning non-bool**: must return a real `bool` (`bool(abs(self))`); note `x or y` returns an operand, not a bool.
- **Using `.format()`/`%` by default**: prefer f-strings, except when the template lives elsewhere (constant, config, DB).

## Code Examples
```python
import collections

Card = collections.namedtuple('Card', ['rank', 'suit'])

class FrenchDeck:
    ranks = [str(n) for n in range(2, 11)] + list('JQKA')
    suits = 'spades diamonds clubs hearts'.split()

    def __init__(self):
        self._cards = [Card(rank, suit) for suit in self.suits
                                        for rank in self.ranks]

    def __len__(self):
        return len(self._cards)

    def __getitem__(self, position):
        return self._cards[position]
```
- **What it demonstrates**: two dunders yield `len()`, indexing, slicing (`deck[12::13]` = aces), iteration, `reversed`, `in`, `random.choice`, `sorted(deck, key=...)`. Immutable until `__setitem__` is added (Ch13).

```python
import math

class Vector:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __repr__(self):
        return f'Vector({self.x!r}, {self.y!r})'

    def __abs__(self):
        return math.hypot(self.x, self.y)

    def __bool__(self):
        return bool(abs(self))

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        return Vector(x, y)

    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)
```
- **What it demonstrates**: repr, abs, bool, + and * as new-object operators. Gap: `3 * v` fails until `__rmul__` (Ch16). Faster `__bool__`: `return bool(self.x or self.y)`.

## Reference Tables
Table 1-1: special methods (operators excluded)

| Category | Methods |
|---|---|
| String/bytes repr | `__repr__ __str__ __format__ __bytes__ __fspath__` |
| Conversion to number | `__bool__ __complex__ __int__ __float__ __hash__ __index__` |
| Emulating collections | `__len__ __getitem__ __setitem__ __delitem__ __contains__` |
| Iteration | `__iter__ __aiter__ __next__ __anext__ __reversed__` |
| Callable/coroutine | `__call__ __await__` |
| Context management | `__enter__ __exit__ __aenter__ __aexit__` |
| Creation/destruction | `__new__ __init__ __del__` |
| Attribute management | `__getattr__ __getattribute__ __setattr__ __delattr__ __dir__` |
| Descriptors | `__get__ __set__ __delete__ __set_name__` |
| ABCs | `__instancecheck__ __subclasscheck__` |
| Class metaprogramming | `__prepare__ __init_subclass__ __class_getitem__ __mro_entries__` |

Table 1-2: operators

| Category | Symbols | Methods |
|---|---|---|
| Unary numeric | `- + abs()` | `__neg__ __pos__ __abs__` |
| Rich comparison | `< <= == != > >=` | `__lt__ __le__ __eq__ __ne__ __gt__ __ge__` |
| Arithmetic | `+ - * / // % @ divmod() round() ** pow()` | `__add__ __sub__ __mul__ __truediv__ __floordiv__ __mod__ __matmul__ __divmod__ __round__ __pow__` |
| Reversed arithmetic | swapped operands | `__radd__ __rsub__ ...` |
| Augmented | `+= -= *= /= //= %= @= **=` | `__iadd__ __isub__ ...` |
| Bitwise | `& \| ^ << >> ~` | `__and__ __or__ __xor__ __lshift__ __rshift__ __invert__` |

## Worked Example
FrenchDeck: define `Card` via `namedtuple`, store 52 cards in a list, add `__len__` + `__getitem__`. Then `len(deck)` -> 52, `deck[-1]` -> `Card(rank='A', suit='hearts')`, `choice(deck)` works with no new method, `deck[12::13]` yields the four aces, `Card('Q','hearts') in deck` works via iteration scan. Ranking: `spades_high(card)` = `rank_index * 4 + suit_value`, used as `sorted(deck, key=spades_high)`.

## Key Takeaways
1. Implement special methods so objects work with built-ins; the interpreter is their only frequent caller.
2. Always give classes a `__repr__`; add `__str__` only when end-user display differs.
3. `__getitem__` + `__len__` alone make a full read-only sequence (iteration, slicing, `in`, `reversed`, `sorted`).
4. Operators return new objects and never mutate operands.
5. Truth value: `__bool__`, else `__len__`, else truthy.
6. Collection ABCs are satisfied structurally; no inheritance needed.

## Connects To
- **Ch 2**: sequence types you get by implementing the sequence dunders.
- **Ch 12**: user-defined sequences (Vector take 2).
- **Ch 13**: ABCs, `__setitem__` for shuffling the deck.
- **Ch 16**: `__rmul__`, `__iadd__`, operator overloading rules.
