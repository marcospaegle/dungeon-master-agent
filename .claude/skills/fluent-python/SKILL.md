---
name: fluent-python
description: "Knowledge base from \"Fluent Python, 2nd Edition\" by Luciano Ramalho. Use when applying Ramalho's frameworks for the Python data model, special methods, sequences/dicts/sets, type hints and protocols, decorators/closures, inheritance and ABCs, operator overloading, iterators/generators, asyncio/concurrency, descriptors and metaprogramming, studying the book, or referencing its concepts."
---

<!-- argument-hint: [topic, framework name, or chapter number] -->

# Fluent Python, 2nd Edition (Python 3.10)
**Author**: Luciano Ramalho | **Pages**: ~1011 | **Chapters**: 24 (5 parts) | **Generated**: 2026-10-10

## How to Use This Skill

- **Without arguments** — use the Core Frameworks below
- **With a topic** — ask about `__slots__`, `singledispatch`, `Protocol`, etc.; I find it in the Topic Index and read the chapter
- **With a chapter** — ask for `ch14`; I load that chapter file
- **Browse** — ask "what chapters do you have?"

For a topic not covered in Core Frameworks, I read the relevant chapter file before answering.

---

## Core Frameworks & Mental Models

**The Python Data Model (Ch 1)** — Python is a framework; your classes implement special methods (`__len__`, `__getitem__`, `__repr__`, `__add__`…) and the interpreter calls them. Never call dunders directly except `super().__init__()`; use `len(x)`, `repr(x)`, `x + y`. Implement `__repr__` always (unambiguous), `__str__` only if end-user output differs. Truthiness: `__bool__`, else `__len__`.

**Implement protocols, not hierarchies (Ch 12-13)** — Duck typing: a sequence needs only `__len__` + `__getitem__` and you get iteration, `in`, slicing, `reversed`. *Typing Map* (2×2): runtime/static × structural/nominal = duck typing, goose typing (`isinstance` against ABCs), static duck typing (`typing.Protocol`), static nominal (ordinary hints). Prefer small `Protocol`s defined at the point of use; use ABCs for goose typing; do not write your own ABC unless building a framework.

**Sequences & mappings (Ch 2-3)** — Container vs flat sequences; tuples are records *and* immutable lists; listcomps/genexps over `map`/`filter`; genexp when you only iterate. `match/case` sequence & mapping patterns destructure; guards add conditions. Subclass `UserDict`/`UserList`, not `dict`/`list`. Missing keys: `setdefault`/`defaultdict` (insert), `__missing__` (custom), `.get` (no insert). Keys must be hashable (stable `__hash__` consistent with `__eq__`).

**Unicode sandwich (Ch 4)** — Decode bytes to `str` on input, work only with `str`, encode on output. Always pass `encoding=` explicitly. Compare text with NFC normalization (`unicodedata.normalize`), case-insensitive with `casefold()`.

**References & mutability (Ch 6)** — Variables are labels, not boxes; `==` compares value, `is` identity. Call by sharing: functions get references. Never use mutable defaults; copy mutable arguments defensively (`list(arg)`). Copies are shallow by default; `copy.deepcopy` for graphs.

**Choose a data class builder (Ch 5)** — `collections.namedtuple` (immutable, tuple-like) → `typing.NamedTuple` (+ hints, methods) → `@dataclass` (mutable by default, `frozen=True`, `field(default_factory=...)`, `__post_init__`). Data classes as scaffolding are fine; as the permanent home of logic they are a code smell.

**First-class functions & type hints (Ch 7-8, 15)** — Prefer comprehensions, `operator.itemgetter/attrgetter`, `functools.partial`; replace `lambda` bodies >1 expression by named functions (Lundh's recipe). *Gradual typing*: hints are optional, never enforced at runtime, checker-only. Use *consistent-with*, not just subtype-of. Prefer abstract parameter types (`Iterable`, `Sequence`, `Mapping`) and concrete return types. Variance: producers covariant, consumers contravariant, mutables invariant. `@overload` for signature-dependent returns; `TypeVar` + bounds/constraints for generics.

**Decorators & closures (Ch 9)** — A decorator is a callable run at *import* time that replaces the function. Know variable lookup (local → enclosing → global → builtin), `nonlocal`, decorator factories (three nested levels), `functools.wraps`, `functools.cache`, `singledispatch`. Strategy/Command patterns collapse to plain functions (Ch 10).

**A Pythonic object (Ch 11)** — Support `__repr__`, `__str__`, `__bytes__`, `__format__`, `__hash__`, `__eq__`, alternate constructor as `@classmethod`; make hashable objects immutable via read-only `@property`; `__slots__` saves memory but has caveats (`__dict__`, `__weakref__`, inheritance).

**Inheritance, for better or worse (Ch 14)** — `super()` follows the MRO (C3); design methods cooperatively. Seven recommendations: avoid subclassing built-ins (use `UserDict`), distinguish interface vs implementation inheritance, make interfaces explicit with ABCs, use mixins for reuse (named `...Mixin`, no state, never instantiated), provide aggregate classes, *favor object composition over class inheritance*, subclass only classes designed for it.

**Operator overloading (Ch 16)** — Infix dispatch: try `a.__op__(b)`; if `NotImplemented`, try `b.__rop__(a)`. Return `NotImplemented` (not raise) for unsupported types. Unary ops and infix ops must not mutate operands; `__iadd__` may mutate and return `self`. `==` falls back to identity; define `__eq__` with `isinstance` check.

**Iterators & generators (Ch 17)** — `iter(x)` resolution: `__iter__`, else `__getitem__` from 0, else TypeError. Iterable ≠ iterator: iterables return a fresh iterator; iterators implement `__next__` and `__iter__` returning self. Prefer generator functions; `yield from` delegates; classic coroutines (`.send()`) are superseded by `async`/`await`. Use `itertools`, `functools.reduce`, `any`/`all` as reducers.

**Context managers, match, else (Ch 18)** — `__enter__`/`__exit__`, `@contextlib.contextmanager` (yield inside try/finally), `else` on `for`/`while`/`try` runs when no break/exception — EAFP style.

**Concurrency (Ch 19-21)** — Three models: threads, processes, `asyncio`. The GIL means only one thread runs Python bytecode but releases on I/O; use threads for I/O, `ProcessPoolExecutor`/multiprocessing for CPU. `concurrent.futures`: `executor.map` (ordered) vs `submit` + `as_completed` (per-future context). `asyncio`: never block the event loop—delegate blocking work to executors (`run_in_executor`); throttle with `Semaphore`; prefer structured concurrency (`TaskGroup`/`gather`); `await` only inside `async def`.

**Dynamic attributes, descriptors, metaprogramming (Ch 22-24)** — *Uniform Access Principle*: start with public attributes, convert to `@property` later. `__getattr__` only on lookup failure; `__setattr__` for all assignments. Descriptors (`__get__`, `__set__`, `__set_name__`) implement properties/validation reused across classes; overriding (has `__set__`) vs nonoverriding. *Customization ladder* for classes: class decorator → `__init_subclass__` → metaclass (last resort). Know the class construction timeline (`__prepare__`, `__new__`, `__init_subclass__`, `__set_name__`, `__init__`).

---

## Chapter Index

| # | Title | Key Frameworks |
|---|-------|----------------|
| [ch01](chapters/ch01-the-python-data-model.md) | The Python Data Model | Data Model as framework; special-method delegation; Collection ABC trio |
| [ch02](chapters/ch02-an-array-of-sequences.md) | An Array of Sequences | Container vs flat; tuple double life; destructuring with match/case; listcomp vs genexp |
| [ch03](chapters/ch03-dictionaries-and-sets.md) | Dictionaries and Sets | Missing-key strategy; subclass UserDict; set algebra; semi-structured data matching |
| [ch04](chapters/ch04-unicode-text-versus-bytes.md) | Unicode Text Versus Bytes | Unicode sandwich; normalize-before-compare ladder; explicit encoding; error-handler choice |
| [ch05](chapters/ch05-data-class-builders.md) | Data Class Builders | Choosing a data class builder; Data Class as Code Smell (scaffolding / intermediate representation); Class patterns (simple/keyword/positional) |
| [ch06](chapters/ch06-object-references-mutability-and-recycling.md) | Object References, Mutability, and Recycling | Variables are labels not boxes; Call by sharing; Defensive programming with mutable parameters; Shallow vs deep copy |
| [ch07](chapters/ch07-functions-as-first-class-objects.md) | Functions as First-Class Objects | Modern replacements for map/filter/reduce; Nine flavors of callables; Lundh's lambda refactoring recipe; operator and partial |
| [ch08](chapters/ch08-type-hints-in-functions.md) | Type Hints in Functions | Gradual typing; Duck vs nominal typing; Subtype-of vs consistent-with; TypeVar and Protocol (static duck typing) |
| [ch09](chapters/ch09-decorators-and-closures.md) | Decorators and Closures | Variable lookup logic; Decorator factory; singledispatch generic functions; Three essential facts |
| [ch10](chapters/ch10-design-patterns-with-first-class-functions.md) | Design Patterns with First-Class Functions | Function-oriented Strategy; Decorator-enhanced Strategy; Command as callable |
| [ch11](chapters/ch11-a-pythonic-object.md) | A Pythonic Object | Object representation methods; Format mini-language extension; Hashable-immutable recipe; __slots__ |
| [ch12](chapters/ch12-special-methods-for-sequences.md) | Special Methods for Sequences | Protocols and duck typing; Slice-aware __getitem__; __getattr__/__setattr__ pair; map-reduce hash |
| [ch13](chapters/ch13-interfaces-protocols-and-abcs.md) | Interfaces, Protocols, and ABCs | Typing Map; Goose typing; Static protocol design; Fail fast |
| [ch14](chapters/ch14-inheritance-for-better-or-for-worse.md) | Inheritance: For Better or for Worse | Cooperative multiple inheritance (MRO + super); Seven recommendations for coping with inheritance; Mixins/aggregate classes |
| [ch15](chapters/ch15-more-about-type-hints.md) | More About Type Hints | Overloads; Variance rules of thumb; Runtime annotations wrapper; Generic classes/protocols |
| [ch16](chapters/ch16-operator-overloading.md) | Operator Overloading | Infix dispatch algorithm (forward/reverse/NotImplemented); Rich comparison rules; Augmented assignment rules |
| [ch17](chapters/ch17-iterators-generators-and-classic-coroutines.md) | Iterators, Generators, and Classic Coroutines | iter() resolution order; Iterable vs Iterator contract; Sentence evolution; yield from baby-steps recursion |
| [ch18](chapters/ch18-with-match-and-else-blocks.md) | with, match, and else Blocks | Context manager protocol; @contextmanager recipe; grammar as sequence patterns (lis.py); else-block rules / EAFP |
| [ch19](chapters/ch19-concurrency-models-in-python.md) | Concurrency Models in Python | Three models (spinner); GIL in 10 points; worker queues + poison pill; constraints manage complexity |
| [ch20](chapters/ch20-concurrent-executors.md) | Concurrent Executors | map vs submit+as_completed; future-to-context dict; sequential-to-concurrent refactor; choose pool type |
| [ch21](chapters/ch21-asynchronous-programming.md) | Asynchronous Programming | Guido's trick; Awaitable; Delegate blocking work to executors; Semaphore throttling; Structured concurrency |
| [ch22](chapters/ch22-dynamic-attributes-and-properties.md) | Dynamic Attributes and Properties | Uniform Access Principle; Virtual attributes (`__getattr__`); Property factory; Cached properties |
| [ch23](chapters/ch23-attribute-descriptors.md) | Attribute Descriptors | Descriptor terminology; Overriding vs nonoverriding; Template method (Validated); `__set_name__` |
| [ch24](chapters/ch24-class-metaprogramming.md) | Class Metaprogramming | Customization ladder; Class construction timeline; Metaclass `__new__`/`__prepare__`; Checked builder |

## Topic Index

- **== vs is** → ch06
- **@ operator** → ch16
- **@property, setters/deleters, property factory** → ch22
- **__add__/__radd__/NotImplemented** → ch16
- **__format__ mini-language** → ch11
- **__getattr__/__setattr__** → ch12
- **__match_args__** → ch11
- **__post_init__** → ch05
- **__slots__** → ch11
- **`+=` puzzler** → ch02
- **`__init_subclass__`, Checked** → ch24
- **`__set_name__`** → ch23
- **`type()` class factory, record_factory** → ch24
- **ABC, abstractmethod, register, __subclasshook__** → ch13
- **actor model / CSP** → ch19
- **aliasing** → ch06
- **Any / consistent-with** → ch08
- **array/memoryview/NumPy/deque** → ch02
- **async context managers, async generators, async comprehensions** → ch21
- **async/await, native coroutines, awaitables** → ch21
- **asyncio.run / gather / as_completed / to_thread / Semaphore** → ch21
- **augmented assignment, __iadd__** → ch16
- **BOM** → ch04
- **bound methods as descriptors** → ch23
- **bytes/bytearray** → ch04
- **cached_property, @cache stacking, key-sharing** → ch22
- **call by sharing** → ch06
- **Callable and variance** → ch08
- **callable types / __call__** → ch07
- **cast** → ch15
- **ChainMap/Counter/OrderedDict** → ch03
- **class attribute override** → ch11
- **class decorators (@checked)** → ch24
- **class patterns / __match_args__** → ch05
- **classic coroutines / send** → ch17
- **classmethod/staticmethod** → ch11
- **ClassVar** → ch05
- **closures** → ch9
- **Collection ABCs** → ch01
- **Command pattern** → ch10
- **composition over inheritance** → ch14
- **comprehensions/genexp** → ch02
- **concurrency vs parallelism** → ch19
- **container vs flat** → ch02
- **contextlib / @contextmanager** → ch18
- **CPU-bound traps, executors** → ch21
- **Curio / TaskGroup / structured concurrency** → ch21
- **data class code smell** → ch05
- **dataclass** → ch05
- **decorators** → ch9
- **del / garbage collection / weakref** → ch06
- **descriptor protocol, `__get__`/`__set__`/`__delete__`** → ch23
- **design patterns/Norvig** → ch10
- **dict syntax/merge** → ch03
- **dict views** → ch03
- **Django/Tkinter hierarchies** → ch14
- **duck vs nominal typing** → ch08
- **duck/goose/static typing** → ch13
- **dynamic attributes, `__getattr__`, `__getattribute__`, `__setattr__`, `__delattr__`** → ch22
- **EAFP vs LBYL** → ch18
- **encodings/codecs** → ch04
- **Executor.map vs submit** → ch20
- **ExitStack** → ch18
- **FastAPI / ASGI / asyncio streams TCP server** → ch21
- **field default_factory** → ch05
- **first-class functions** → ch07
- **Flyweight** → ch10
- **for/while/try else** → ch18
- **FrozenJSON, `__new__`, Record/Event** → ch22
- **functools.cache/lru_cache** → ch9
- **functools.partial** → ch07
- **Future / as_completed** → ch20
- **generator function/expression** → ch17
- **Generator type hints/variance** → ch17
- **generic collections** → ch08
- **generic protocol** → ch15
- **Generic, TypeVar, variance** → ch15
- **get_type_hints, PEP 563** → ch15
- **GIL** → ch19
- **gradual typing / Mypy** → ch08
- **hashable** → ch03
- **hashable/immutable** → ch11
- **higher-order functions** → ch07
- **import time vs runtime, class construction order** → ch24
- **InitVar** → ch05
- **interning** → ch06
- **iter() protocol** → ch17
- **Iterator pattern** → ch17
- **itertools** → ch17
- **keyword-only / positional-only params** → ch07
- **lambda** → ch07
- **mapping patterns** → ch03
- **match/case interpreter (lis.py)** → ch18
- **metaclass conflict** → ch24
- **metaclasses, MetaBunch, CheckedMeta, `__prepare__`, AutoConst** → ch24
- **mixins, aggregate classes** → ch14
- **monkey patching** → ch13
- **mutable default arguments** → ch06
- **name mangling/private** → ch11
- **namedtuple** → ch05
- **NamedTuple** → ch05
- **nonlocal** → ch9
- **NoReturn** → ch08
- **normalization/casefold** → ch04
- **numbers ABCs** → ch13
- **operator module** → ch07
- **operators overview** → ch01
- **Optional / Union** → ch08
- **OR-patterns** → ch18
- **overload** → ch15
- **overriding vs nonoverriding descriptors** → ch23
- **parameterized decorator** → ch9
- **pattern matching sequences** → ch02
- **poison pill / queues** → ch19
- **Protocol** → ch08
- **Protocol, runtime_checkable, SupportsX** → ch13
- **protocols/duck typing** → ch12
- **reduce/map-reduce hashing** → ch12
- **repr/str** → ch01
- **repr/str/bytes/format** → ch11
- **reprlib** → ch12
- **rich comparison** → ch16
- **setdefault/defaultdict/__missing__** → ch03
- **sets and set ops** → ch03
- **shallow/deep copy** → ch06
- **singledispatch** → ch9
- **slicing** → ch02
- **slicing/slice objects** → ch12
- **sort/sorted** → ch02
- **special methods** → ch01
- **stacked decorators** → ch9
- **str vs bytes APIs** → ch04
- **Strategy pattern** → ch10
- **super, MRO, C3, diamond** → ch14
- **tail calls** → ch18
- **threading / multiprocessing / asyncio spinner** → ch19
- **ThreadPoolExecutor / ProcessPoolExecutor** → ch20
- **tuple as record** → ch02
- **TypedDict** → ch15
- **TypeVar** → ch08
- **typing *args/**kwargs** → ch08
- **Typing Map** → ch13
- **unary operators** → ch16
- **Unicode errors** → ch04
- **Unicode sandwich** → ch04
- **Unicode sorting** → ch04
- **unicodedata** → ch04
- **Uniform Access Principle** → ch22
- **unpacking** → ch02
- **UserDict** → ch03
- **UserDict, built-in subclassing** → ch14
- **Validated / template method** → ch23
- **variable annotations** → ch05
- **variable scope** → ch9
- **with / context managers** → ch18
- **WSGI/ASGI/task queues** → ch19
- **yield from** → ch17
- **zip** → ch12

## Supporting Files

- [glossary.md](glossary.md) — key terms with definitions
- [patterns.md](patterns.md) — techniques and idioms (when/how/trade-offs)
- [cheatsheet.md](cheatsheet.md) — decision rules, thresholds, smells

---

## Scope & Limits

This skill covers the book's content (2nd edition, Python 3.10) as synthesized summaries, not book text. Some code listings in the extraction were flattened or missing and were reconstructed from surrounding text, so verify exact syntax against the book or current Python docs. For hands-on implementation in your codebase, combine with project tools. The Chapter 16 heading was lost in extraction; it is titled "Operator Overloading".
