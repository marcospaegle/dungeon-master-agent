# Chapter 16: Operator Overloading

## Core Idea
Python allows infix and unary operator overloading with guardrails. Operator methods return new objects, return `NotImplemented` (not raise) for unsupported operands, and rely on forward/reverse dispatch; comparisons and augmented assignment have special rules.

## Frameworks Introduced
- **Infix dispatch algorithm** for `a + b` (generalizes to all arithmetic operators):
  1. If `a` has `__add__`, call `a.__add__(b)`; return unless `NotImplemented`.
  2. Else (or if NotImplemented) if `b` has `__radd__`, call `b.__radd__(a)`; return unless `NotImplemented`.
  3. Else raise `TypeError` ("unsupported operand type(s)...").
  - How to write: do not type-check with isinstance unless needed; `try: ... except TypeError: return NotImplemented`. Exceptions in an operator method abort dispatch and block the reverse method.
- **Rich comparison dispatch**: same method used forward and reverse (`__eq__`/`__eq__`; `__gt__` reversed to `__lt__`). Fallbacks: `==` compares `id()`, `!=` is `not (a == b)`, ordering raises `TypeError`.
- **Return-new-object rule**: unary and infix operators never mutate operands; only augmented assignment may mutate `self`, and then must `return self`.
- **Choosing the operand-check style**: duck typing (try and catch -> NotImplemented) is flexible; goose typing (`isinstance` against ABC) is more predictable. Libraries: duck typing; operator methods often benefit from goose typing.

## Key Concepts
- **Infix operator**: sits between operands (`a + b`); **unary**: `-`, `+`, `~` (`__neg__`, `__pos__`, `__invert__`), plus `abs()` -> `__abs__`.
- **Forward / reverse (reflected) methods**: `__add__` / `__radd__`; author prefers "forward" and "reversed".
- **`NotImplemented` vs `NotImplementedError`**: singleton value an operator method returns to decline vs exception for abstract stubs.
- **In-place methods** (`__iadd__`, etc.): called for `a += b`; if absent, `a += b` is `a = a + b`.
- **Language limits**: cannot change operators of built-in types, cannot create new operators, cannot overload `is`, `and`, `or`, `not` (bitwise `& | ~` OK).
- **`@` operator** (PEP 465, Python 3.5): `__matmul__`, `__rmatmul__`, `__imatmul__`; unused in stdlib.
- **`zip(strict=True)`**: keyword-only,  (3.10) raises `ValueError` on unequal lengths (fail fast).

## Mental Models
- Think of `NotImplemented` as "ask the other operand"; raising TypeError yourself forecloses that.
- If a forward method only handles `self`'s own type, writing the reverse method is pointless (reverse only runs for different types).
- `+` strict, `+=` liberal: `list + x` needs a list; `list += x` accepts any iterable (like `extend`). Mutable `__iadd__` can be liberal since the result type is known.
- For commutative operators `__radd__ = __add__` (or `return self + other`); not valid for non-commutative ops like sequence concatenation.

## Anti-patterns
- **Raising TypeError (or propagating it) from `__add__` for bad operands**: blocks the reverse method; also gives misleading messages (`float` and `str` rather than `Vector` and `str`).
- **In-place special methods on immutable types** (Vector): wrong; augmented ops should just fall back to `a = a + b`.
- **Forgetting `return self` in `__iadd__`**: rebinding `globe += x` would set it to None.
- **Overly liberal `__eq__`**: `Vector([1,2,3]) == (1,2,3)` True; Zen: "In the face of ambiguity, refuse the temptation to guess." `[1,2] == (1,2)` is False in Python.
- **Mutating self in unary/infix operators.**
- **Overloading for non-intuitive meaning** (`+` for list insertion): Gosling's complaint; operator overloading shines for numeric notation.

## Code Examples
```python
# unary
def __abs__(self):
    return math.hypot(*self)
def __neg__(self):
    return Vector(-x for x in self)
def __pos__(self):
    return Vector(self)

# +
def __add__(self, other):
    try:
        pairs = itertools.zip_longest(self, other, fillvalue=0.0)
        return Vector(a + b for a, b in pairs)
    except TypeError:
        return NotImplemented

def __radd__(self, other):
    return self + other

# * (duck typing: float() conversion instead of numbers.Real check)
def __mul__(self, scalar):
    try:
        factor = float(scalar)
    except TypeError:
        return NotImplemented
    return Vector(n * factor for n in self)

def __rmul__(self, scalar):
    return self * scalar

# @ (goose typing)
def __matmul__(self, other):
    if (isinstance(other, abc.Sized) and
        isinstance(other, abc.Iterable)):
        if len(self) == len(other):
            return sum(a * b for a, b in zip(self, other))
        else:
            raise ValueError('@ requires vectors of equal length.')
    else:
        return NotImplemented

def __rmatmul__(self, other):
    return self @ other

# ==
def __eq__(self, other):
    if isinstance(other, Vector):
        return (len(self) == len(other) and
                all(a == b for a, b in zip(self, other)))
    else:
        return NotImplemented
```
- **What it demonstrates**: the canonical operator-method patterns; `zip_longest` pads shorter vector with 0.0; `__ne__` inherited from object.

```python
class AddableBingoCage(BingoCage):
    def __add__(self, other):
        if isinstance(other, Tombola):
            return AddableBingoCage(self.inspect() + other.inspect())
        else:
            return NotImplemented

    def __iadd__(self, other):
        if isinstance(other, Tombola):
            other_iterable = other.inspect()
        else:
            try:
                other_iterable = iter(other)
            except TypeError:
                msg = ('right operand in += must be '
                       "'Tombola' or an iterable")
                raise TypeError(msg)
        self.load(other_iterable)
        return self
```
- **What it demonstrates**: `__add__` returns a new instance, `__iadd__` mutates and returns `self`; no `__radd__` by design.

## Reference Tables
| Operator | Forward | Reverse | In-place |
|---|---|---|---|
| + | `__add__` | `__radd__` | `__iadd__` |
| - | `__sub__` | `__rsub__` | `__isub__` |
| * | `__mul__` | `__rmul__` | `__imul__` |
| / | `__truediv__` | `__rtruediv__` | `__itruediv__` |
| // | `__floordiv__` | `__rfloordiv__` | `__ifloordiv__` |
| % | `__mod__` | `__rmod__` | `__imod__` |
| divmod() | `__divmod__` | `__rdivmod__` | `__idivmod__` |
| **, pow() | `__pow__` | `__rpow__` | `__ipow__` |
| @ | `__matmul__` | `__rmatmul__` | `__imatmul__` |
| & | `__and__` | `__rand__` | `__iand__` |
| \| | `__or__` | `__ror__` | `__ior__` |
| ^ | `__xor__` | `__rxor__` | `__ixor__` |
| << | `__lshift__` | `__rlshift__` | `__ilshift__` |
| >> | `__rshift__` | `__rrshift__` | `__irshift__` |

| Comparison | Forward | Reverse | Fallback |
|---|---|---|---|
| a == b | `a.__eq__(b)` | `b.__eq__(a)` | `id(a) == id(b)` |
| a != b | `a.__ne__(b)` | `b.__ne__(a)` | `not (a == b)` |
| a > b | `a.__gt__(b)` | `b.__lt__(a)` | TypeError |
| a < b | `a.__lt__(b)` | `b.__gt__(a)` | TypeError |
| a >= b | `a.__ge__(b)` | `b.__le__(a)` | TypeError |
| a <= b | `a.__le__(b)` | `b.__ge__(a)` | TypeError |

Unary: `-` `__neg__`; `+` `__pos__`; `~` `__invert__`; `abs()` `__abs__`. Unary + on an immutable returns self (else a copy); `x != +x` for Decimal with changed context precision and for Counter (drops zero/negative tallies).

## Worked Example
`vc == v2d` with `Vector.__eq__` returning NotImplemented for non-Vectors: (1) `Vector.__eq__(vc, v2d)` -> NotImplemented; (2) Python tries `Vector2d.__eq__(v2d, vc)`, which converts both to tuples -> True. For `va == (1,2,3)`: `Vector.__eq__` -> NotImplemented; `tuple.__eq__(t3, va)` -> NotImplemented; Python falls back to comparing ids -> False. Chosen deliberately so a Vector no longer equals a tuple.

## Key Takeaways
1. Operator methods return new objects and never mutate operands (except in-place methods, which must return `self`).
2. Return `NotImplemented` (not raise) to decline; this activates reverse dispatch and clean TypeError messages.
3. Commutative reverse methods can just delegate to the forward method.
4. `==` and `!=` never error; `__ne__` is derived from `__eq__`; ordering raises TypeError on NotImplemented.
5. Without `__iadd__` etc., `+=` is `a = a + b`; never define in-place methods for immutables.
6. `+` is typically stricter than `+=` about operand types.
7. `functools.total_ordering` generates remaining comparisons.

## Connects To
- **Ch 1**: Vector `__add__`/`__mul__` first sketch; special methods.
- **Ch 11/12**: `Vector2d`, multi-dimensional `Vector`.
- **Ch 13**: goose typing, `Sized`/`Iterable` `__subclasshook__`, BingoCage/Tombola.
- **Ch 17**: generators and lazy evaluation (genexp traceback shows deferred evaluation).
