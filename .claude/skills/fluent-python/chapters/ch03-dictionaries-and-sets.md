# Chapter 3: Dictionaries and Sets

## Core Idea
Dicts and sets are hash-table based and underpin Python itself (attributes, namespaces, kwargs). Master modern dict syntax, missing-key strategies, the stdlib mapping variants, set algebra, and the practical consequences of hashing.

## Frameworks Introduced
- **Missing-key strategy selection**: pick how a lookup of an absent key behaves.
  - When to use: dict values that are mutable collections, or keys needing normalization.
  - How: (a) `d.setdefault(k, []).append(v)` for one-off insert-or-update in a single lookup; (b) `defaultdict(factory)` when every `d[k]` should auto-create; (c) subclass + `__missing__` when the default depends on the key.
  - Why it works: `dict.__getitem__` calls `__missing__` on a miss. Failure mode: `defaultdict` triggers only through `d[k]`; `d.get(k)` still returns `None` and `k in d` stays False.
- **Subclass UserDict, not dict** for custom mappings.
  - How: `UserDict` wraps a real `dict` in `self.data` (composition), so `__setitem__`, `__contains__`, `get`, `update` cooperate consistently; built-in `dict` shortcuts bypass overridden methods.
- **Set algebra instead of loops**: `found = len(needles & haystack)`.
  - How: `|` union, `&` intersection, `-` difference, `^` symmetric difference; methods (`.union(it)`) accept any iterable.
- **Semi-structured data matching** (JSON): include a `type` field, a schema version field (`api`), per-type invalid cases, then catch-all.

## Key Concepts
- **Hashable**: has a `__hash__` that never changes during lifetime and an `__eq__`; equal objects must have equal hash codes. Tuples hashable only if all items are; `frozenset` always. Hash codes are only stable within one process (salted).
- **dictcomp / setcomp**: `{k: v for ...}`, `{x for ...}`.
- **Mapping unpacking**: `**` multiple times in calls (keys unique) and in literals (later overrides).
- **`|` / `|=` (3.9)**: new merged dict vs in-place update; right side wins.
- **Mapping patterns**: partial matches succeed; key order irrelevant; `**rest` captures extras (must be last, `**_` forbidden); implemented with `d.get(key, sentinel)` so no `__missing__`/defaultdict side effects.
- **`__missing__`**: hook called by `dict.__getitem__` (not defined on `dict` itself).
- **OrderedDict**: equality is order-sensitive, `popitem(last=False)`, `move_to_end()`; good for LRU-style reordering.
- **ChainMap**: searches several mappings in order, references not copies; writes go to the first. Model of nested scopes.
- **Counter**: multiset/tally; `update` adds; `most_common(n)`; supports `+` and `-`.
- **`MappingProxyType`**: read-only but dynamic view of a mapping.
- **Dict views** (`dict_keys/values/items`): dynamic, read-only, non-subscriptable; `keys()` and `items()` support set operators.
- **Key-sharing dict (PEP 412)**: instances share key table when attributes are created in `__init__`.

## Mental Models
- Use `d.get(k, default)` for reads, `setdefault` for read-then-mutate, `defaultdict` for accumulate-everywhere.
- Think of a ChainMap as a stack of scopes (`ChainMap(locals(), globals(), vars(builtins))`).
- Use `isinstance(x, abc.Mapping)` rather than `dict` to accept alternative mappings.
- Use a `set` when you ask "is X in here?" a lot; use `dict.fromkeys(l)` to dedupe while preserving order.
- Think of `update(m)` as duck typing: if `m` has `.keys()`, treat as mapping, else as iterable of pairs; constructors reuse it.

## Anti-patterns
- **`get` then mutate then reassign** (`occ = index.get(w, []); occ.append(x); index[w] = occ`): two lookups; use `setdefault`.
- **`__missing__` without a `str` guard when converting** (`self[str(key)]`): infinite recursion if `str(key)` is also missing.
- **Subclassing `dict` and overriding `__setitem__`**: `update`/`__init__`/`setdefault` skip it. Use `UserDict`.
- **`{}` for empty set**: that is a dict; write `set()`.
- **Relying on set ordering**: depends on hash/insertion, may change after resize.
- **Adding instance attributes outside `__init__`**: breaks key-sharing, costs memory.
- **Unhashable values in `dict_items` set ops**: raises `TypeError`.
- **Mutable keys / hash from mutable state**: only use immutable attributes in `__eq__`/`__hash__`.

## Code Examples
```python
def get_creators(record: dict) -> list:
    match record:
        case {'type': 'book', 'api': 2, 'authors': [*names]}:
            return names
        case {'type': 'book', 'api': 1, 'author': name}:
            return [name]
        case {'type': 'book'}:
            raise ValueError(f"Invalid 'book' record: {record!r}")
        case {'type': 'movie', 'director': name}:
            return [name]
        case _:
            raise ValueError(f'Invalid record: {record!r}')
```
- **What it demonstrates**: mapping patterns mixed with sequence patterns; versioned records; specific-invalid then catch-all.

```python
index.setdefault(word, []).append(location)   # one lookup
index = collections.defaultdict(list)          # then index[word].append(location)
```

```python
class StrKeyDict(collections.UserDict):
    def __missing__(self, key):
        if isinstance(key, str):
            raise KeyError(key)
        return self[str(key)]

    def __contains__(self, key):
        return str(key) in self.data

    def __setitem__(self, key, item):
        self.data[str(key)] = item
```
- **What it demonstrates**: normalize keys on insert, update, and lookup; `get`/`update` inherited from `Mapping`/`MutableMapping`.

```python
>>> {'a': 0, **{'x': 1}, 'y': 2, **{'z': 3, 'x': 4}}
{'a': 0, 'x': 4, 'y': 2, 'z': 3}
>>> d1.keys() & d2.keys()      # set ops on views
>>> {*a, *b, *c}               # union of iterables into a new set
```

## Reference Tables
| Operation | Syntax | Notes |
|---|---|---|
| Union / merge | `a \| b`, `a \|= b` | dict 3.9+, set |
| Intersection | `a & b` | views too |
| Difference | `a - b` | |
| Symmetric diff | `a ^ b` | |
| Subset / proper | `<=` / `<` | `issubset(it)` takes iterables |
| Superset / proper | `>=` / `>` | |
| Disjoint | `isdisjoint(it)` | |
| Set mutators | `add, discard, remove (KeyError), pop, clear` | `frozenset` has none |

`__missing__` support by base class: `dict` subclass -> only `d[k]`; `UserDict` subclass -> `d[k]` and `d.get(k)`; `abc.Mapping` -> only if your `__getitem__` calls it.

Dict method highlights: `fromkeys`, `get`, `setdefault`, `pop`, `popitem` (last inserted; `OrderedDict` accepts `last=False`), `update`, `__reversed__`, `__or__/__ior__/__ror__`.

## Worked Example
Word index of the Zen of Python: for each match, `location = (line_no, column_no)`. Version 0 uses `get` + append + reassign (three lines, two searches). Version 1 collapses to `index.setdefault(word, []).append(location)`. Version 2 uses `defaultdict(list)` so `index[word].append(location)` always works. Output sorted with `sorted(index, key=str.upper)` (pass the method, don't call it).

## Key Takeaways
1. Keys/set elements must be hashable; `__eq__` and `__hash__` must agree and rely on immutable state.
2. Use `setdefault`/`defaultdict`/`__missing__` instead of get-then-reassign.
3. Extend `UserDict` for custom mappings; `dict` subclasses silently bypass overrides.
4. Dict views and sets give declarative algebra that replaces loops and ifs.
5. `dict` preserves insertion order (official in 3.7); `OrderedDict` still differs in equality and `move_to_end`.
6. Pattern matching mappings tolerates extra keys; sequences do not.
7. Hash tables cost memory (keep at least 1/3 empty) but give near O(1) access.

## Connects To
- **Ch 1**: `Mapping`/`Set` ABCs and operator dunders.
- **Ch 2**: sequence patterns, PEP 448 unpacking, `in` on large lists.
- **Ch 11/16**: hash/eq for user classes; operator overloading.
- **Ch 13**: ABCs, virtual subclasses.
- **Ch 14**: why subclassing built-ins is tricky.
- **Ch 5/ Ch 22**: `__slots__` and instance `__dict__` memory.
