# Chapter 15: More About Type Hints

## Core Idea
Advanced gradual typing: overloads, TypedDict, cast, runtime access to annotations, and generics with variance. Static typing helps but cannot validate dynamic data, and 100% annotation is not the goal.

## Frameworks Introduced
- **Variance rules of thumb**:
  1. If a type parameter describes data that comes OUT of the object, it can be covariant.
  2. If it describes data that goes INTO the object after construction, it can be contravariant.
  3. If it does both, it must be invariant.
  4. To err on the safe side, make parameters invariant (TypeVar default).
  - When to use: declaring TypeVars for generic containers/protocols/callback APIs; mostly library authors.
  - How: `T_co = TypeVar('T_co', covariant=True)`, `T_contra = TypeVar('T_contra', contravariant=True)`. Variance is declared on the TypeVar, then used in `Generic[T_co]`.
  - Why: `Callable[[Param...], Return]` is contravariant in params and covariant in return. Mutable collections (list, set) are invariant since T appears in `append(x: T)` and `pop() -> T`.
- **Overload recipe**: write `@overload` signatures (bodies `...`) immediately before the real un-annotated implementation; checker tries overloads in order; use when return type depends on argument types. Tools: bounded TypeVar `LT = TypeVar('LT', bound=SupportsLessThan)`, `Union[T, DT]` for `default=`.
- **Dealing with runtime annotations**: avoid reading `__annotations__` directly; use `typing.get_type_hints` (3.5+) or `inspect.get_annotations` (3.10+); wrap it in one function of your own (e.g. `Checked._fields`) so future changes are localized.
- **Cafeteria analogy for variance** (Erik Meijer): juice dispenser rule. `BeverageDispenser[Juice]` required.
  - Invariant: only exactly `[Juice]` accepted (even `[OrangeJuice]` rejected).
  - Covariant: `[Juice]` and `[OrangeJuice]` accepted, `[Beverage]` rejected.
  - Contravariant `TrashCan[T_contra]` where `deploy` needs `TrashCan[Biodegradable]`: `[Biodegradable]` and `[Refuse]` accepted, `[Compostable]` rejected (more general accepts more).

## Key Concepts
- **Generic type**: declared with type variables (`LottoBlower[T]`). **Formal type parameter**: the type variable (`KT`, `VT`). **Parameterized type**: with actual params (`LottoBlower[int]`). **Actual type parameter**: the `int` (terms from Bloch).
- **Invariant / Covariant / Contravariant**: `L[A]` unrelated to `L[B]` / `A :> B` implies `C[A] :> C[B]` / `A :> B` implies `K[A] <: K[B]`.
- **`typing.TypedDict`**: type-checker-only description of a dict with fixed string keys; at runtime the constructor returns a plain `dict`, no attrs, no defaults, no methods.
- **`typing.cast(typ, val)`**: returns `val` unchanged; tells checker to blindly believe `typ`.
- **`TYPE_CHECKING`**: True only for the checker; guards `reveal_type(...)` (a Mypy-only function).
- **PEP 563** (`from __future__ import annotations`): annotations stored as strings, not evaluated at import; default postponed beyond 3.10 (pydantic/FastAPI rely on runtime types). PEP 649 under consideration.
- **Forward reference**: must write `'Rectangle'` as a string inside the class itself (or use the `__future__` import).
- **Sentinel**: `MISSING = object()` to distinguish "not passed" from `None` (`max(default=...)`).
- **`Any`**: consistent-with every type; contagious.

## Mental Models
- Use `@overload` when "the return type depends on the types of two or more parameters".
- Use TypedDict for structure documentation only; for JSON use runtime validation (pydantic). Think of it "as useful as comments" without a checker.
- Use `cast` sparingly: better than `# type: ignore` (less informative) or `Any` (contagious), but frequent use is a smell of misuse or poor dependencies.
- Use gradual typing pragmatically: leave hard-to-annotate Pythonic APIs unannotated, or `# type: ignore` when a rabbit hole costs hours.

## Anti-patterns
- **Believing TypedDict validates JSON**: `from_json(...) -> BookDict` returning `json.loads()` (Any) passes Mypy yet runtime content can be anything; `to_xml` produced garbage on a non-book.
- **Assigning `Any` to annotated variable to silence `--disallow-any-expr`**: false sense of safety.
- **Reading `__annotations__` directly**: strings vs types depending on PEP 563; inner/function-local classes fail `get_type_hints`.
- **Aiming for 100% annotations**: noise and cumbersome APIs. Six overloads for `max`; copy-pasting identical overloads for `min`.
- **Covariant/contravariant mutable containers**: unsound.

## Code Examples
```python
from typing import TypeVar, Generic

T = TypeVar('T')

class LottoBlower(Tombola, Generic[T]):
    def __init__(self, items: Iterable[T]) -> None:
        self._balls = list[T](items)
    def load(self, items: Iterable[T]) -> None:
        self._balls.extend(items)
    def pick(self) -> T:
        ...
    def inspect(self) -> tuple[T, ...]:
        return tuple(self._balls)

machine = LottoBlower[int](range(1, 11))   # Mypy: first is int, inspect() is tuple[int, ...]
```
- **What it demonstrates**: generic class declared via `Generic[T]` (multiple inheritance); errors for `LottoBlower[int]([1, .2])`.

```python
T_co = TypeVar('T_co', covariant=True)

@runtime_checkable
class RandomPicker(Protocol[T_co]):
    def pick(self) -> T_co: ...
```
- **What it demonstrates**: generic covariant protocol (T only in return); same as `SupportsAbs(Protocol[T_co])`.

```python
@overload
def max(__arg1: LT, __arg2: LT, *args: LT, key: None = ...) -> LT: ...
@overload
def max(__arg1: T, __arg2: T, *args: T, key: Callable[[T], LT]) -> T: ...
@overload
def max(__iterable: Iterable[LT], *, key: None = ...) -> LT: ...
@overload
def max(__iterable: Iterable[T], *, key: Callable[[T], LT]) -> T: ...
@overload
def max(__iterable: Iterable[LT], *, key: None = ..., default: DT) -> Union[LT, DT]: ...
@overload
def max(__iterable: Iterable[T], *, key: Callable[[T], LT], default: DT) -> Union[T, DT]: ...
```
- **What it demonstrates**: Mypy now rejects `max([None, None])`; each overload = one combination of key/default presence.

```python
class BookDict(TypedDict):
    isbn: str
    title: str
    authors: list[str]
    pagecount: int

def find_first_str(a: list[object]) -> str:
    index = next(i for i, x in enumerate(a) if isinstance(x, str))
    return cast(str, a[index])
```

## Reference Tables
| Max overload group | Return type |
|---|---|
| items LT, no key/default | `LT` |
| key given, no default | `T` |
| default given (no key) | `Union[LT, DT]` |
| key and default | `Union[T, DT]` |

| Type | Variance |
|---|---|
| list, set, dict (mutable) | invariant |
| frozenset, Iterator, Callable return | covariant |
| Callable params, TrashCan-like sinks | contravariant |

Naming: `_co`, `_contra` suffixes (typeshed); Soapbox proposes `T_out`/`T_in` like Kotlin `out T`/`in T`.

## Worked Example
Cafeteria: `class Beverage / Juice(Beverage) / OrangeJuice(Juice)`; `def install(dispenser: BeverageDispenser[Juice])`. With `T = TypeVar('T')` (invariant) both `BeverageDispenser(Beverage())` and `BeverageDispenser(OrangeJuice())` fail Mypy. Switch to `T_co` (covariant) and the OrangeJuice dispenser passes; Beverage still fails. For `TrashCan[T_contra]` with `deploy(trash_can: TrashCan[Biodegradable])`, `TrashCan[Refuse]` passes and `TrashCan[Compostable]` fails.

## Key Takeaways
1. `@overload` is the way to link return type to argument types; implementation stays unannotated.
2. TypedDict is annotation-only; JSON handling needs runtime validation.
3. `cast` is a no-op at runtime; use rarely, prefer it to `ignore`/`Any`.
4. Read annotations via `get_type_hints`/`inspect.get_annotations`, wrapped in your own helper; this area is in flux (PEP 563 vs 649).
5. Default to invariant; covariant for output-only, contravariant for input-only.
6. Gradual typing means you may skip hints when cost exceeds value.

## Connects To
- **Ch 8**: type hint foundations, Callable variance, Protocol intro, consistent-with.
- **Ch 13**: Tombola, RandomPicker (non-generic), SupportsComplex.
- **Ch 5**: NamedTuple vs TypedDict.
- **Ch 24**: `Checked` class using `get_type_hints`.
- **Ch 17/21**: Generator/Coroutine variance.
