# Chapter 9: Decorators and Closures

## Core Idea
A decorator is a callable that takes a function and returns it or replaces it with another callable; it runs at import time. Writing real decorators requires closures (functions that keep bindings of free variables) and, for rebinding, `nonlocal`.

## Frameworks Introduced
- **Three essential facts about decorators**: (1) a decorator is a function or another callable; (2) it may replace the decorated function with a different one; (3) decorators are executed immediately when a module is loaded.
  - When to use: to "mark" or wrap functions (registration, timing, caching, dispatch).
  - How: `@decorate def target(): ...` is exactly `target = decorate(target)`.
  - Failure mode: forgetting the decorator returns a function; the name is rebound to whatever is returned (`None` if you forget `return`).
- **Variable lookup logic (compile-time rules)**: decided when the function is compiled.
  - If `global x`: x is the module global, assigned there.
  - If `nonlocal x`: x is the local of the nearest enclosing function defining it.
  - If x is a parameter or assigned in the body: x is local.
  - If x is only referenced: search enclosing function scopes, then module globals, then `__builtins__.__dict__`.
  - Why it matters: assignment anywhere in the body makes the name local for the whole body (hence `UnboundLocalError`).
- **Decorator factory (parameterized decorator)**: a function taking the arguments and returning the actual decorator. Three nesting levels: factory -> `decorate(func)` -> `wrapper(*args)`.
  - When to use: decorator needs configuration (`@register(active=False)`, `@clock('{name}')`).
  - How: `@factory(args)` evaluates `factory(args)` first, then applies the result to the function. Even with no args you must call it: `@register()`.
  - Alternative: class with `__init__(self, config)` and `__call__(self, func)`; better for non-trivial decorators (Regebro, Dumpleton's `wrapt`).
- **Single-dispatch generic function** (`functools.singledispatch`): a group of functions doing the same operation depending on the type of the first argument.
  - When to use: need modular, extensible per-type behavior, including types you cannot edit; replaces if/elif type chains.
  - How: decorate base with `@singledispatch` (catch-all for `object`), then `@base.register` on functions whose first parameter has a type hint; the most specific matching type wins regardless of order. Names of specialized functions irrelevant (use `_`).
  - Register ABCs (`numbers.Integral`, `abc.Sequence`), not concrete types (`int`, `list`).
  - Not Java-style overloading; the advantage is that each module can register its own implementations.

## Key Concepts
- **Import time vs runtime**: decorators run at import time (right after def); decorated function bodies run only when called.
- **Registration decorator**: returns the original function unchanged after adding it to a registry (web routes, strategies).
- **Closure**: function with extended scope that includes nonglobal variables referenced in its body but defined in an enclosing function; retains bindings of free variables after the outer function returns.
- **Free variable**: variable not bound in the local scope; its binding lives in `func.__closure__` (cells; `.cell_contents`), names in `func.__code__.co_freevars`.
- **`nonlocal`**: declares a name as free even when assigned in the function so rebinding changes the closure binding. Needed for immutables (`count += 1`); mutable lists need none.
- **`functools.wraps`**: decorator that copies `__name__`, `__doc__` etc. from wrapped to wrapper; use in every real decorator.
- **Memoization** (`functools.cache`, 3.9): saves results by arguments; all arguments must be hashable (dict keys).
- **`lru_cache`**: bounded memoization; `maxsize=128` default (power of 2 best), `typed=False`; `maxsize=None` disables LRU = `@cache`.
- **Stacked decorators**: `@alpha @beta def f` == `f = alpha(beta(f))`; beta applied first.
- **Dynamic vs lexical scope**: Python is lexical (free variables resolved where defined); dynamic scope resolves them where called and breaks function opacity.

## Mental Models
- Think of `@d` as pure syntactic sugar: `f = d(f)`. Anything you can do with the call form (metaprogramming at runtime) works.
- Think of a closure as a function carrying a private backpack of the variables it captured.
- Use `@cache` in short-lived scripts; use `@lru_cache(maxsize=N)` in long-running processes.
- Python decorator vs GoF Decorator: the inner returned function conforms to the component's interface (same arguments) and forwards calls, so decorators stack; but for the actual GoF pattern, classes are usually better.

## Anti-patterns
- **Assigning to a captured immutable without `nonlocal`**: `count += 1` makes `count` local -> `UnboundLocalError`.
- **Decorator without `functools.wraps`**: masks `__name__`/`__doc__` (`factorial.__name__ == 'clocked'`).
- **Wrapper accepting only `*args`**: breaks keyword calls; use `*args, **kwargs`.
- **Unbounded `@cache` in long-running processes**: can consume all memory.
- **Caching functions with unhashable args**: raises `TypeError`.
- **Registering `@singledispatch` against `int`/`list`**: use ABCs to support compatible types. `Union` hints are not supported by `register`.
- **Forgetting parentheses on a factory** (`@register` vs `@register()`): passes the function as the config argument.
- **Obeying linters that discourage `**locals()`/dynamic features blindly**: know when to ignore them (author's view).

## Code Examples
```python
import time
import functools

def clock(func):
    @functools.wraps(func)
    def clocked(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        name = func.__name__
        arg_lst = [repr(arg) for arg in args]
        arg_lst.extend(f'{k}={v!r}' for k, v in kwargs.items())
        arg_str = ', '.join(arg_lst)
        print(f'[{elapsed:0.8f}s] {name}({arg_str}) -> {result!r}')
        return result
    return clocked
```
- **What it demonstrates**: well-behaved decorator: closure over `func`, `wraps`, keyword support, returns original result.

```python
def make_averager():
    count = 0
    total = 0
    def averager(new_value):
        nonlocal count, total
        count += 1
        total += new_value
        return total / count
    return averager
```
- **What it demonstrates**: `nonlocal` to rebind free variables of immutable type.

```python
registry = set()

def register(active=True):          # decorator factory
    def decorate(func):             # the actual decorator
        if active:
            registry.add(func)
        else:
            registry.discard(func)
        return func
    return decorate

@register(active=False)
def f1(): ...
@register()
def f2(): ...
```
- **What it demonstrates**: parameterized registration; `register()(f3)` is the non-@ call form.

```python
@singledispatch
def htmlize(obj: object) -> str:
    content = html.escape(repr(obj))
    return f'<pre>{content}</pre>'

@htmlize.register
def _(text: str) -> str: ...
@htmlize.register
def _(seq: abc.Sequence) -> str: ...
@htmlize.register
def _(n: numbers.Integral) -> str: ...
@htmlize.register(decimal.Decimal)   # no-hint form, works since 3.4
@htmlize.register(float)             # register returns undecorated fn: stackable
def _(x) -> str: ...
```
- **What it demonstrates**: generic function; `bool` (an Integral subtype) can get its own more specific implementation.

```python
class clock:                         # class-based parameterized decorator
    def __init__(self, fmt=DEFAULT_FMT):
        self.fmt = fmt
    def __call__(self, func):
        def clocked(*_args):
            ...
            print(self.fmt.format(**locals()))
            return _result
        return clocked
```

## Reference Tables
| Tool | Version | Notes |
|---|---|---|
| `functools.cache` | 3.9 | unbounded `lru_cache(maxsize=None)` |
| `@lru_cache` bare (no parens) | 3.8 | before 3.8 must write `@lru_cache()` |
| `singledispatch` | 3.4 (type hints 3.7) | first-arg dispatch only (multiple dispatch = more args) |
| built-in method decorators | | `property`, `classmethod`, `staticmethod` |

| Scope case | Result |
|---|---|
| read undeclared name, found nowhere | `NameError` |
| read name later assigned in same function | `UnboundLocalError` |
| `global b` then assign | rebinds module global |
| `nonlocal x` then assign | rebinds closure cell |

## Worked Example
Fibonacci: the naive recursive `@clock` version calls `fibonacci(1)` 8 times for n=6 (fibonacci(30): 2,692,537 calls, 12.09s). Stack `@functools.cache` above `@clock`: `fibonacci = cache(clock(fibonacci))`; each n is computed once (31 calls, 0.00017s). Cache wraps clock, so repeated calls are intercepted before reaching the timer.

## Key Takeaways
1. A decorator is `f = d(f)`; it executes at import, the decorated function at call time.
2. Python decides local vs nonlocal vs global at compile time from assignments; use `nonlocal`/`global` to rebind.
3. Closures keep free-variable bindings in `__closure__` cells after the outer function returns.
4. Always use `functools.wraps` and `*args, **kwargs` in wrappers.
5. Parameterized decorators = factory returning decorator; class-based `__call__` is cleaner for complex ones.
6. Prefer `lru_cache(maxsize=...)` in servers; `cache` for scripts; args must be hashable.
7. Register `singledispatch` implementations on ABCs for broad, extensible type support.

## Connects To
- **Ch 7/8**: functions as first-class objects, type hints used by singledispatch.
- **Ch 10**: registration decorator builds the Strategy `promos` list.
- **Ch 13**: ABCs and Protocols used with singledispatch.
- **Ch 22/23**: `property`, descriptors; **Ch 24**: class decorators and metaprogramming.
