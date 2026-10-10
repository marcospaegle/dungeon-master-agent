# Cheatsheet — decision rules, thresholds, smells

Read as "When X, do Y, because Z." Grouped by chapter range.

## Ch 1-4

- When implementing only one of `__repr__`/`__str__`, choose `__repr__`, because str falls back to it (Ch 1).
- When you need `len`-like behavior, define `__len__`; call `len()`, not the dunder, because built-ins are faster (Ch 1).
- When overloading `+`/`*`, return a new object; never mutate operands (Ch 1).
- When a loop only builds a list, use a listcomp; if it exceeds two lines, use a `for` (Ch 2).
- When the output feeds another constructor or loop, use a genexp, not a listcomp (Ch 2).
- When a tuple is a record, unpack it; when it is an immutable list, check `hash(t)` if immutability matters (Ch 2).
- When holding millions of numbers, use `array.array` (or NumPy); for FIFO use `deque`, not `list.pop(0)` (Ch 2).
- When `in` is called often on big collections, use a `set` (Ch 2).
- When writing `a * n` with mutable items, stop: aliasing bug (Ch 2).
- When a match subject could be a string, remember str is atomic (Ch 2).
- When doing `get` + mutate + store on a dict, use `setdefault` or `defaultdict` (Ch 3).
- When writing a custom mapping, subclass `UserDict` not `dict`, because built-in shortcuts ignore overrides (Ch 3).
- When you need read-only exposure of a mapping, wrap in `MappingProxyType` (Ch 3).
- When you need dedupe + order, `dict.fromkeys`; unordered dedupe, `set` (Ch 3).
- When defining `__eq__`, define `__hash__` from the same immutable attributes (Ch 3).
- When opening a text file, always pass `encoding=` (Ch 4).
- When comparing user text, NFC + casefold; use NFKC only for search/index because it loses data (Ch 4).
- When sorting human text, use `pyuca`/PyICU, not `sorted` or fragile `setlocale` (Ch 4).
- When an encoding is unknown, you can't know; use metadata, Chardet, or UTF-8-then-cp1252 (Ch 4).
- When handling BOM'd files, read `utf-8-sig`, write `utf-8` (Ch 4).
- Smell: `errors='ignore'` anywhere = silent data loss (Ch 4).

## Ch 5-8

- When a dataclass field default is a list/dict/set/other mutable, use `field(default_factory=...)`, because the literal is shared across instances (dataclass only rejects list/dict/set) (Ch 5)
- When you need ClassVar vs field: annotated top-level attribute becomes an instance field; use `ClassVar[...]` for class attributes (Ch 5)
- When data class has no behavior and is permanent, treat as smell: move behavior in, unless it is scaffolding or an intermediate representation (immutable at boundaries) (Ch 5)
- When you need type info from a class, use `inspect.get_annotations` (3.10) or `typing.get_type_hints`, not `__annotations__`, because they resolve forward references (Ch 5)
- When writing `case float:` meaning a type test, write `case float():` because the bare name is a capture pattern that matches everything (Ch 5)
- When comparing to None or sentinel use `is`; otherwise `==`; never use `is` for str/int because interning is an implementation detail (Ch 6)
- When a parameter default would be mutable, use None and create inside, because defaults are evaluated once and live in `__defaults__` (Ch 6)
- When storing a received mutable argument, copy it unless the method is meant to mutate it, because aliasing surprises clients (Ch 6)
- When you need independent nested copies, use deepcopy; shallow copies share inner mutables (and `+=` on tuple vs list differ) (Ch 6)
- When relying on file/resource cleanup, use `with`, not refcount timing or `__del__` (Ch 6)
- When a lambda is hard to read, apply Lundh's recipe (comment, name, def, delete comment) (Ch 7)
- When summing use `sum`, not `reduce(add)`; when mapping/filtering use comprehensions (Ch 7)
- When you need a callable with state across calls, use `__call__` (or a closure) (Ch 7)
- When an API's argument should never be passed by name use `/`; when it must be named use `*` (Ch 7)
- When you must adapt a function to a callback taking fewer arguments, use `functools.partial` (Ch 7)
- When annotating parameters, prefer abstract types (Mapping, Sequence, Iterable); when annotating returns, prefer concrete types (Ch 8)
- When return type depends on input type, use TypeVar, not Union; avoid Union returns otherwise (Ch 8)
- When you need only iteration, `Iterable`; when `len()`/index needed, `Sequence` (Ch 8)
- When numeric argument annotation is needed, use float (accepts int) or complex rather than the `numbers` ABCs (Ch 8)
- When a TypeVar needs a capability (hash, <), use `bound=` with an ABC or a custom Protocol; use restricted TypeVar only for a fixed small set (Ch 8)
- When type hints would make an API clumsy or the code is exploratory, skip them; hints are no substitute for tests and cannot express value constraints (Ch 8)

## Ch 9-12

- When a decorator takes args, write a factory (or class); because Python passes only the function to the decorator.
- When assigning to a variable from an enclosing function, declare `nonlocal`; because assignment makes it local.
- When writing any decorator, use `functools.wraps`; because otherwise `__name__`/`__doc__` are lost.
- When a process is long-running, bound the cache with `lru_cache(maxsize=...)`; because `cache` is unbounded.
- When extending `singledispatch`, register ABCs not concrete types; because it supports more compatible types.
- When strategy classes have one method and no state, use functions; because they are lighter and already shared (Flyweight).
- When new strategies could be forgotten in a list, use a registration decorator; because it keeps definition and registry together.
- When an interface has one generically named method (execute/run/do_it), consider a callable; because boilerplate drops.
- When app (not library), implement only needed special methods; because end users do not care about "Pythonic".
- When making an object hashable, make it immutable and hash the same attributes `__eq__` uses; because hash must not change and equal objects must hash equally.
- When you need privacy, use `_x` by convention; `__x` only to avoid subclass clashes; neither is security.
- When storing millions of instances, consider `__slots__` (or NumPy/pandas); because `__dict__` costs ~3x memory (1.55 GiB vs 551 MiB for 10M). Redeclare in subclasses.
- When customizing a default, subclass and override the class attribute; because that is explicit and permanent.
- When writing a sequence constructor, take one iterable; because built-ins do.
- When you implement `__getattr__`, also implement `__setattr__`; because assignment otherwise shadows virtual attributes.
- When using `reduce`, always pass an initializer (identity); because empty input raises `TypeError`.
- When zipping unequal-length iterables, check lengths or use `strict=True`; because zip truncates silently.
- When summing, prefer `sum(genexp)` over `reduce`; because clearer and safe on empty.
- `__repr__` must never raise and must be bounded; `__format__` is for end users.
- Small smell: `isinstance` chains usually bad OO, but slice-vs-index in `__getitem__` is justified.

## Ch 13-16

- When you need to check an argument's kind, use isinstance against an ABC (not concrete class) only to enforce an API contract; otherwise duck-type, because concrete checks kill polymorphism (Ch 13)
- When a chain of isinstance if/elif appears, replace with polymorphism, because it is a design smell (Ch 13)
- When you don't need to run isinstance, just try the operation (EAFP), e.g. `complex(o)` (Ch 13)
- When a class implements a collections concept, subclass or register with the ABC; don't write your own ABCs/metaclasses unless building a framework (Ch 13)
- When designing protocols, keep them 1-2 methods, define near the client, name SupportsX/HasX (Ch 13)
- When you need static typing of numbers, use SupportsFloat etc.; when you need runtime checks use numbers ABCs (Ch 13)
- When you need to test hashability or iterability use hash()/iter(), not isinstance (Ch 13)
- When wanting a custom dict/list/str, subclass User* classes, not built-ins, because C methods ignore overrides (Ch 14)
- When overriding a method, call super().method(), never the base class by name (Ch 14)
- When writing a mixin, put it first in the bases, make it stateless, suffix Mixin, make every method cooperate (Ch 14)
- When tempted to inherit for reuse, prefer composition/delegation; reserve inheritance for interface (ABC) (Ch 14)
- When writing an application and building multilevel hierarchies, suspect reinvention, bad framework, or overengineering (Ch 14)
- When tempted to subclass a concrete class, don't; "all non-leaf classes should be abstract" (Ch 14)
- When a return type depends on arg types, use @overload (Ch 15)
- When handling JSON, use runtime validation (pydantic); TypedDict gives false safety (Ch 15)
- When cast() appears often, treat it as a smell; prefer cast to type: ignore or Any (Ch 15)
- When reading annotations at runtime, use get_type_hints/inspect.get_annotations via a wrapper (Ch 15)
- When unsure about variance, use invariant (Ch 15); output-only -> covariant; input-only -> contravariant; both -> invariant (Ch 15)
- When annotating is costing more than it gives, leave code unannotated or use # type: ignore (Ch 15)
- When an operator can't handle an operand, return NotImplemented, never raise TypeError (Ch 16)
- When the forward method handles only same-type operands, skip the reverse method (Ch 16)
- When defining operators, never mutate operands; in-place methods must return self and only for mutable types (Ch 16)
- When comparing with foreign types, be conservative: return NotImplemented from __eq__ unless equality is meaningful (Ch 16)
- When + needs strictness, make += accept any iterable (Ch 16)
- When avoiding isinstance with a numeric scalar, convert with float() and catch TypeError (Ch 16)

## Ch 17-20

- When a class only iterates, make `__iter__` a generator, because it removes iterator-state bookkeeping.
- When checking if something is iterable, call `iter(x)` and catch `TypeError`, because `isinstance(Iterable)` misses `__getitem__` objects.
- Never give the iterable a `__next__`, because multiple traversals need independent iterators.
- When a genexp spans more than a couple of lines, write a generator function, for readability.
- When using `groupby`, sort (or cluster) by the key first, because it groups only consecutive items.
- When float steps accumulate, compute `begin + step*index`, because repeated addition drifts.
- When annotating a generator used as iterator, use `Iterator[T]`; use `Generator[Y,S,R]` only for coroutines.
- When you need to reuse a stdlib generator, check `itertools` first, because it likely exists (20 functions).
- When writing a `@contextmanager`, wrap `yield` in `try/finally`, because exceptions raise at the yield.
- When entering an unknown number of context managers, use `ExitStack`; for a fixed few use parenthesized `with` (3.10).
- When code after a risky call should run only on success, put it in `else`, not `try`, because `try` should guard only what can raise.
- Prefer EAFP over LBYL in concurrent code, because LBYL has check/use races.
- Python has no PTC; don't write tail-recursive code for speed, because there's no gain and recursion limit is 1000.
- When the work is I/O-bound, use threads or asyncio; when CPU-bound, use processes, because the GIL serializes Python bytecode.
- Never call blocking functions in a coroutine; use `await asyncio.sleep` / executors, because the loop is single-threaded.
- A thread is interrupted every 5 ms (switch interval); with 2 threads one CPU-bound, spinner still runs, but 2+ CPU-bound threads is slower than sequential.
- Number of CPU-bound processes ~ number of physical cores (best median at 6 on 6-core/12-thread); hyperthreading doesn't help.
- Use `...` (Ellipsis) not `object()` as sentinel across processes, because pickling breaks identity.
- When results arrive out of order, carry the input in the result (or a future->input dict).
- Use `executor.map` for ordered same-callable jobs; `submit`+`as_completed` for different callables or completion-order handling.
- ThreadPoolExecutor for I/O; ProcessPoolExecutor never helps I/O-bound jobs.
- When testing concurrent clients, use local servers and a concurrency cap, because you can DoS public servers.
- Avoid managing threads/locks directly in application code; use executors, task queues, app servers.

## Ch 21-24

- When writing async code, make every I/O function a coroutine or delegate it to a thread/process, because one blocking call freezes the event loop (Ch 21).
- When you need results as completed, use `as_completed`; when you need ordered results, use `gather` (set `return_exceptions=True` per Caleb) (Ch 21).
- When limiting concurrency, use `asyncio.Semaphore` as an async context manager held briefly, because it is safer than manual acquire/release (Ch 21).
- When a CPU-bound hot spot appears, use process pool, task queue (picked early), or native code; if you do nothing, record it as technical debt (Ch 21).
- When using callbacks in modern app-level async code, stop; use await, because callbacks are legacy patterns (Ch 21).
- When unsure if an API method is a coroutine, check the docs (e.g., `write` vs `drain`) (Ch 21).
- When designing class APIs, expose public attributes first and wrap with `@property` later, because clients do not change (Ch 22).
- When a property needs the raw same-named attribute, read `self.__dict__['name']` to avoid recursion (Ch 22).
- When caching a property: `cached_property` unless same-name dependency, `__slots__` or memory key-sharing matters; then `@property` over `@cache` (Ch 22).
- When building attributes from external data, expect keyword/invalid identifier names and method shadowing; consider a mapping with `__getitem__` instead (Ch 22).
- When tempted to override `__getattribute__`/`__setattr__`, use `__getattr__`, properties or descriptors first, because they are less error prone (Ch 22).
- When the same property logic repeats, move to a descriptor class (not a property factory) (Ch 22/23).
- When coding descriptors, store values in the managed instance (`instance.__dict__`), never in the descriptor (Ch 23).
- When you need a read-only descriptor, implement `__set__` raising AttributeError or use `property`, because nonoverriding descriptors get shadowed (Ch 23).
- When a descriptor needs to know its attribute name, use `__set_name__`, not constructor arguments (Ch 23).
- When validation only (no transform on read), implement `__set__` only so reads are fast (Ch 23).
- When you want to control class-level assignment, you need a metaclass; descriptors cannot (Ch 23).
- When you must customize classes, climb the ladder: factory, `__set_name__`, `__init_subclass__`, class decorator, metaclass last (Ch 24).
- When you need `__slots__` generated, use a factory or metaclass; `__init_subclass__` and decorators run too late (Ch 24).
- When calling `__init_subclass__`, always `super().__init_subclass__()` (Ch 24).
- When combining ABC with a custom metaclass, expect "metaclass conflict"; avoid or combine at your peril (Ch 24).
- When writing metaclasses, hide behind a base class; metaclasses are implementation details (Ch 24).
- When in application code, avoid Ch 24 techniques; "good frameworks are extracted, not invented" (Ch 24).
- Afterword: Python is "a language for consenting adults"; engage with the community; Pythonic style resources: PEP 8, Hitchhiker's Guide, Hettinger/Rhodes talks.

