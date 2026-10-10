# Chapter 14: Inheritance: For Better or for Worse

## Core Idea
Inheritance couples classes tightly and there is no general theory guiding it (Alan Kay), so use super() consistently, don't subclass built-ins, understand the MRO for cooperative multiple inheritance, and follow rules of thumb that favor composition, ABCs, and explicit mixins.

## Frameworks Introduced
- **Cooperative multiple inheritance**: methods that call `super().m()` are "cooperative"; the MRO decides activation order, `super()` decides whether each class actually runs.
  - When to use: mixins and diamond hierarchies.
  - How: (1) every method `m` of a non-root class calls `super().m()`; (2) cooperating methods need compatible signatures; (3) list mixins before the classes they wrap in the bases tuple.
  - Failure mode: one non-cooperative method (e.g. `B.pong` in the diamond) "drops the ball" and silently ends the chain.
- **Seven recommendations to cope with inheritance**:
  1. Favor object composition over class inheritance (a Widget shouldn't "be" a geometry manager; hold and delegate).
  2. Understand why inheritance is used: interface inheritance (subtype, "is-a", use ABCs) vs implementation inheritance (reuse; mixins; often replaceable by composition).
  3. Make interfaces explicit with ABCs (or `typing.Protocol`); ABCs subclass only `abc.ABC`/other ABCs.
  4. Use explicit mixins for code reuse: no "is-a", never instantiated, one specific behavior, few closely related methods, no instance state, `Mixin` suffix.
  5. Provide aggregate classes to users (class built only from bases, e.g. Django `ListView`, `tkinter.Widget`).
  6. Subclass only classes designed for subclassing (docs say which methods to override; `@final` from PEP 591 enforces).
  7. Avoid subclassing from concrete classes ("all non-leaf classes should be abstract", Meyers).
- **Think about the classes you really need**: application code mostly writes leaf classes. Multilevel hierarchies in app code mean: reinventing the wheel, bad framework, overengineering (KISS), or boredom.

## Key Concepts
- **`super()`**: returns a dynamic proxy that finds the method in superclasses of `type` (default: class owning the method) and binds to `object_or_type` (default `self`). 2-arg form only for skipping MRO parts/debugging.
- **MRO (`__mro__`)**: tuple of classes in method search order, computed by C3 (accounts for the order of bases in the class statement); not breadth-first in general.
- **Diamond problem**: naming conflicts when two superclasses define the same method; resolved by MRO.
- **Mixin class**: designed to be subclassed together with at least one other class; adds/customizes behavior of siblings; convention only.
- **Mixin method**: concrete method in a collections.abc ABC (ABCs are both interface and mixin).
- **Aggregate class** (Booch): built primarily by inheriting mixins, adds no structure/behavior of its own.
- **Late binding**: method lookup always starts at the receiver's class; CPython built-ins (C code) violate this.
- **`UserDict/UserList/UserString`**: pure-Python wrappers designed for subclassing; slower than built-ins.
- **Traits**: explicit mixin construct in Scala, Rust, PHP, Squeak/Pharo; Ruby modules are "pure" mixins with no inheritance.

## Mental Models
- Use `UserDict` (or `MutableMapping`) when you need a custom mapping; dict subclassing needed 33 lines vs 16 for `StrKeyDict`.
- Think of the MRO as a linearized list; `super()` means "next in the MRO of the instance's class", not "my parent".
- Use composition+delegation to replace mixins for sharing behavior, but it cannot replace interface inheritance for a type hierarchy.
- "More often than not, a function is all you need" (Schlawack).

## Anti-patterns
- **Calling `OrderedDict.__setitem__(self, ...)` instead of `super()`**: hardcodes the base class and breaks multiple inheritance logic.
- **Omitting `super().__init__(...)`**: unlike Java, Python never calls the superclass constructor automatically.
- **Subclassing `dict`/`list`/`str` and overriding methods**: `dict.__init__`, `dict.update`, `dict.get` ignore overridden `__setitem__`/`__getitem__`. Only affects direct subclasses of C-coded built-ins.
- **Mixin that holds state or is the only base of a concrete class.**
- **Giant catch-all bases** like `tkinter.Misc` (100+ methods, every widget inherits clipboard/selection/timer; `dir(tkinter.Button)` shows 214 attributes). Split into specialized mixins.
- **Overriding methods of complex concrete classes**: superclass methods may ignore overrides.

## Code Examples
```python
class LastUpdatedOrderedDict(OrderedDict):
    """Store items in the order they were last updated"""
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)
```
- **What it demonstrates**: recommended super() override pattern.

```python
class DoppelDict(dict):
    def __setitem__(self, key, value):
        super().__setitem__(key, [value] * 2)
# DoppelDict(one=1) -> {'one': 1}  (init ignored override); dd.update(three=3) also ignores it
# Fix: class DoppelDict2(collections.UserDict) -> {'one': [1, 1]} and update works
```

```python
class Root:
    def ping(self): print(f'{self}.ping() in Root')
    def pong(self): print(f'{self}.pong() in Root')
class A(Root):
    def ping(self): print(f'{self}.ping() in A'); super().ping()
    def pong(self): print(f'{self}.pong() in A'); super().pong()
class B(Root):
    def ping(self): print(f'{self}.ping() in B'); super().ping()
    def pong(self): print(f'{self}.pong() in B')       # does not cooperate
class Leaf(A, B):
    def ping(self): print(f'{self}.ping() in Leaf'); super().ping()
# Leaf.__mro__ == (Leaf, A, B, Root, object)
# leaf.ping(): Leaf, A, B, Root.  leaf.pong(): A, B only (B stops the chain)
```
- **What it demonstrates**: MRO + super() jointly determine activation; Leaf(B, A) would reorder everything.

```python
class UpperCaseMixin:
    def __setitem__(self, key, item):
        super().__setitem__(_upper(key), item)
    def __getitem__(self, key):
        return super().__getitem__(_upper(key))
    def get(self, key, default=None):
        return super().get(_upper(key), default)
    def __contains__(self, key):
        return super().__contains__(_upper(key))

class UpperDict(UpperCaseMixin, collections.UserDict):  # mixin FIRST
    pass
class UpperCounter(UpperCaseMixin, collections.Counter):
    """Specialized 'Counter' that uppercases string keys"""
```
- **What it demonstrates**: mixin must precede the class it wraps; `get` was required for Counter because `dict.get` doesn't call `__getitem__`.

## Reference Tables
| Class | MRO |
|---|---|
| `tkinter.Toplevel` | Toplevel, BaseWidget, Misc, Wm, object |
| `tkinter.Button` | Button, Widget, BaseWidget, Misc, Pack, Place, Grid, object |
| `tkinter.Text` | Text, Widget, BaseWidget, Misc, Pack, Place, Grid, XView, YView, object |

Real-world multiple inheritance: collections.abc (ABCs as mixins); `ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer)` (mixin `process_request` starts a thread, no super; `server_close` calls super then joins threads); Django `ListView(MultipleObjectTemplateResponseMixin, BaseListView)` (empty body; `View` + `TemplateResponseMixin`, `MultipleObjectMixin`).

## Worked Example
`LeafUA(U, A)` where `U` is unrelated to the diamond: `U().ping()` raises `AttributeError: 'super' object has no attribute 'ping'` (MRO is U, object), but in `LeafUA` the MRO is LeafUA, U, A, Root, object so U.ping cooperates and reaches A and Root. With bases `(A, U)`, `A.ping` would go to Root and never reach U. `super()` binding is dynamic.

## Key Takeaways
1. Always use `super()`; always call `super().__init__`.
2. Never subclass built-in collections directly for overriding; use `UserDict/UserList/UserString` or ABCs.
3. MRO is C3 over the bases order; cooperative methods must all call `super()` and share signatures.
4. Mixins go first in the bases list, are stateless, named `...Mixin`.
5. Prefer composition; use inheritance for interface (ABCs) and rarely implementation (mixins).
6. Library design may need deep hierarchies (GUI toolkits); application code usually shouldn't.
7. Modern trend (Go, Julia, Rust traits): limit or avoid inheritance.

## Connects To
- **Ch 3**: `UserDict`, `__missing__` inconsistencies in built-ins.
- **Ch 13**: ABCs as mixins; goose typing.
- **Ch 11/12**: classes used as bases in examples.
- **Ch 23/24**: descriptors and metaclasses behind `super`.
