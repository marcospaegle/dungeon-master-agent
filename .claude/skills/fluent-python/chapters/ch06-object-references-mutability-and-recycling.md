# Chapter 6: Object References, Mutability, and Recycling

## Core Idea
A name is not the object: Python variables are labels bound to objects, not boxes holding values. Aliasing, shallow vs. deep copies, call by sharing, and mutable defaults all follow from this, and are the root of many subtle bugs.

## Frameworks Introduced
- **Variables are labels, not boxes**: `b = a` attaches a second label to the same object; nothing is copied.
  - When to use: reason about any assignment/aliasing bug.
  - How: read the right-hand side first (the object is created or fetched), then bind the name. Say "variable s is bound to the object", never "the object is assigned to s". Prefer verb "bind".
- **Identity / Value / Type**: every object has an identity (never changes; `id()`, `is`), a type, and a value (the only part that may change).
  - How: `==` compares values (`__eq__`), `is` compares identity (cannot be overloaded, so it is faster).
- **Call by sharing**: the only parameter-passing mode. Each formal parameter gets a copy of the reference, so parameters are aliases of the arguments.
  - Consequence: a function may mutate mutable arguments but cannot replace the caller's object; rebinding inside has no external effect.
  - Failure mode: callers' lists/dicts get mutated unexpectedly.
- **Defensive programming with mutable parameters**: unless a method is explicitly meant to mutate its argument, do not alias it into `self`; copy it (`list(passengers)`). Principle of least astonishment.
  - Trade-off: copy costs CPU/memory, but an API with subtle bugs is usually worse.
- **None-default idiom**: `def __init__(self, passengers=None): if passengers is None: self.passengers = [] else: self.passengers = list(passengers)`.

## Key Concepts
- **Alias**: two or more names bound to the same object.
- **Shallow copy**: outer container duplicated, filled with references to the same items (`list(l)`, `l[:]`, `copy.copy`).
- **Deep copy**: duplicates with no shared embedded objects (`copy.deepcopy`); handles cycles by remembering already-copied objects. Customize with `__copy__`/`__deepcopy__`.
- **Container immutability**: a tuple's immutability covers the references it holds, not the referenced objects; identity of items never changes but their value can.
- **Reference counting**: CPython's primary GC; object destroyed immediately at refcount zero. A generational GC (since 2.0) handles unreachable reference cycles.
- **`del`**: a statement that deletes a reference (name), not an object. Objects die when unreachable.
- **`__del__`**: called by the interpreter just before destruction to release external resources; rarely needed, never call it yourself.
- **Weak reference**: a reference that does not increase refcount; used by `weakref.finalize`, `WeakValueDictionary`, `WeakKeyDictionary`, `WeakSet` (useful for caches).
- **Interning**: CPython shares some small ints and strings; undocumented, implementation-specific.
- **Sentinel**: unique object (`END_OF_DATA = object()`) tested with `is`.

## Mental Models
- Use `==` by default; use `is` only for singletons (`None`, sentinels): `x is None`, `x is not None`.
- Think of a function parameter as a second sticky note on the caller's object.
- Immutable objects make aliasing irrelevant; identity only matters when objects are mutable (so interning is safe).
- To understand any assignment, read the right side first.

## Anti-patterns
- **Mutable default parameter (`passengers=[]`)**: default is evaluated once at function definition and stored in `func.__defaults__`; all calls relying on it share (and mutate) it ("HauntedBus").
- **Aliasing a received mutable argument (`self.passengers = passengers`)**: caller's list changes when the object mutates it ("TwilightBus").
- **`is` for strings/ints/tuples equality**: interning is an implementation detail; use `==`.
- **Assuming `t[:]`, `tuple(t)`, `frozenset.copy()`, `str` slice copy anything**: they return the same object for immutables (harmless "lies").
- **Relying on `__del__` / immediate finalization**: other implementations (PyPy, Jython) do not use refcounts; use `with` for files.
- **`open(...).write(...)` without `with`**: safe in CPython only by refcount luck.
- **Shallow copy when items are mutable and must not be shared**: use `deepcopy`.

## Code Examples
```python
>>> t1 = (1, 2, [30, 40])
>>> t2 = (1, 2, [30, 40])
>>> t1 == t2
True
>>> t1[-1].append(99)
>>> t1 == t2
False
```
- **What it demonstrates**: tuple "immutability" is only of references; same id for `t1[-1]`, different value.

```python
l1 = [3, [66, 55, 44], (7, 8, 9)]
l2 = list(l1)                 # shallow copy
l1.append(100)
l1[1].remove(55)              # visible in l2[1] (shared inner list)
l2[1] += [33, 22]             # += mutates shared list in place
l2[2] += (10, 11)             # += on tuple builds NEW tuple, rebinds l2[2]
```
- **What it demonstrates**: `+=` mutates mutable operands in place but rebinds for immutables.

```python
class Bus:
    def __init__(self, passengers=None):
        if passengers is None:
            self.passengers = []
        else:
            self.passengers = list(passengers)
```
- **What it demonstrates**: correct pattern avoiding both HauntedBus and TwilightBus bugs; also accepts any iterable.

```python
>>> import weakref
>>> s1 = {1, 2, 3}
>>> s2 = s1
>>> def bye():
...     print('...like tears in the rain.')
>>> ender = weakref.finalize(s1, bye)
>>> del s1            # object survives, s2 still refers
>>> s2 = 'spam'       # last ref gone -> callback fires
...like tears in the rain.
```
- **What it demonstrates**: `del` removes a name only; `finalize` holds a weak ref.

## Reference Tables
| Operation | Copies? |
|---|---|
| `b = a` | no, alias |
| `list(l)`, `l[:]`, `copy.copy(x)` | shallow |
| `copy.deepcopy(x)` | deep, cycle-safe |
| `tuple(t)`, `t[:]`, `str`/`bytes`/`frozenset.copy()` | returns same object |

| Parameter-passing mode | Function gets |
|---|---|
| call by value | copy of value |
| call by reference | pointer to variable |
| call by sharing (Python) | copy of the reference; can mutate, cannot rebind caller's name |

## Worked Example
HauntedBus: `HauntedBus.__init__(self, passengers=[])` assigns `self.passengers = passengers`. `bus2 = HauntedBus(); bus2.pick('Carrie')` mutates the default list; `bus3 = HauntedBus()` then sees `['Carrie']`; `bus2.passengers is bus3.passengers` is `True`; `HauntedBus.__init__.__defaults__` shows `(['Carrie', 'Dave'],)`. `bus1` (given its own list) is unaffected. Fix: None-default plus `list(passengers)`.

## Key Takeaways
1. Simple assignment never copies; `b = a` creates an alias.
2. Shallow copy is the default for built-in collections; use `copy.deepcopy` when nested mutables must not be shared.
3. Functions receive aliases (call by sharing); copy mutable arguments you keep, and never use mutable parameter defaults (use `None`).
4. Use `==` for value, `is` only for `None`/sentinels; never depend on interning.
5. `del` removes references, not objects; CPython frees on refcount zero plus a cycle collector; use `with` for resources and `weakref` for non-owning refs.
6. Tuples of mutable items can change value; only item identity is fixed.

## Connects To
- **Ch 2**: `+=` puzzler, hashability and relative tuple immutability.
- **Ch 5**: `default_factory` solves the mutable default in dataclasses.
- **Ch 7**: functions are objects whose `__defaults__` hold defaults.
- **Ch 8**: `None` default and `Optional`.
- **Ch 9**: closures capture references.
