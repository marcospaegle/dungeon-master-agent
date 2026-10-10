# Patterns & Idioms — Fluent Python (2nd ed.)

Each entry: When to use / How / Trade-offs. Grouped by chapter range.

# Ch 1-4

### Implement a sequence via delegation
When to use: custom collection that should act like a list. How: `__len__` and `__getitem__` delegate to inner list. Trade-offs: read-only by default; add `__setitem__` for mutation (Ch 1).
### Vector-style value class
When to use: numeric-like objects. How: `__repr__` with `!r`, `__abs__`, `__bool__`, operators returning new instances. Trade-offs: add `__rmul__` etc. for symmetry (Ch 1).
### Lazy fill with genexp
When to use: initializing tuple/array or iterating Cartesian products. How: `tuple(f(x) for x in it)`. Trade-offs: single pass only (Ch 2).
### Destructure with match/case
When to use: dispatch on shape of nested sequences. How: sequence patterns + guards + `case _`. Trade-offs: 3.10+; str/bytes not matched as sequences (Ch 2).
### Named slices
When to use: fixed-width records. How: `NAME = slice(a, b)`; `line[NAME]`. Trade-offs: none (Ch 2).
### Safe nested list init
How: `[[x] * n for _ in range(m)]` (Ch 2).
### Bounded deque for recent items
How: `deque(maxlen=n)`; `append` discards from the opposite end (Ch 2).
### setdefault accumulate
How: `d.setdefault(k, []).append(v)`; one lookup. Trade-offs: builds the default list every call; `defaultdict` cleaner when used everywhere (Ch 3).
### Key-normalizing mapping
How: subclass `UserDict`; override `__missing__`, `__contains__`, `__setitem__` to `str(key)` (Ch 3).
### Set algebra on dict views
How: `d1.keys() & d2.keys()`, `needles & haystack`. Trade-offs: `items()` needs hashable values (Ch 3).
### Ordered dedupe
How: `list(dict.fromkeys(items))` (Ch 3).
### Unicode sandwich
How: `open(..., encoding='utf_8')`; str inside; encode at output (Ch 4).
### Normalized comparison
How: `normalize('NFC', a).casefold() == normalize('NFC', b).casefold()` (Ch 4).
### Strip diacritics
How: NFD, drop `combining()` chars, NFC; limit to Latin bases to avoid mangling Greek (Ch 4).
### Try UTF-8 then cp1252
How: decode UTF-8; on `UnicodeDecodeError` decode as cp1252. Trade-offs: heuristic, legacy backends only (Ch 4).

# Ch 5-8

### Choose the data class builder
When to use: you need a simple record class.
How: immutable + tuple semantics -> typing.NamedTuple; mutable/validation/defaults factories/InitVar -> @dataclass(frozen=True optional); runtime creation -> namedtuple()/make_dataclass().
Trade-offs: namedtuple compat (unpacking, sorting) vs dataclass flexibility; dataclass requires type hints; for validation beyond hints use attrs/pydantic-type libs.

### Dataclass with validation and derived fields
When to use: field value computed from others or must be validated at construction.
How: `__post_init__(self)`; use `ClassVar` for shared class state and `field(default_factory=list)` for mutable defaults; `InitVar` for init-only inputs (receive in __post_init__).
Trade-offs: defaults in a parent class force defaults in subclass fields; avoid hierarchies.

### Defensive copy of mutable argument (None-default idiom)
When to use: class/function stores or mutates a mutable parameter.
How: `param=None`; `if param is None: self.x = [] else: self.x = list(param)`.
Trade-offs: costs a copy; accepts any iterable; prevents aliasing and shared-default bugs.

### Choose copy depth
When to use: duplicating objects containing other objects.
How: `list(x)`/`x[:]`/`copy.copy` for shallow when items immutable or sharing is desired; `copy.deepcopy` otherwise; customize via `__copy__`/`__deepcopy__`.
Trade-offs: deep copy cost and surprising copying of resources/singletons.

### Replace map/filter/reduce
When to use: functional-style transforms.
How: listcomp/genexp with `if` for map+filter; `sum`, `all`, `any` for common reductions; `functools.reduce` with `operator` function otherwise.
Trade-offs: reduce still fine for non-sum folds (e.g., mul, hashing).

### Replace trivial lambdas with operator / partial
When to use: key functions and callbacks.
How: `itemgetter(1)`, `attrgetter('a.b')`, `methodcaller('replace', ' ', '-')`; `partial(f, 'img', class_='x')`.
Trade-offs: more readable and picklable-friendly than lambda; partial objects expose `.func/.args/.keywords`.

### Callable object with state
When to use: function-like thing with memory across calls, or decorator that remembers.
How: class with `__call__`; or a closure (Ch 9).
Trade-offs: more verbose than a closure but easier to extend with methods.

### Gradual annotation with Mypy
When to use: introducing hints into untyped code.
How: start unannotated; use `--disallow-incomplete-defs`; add return type then parameters per function; write tests with `-> None`; persist in mypy.ini; add `# type: ignore` for untyped third-party imports.
Trade-offs: partial coverage is fine; avoid chasing 100%.

### Bounded TypeVar + Protocol
When to use: generic function needing a capability (ordering, hashing) while returning the element type.
How: `class SupportsLessThan(Protocol): def __lt__(self, other: Any) -> bool: ...`; `LT = TypeVar('LT', bound=SupportsLessThan)`; `def top(series: Iterable[LT], length: int) -> list[LT]`.
Trade-offs: no registration needed; the checker verifies callers.

# Ch 9-12

### Registration decorator
When to use: collect functions in a central registry (routes, strategies, plugins).
How: `def register(f): registry.append(f); return f`; apply `@register`.
Trade-offs: explicit and decoupled across modules; runs at import time, so module must be imported.

### Parameterized decorator (factory)
When to use: decorator needs configuration.
How: `def deco(arg): def decorate(func): @wraps(func) def wrapper(*a, **kw): ...; return wrapper; return decorate; return decorate`; or class with `__init__(cfg)` and `__call__(func)`.
Trade-offs: three nesting levels; class form easier to read/maintain; always call with parentheses.

### Well-behaved wrapper decorator
When to use: add behavior (timing, logging) around calls.
How: `@functools.wraps(func)`, `*args, **kwargs`, return the original result.
Trade-offs: without `wraps` name/doc lost; for industrial grade see `wrapt`.

### Cache expensive pure functions
When to use: recursion or remote API calls with hashable args.
How: `@functools.cache` (scripts) or `@lru_cache(maxsize=N)` (long-running); stack above other decorators.
Trade-offs: memory growth; hashable args only.

### singledispatch generic function
When to use: per-type behavior that modules must extend independently.
How: `@singledispatch` on base; `@base.register` with type hint on first parameter; register ABCs.
Trade-offs: first-arg only; not overloading; no `Union` registration.

### Function-as-strategy
When to use: stateless, single-method strategy.
How: pass `Callable[[Context], Result]`; call `self.strategy(self)`; keep functions in a list or registry.
Trade-offs: use classes/closures when strategy needs state.

### Callable command / MacroCommand
When to use: callbacks, menu actions, composite actions.
How: pass functions; `MacroCommand.__call__` iterates a list of callables.
Trade-offs: undo needs stateful callable instance or closure.

### Alternative constructor
When to use: build instance from another representation (bytes, dict, string).
How: `@classmethod def frombytes(cls, octets): ... return cls(*memv)`.
Trade-offs: uses `cls`, so subclasses inherit correctly.

### Extending format mini-language
When to use: custom display forms for a class.
How: in `__format__`, test/strip unique suffix, delegate rest to `format(component, spec)`.
Trade-offs: avoid built-in letters.

### Slice-aware `__getitem__`
When to use: user-defined sequence.
How: `isinstance(key, slice)` -> `type(self)(self._data[key])`, else `operator.index(key)`.
Trade-offs: no multidim indexing unless you handle tuples.

### Virtual attributes (getattr+setattr)
When to use: shortcut read-only names (`v.x`) for positions.
How: `__getattr__` looks up in `__match_args__`; `__setattr__` rejects those names; delegate others to `super().__setattr__`.
Trade-offs: more code than properties but scales to many names.

### Aggregate hash with reduce
When to use: hash of many components.
How: `functools.reduce(operator.xor, (hash(x) for x in self), 0)`.
Trade-offs: xor is simple; lazy, no tuple copy.

# Ch 13-16

### Narrow client-side protocol
When to use: function needs one capability from its argument. How: define `class SupportsX(Protocol)` with one method near the consumer; mark @runtime_checkable only if isinstance needed; extend via derived protocol re-listing Protocol. Trade-offs: flexible and low coupling; runtime check ignores signatures.

### ABC with mixin methods
When to use: framework extension point. How: subclass abc.ABC; @abstractmethod for required methods; write concrete methods using only the interface (Tombola.inspect/loaded). Trade-offs: subclasses get correct-but-slow defaults, override for speed; instantiation fails until all abstracts done.

### Register a third-party class
When to use: class you don't own satisfies an ABC. How: `ABC.register(Cls)` or decorator on your own class. Trade-offs: no inheritance, unchecked, invisible to static checkers.

### Defensive input handling (EAFP / fail fast)
When to use: accept "any iterable". How: `self._x = list(arg)` or `iter(arg)`; try the operation and catch AttributeError/TypeError instead of isinstance; use hash(obj) to test hashability. Trade-offs: clear early error; copy cost.

### Cooperative mixin
When to use: add behavior across siblings (e.g. UpperCaseMixin). How: mixin methods call super().m(...) with same signature; list mixin first in bases. Trade-offs: depends on every sibling method routing through the right method (dict.get skips __getitem__).

### Subclass UserDict instead of dict
When to use: custom mapping/list/string. How: derive from collections.UserDict/UserList/UserString or the ABC. Trade-offs: slower than built-ins, but overrides are honored.

### Aggregate class
When to use: a combination of bases is commonly needed. How: empty-body class inheriting the mixins in the right order with a docstring (Django ListView). Trade-offs: hides MRO ordering from users.

### Overloaded signatures
When to use: return type depends on argument combination. How: stack @overload stubs above an unannotated implementation; use bound TypeVar and Union[T, DT]. Trade-offs: verbose (6 for max), duplicated for min.

### Wrap annotation introspection
When to use: reading type hints at runtime. How: one helper (`_fields`) calling get_type_hints; rest of code calls helper. Trade-offs: localizes change as PEP 563/649 evolve.

### Generic class / covariant protocol
When to use: container or producer parameterized by element type. How: `class C(Base, Generic[T])`; for output-only protocols use `Protocol[T_co]`. Trade-offs: default invariance is safest.

### Forward/reverse operator pair
When to use: binary operator with mixed operand types. How: forward tries op, `except TypeError: return NotImplemented`; reverse delegates (`return self + other`) when commutative. Trade-offs: reverse unnecessary if forward is same-type only.

### Immutable vs mutable operator
When to use: choosing __add__ vs __iadd__. How: __add__ returns new instance; __iadd__ mutates, accepts any iterable, returns self. Trade-offs: immutables skip __iadd__.

# Ch 17-20

### Generator as __iter__
When to use: a class exists to expose its items for iteration.
How: define `__iter__` with `yield` (or `yield from self.items`, or return a genexp); source lazily (`re.finditer`).
Trade-offs: loses nothing vs a hand-written Iterator class; each `iter()` call gives fresh state.

### Recursive yield from tree traversal
When to use: trees, nested structures, directory-like data.
How: `def tree(node, level=0): yield node, level; for child in children(node): yield from tree(child, level+1)`; base case = no children.
Trade-offs: limited by recursion limit (~1000).

### Stdlib generator pipelines
When to use: filter/map/merge/reshape streams lazily.
How: compose `islice`, `takewhile`, `chain`, `groupby` (pre-sorted), `tee`, `accumulate`, `starmap`.
Trade-offs: iterators are one-shot; `tee` buffers; infinite sources need bounding.

### Coroutine with sentinel return
When to use: (legacy) consumer that returns an aggregate.
How: loop on `x = yield`; break on sentinel; `return Result`; retrieve via `StopIteration.value` or `yield from`.
Trade-offs: cumbersome; use native coroutines for real work.

### Context manager via generator
When to use: paired setup/teardown.
How: `@contextmanager def cm(): setup; try: yield value; finally: teardown`.
Trade-offs: default suppresses exceptions; must guard yield.

### Context manager class
When to use: need reuse state or explicit exception handling in `__exit__`.
How: `__enter__` returns the `as` object; `__exit__(exc_type, exc_value, tb)` returns True to suppress.
Trade-offs: more boilerplate than generator form.

### match/case interpreter
When to use: language/DSL/rule processors.
How: one `case` per grammar form with sequence patterns, guards (`if body`), `|` alternatives, `case _` error.
Trade-offs: guards needed to separate keyword forms from calls; Norvig suggests one case per keyword with internal checks for better errors.

### try/except/else; for/else
When to use: keep `try` narrow; search loops with not-found handling.
How: `try: risky() except E: ... else: follow_up()`; `for ...: if hit: break; else: not_found()`.
Trade-offs: `else` wording confusing ("then").

### Thread + Event signalling
When to use: stop a background thread.
How: worker loops `if done.wait(timeout): break`; main calls `done.set()`; `join()`.
Trade-offs: no way to kill threads externally.

### asyncio supervisor
When to use: run concurrent tasks in coroutines.
How: `asyncio.run(supervisor())`; inside, `create_task(...)`, `await ...`, `task.cancel()`.
Trade-offs: any blocking call stalls everything.

### Worker queues with poison pills
When to use: manual process pool.
How: jobs queue + results queue; N workers loop on `jobs.get()`; enqueue one sentinel per worker; collect until N done-markers; include input in result.
Trade-offs: complex; prefer ProcessPoolExecutor.

### Executor.map
When to use: same function over many inputs, ordered output.
How: `with ThreadPoolExecutor() as ex: list(ex.map(fn, items))`.
Trade-offs: ordered, head-of-line blocking.

### submit + as_completed with dict
When to use: progress, per-task errors, out-of-order handling.
How: `d = {ex.submit(fn, x): x for x in xs}`; `for f in as_completed(d): f.result()`; `d[f]` for context.
Trade-offs: more code than `map`.

# Ch 21-24

### Run blocking work off the event loop
When to use: file I/O, blocking libs, CPU work inside async code.
How: `await asyncio.to_thread(fn, *args, **kw)` (3.9+) or `loop.run_in_executor(None, fn, *args)`; `ProcessPoolExecutor` created once in supervisor for CPU-bound.
Trade-offs: threads cannot be cancelled; shutdown can hang; sometimes thread pool beats async drivers (Motor).

### Semaphore throttling
When to use: limit concurrent requests in async clients.
How: `semaphore = asyncio.Semaphore(n)` in supervisor, pass to workers, `async with semaphore:` around only the I/O call.
Trade-offs: keep hold time minimal; BoundedSemaphore guards against over-release.

### Supervisor + as_completed progress
When to use: need results as they finish (progress bars, early error handling).
How: build coroutine list, `for coro in asyncio.as_completed(coros): result = await coro`; wrap iterator with tqdm; extract context from the exception since awaitables cannot be mapped back.
Trade-offs: `gather` simpler when all results needed in order.

### Async generator and @asynccontextmanager
When to use: stream results as they arrive; write async context managers without a class.
How: `async def` + `yield`, consume with `async for`; decorate with `@asynccontextmanager` (before yield = `__aenter__`, after = `__aexit__`).
Trade-offs: no return values, not awaitable.

### Wrap blocking API in a coroutine facade
When to use: library API that must look async but core is threaded.
How: hide `run_in_executor` inside coroutine methods.
Trade-offs: consistent interface; cancellation is fake.

### __getattr__ façade for nested data (FrozenJSON)
When to use: read-only exploration of JSON-like data with dotted access.
How: `__getattr__` delegates to the inner dict then wraps value recursively; `__dir__` for autocompletion; escape keywords with trailing `_`.
Trade-offs: key/method shadowing; prefer custom mapping with `__getitem__` for untrusted keys.

### __new__ as a factory
When to use: constructor should return different types (lists, scalars, instance).
How: `__new__(cls, arg)` returns `super().__new__(cls)` or other object; `__init__` is skipped if not instance of cls.
Trade-offs: surprising; use a classmethod `build` for clarity.

### Computed property with caching
When to use: derived/linked data expensive to compute.
How: `@cached_property`; or `@property` stacked on `@cache` when the method needs a same-named attribute or `__slots__`; raw data via `self.__dict__['name']`.
Trade-offs: cached_property defeats key sharing, no `__slots__`; handmade `hasattr` caches are racy.

### Validated descriptor with __set_name__
When to use: same validation across many attributes/classes.
How: `Validated(abc.ABC)` with `__set_name__`, `__set__` calling abstract `validate` and storing result in `instance.__dict__`; subclasses implement `validate`.
Trade-offs: set-only descriptors keep reads fast; add `__get__` only if storage name differs.

### Class builder via __init_subclass__ (Checked)
When to use: class statement with annotations should be enhanced at creation.
How: `__init_subclass__(subclass)` replaces annotations with `Field` descriptors; call `super().__init_subclass__()`.
Trade-offs: cannot set `__slots__`; hierarchy conflicts.

### Class decorator builder (@checked)
When to use: same enhancement without base class or metaclass interference.
How: function takes cls, `setattr`s Fields and methods, returns cls.
Trade-offs: runs even later; cannot set `__slots__`.

### Metaclass __new__ to configure __slots__
When to use: need namespace changes before `type.__new__` (slots, defaults).
How: subclass `type`, edit `cls_dict`, call `super().__new__(meta_cls, name, bases, cls_dict)`; expose via plain base class with `metaclass=`.
Trade-offs: one metaclass per hierarchy; hard to maintain.

### __prepare__ + __missing__ namespace hack
When to use: bare names in a class body create entries (AutoConst).
How: `__prepare__` returns a dict subclass with `__missing__`; skip dunder keys.
Trade-offs: clever, framework-level only.

