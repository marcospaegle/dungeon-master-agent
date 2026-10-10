# Chapter 18: with, match, and else Blocks

## Core Idea
Three underused control-flow features: `with` (context managers = the complement of the subroutine: factor out setup/teardown "bread"), `match/case` (sequence patterns express a language grammar, shown via Norvig's `lis.py` interpreter), and `else` on `for`/`while`/`try` ("then", not "otherwise").

## Frameworks Introduced
- **Context manager protocol**: "The context manager interface consists of the `__enter__` and `__exit__` methods."
  - When to use: any paired before/after operation (resources, locks, transactions, patching, temporary state), not only closing files.
  - How: `with expr as target:` -> `expr` evaluates to the manager; `target` is bound to what `__enter__` returns (not the manager); on any exit (return, exception, `sys.exit`) `__exit__(exc_type, exc_value, traceback)` is called on the *manager*. Return truthy from `__exit__` to suppress the exception; `None`/falsy propagates it.
  - Why it works / failure mode: `with` blocks do not create a new scope. The three `__exit__` args equal `sys.exc_info()` in `finally`.
- **@contextmanager recipe**: one `yield` splits a generator: before = `__enter__`, yielded value = `as` target, after = `__exit__`.
  - When to use: leaner than a class with two methods.
  - How: decorate generator; wrap `yield` in `try/finally` (or `except`) to guarantee cleanup.
  - Why it works / failure mode: the decorator's `__exit__` calls `gen.throw(exc)` at the yield; **inverted default**: it assumes any exception sent in was handled and suppresses it. Without try/finally around the yield, an exception in the with-body skips cleanup.
- **Hettinger's "factoring out the bread"**: subroutines factor out the filling (A;B;C and P;B;Q -> B); `with` factors out the bread (shared before/after around varying filling).
- **Grammar as sequence patterns (lis.py)**: S-expressions parse to nested Python lists; each Scheme form maps to one `case` pattern in `evaluate`.
  - How: `match exp:` with cases for atoms (`int(x) | float(x)`, `Symbol(var)`), special forms (`['quote', x]`, `['if', t, c, a]`, `['lambda', [*parms], *body] if body`, `['define', ...]`, `['set!', ...]`), function call `[func_exp, *args] if func_exp not in KEYWORDS`, catch-all `case _: raise SyntaxError(...)`.
  - Why it works / failure mode: guard on the function-call case is needed because `[func_exp, *args]` matches any non-empty list including malformed keyword forms.
- **else-block rules**: `for`: runs only if loop completes without `break`. `while`: runs only if condition became falsy (not `break`). `try`: runs only if no exception in the try block. All skipped on return/break/continue/exception jumping out.
- **EAFP vs LBYL**: Easier to Ask Forgiveness than Permission (try/except, assume valid) vs Look Before You Leap (if-tests; racy in threads).

## Key Concepts
- **context manager**: object with `__enter__`/`__exit__` controlling a `with`, as iterators control `for`.
- **exc_type, exc_value, traceback**: the three args of `__exit__`; all `None` on normal exit.
- **ExitStack**: enters a variable number of context managers; exits in LIFO order.
- **ContextDecorator**: lets a context manager also decorate a function; `@contextmanager` generators get this for free.
- **OR-pattern**: `a | b` inside `case`; all subpatterns must bind the same variables; does not call `__or__`; can appear in subpatterns (`['lambda' | 'λ', ...]`).
- **S-expression / Atom / Symbol / Expression**: prefix-notation syntax; `Symbol = str`, `Atom = float | int | Symbol`, `Expression = Atom | list`.
- **Environment**: `ChainMap` subclass with `change()` that updates the first mapping where key exists (needed for `set!`); like `nonlocal`.
- **Procedure**: class implementing a closure (params, body, env); `__call__` builds `Environment(dict(zip(parms, args)), self.env)`.
- **special form / reserved keyword**: needed for specialized evaluation rules (quote, lambda), control flow (if), environment management (define, set!).
- **proper tail call (PTC)**: Scheme feature making recursion-as-iteration viable; CPython deliberately lacks it (debuggability).

## Mental Models
- Use `with` when you have paired operations around a block, not just resource release.
- Think of the `try` body as containing *only* the statements that can raise the expected exception; put follow-up code in `else`.
- Think of `for/else` as "for ... then": run loop, then do this unless you broke out.
- Use `case _:` as the `else` of `match` (no `else` clause exists).
- Use a `nonlocal x` <-> `(set! x ...)` analogy: both update a variable in an enclosing scope; Scheme `define` always creates local.

## Anti-patterns
- **Class-based manager for trivial setup/teardown**: use `@contextmanager`.
- **No try/finally around `yield` in `@contextmanager`**: cleanup skipped on error ("unavoidable price").
- **Putting `after_call()` inside the `try` block**: masks errors from the wrong call; use `else`.
- **Hand-nesting `with` / manually stacking N managers**: use parenthesized `with (...)` (3.10) or `ExitStack`.
- **Sentinel control flags in loops**: `for/else` removes them.
- **`if key in m: return m[key]` in threaded code**: LBYL race; use EAFP or locks.
- **`__exit__` returning truthy by accident**: silently swallows exceptions.

## Code Examples
```python
class LookingGlass:
    def __enter__(self):
        self.original_write = sys.stdout.write
        sys.stdout.write = self.reverse_write
        return 'JABBERWOCKY'
    def reverse_write(self, text):
        self.original_write(text[::-1])
    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout.write = self.original_write
        if exc_type is ZeroDivisionError:
            print('Please DO NOT divide by zero!')
            return True
```
- **What it demonstrates**: `__enter__` return value vs manager; `__exit__` returning True suppresses exception.

```python
@contextlib.contextmanager
def looking_glass():
    original_write = sys.stdout.write
    def reverse_write(text):
        original_write(text[::-1])
    sys.stdout.write = reverse_write
    msg = ''
    try:
        yield 'JABBERWOCKY'
    except ZeroDivisionError:
        msg = 'Please DO NOT divide by zero!'
    finally:
        sys.stdout.write = original_write
        if msg:
            print(msg)
```
- **What it demonstrates**: generator-based manager with exception handling and guaranteed restore.

```python
with (
    CtxManager1() as example1,
    CtxManager2() as example2,
):
    ...
```
- **What it demonstrates**: Python 3.10 parenthesized context managers.

```python
for item in my_list:
    if item.flavor == 'banana':
        break
else:
    raise ValueError('No banana flavor found!')

try:
    dangerous_call()
except OSError:
    log('OSError...')
else:
    after_call()
```

```python
class Environment(ChainMap[Symbol, Any]):
    def change(self, key: Symbol, value: Any) -> None:
        for map in self.maps:
            if key in map:
                map[key] = value
                return
        raise KeyError(key)

class Procedure:
    def __init__(self, parms, body, env):
        self.parms = parms; self.body = body; self.env = env
    def __call__(self, *args):
        local_env = dict(zip(self.parms, args))
        env = Environment(local_env, self.env)
        for exp in self.body:
            result = evaluate(exp, env)
        return result
```

## Reference Tables
| contextlib tool | Purpose |
|---|---|
| `closing` | context manager from object with `close()` |
| `suppress` | temporarily ignore listed exceptions |
| `nullcontext` | no-op stand-in for conditional code (3.7) |
| `redirect_stdout/stderr` | temporary replacement of stdout/stderr |
| `@contextmanager` | generator -> context manager |
| `AbstractContextManager` | ABC for subclassing |
| `ContextDecorator` | manager usable as decorator |
| `ExitStack` | variable number of managers, LIFO exit |
| `AbstractAsyncContextManager`, `@asynccontextmanager`, `AsyncExitStack` | async variants (3.7) |

| lis.py case | Subject | Action |
|---|---|---|
| `int(x) \| float(x)` | number | return as is |
| `Symbol(var)` | identifier | `env[var]` |
| `['quote', x]` | quote form | return x unevaluated |
| `['if', test, cons, alt]` | if form | evaluate test, then branch |
| `['lambda', [*parms], *body] if body` | lambda | `Procedure(parms, body, env)` |
| `['define', Symbol(name), value_exp]` | define var | `env[name] = evaluate(...)` |
| `['define', [Symbol(name), *parms], *body] if body` | define function | `env[name] = Procedure(...)` |
| `['set!', Symbol(name), value_exp]` | assignment | `env.change(name, ...)` |
| `[func_exp, *args] if func_exp not in KEYWORDS` | call | eval func and args, `proc(*values)` |
| `_` | anything else | `SyntaxError(lispstr(exp))` |

## Worked Example
`(define (make-averager) (define count 0) (define total 0) (lambda (new-value) (set! count (+ count 1)) (set! total (+ total new-value)) (/ total count)))`. `avg = (make-averager)`; `(avg 10)` -> 10.0, `(avg 11)` -> 10.5, `(avg 15)` -> 12.0. The lambda becomes a `Procedure` closing over the env holding `count` and `total`; `set!` calls `Environment.change` to mutate the outer bindings, exactly like `nonlocal` in Ch 9.

## Key Takeaways
1. `with` is not just for closing files: it factors out any setup/teardown pair.
2. `as` target = return value of `__enter__`; `__exit__` is called on the manager; truthy return swallows the exception.
3. Use `@contextmanager` for brevity but always guard the `yield` with `try/finally`; its default suppresses exceptions.
4. Check `contextlib` before writing your own manager.
5. `match/case` sequence patterns map grammar rules to code with great clarity; guards disambiguate overlapping patterns.
6. `else` on loops/try means "then": use it to drop flags and to keep `try` bodies minimal (EAFP).
7. CPython has no PTC by design; recursion limit ~1000 is the main constraint on functional style.

## Connects To
- **Ch 2**: pattern matching sequences (`evaluate` earlier shown with if/elif).
- **Ch 9**: closures, `nonlocal`, running average (the Procedure class is a closure).
- **Ch 17**: generators power `@contextmanager`.
- **Ch 21**: `async with`, `@asynccontextmanager`.
