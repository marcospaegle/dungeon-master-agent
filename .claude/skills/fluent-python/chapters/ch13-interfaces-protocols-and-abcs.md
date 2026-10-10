# Chapter 13: Interfaces, Protocols, and ABCs

## Core Idea
OOP is about interfaces. Python gives four complementary ways to program with them (duck, goose, static, static duck typing); rejecting any one makes you work harder than needed. Pick by whether you want runtime vs static checking, and structural vs nominal matching.

## Frameworks Introduced
- **The Typing Map**: two axes. Top half = runtime checks (interpreter only); bottom = needs external checker (Mypy, PyCharm). Left = structural (what methods the object has); right = nominal (the name of its class/superclasses).
  - Duck typing = runtime + structural. Goose typing = runtime + nominal (ABCs). Static typing = static + nominal. Static duck typing = static + structural (`typing.Protocol`).
  - When to use: choosing how to constrain an argument. Static typing with only concrete types is the "poor" version; prefer interfaces (protocols/ABCs).
- **Goose typing** (Alex Martelli): `isinstance(obj, cls)` is fine as long as `cls` is an ABC (metaclass `abc.ABCMeta`).
  - How: (1) subclass an ABC to declare you implement a known interface, or `register` a class you don't own as a virtual subclass; (2) type-check with ABCs, never concrete classes, in `isinstance`/`issubclass`.
  - Why: `draw()` on Artist/Gunslinger/Lottery shows name-only duck typing gives accidental similarity (phenetics); inheritance/registration is an explicit semantic assertion (cladistics).
- **Fail fast / defensive duck typing**: reject bad input at the top of the function, not by `isinstance`, but by using it: `self._balls = list(iterable)` (any iterable OK, TypeError immediately, copies arg). Use `len(x)` to reject iterators, `iter(x)` if any iterable is fine, `hash(obj)` to test hashability, EAFP try/except to branch on shape.
- **Protocol design best practices**: narrow protocols (often one method, rarely >2), role interfaces (Fowler), define the protocol next to the client code that uses it (Interface Segregation Principle). Naming (typeshed): plain names for clear concepts (`Iterator`); `SupportsX` for callable-method protocols; `HasX` for attribute protocols; Go style `-er` (`Reader`) for single verbs. Extend by deriving a new protocol, not by growing the old one.

## Key Concepts
- **Dynamic protocol**: informal, implicit interface defined by convention/docs; partial implementation is OK (e.g. only `__getitem__`). Not statically checkable.
- **Static protocol**: `typing.Protocol` subclass (PEP 544, 3.8); must provide every declared method; verified by type checkers. Neither kind requires inheriting by name.
- **ABC**: class with `metaclass=ABCMeta` (subclass `abc.ABC`); `@abc.abstractmethod` methods block instantiation (`TypeError: Can't instantiate abstract class ...`), checked at instantiation, not import.
- **Virtual subclass**: `SomeABC.register(Cls)`; `issubclass`/`isinstance` say True, but no inheritance, not in `__mro__`, never validated, invisible to static checkers (Mypy #2922).
- **`__subclasshook__`**: classmethod letting an ABC recognize classes structurally (e.g. `Sized` checks `__len__` in the `__mro__` dicts; returns True or NotImplemented).
- **Mixin methods**: concrete methods in collections.abc ABCs, written only in terms of the ABC's public interface.
- **`@runtime_checkable`**: makes a Protocol work with `isinstance`; relies on `__subclasshook__`; checks only method presence, not signatures/annotations. Not inherited by derived protocols; reapply it.
- **Monkey patching**: changing a class/module at runtime without touching source; Python can't patch built-in types (a feature).
- **Nominal vs structural typing**: link by declared name vs by public interface.

## Mental Models
- Think of a protocol as an "informal interface" (Smalltalk sense); `__getitem__` is the key of the sequence protocol.
- Use ABCs for extension points in frameworks and for API contracts ("Dude, you have to implement this if you want to call me"); use duck typing in application code.
- Use register to retrofit an interface onto someone else's class; use subclassing when you also want inherited mixin methods.
- Python "digs" sequences: if `__iter__` or `__contains__` is missing, it falls back to `__getitem__` with ints from 0.

## Anti-patterns
- **`type(foo) is bar` / isinstance against concrete classes**: blocks polymorphism and inheritance.
- **if/elif/elif isinstance chains**: code smell; use polymorphism. isinstance vs ABC is OK only to enforce an API contract.
- **Defining your own ABCs/metaclasses in app code**: for framework authors only (Martelli: <1% of advanced users). Use existing ABCs correctly for "99.9% of the benefits".
- **Writing `__subclasshook__` in your own ABCs**: only safe for single special-method ABCs like `Sized`. Mappings have `__len__/__getitem__/__iter__` but are not Sequences, so `Sequence` has no hook.
- **Trusting `isinstance(obj, Hashable)`/`Iterable`**: tuple with unhashable items passes Hashable; `__getitem__`-only classes fail Iterable but iterate. Use `hash(obj)` / `iter(obj)`.
- **Runtime-checking numeric protocols with complex**: Python 3.9 `complex.__float__` exists only to raise; `isinstance(c, SupportsFloat)` is True misleadingly.
- **Using `numbers` ABCs with static checkers**: `numbers.Number` has no methods; Mypy rejects arithmetic on it. Use `SupportsFloat`, `SupportsComplex` etc. for static typing; numbers ABCs only for runtime.
- **Placing a decorator between `@abstractmethod` and `def`**: `@abstractmethod` must be innermost. `@abstractclassmethod/@abstractproperty` are deprecated since 3.3 (stack decorators instead).

## Code Examples
```python
import abc

class Tombola(abc.ABC):
    @abc.abstractmethod
    def load(self, iterable):
        """Add items from an iterable."""

    @abc.abstractmethod
    def pick(self):
        """Remove item at random, returning it.
        This method should raise `LookupError` when the instance is empty.
        """

    def loaded(self):
        return bool(self.inspect())

    def inspect(self):
        items = []
        while True:
            try:
                items.append(self.pick())
            except LookupError:
                break
        self.load(items)
        return tuple(items)

@Tombola.register          # virtual subclass, no inheritance
class TomboList(list):
    def pick(self):
        if self:
            position = randrange(len(self))
            return self.pop(position)
        else:
            raise LookupError('pop from empty TomboList')
    load = list.extend
    def loaded(self):
        return bool(self)
    def inspect(self):
        return tuple(self)
```
- **What it demonstrates**: an ABC with 2 abstract + 2 concrete methods (concrete ones only use the interface); subclasses may override for speed; registered classes pass `isinstance` but `Tombola` is absent from `TomboList.__mro__`.

```python
from typing import TypeVar, Protocol

T = TypeVar('T')

class Repeatable(Protocol):
    def __mul__(self: T, repeat_count: int) -> T: ...

RT = TypeVar('RT', bound=Repeatable)

def double(x: RT) -> RT:
    return x * 2
```
- **What it demonstrates**: static duck typing; `double` accepts any type that supports `* int`, result type = arg type.

```python
@runtime_checkable
class RandomPicker(Protocol):
    def pick(self) -> Any: ...

@runtime_checkable
class LoadableRandomPicker(RandomPicker, Protocol):   # must name Protocol again
    def load(self, Iterable) -> None: ...
```
- **What it demonstrates**: single-method protocol; extension requires re-listing `Protocol` and re-applying `@runtime_checkable`.

```python
def set_card(deck, position, card):
    deck._cards[position] = card
FrenchDeck.__setitem__ = set_card     # now random.shuffle(deck) works
```
- **What it demonstrates**: monkey-patching a missing method of the mutable-sequence protocol.

## Reference Tables
| Approach | When checked | Matches by | Mechanism |
|---|---|---|---|
| Duck typing | runtime | structure | just call the methods; EAFP |
| Goose typing | runtime | name (declared/registered; some structural via hook) | ABCs + isinstance |
| Static typing | static | name | annotations, concrete or ABC types |
| Static duck typing | static (+ optional runtime) | structure | `typing.Protocol` |

| Dynamic protocol | Static protocol |
|---|---|
| Partial implementation is fine | Must provide all declared methods |
| Cannot be verified by checkers | Verified by checkers |
| Neither needs inheritance by name | |

collections.abc clusters: `Iterable/Container/Sized` (-> `__iter__`, `__contains__`, `__len__`); `Collection` (3.6, no methods); `Sequence/Mapping/Set` (+ mutable versions); `MappingView` (Items/Keys/ValuesView); `Iterator` (subclasses Iterable); `Callable`, `Hashable` (prefer `callable(obj)`).
FrenchDeck2(MutableSequence) must implement `__getitem__ __setitem__ __delitem__ __len__ insert`; inherits from Sequence: `__contains__ __iter__ __reversed__ index count`; from MutableSequence: `append reverse extend pop remove __iadd__`.

## Worked Example
Tombola: ABC defines `load`/`pick` abstract, `loaded`/`inspect` concrete. `BingoCage(Tombola)` (shuffle + pop, `SystemRandom`) inherits the slow concrete methods; `LottoBlower(Tombola)` overrides `loaded`/`inspect` and translates `ValueError` from `randrange` into `LookupError`; `TomboList(list)` is registered. A `Fake(Tombola)` missing `load` raises TypeError on instantiation. `LookupError` is chosen because `IndexError` and `KeyError` subclass it.

## Key Takeaways
1. Use all four typing approaches; choose by structural/nominal and runtime/static needs.
2. Dynamic protocols tolerate partial implementation; static protocols don't. Neither needs declared inheritance.
3. Goose typing: subclass or register against ABCs, and isinstance only against ABCs.
4. ABC concrete methods may only rely on the ABC's own interface; subclasses override for performance.
5. Prefer narrow, client-side, `SupportsX`-named protocols; extend by deriving.
6. Runtime protocol checks look only at method names; prefer EAFP (`complex(o)`) when you just need to use the object.
7. Mixing numbers ABCs (runtime) and numeric protocols (static) is an unresolved wart.

## Connects To
- **Ch 1**: FrenchDeck and the sequence protocol.
- **Ch 8**: first look at static protocols and consistent-with.
- **Ch 14**: ABC multiple inheritance, MRO, mixins.
- **Ch 15**: generic protocols (`RandomPicker[T_co]`).
- **Ch 16**: goose typing in operator methods (`abc.Sized`+`abc.Iterable`).
- **Ch 17**: `iter()` and `__getitem__` fallback.
