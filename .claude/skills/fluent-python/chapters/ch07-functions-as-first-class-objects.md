# Chapter 7: Functions as First-Class Objects

## Core Idea
Python functions are objects that can be created at runtime, assigned, passed, and returned, which enables a functional style (higher-order functions, `operator`, `functools.partial`) even though Python is not a functional language by design.

## Frameworks Introduced
- **First-class object (definition)**: a program entity that can be (1) created at runtime, (2) assigned to a variable or data structure element, (3) passed as an argument, (4) returned as a result. All Python functions qualify ("first-class functions" implies an elite, but in Python all are).
- **Modern replacements for map/filter/reduce**:
  - When to use: replace `map`/`filter` with listcomp/genexp; replace `reduce(add, ...)` with `sum`; use `all`/`any` for boolean reduction.
  - How: `[factorial(n) for n in range(6) if n % 2]` instead of `list(map(factorial, filter(lambda n: n % 2, range(6))))`.
  - Why: more readable, no `lambda`. `reduce` moved to `functools` in Python 3; `apply` removed (use `fn(*args, **kwargs)`).
- **Fredrik Lundh's lambda refactoring recipe** (when a lambda is hard to read):
  1. Write a comment explaining what the lambda does.
  2. Study the comment and think of a name capturing its essence.
  3. Convert the lambda to a `def` using that name.
  4. Remove the comment.
- **The Nine Flavors of Callable Objects** (test with `callable()`): see Reference Tables.
- **Parameter kinds**: positional-only (`/`), positional-or-keyword, `*args`, keyword-only (after `*`), `**kwargs`.

## Key Concepts
- **Higher-order function**: takes a function as argument or returns one (`sorted(key=)`, `map`, `filter`, `functools.partial`).
- **Anonymous function**: `lambda`; body is a pure expression only (no `while`, `try`, `=`; `:=` allowed but a smell).
- **`__call__`**: instance method making instances callable; good for function-like objects with internal state across calls and for decorators.
- **Keyword-only parameter**: parameter after `*args` or a bare `*`; can be mandatory (no default).
- **Positional-only parameter**: parameter before `/` (3.8+; syntax error before), like built-in `divmod(a, b)`.
- **`operator.itemgetter` / `attrgetter` / `methodcaller`**: factories that build functions replacing trivial lambdas. `attrgetter` supports dotted names (`'coord.lat'`); multiple args return tuples.
- **`functools.partial`**: freezes some positional/keyword arguments of a callable and returns a new callable (`.func`, `.args`, `.keywords`). `partialmethod` is its method variant.
- **Reducing built-ins**: `sum`, `all` (`all([])` is `True`), `any` (`any([])` is `False`).

## Mental Models
- Use a listcomp/genexp before `map`/`filter`; in Python 3, `map`/`filter` return lazy iterators, so the direct substitute is a genexp.
- Use `lambda` only as an argument to a higher-order function; otherwise `def`.
- Use a `__call__` class when you need state kept between calls (BingoCage, memoizing decorator); closures are the functional alternative (Ch 9).
- Use `partial` to adapt a function to a callback API requiring fewer arguments.

## Anti-patterns
- **Complex lambdas**: unreadable and no names in stack traces; refactor with Lundh's recipe.
- **`lambda a, b: a*b` / `lambda fields: fields[1]`**: use `operator.mul` / `itemgetter(1)`.
- **`reduce` for summation**: use `sum`.
- **Using `isinstance` guesses to detect callables**: use `callable()`; generators/coroutines are callable but return objects needing further processing.
- **Mutable state sneaking via default args**: see Ch 6.

## Code Examples
```python
def tag(name, *content, class_=None, **attrs):
    """Generate one or more HTML tags"""
    if class_ is not None:
        attrs['class'] = class_
    attr_pairs = (f' {attr}="{value}"'
                  for attr, value in sorted(attrs.items()))
    attr_str = ''.join(attr_pairs)
    if content:
        elements = (f'<{name}{attr_str}>{c}</{name}>'
                    for c in content)
        return '\n'.join(elements)
    else:
        return f'<{name}{attr_str} />'
```
- **What it demonstrates**: `*content` collects extra positionals as tuple; `class_` is keyword-only; `**attrs` collects other keywords; `tag(**my_tag)` unpacks a dict (a `'class'` string key is fine). Positional-only variant: `def tag(name, /, *content, class_=None, **attrs)`.

```python
class BingoCage:
    def __init__(self, items):
        self._items = list(items)
        random.shuffle(self._items)
    def pick(self):
        try:
            return self._items.pop()
        except IndexError:
            raise LookupError('pick from empty BingoCage')
    def __call__(self):
        return self.pick()
```
- **What it demonstrates**: callable instance with state; copies input to avoid side effects.

```python
>>> def f(a, *, b): return a, b
>>> f(1, b=2)
(1, 2)
>>> from functools import partial
>>> picture = partial(tag, 'img', class_='pic-frame')
>>> picture(src='wumpus.jpeg')
'<img class="pic-frame" src="wumpus.jpeg" />'
>>> nfc = functools.partial(unicodedata.normalize, 'NFC')
```
- **What it demonstrates**: bare `*` for keyword-only; `partial` freezing positional and keyword args.

```python
from operator import itemgetter, attrgetter, methodcaller
sorted(metro_data, key=itemgetter(1))
attrgetter('name', 'coord.lat')
methodcaller('replace', ' ', '-')
```

## Reference Tables
The nine callable types (Python 3.9 data model):

| Flavor | Notes |
|---|---|
| User-defined functions | `def` or `lambda` |
| Built-in functions | C, e.g. `len`, `time.strftime` |
| Built-in methods | C, e.g. `dict.get` |
| Methods | functions defined in a class body |
| Classes | runs `__new__` then `__init__`; no `new` operator |
| Class instances | if class defines `__call__` |
| Generator functions | have `yield`; return generator |
| Native coroutine functions | `async def` (3.5); return coroutine |
| Asynchronous generator functions | `async def` + `yield` (3.6) |

`operator` module: arithmetic function equivalents (`mul`, `add`, ...); `i`-prefixed names are augmented assignment (`iadd`); also `itemgetter`, `attrgetter`, `methodcaller`.

## Worked Example
Rhyme-index sorting: `sorted(fruits, key=reverse)` where `reverse = lambda word: word[::-1]` (inline: `key=lambda word: word[::-1]`). Items are unchanged; only the reversed spelling is the sort key, grouping the berries together. Factorial: `reduce(lambda a, b: a*b, range(1, n+1))` becomes `reduce(mul, range(1, n+1))` with `from operator import mul`.

## Key Takeaways
1. Functions are instances of `function`; they have `__doc__`, can be aliased, stored, passed and returned.
2. Prefer comprehensions/generator expressions and `sum`/`all`/`any` over `map`/`filter`/`reduce`.
3. `lambda` is for short throwaway callbacks; otherwise name the function.
4. There are nine callable flavors; use `callable()`.
5. Keyword-only (`*`) and positional-only (`/`) parameters give precise API control.
6. `operator` factories and `functools.partial` replace many lambdas and adapt signatures.

## Connects To
- **Ch 6**: parameter aliasing and mutable defaults.
- **Ch 8**: annotating `*args`, `**kwargs`, `Callable`.
- **Ch 9**: closures and decorators (`functools.cache`, `singledispatch`).
- **Ch 10**: first-class functions simplify design patterns.
- **Ch 17/21**: generators and coroutines as callable flavors.
