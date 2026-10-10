# Chapter 22: Dynamic Attributes and Properties

## Core Idea
Dynamic attributes present `obj.attr` syntax but compute on demand (Meyer's Uniform Access Principle). `@property` and `__getattr__` let you keep public data attributes in your API and add validation or computation later without breaking clients.

## Frameworks Introduced
- **Uniform Access Principle (Meyer)**: "All services offered by a module should be available through a uniform notation, which does not betray whether they are implemented through storage or through computation."
  - When to use: start with plain public attributes; convert to a property when you need validation/computation.
  - Failure mode: callers cannot tell if `product.price` is cheap; abstraction hides runtime cost (hence the caching need).
- **Virtual attributes**: attributes not declared in the class source and not in instance `__dict__`, computed/retrieved when reading a nonexistent name via `__getattr__`.
- **Attribute lookup priority (what really happens on `obj.attr`)**: search starts at `type(obj)`; an overriding descriptor/property named `attr` wins over the instance `__dict__`; otherwise instance `__dict__`, then class/superclasses; `__getattr__` only if all of that fails.
- **Property factory**: higher-order function returning `property(getter, setter)` built from closures holding `storage_name`; remove repeated getter/setter pairs. (Superseded by descriptor classes, Ch 23.)
- **Four-step progression for computed properties** (Record/Event on OSCON data): (1) data-driven attribute creation with `__dict__.update(kwargs)`; (2) property to dereference a linked record; (3) property overriding an existing attribute (read raw data via `self.__dict__[...]`); (4) caching: handmade, then `functools.cached_property`, or `@property` stacked on `@cache`.

## Key Concepts
- **`__getattr__`**: called only after normal lookup (instance, class, superclasses) fails.
- **`__new__`**: real constructor; implicitly a class method; if it returns an instance of a different class, `__init__` is not called. `__init__` is an *initializer*.
- **Bunch idiom**: `self.__dict__.update(kwargs)` to make attributes from keyword args (stdlib analogues: `types.SimpleNamespace`, `argparse.Namespace`).
- **`property(fget=None, fset=None, fdel=None, doc=None)`**: a class; always a class attribute; decorator form `@x.setter`, `@x.deleter`; getter docstring becomes the property doc.
- **`cached_property`** (3.8): non-overriding descriptor; stores result in same-named instance attribute; thread safe; writes allowed; delete attribute to clear.
- **Key-sharing dict (PEP 412)**: instances share key table if all attributes are created in `__init__`; adding attributes later (handmade caches, `cached_property`) defeats it.
- **`__dict__`, `__slots__`, `__class__`**: special attributes affecting attribute handling; special methods are looked up on the class only.
- **Name-mangling `self.__data`**: stored as `_FrozenJSON__data`.

## Mental Models
- Properties are class attributes that manage access on instances; a property shadows an instance attribute of the same name, but a plain class attribute does not.
- To bypass a property inside its own getter/setter, go through `instance.__dict__[name]` (avoids infinite recursion).
- `__getattr__` is safe, narrow (only missing names); `__getattribute__` and `__setattr__` are called for every access, and harder to get right. Prefer properties/descriptors.
- Use a custom mapping (`__getitem__`) rather than dynamic `__getattr__` if keys are untrusted data: avoids shadowing/overwrite bugs.

## Anti-patterns
- **Getters/setters from the start (Java style)**: Python lets you expose public attributes and wrap later; Martelli calls accessors "goofy idioms".
- **Building attributes from data keys that are keywords/invalid identifiers**: `student.class` is a SyntaxError; use `keyword.iskeyword` and append `_`, or `s.isidentifier()` checks.
- **Instance attributes from data shadowing methods** (`self.fetch` when a record has key `'fetch'`): call via `self.__class__.fetch(key)`.
- **`hasattr`-based handmade caches**: break key-sharing; racy in multithreaded code.
- **`cached_property` where the method reads an attribute of the same name**, with `__slots__`, or when key sharing matters.
- **Raising `KeyError` from `__getattr__`**: should be `AttributeError`.
- **Turning mutating methods into properties** (`my_list.clear` would delete on access).

## Code Examples
```python
class FrozenJSON:
    """A read-only façade for navigating a JSON-like object using attribute notation"""
    def __new__(cls, arg):
        if isinstance(arg, abc.Mapping):
            return super().__new__(cls)
        elif isinstance(arg, abc.MutableSequence):
            return [cls(item) for item in arg]
        else:
            return arg
    def __init__(self, mapping):
        self.__data = {}
        for key, value in mapping.items():
            if keyword.iskeyword(key):
                key += '_'
            self.__data[key] = value
    def __getattr__(self, name):
        try:
            return getattr(self.__data, name)       # keys(), items()...
        except AttributeError:
            return FrozenJSON(self.__data[name])
    def __dir__(self):
        return self.__data.keys()
```
- **What it demonstrates**: `__getattr__` on missing names, `__new__` as a flexible factory, keyword escaping, `__dir__` for autocompletion.

```python
class Event(Record):
    @property
    def venue(self):
        key = f'venue.{self.venue_serial}'
        return self.__class__.fetch(key)

    @property
    @cache                       # order matters: property on top
    def speakers(self):
        spkr_serials = self.__dict__['speakers']   # bypass the property
        fetch = self.__class__.fetch
        return [fetch(f'speaker.{key}') for key in spkr_serials]
```
```python
class LineItem:
    @property
    def weight(self):
        return self.__weight
    @weight.setter
    def weight(self, value):
        if value > 0:
            self.__weight = value
        else:
            raise ValueError('value must be > 0')
```
```python
def quantity(storage_name):
    def qty_getter(instance):
        return instance.__dict__[storage_name]
    def qty_setter(instance, value):
        if value > 0:
            instance.__dict__[storage_name] = value
        else:
            raise ValueError('value must be > 0')
    return property(qty_getter, qty_setter)

class LineItem:
    weight = quantity('weight')
    price = quantity('price')
```
- **What it demonstrates**: closure over `storage_name`; writes go to `__dict__` to bypass the property. Repeating the name is unavoidable until `__set_name__` (Ch 23).

```python
class BlackKnight:
    @property
    def member(self): ...
    @member.deleter
    def member(self): ...        # triggered by del knight.member
# classic form: member = property(member_getter, fdel=member_deleter)
```

## Reference Tables
| Built-in | Purpose |
|---|---|
| `dir([obj])` | "interesting" names; honors `__dir__`; works with `__slots__` |
| `getattr(obj, name[, default])` | read by name string (inherited too) |
| `hasattr(obj, name)` | `getattr` + catch AttributeError |
| `setattr(obj, name, value)` | write |
| `vars([obj])` | `__dict__`; fails for `__slots__`-only instances |

| Special method | Trigger |
|---|---|
| `__getattribute__` | every read (dot, getattr, hasattr); use `super().__getattribute__` inside |
| `__getattr__` | only when lookup failed |
| `__setattr__` | every write (dot, setattr) |
| `__delattr__` | `del obj.attr`; if defined, property deleter is never called |
| `__dir__` | `dir(obj)`, tab-completion |

| `property` vs `cached_property` | property | cached_property |
|---|---|---|
| Descriptor kind | overriding | nonoverriding |
| Writes | blocked unless setter | allowed |
| `__slots__` | OK | not usable |
| Key sharing | kept | defeated |
| Thread safe | n/a | yes |

## Worked Example
OSCON feed: JSON with `Schedule` -> `conferences/events/speakers/venues`, each record having `serial`. `load()` turns every record into `Record(**raw)` keyed `'speaker.3471'` (record type = collection name minus trailing `s`; picks subclass `Event` via `globals().get(cls_name, Record)`). `Event.venue` dereferences `venue_serial` via `fetch`; `Event.speakers` overrides the raw `speakers` list of serials (read via `__dict__`) and returns `Record`s, cached with `@property` over `@cache`. `fetch` is a `staticmethod` operating on the private class attribute `Record.__index`.

## Key Takeaways
1. Expose public attributes first; upgrade to `@property` when you need validation/computation; clients do not change.
2. `__getattr__` runs only on failed lookup; translate misses to `AttributeError`.
3. Properties override instance attributes; get raw data via `instance.__dict__` to avoid recursion.
4. For caching: prefer `cached_property` unless it has a same-named attribute, `__slots__`, or key-sharing concerns; then `@property` over `@cache`.
5. Dynamic attribute names from data risk keywords, invalid identifiers and shadowing methods.
6. `__getattribute__`/`__setattr__` are blunt; properties/descriptors are less error prone.

## Connects To
- **Ch 11**: Vector `__getattr__`, `@property` for read-only; **Ch 3**: `__missing__`.
- **Ch 9**: `@cache`, stacked decorators. **Ch 8/5**: type hints; `__slots__`.
- **Ch 23**: properties are overriding descriptors; descriptor classes replace property factories.
