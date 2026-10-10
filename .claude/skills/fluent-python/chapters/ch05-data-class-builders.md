# Chapter 5: Data Class Builders

## Core Idea
Python has three shortcuts for classes that are just collections of fields: `collections.namedtuple`, `typing.NamedTuple`, and `@dataclasses.dataclass`. They generate `__init__`, `__repr__`, `__eq__` (and more) so you skip boilerplate; but "Data Class" is also a code smell: a class with no behavior often signals misplaced logic.

## Frameworks Introduced
- **Choosing a data class builder**: three builders, differing in mutability, syntax, and customization.
  - When to use: any record-like class. `namedtuple` = simplest/legacy; `NamedTuple` = tuple semantics + type hints + class syntax; `@dataclass` = mutable instances, most options.
  - How: need immutable and tuple-compatible (unpack, index, `json`-ready via `_asdict`) -> `NamedTuple`. Need mutability, defaults factories, `__post_init__`, `InitVar`, ordering -> `@dataclass` (add `frozen=True` for protection). Need runtime-built classes -> `namedtuple(...)`/`NamedTuple(...)`/`make_dataclass(...)`.
  - Failure mode: PEP 557 "Rationale" says dataclass is NOT appropriate when API compatibility with tuples/dicts is required, or when type validation beyond PEP 484/526 or value validation/conversion is required (use `attrs` or pydantic-style libs).
- **Data Class as Code Smell (Fowler/Beck)**: data classes are "dumb data holders ... manipulated in far too much detail by other classes."
  - When to use: reviewing any data class; ask "what behavior belongs in this class?" then move it in.
  - How: Two legitimate scenarios: (1) **Scaffolding**: temporary starting point; grow methods over time. (2) **Intermediate representation**: records about to be exported/just imported across a system boundary; treat as immutable; if values must change on import/export, write your own builder methods instead of `asdict`/constructor.
  - Why: OOP puts behavior and data in the same unit; otherwise logic is scattered and duplicated.
- **Class patterns (pattern matching on instances)**: simple, keyword, positional (see Code Examples).

## Key Concepts
- **namedtuple**: factory function building a `tuple` subclass with field names; instances use the same memory as a tuple (names live in the class).
- **typing.NamedTuple**: same as namedtuple plus type annotations; uses a metaclass, so `issubclass(Coordinate, typing.NamedTuple)` is `False` but `issubclass(Coordinate, tuple)` is `True`.
- **@dataclass**: class decorator (no inheritance, no metaclass); class is a plain `object` subclass; reads `__annotations__` at class creation.
- **Variable annotation (PEP 526)**: `var_name: some_type [= value]`. No runtime enforcement; `a: int` with no value creates only an `__annotations__` entry, no attribute.
- **`default_factory`**: zero-arg callable in `dataclasses.field` invoked per instance; required for mutable defaults.
- **`__post_init__`**: hook called as the last step of the generated `__init__`; used for validation and derived fields.
- **`ClassVar`**: pseudotype (`typing.ClassVar[set[str]]`) marking a class attribute so `@dataclass` skips making a field.
- **`InitVar`**: pseudotype (`dataclasses.InitVar[T]`) for init-only args: accepted by `__init__` and passed to `__post_init__`, but not a field, not in `fields()`.
- **`__match_args__`**: tuple of attribute names defining positional order in class patterns; auto-created by all three builders.
- **Code smell (Fowler)**: a quick-to-spot surface indication that usually corresponds to a deeper problem; not inherently bad.

## Mental Models
- Think of type hints as "documentation that can be verified by IDEs and type checkers"; Python itself ignores them.
- Use `NamedTuple` when you'd otherwise return a tuple but want names; use `@dataclass` when the thing has identity and changes.
- For `@dataclass`, "annotated at class top level = instance field"; "unannotated = class attribute". This reverses the usual rule that everything at class top level is a class attribute.

## Anti-patterns
- **Mutable literal default (`guests: list = []`)**: `@dataclass` raises `ValueError` for list/dict/set only; other mutable defaults are NOT flagged, so use `field(default_factory=...)` yourself.
- **Reading `__annotations__` directly**: use `inspect.get_annotations(cls)` (3.10) or `typing.get_type_hints(cls)` (3.5-3.9) to resolve forward references.
- **Un-annotated class var in a dataclass wanting a type**: a plain annotation makes it an instance field; use `ClassVar[...]`.
- **Hierarchies of data classes**: usually a bad idea (chapter 14); the book only does it to shorten the example. Field order follows MRO, and a default in a parent forces defaults below.
- **`unsafe_hash=True`**: only for logically immutable classes that can still be mutated; read the docs first.
- **Injecting methods into namedtuple** (`Card.overall_rank = spades_high`): works but is a hack; use class syntax.
- **Data class with only getters/setters left forever**: the smell.

## Code Examples
```python
from dataclasses import dataclass, field
from typing import ClassVar
from club import ClubMember

@dataclass
class HackerClubMember(ClubMember):
    all_handles: ClassVar[set[str]] = set()
    handle: str = ''

    def __post_init__(self):
        cls = self.__class__
        if self.handle == '':
            self.handle = self.name.split()[0]
        if self.handle in cls.all_handles:
            msg = f'handle {self.handle!r} already exists.'
            raise ValueError(msg)
        cls.all_handles.add(self.handle)
```
- **What it demonstrates**: `ClassVar` keeps `all_handles` out of the fields; `__post_init__` does derived value + validation; `handle` must be passed by keyword if `guests` is skipped.

```python
@dataclass
class ClubMember:
    name: str
    guests: list[str] = field(default_factory=list)
    athlete: bool = field(default=False, repr=False)

@dataclass
class C:
    i: int
    j: int = None
    database: InitVar[DatabaseType] = None
    def __post_init__(self, database):
        if self.j is None and database is not None:
            self.j = database.lookup('j')
```
- **What it demonstrates**: per-field options; `InitVar` passes a non-field arg to `__post_init__`.

```python
match city:
    case City(continent='Asia', country=cc): ...   # keyword pattern
    case City('Asia', _, country): ...             # positional, needs __match_args__
    case float(): ...                              # simple class pattern, no binding
    case float: ...                                # BUG: binds any subject to name "float"
```
- **What it demonstrates**: class pattern forms; always call with parens.

## Reference Tables
Table 5-1. Feature comparison (x = instance)

| | namedtuple | NamedTuple | dataclass |
|---|---|---|---|
| mutable instances | NO | NO | YES |
| class statement syntax | NO | YES | YES |
| construct dict | `x._asdict()` | `x._asdict()` | `dataclasses.asdict(x)` |
| get field names | `x._fields` | `x._fields` | `[f.name for f in dataclasses.fields(x)]` |
| get defaults | `x._field_defaults` | `x._field_defaults` | `[f.default for f in dataclasses.fields(x)]` |
| get field types | N/A | `x.__annotations__` | `x.__annotations__` |
| new instance with changes | `x._replace(...)` | `x._replace(...)` | `dataclasses.replace(x, ...)` |
| new class at runtime | `namedtuple(...)` | `NamedTuple(...)` | `dataclasses.make_dataclass(...)` |

Table 5-2. `@dataclass` options (keyword-only)

| Option | Meaning | Default | Notes |
|---|---|---|---|
| init | generate `__init__` | True | ignored if user defines it |
| repr | generate `__repr__` | True | ignored if user defines it |
| eq | generate `__eq__` | True | ignored if user defines it |
| order | generate `__lt__ __le__ __gt__ __ge__` | False | error if eq=False or methods defined/inherited |
| unsafe_hash | generate `__hash__` | False | complex caveats |
| frozen | block attribute assignment | False | "reasonably safe", not truly immutable |

`eq=True, frozen=True` -> generated `__hash__` from all fields not excluded. `frozen=False` -> `__hash__ = None` (unhashable).

Table 5-3. `field()` options

| Option | Meaning | Default |
|---|---|---|
| default | default value | _MISSING_TYPE |
| default_factory | 0-arg callable for default | _MISSING_TYPE |
| init | include in `__init__` params | True |
| repr | include in `__repr__` | True |
| compare | use in `__eq__`, `__lt__`... | True |
| hash | include in `__hash__` | None (use if compare=True) |
| metadata | user mapping, ignored by dataclass | None |

namedtuple extras: `_fields`, `_make(iterable)`, `_asdict()` (plain dict since 3.8), `_replace()`, `defaults=` kwarg (3.7, fills rightmost fields).

## Worked Example
Dublin Core `Resource`: `identifier: str` is the only required field; `title: str = '<untitled>'` starts defaults (all later fields must default); `creators: list[str] = field(default_factory=list)`; `date: Optional[date] = None`; `type: ResourceType = ResourceType.BOOK` (an `Enum`). Custom `__repr__` iterates `dataclasses.fields(cls)` and uses `getattr(self, f.name)` with `!r` to print one `name = value,` per line.

## Key Takeaways
1. Type hints have zero runtime effect; `Coordinate('Ni!', None)` builds fine. Only Mypy etc. flag it.
2. `namedtuple`/`NamedTuple` are immutable tuple subclasses; `@dataclass` is mutable unless `frozen=True`.
3. Mutable defaults need `default_factory`; the built-in check only covers list/dict/set.
4. Use `ClassVar` for class attributes and `InitVar` for init-only args in dataclasses; `__post_init__` for validation/derived fields.
5. All builders create `__match_args__`, enabling positional class patterns; keyword patterns work on any class with public attributes.
6. A data class with no behavior is a smell unless it is scaffolding or an intermediate representation.

## Connects To
- **Ch 2**: named tuples and sequence pattern matching originated there.
- **Ch 6**: mutable default hazard explained in depth.
- **Ch 8/15**: type hints for functions and classes; `TypedDict` is not a builder.
- **Ch 14**: why data class hierarchies are a bad idea.
- **Ch 23/24**: descriptors behind `_tuplegetter`; metaclass used by `NamedTuple`; `__match_args__` for custom classes (Ch 11).
