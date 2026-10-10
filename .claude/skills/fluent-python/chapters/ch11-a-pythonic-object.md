# Chapter 11: A Pythonic Object

## Core Idea
Via the data model, user-defined types can behave like built-ins without inheritance. Observe how real Python objects behave and implement the same special methods and conventions ("To build Pythonic objects, observe how real Python objects behave"), but only as far as your context (library vs app) requires.

## Frameworks Introduced
- **Object representation methods**: `repr()` = "as the developer wants to see it" (`__repr__`); `str()` = "as the user wants to see it" (`__str__`); `__bytes__` (via `bytes()`); `__format__(format_spec)` (via `format()`, f-strings, `str.format()`).
  - How: `__repr__` should emulate the constructor call (`Vector2d(3.0, 4.0)`); use `type(self).__name__` so subclasses inherit it.
- **Format Specification Mini-Language extension**: each class interprets `format_spec` itself.
  - How: strip your custom suffix, format components with the standard spec. Example: suffix `'p'` -> polar `<r, theta>`; else Cartesian.
  - Rule: avoid codes used by built-ins (int `bcdoxXn`, float `eEfFgGn%`, str `s`); reuse is legal but confusing.
  - Without `__format__`, `object.__format__` returns `str(obj)` for empty spec and raises `TypeError` for a non-empty spec.
- **Hashable-and-immutable recipe**: implement `__hash__` + `__eq__` consistently (equal objects -> equal hashes), hash the tuple of the attributes used in `__eq__`, and make attributes read-only via private attribute + `@property`.
- **Private/protected conventions**: `self.__x` (two leading underscores, at most one trailing) triggers **name mangling** to `_Class__x`: protects against accidental subclass clobbering, "safety, not security". `self._x` is "protected" by convention only.
- **`__slots__`**: class attribute listing instance attribute names; stores them in a hidden array of references instead of a per-instance `__dict__`.
  - When to use: millions of instances. For 10M `Vector2d`: 1.55 GiB with `__dict__` vs 551 MiB with `__slots__`, and faster.
- **Class attribute as instance default / override**: read `self.typecode`; set on the instance to shadow for one object, or subclass and override at class level (idiomatic; Django class-based views).
- **Properties reduce up-front cost**: start with public attributes; convert to properties later without changing the API (unlike Java getters/setters).

## Key Concepts
- **`@classmethod`**: receives the class (`cls`) as first argument; main use is alternative constructors (`frombytes`).
- **`@staticmethod`**: receives no special first argument; just a function in a class body; author finds few good uses.
- **`__match_args__`**: class attribute tuple of attribute names enabling positional class patterns in `match` (3.10).
- **Name mangling**: `__mood` stored as `_Dog__mood` in instance `__dict__`.
- **`__iter__`**: makes an object iterable, which enables unpacking (`x, y = v`) and `*self`.
- **`__abs__`, `__bool__`**: reduce object to number/truth.
- **`__weakref__`**: instance attribute required for weak references; must be added to `__slots__` if needed.
- **Pythonic**: (Faassen) as easy and natural as possible for a Python programmer to pick up; not the most obscure features.

## Mental Models
- Use `frombytes`-style naming borrowed from `array.array`: copy standard-library API names.
- Think of name mangling as the cover on a switch: prevents accidents, not sabotage.
- Use a subclass whose only content is a class attribute override to customize behavior cleanly (`ShortVector2d`).
- An app class should be "as simple as the requirements dictate"; a library class should implement what Pythonistas expect (eq, repr, hash, etc.).
- Conversion hooks for numeric types: `__int__`, `__float__`, `__complex__`.

## Anti-patterns
- **Hardcoding the class name in `__repr__`**: subclasses must override; use `type(self).__name__`.
- **Using `__eq__` as `tuple(self) == tuple(other)`**: `Vector2d(3,4) == [3,4]` is True; may be a bug (see Ch 16).
- **`__hash__` without immutability**: hash must never change over the object's life.
- **Redeclaring nothing in `__slots__` subclasses**: subclasses without `__slots__` regain `__dict__` (`OpenPixel`).
- **Adding `'__dict__'` to `__slots__` casually**: may erase memory savings ("careless optimization is worse than premature optimization").
- **`__slots__` just to block new attributes**: not its purpose.
- **Treating `__x` as real privacy / using double underscore everywhere** (Ian Bicking: "Never, ever use two leading underscores"; prefer single underscore).
- **Writing getters/setters up front** in Python.
- **Implementing every special method in application code**: end users do not care.

## Code Examples
```python
from array import array
import math

class Vector2d:
    __match_args__ = ('x', 'y')
    typecode = 'd'

    def __init__(self, x, y):
        self.__x = float(x)
        self.__y = float(y)

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    def __iter__(self):
        return (i for i in (self.x, self.y))

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({!r}, {!r})'.format(class_name, *self)

    def __str__(self):
        return str(tuple(self))

    def __bytes__(self):
        return (bytes([ord(self.typecode)]) +
                bytes(array(self.typecode, self)))

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __hash__(self):
        return hash((self.x, self.y))

    def __abs__(self):
        return math.hypot(self.x, self.y)

    def __bool__(self):
        return bool(abs(self))

    def angle(self):
        return math.atan2(self.y, self.x)

    def __format__(self, fmt_spec=''):
        if fmt_spec.endswith('p'):
            fmt_spec = fmt_spec[:-1]
            coords = (abs(self), self.angle())
            outer_fmt = '<{}, {}>'
        else:
            coords = self
            outer_fmt = '({}, {})'
        components = (format(c, fmt_spec) for c in coords)
        return outer_fmt.format(*components)

    @classmethod
    def frombytes(cls, octets):
        typecode = chr(octets[0])
        memv = memoryview(octets[1:]).cast(typecode)
        return cls(*memv)
```
- **What it demonstrates**: the full set of representation, conversion, hashing, formatting and alternative-constructor methods.

```python
class Pixel:
    __slots__ = ('x', 'y')      # no __dict__; no other attributes

class ColorPixel(Pixel):
    __slots__ = ('color',)      # must redeclare; trailing comma for 1-tuple
```

```python
match v:
    case Vector2d(0, 0): print(f'{v!r} is null')
    case Vector2d(_, 0): print(f'{v!r} is horizontal')
    case Vector2d(x, y) if x==y: print(f'{v!r} is diagonal')
```
- **What it demonstrates**: positional patterns enabled by `__match_args__`.

## Reference Tables
| Method | Called by |
|---|---|
| `__repr__` | `repr()`, console, debugger |
| `__str__` | `str()`, `print()` |
| `__bytes__` | `bytes()` |
| `__format__` | `format()`, f-string `{x:spec}`, `str.format()` |
| `__abs__`/`__bool__`/`__hash__` | `abs()`/`bool()`/`hash()` |
| `__int__`/`__float__`/`__complex__` | `int()`/`float()`/`complex()` |

| `__slots__` caveat | Fix |
|---|---|
| subclass regains `__dict__` | redeclare `__slots__` in each subclass (`()` if no new attrs) |
| only slot-named attributes allowed | add `'__dict__'` (may defeat savings) |
| no `@cached_property` | add `'__dict__'` |
| no weak references | add `'__weakref__'` |

| classmethod vs staticmethod | first arg |
|---|---|
| `Demo.klassmeth('spam')` | `(Demo, 'spam')` |
| `Demo.statmeth('spam')` | `('spam',)` |

## Worked Example
Make `Vector2d` hashable: `hash(v)` raises `TypeError: unhashable type` because `__eq__` defined without `__hash__`. Steps: (1) store `self.__x`/`self.__y`, expose `@property x`/`y` (assigning `v1.x = 7` now raises `AttributeError`); (2) `__hash__` returns `hash((self.x, self.y))`; (3) now `{v1, v2}` works. `v1.__dict__` shows `{'_Vector2d__y': 4.0, '_Vector2d__x': 3.0}`.

## Key Takeaways
1. Implement `__repr__`, `__str__`, `__bytes__`, `__format__` for different audiences; keep them returning `str` (except `__bytes__`).
2. Use `@classmethod` for alternative constructors; `@staticmethod` is rarely needed.
3. Extend `__format__` with a unique suffix code.
4. Hashability requires consistent `__eq__`/`__hash__` and immutable state.
5. Name mangling is safety, not security; prefer `_x` convention.
6. `__slots__` only pays off with millions of instances and has several caveats.
7. Class attributes serve as overridable defaults; subclass to customize.

## Connects To
- **Ch 1**: data model; first `Vector`.
- **Ch 5**: dataclasses autogenerate these methods; **Ch 12**: N-dim `Vector`.
- **Ch 16**: `__eq__` semantics and operator overloading.
- **Ch 22**: properties; **Ch 23**: descriptors; **Ch 17**: generators behind `__iter__`.
