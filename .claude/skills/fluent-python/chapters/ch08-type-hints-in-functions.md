# Chapter 8: Type Hints in Functions

## Core Idea
Python uses a gradual type system: type hints are optional, unenforced at runtime, and checked statically (Mypy etc.). It mixes duck typing with nominal typing, and `Protocol` adds static duck typing. Hints help most in large codebases and do not replace tests.

## Frameworks Introduced
- **Gradual typing** (PEP 484): a gradual type system (1) is optional (no warnings for unhinted code; checker assumes `Any`), (2) does not catch type errors at runtime, (3) does not enhance performance.
  - When to use: add hints function by function as tests/CI justify; leave out hints that complicate APIs. Don't chase 100% coverage.
  - How (Mypy workflow): run `mypy` (unannotated functions ignored); add `--disallow-incomplete-defs` to force full annotation of any function you start annotating; add return type first, then params; use `--disallow-untyped-defs` for strictness; save options in `mypy.ini`; annotate tests with `-> None` or Mypy skips them.
  - Failure mode: forcing coverage yields thoughtless hints and clumsy APIs.
- **Types are defined by supported operations**: a type is a set of values plus the operations you can apply (PEP 483). `double(x: abc.Sequence)` with `x * 2` is rejected since `Sequence` has no `__mul__`.
- **Duck typing vs nominal typing**:
  - Duck: objects have types, variables don't; checked at runtime; flexible, more runtime errors.
  - Nominal: variables and objects have types; enforced statically by reading source; may reject code that runs (`alert_bird(daffy)`), catches errors early.
  - Static duck typing = `typing.Protocol` (structural subtyping, PEP 544).
- **Subtype-of vs consistent-with** (gradual typing):
  1. If T2 is subtype-of T1, T2 is consistent-with T1 (Liskov Substitution, "behavioral subtyping").
  2. Every type is consistent-with `Any`.
  3. `Any` is consistent-with every type.
  - Exception ("practicality beats purity"): `int` consistent-with `float` consistent-with `complex`.
- **Postel's law for annotations**: "Be conservative in what you send, be liberal in what you accept": parameters use abstract types (`Mapping`, `Sequence`, `Iterable`), returns use concrete types (`list[str]`).
- **Choosing a numeric annotation**: the `numbers` ABCs (numeric tower) are not supported statically. Use concrete `int`/`float`/`complex`; or a Union like `Union[float, Decimal, Fraction]`; or numeric protocols (`SupportsFloat`).
- **Types usable in annotations**: `Any`, simple classes, `Optional`/`Union`, generic collections, tuples (3 forms), mappings, ABCs, `Iterable`, `TypeVar`, `Protocol`, `Callable`, `NoReturn`.

## Key Concepts
- **`Any`**: dynamic type; top and bottom of hierarchy; implied for unannotated code. Unlike `object`, which supports few operations (`x * 2` on `object` is an error).
- **`Optional[T]`**: shortcut for `Union[T, None]`; does not make a parameter optional (the default value does). 3.10: `str | None`.
- **`Union`**: needs 2+ types, flattens when nested; `Union[int, float]` is redundant (use `float`).
- **Generic collection**: `list[str]`, `dict[str, set[str]]`; `stuff: list` == `list[Any]`.
- **Type alias**: `FromTo = tuple[str, str]`; 3.10: `FromTo: TypeAlias = tuple[str, str]`.
- **TypeVar**: introduces a type variable name (`T = TypeVar('T')`); the same T in a signature binds to the same type. Needed because PEP 484 changed only `typing`, not syntax.
- **Restricted TypeVar**: `TypeVar('NumberT', float, Decimal, Fraction)`; resolves to one of the listed types.
- **Bounded TypeVar**: `TypeVar('HashableT', bound=Hashable)`; resolves to the inferred type if consistent-with the bound.
- **`AnyStr`**: `TypeVar('AnyStr', bytes, str)`.
- **Protocol**: `typing.Protocol` subclass defining methods; type T is consistent-with it if T implements all methods with matching signatures; no inheritance/registration needed.
- **Variance**: `Callable` is covariant in return type, contravariant in parameter types. Most parameterized generics (e.g., `list[float]`) are invariant.
- **Stub file / Typeshed**: `.pyi` files with signatures only (like C headers); stdlib hints live in Typeshed.
- **`NoReturn`**: return type of functions that never return (e.g., `sys.exit`).
- **Inference**: type checker guessing types (`x = len(s) * 10` is `int`).

## Mental Models
- Use `Iterable` for parameters you only loop over (accepts generators); use `Sequence` when you need `len()`/indexing. Both are too vague as return types.
- Use a `TypeVar` when return type must follow input type (`sample`, `mode`, `top`); `Union` is wrong for "same type out as in".
- Use `bound=` when you need a capability (hashable, `__lt__`); use restricted when only specific types are valid.
- Think of `Callable[[Params], Ret]` substitution: a callback may return a narrower type and accept a wider parameter type.

## Anti-patterns
- **`def hex2rgb(color=str)`**: that's a default value, not an annotation; Mypy's message is unhelpful.
- **Returning `Union` types**: forces callers to check type at runtime (only OK in cases like `parse_token`).
- **Concrete `dict[str,int]` parameter**: rejects `UserDict` (a sibling, not subclass, of `dict`); use `Mapping` / `MutableMapping`.
- **`Optional` without `= None`**: parameter remains required at runtime.
- **`Iterable[Hashable] -> Hashable`**: return is useless (only `hash()` allowed); use bounded TypeVar.
- **Expecting types to enforce value constraints**: cannot express "int > 0" or "6-12 ASCII letters"; not for business logic.
- **Mandating hints everywhere**: lose `config(**settings)`, metaprogramming, properties, descriptors; type checkers lag Python releases; false positives and negatives exist.
- **Spaces style**: `name: str`, and ` = ` around defaults when annotated (use flake8 and blue).

## Code Examples
```python
def show_count(count: int, singular: str, plural: str = '') -> str:
    if count == 1:
        return f'1 {singular}'
    count_str = str(count) if count else 'no'
    if not plural:
        plural = singular + 's'
    return f'{count_str} {plural}'
```
- **What it demonstrates**: type-driven development: write a failing test with 3rd arg, Mypy says "Too many arguments", then add the optional parameter.

```python
from collections.abc import Iterable
from typing import TypeVar, Protocol, Any

class SupportsLessThan(Protocol):
    def __lt__(self, other: Any) -> bool: ...

LT = TypeVar('LT', bound=SupportsLessThan)

def top(series: Iterable[LT], length: int) -> list[LT]:
    ordered = sorted(series, reverse=True)
    return ordered[:length]
```
- **What it demonstrates**: static duck typing: `str`, `tuple`, `float` qualify without registration; `top(list_of_object, 3)` errors: `Value of type variable "LT" of "top" cannot be "object"`.

```python
HashableT = TypeVar('HashableT', bound=Hashable)
def mode(data: Iterable[HashableT]) -> HashableT: ...

from typing import Optional
def tag(name: str, /, *content: str, class_: Optional[str] = None, **attrs: str) -> str: ...
# inside: content is tuple[str, ...]; attrs is dict[str, str]

def update(probe: Callable[[], float], display: Callable[[float], None]) -> None: ...
```
- **What it demonstrates**: bounded TypeVar; hints for `*args`/`**kwargs` apply per element; Callable variance (`display_wrong(int)` is rejected, `display_ok(complex)` accepted).

## Reference Tables
Tuple annotation forms:

| Use | Hint |
|---|---|
| record | `tuple[str, float, str]` |
| record with named fields | `typing.NamedTuple` subclass (consistent-with `tuple[float, float]`, not vice versa) |
| immutable sequence | `tuple[int, ...]` (1+ items); `tuple` == `tuple[Any, ...]` |

Legacy typing equivalents (deprecated for 3.9+): `list`->`List`, `set`->`Set`, `frozenset`->`FrozenSet`, `deque`->`Deque`, `abc.Sequence`->`Sequence`, `abc.MutableSequence`, `abc.Set`->`AbstractSet`, `abc.MutableSet`. Python <3.9 needs `from __future__ import annotations` (3.7+) for `list[str]`.

Annotation tips: positional-only via `/` (3.8+) or `__name` prefix (PEP 484 convention). `Callable[..., Ret]` for flexible signature. Mypy tools: `reveal_type()`, `typing.TYPE_CHECKING`.

## Worked Example
`show_count` annotated gradually: (1) plain, Mypy passes because untyped defs are ignored; (2) `--disallow-incomplete-defs` + add `-> str`: Mypy now complains arguments lack annotations; (3) `count: int, word: str`; (4) add test calling with plural, Mypy flags "Too many arguments", add `plural: str = ''` (or `Optional[str] = None` when None fits better, mandatory for mutable-type defaults).

## Key Takeaways
1. Hints are optional, unenforced at runtime, no speedup; use them where cost/benefit justifies, with tests still primary.
2. Accept abstract (`Mapping`, `Sequence`, `Iterable`), return concrete (`list[str]`).
3. `Any` is consistent-with everything; `object` is just a general type with few operations.
4. `TypeVar` (restricted or `bound=`) ties return type to input type; `Protocol` types capabilities structurally.
5. `Callable` is covariant in return, contravariant in parameters.
6. Type checkers cannot express value constraints; do not treat them as the ultimate arbiter.

## Connects To
- **Ch 5**: `typing.NamedTuple`, PEP 526 annotations, `Optional`/generics basics.
- **Ch 6**: None default for mutables.
- **Ch 7**: `tag`, positional-only params, `Callable`.
- **Ch 13**: Protocols vs ABCs, typed `double`, numeric protocols.
- **Ch 15**: variance, overloads, `TypedDict`, casting, runtime annotations.
- **Ch 17**: `Iterator` return type.
