# Chapter 23: Attribute Descriptors

## Core Idea
A descriptor is a class implementing `__get__`/`__set__`/`__delete__` (any subset), instances of which are declared as class attributes of a managed class to reuse access logic across attributes. Properties, methods, `cached_property`, and ORM fields are all descriptors.

## Frameworks Introduced
- **Descriptor terminology** (use precisely):
  - *Descriptor class*: implements the protocol (`Quantity`).
  - *Managed class*: declares descriptor instances as class attributes (`LineItem`).
  - *Descriptor instance*: each instance of the descriptor class, a class attribute of the managed class.
  - *Managed instance*: one instance of the managed class.
  - *Storage attribute*: attribute on the managed instance holding the value.
  - *Managed attribute*: public attribute handled by the descriptor instance, values in storage attributes.
- **Mills & Gizmos Notation (MGN)**: annotate UML so class = "mill" (complicated machine), instance = "gizmo"; a metaclass is a mill producing mills.
- **Overriding vs nonoverriding descriptors**: decided by presence of `__set__`.
  - Overriding (data/enforced): has `__set__`; intercepts assignments, wins over instance `__dict__` on writes (and on reads if it has `__get__`).
  - Nonoverriding (nondata/shadowable): only `__get__`; a same-named instance attribute shadows it.
- **Template method / Self-Delegation** (Gamma; Martelli's preferred name): `Validated.__set__` calls abstract `self.validate(name, value)` and stores the returned value; subclasses `Quantity`, `NonBlank` implement `validate` (may clean/normalize and return the value).
- **`__set_name__(self, owner, name)`** (3.6, PEP 487): called by `type.__new__` on each descriptor in the class body; sets the storage name automatically, removing the repeated-name, copy-paste-error-prone argument.

## Key Concepts
- **Descriptor protocol**: dynamic protocol (no subclassing); partial implementations OK; most real descriptors implement only `__get__` and `__set__`.
- **`__get__(self, instance, owner)`**: `instance` is `None` when accessed via the class; good practice: return `self` then.
- **`__set__(self, instance, value)`**: `self` = descriptor instance, `instance` = managed instance; store in `instance.__dict__`, never via `setattr` on the same name (infinite recursion).
- **Bound method**: result of `function.__get__(instance)`; has `__self__` and `__func__`; `function.__get__(None, cls)` returns the function.
- **`property`**: overriding descriptor even without setter; default `__set__` raises `AttributeError`; also supplies `__delete__`.
- **Overwriting on the class**: any descriptor can be replaced by assigning to the class; class-level writes cannot be controlled by descriptors in that class (need a metaclass).

## Mental Models
- Think "`obj.x` starts at `type(obj)`": overriding descriptor in class wins; else instance `__dict__`; else nonoverriding descriptor / class attribute.
- The descriptor instance is shared by all managed instances; per-instance data belongs in the managed instance.
- Descriptors are the infrastructure behind methods, properties, `cached_property`, `classmethod`, `staticmethod`, Django fields.
- Special methods are looked up on the class, so instance attributes cannot shadow them; ordinary methods can be shadowed (`obj.spam = 7`).

## Anti-patterns
- **Storing values in the descriptor instance** (`self.value = ...`/dict in descriptor): shared across all managed instances (class attribute). Store in `instance`.
- **Read-only descriptor without `__set__`**: assigning to the instance silently shadows it; implement `__set__` raising `AttributeError`, or just use `property`.
- **Hand-typing storage names** (`price = Quantity('weight')`): clobbers wrong attribute; use `__set_name__`.
- **Calling `setattr(instance, self.storage_name, ...)` when storage name == managed name** (recursion).
- **Per-field docstrings expected from a shared descriptor class**: docstring is of the class, one for all instances; customizing is surprisingly hard.
- **Decorating methods with a class-based decorator lacking `__get__`**: it won't bind `self`.

## Code Examples
```python
class Quantity:
    def __set_name__(self, owner, name):
        self.storage_name = name
    def __set__(self, instance, value):
        if value > 0:
            instance.__dict__[self.storage_name] = value
        else:
            msg = f'{self.storage_name} must be > 0'
            raise ValueError(msg)
    # no __get__ needed: storage name == managed name, instance __dict__ read directly

class LineItem:
    weight = Quantity()
    price = Quantity()
```
- **What it demonstrates**: set-only (overriding) validation descriptor; reading is fastest because instance `__dict__` has the value and no `__get__` runs.

```python
class Validated(abc.ABC):
    def __set_name__(self, owner, name):
        self.storage_name = name
    def __set__(self, instance, value):
        value = self.validate(self.storage_name, value)
        instance.__dict__[self.storage_name] = value
    @abc.abstractmethod
    def validate(self, name, value):
        """return validated value or raise ValueError"""

class Quantity(Validated):
    def validate(self, name, value):
        if value <= 0:
            raise ValueError(f'{name} must be > 0')
        return value

class NonBlank(Validated):
    def validate(self, name, value):
        value = value.strip()
        if not value:
            raise ValueError(f'{name} cannot be blank')
        return value
```
```python
def __get__(self, instance, owner):
    if instance is None:
        return self                 # class access returns the descriptor (introspection)
    else:
        return instance.__dict__[self.storage_name]
```
```python
>>> Text.reverse.__get__(word)           # bound method
>>> Text.reverse.__get__(None, Text)     # plain function
>>> word.reverse.__self__                # Text('forward')
>>> word.reverse.__func__ is Text.reverse   # True
```

## Reference Tables
| Kind | Methods | `obj.x = v` | `obj.x` read | Instance `__dict__['x']` |
|---|---|---|---|---|
| Overriding | `__get__`+`__set__` | calls `__set__` | calls `__get__` | ignored (descriptor still wins) |
| Overriding, no `__get__` | `__set__` | calls `__set__` | returns descriptor, unless instance attr exists, then returns that | shadows on read only |
| Nonoverriding | `__get__` only | creates instance attr (shadows) | `__get__` until shadowed; `del obj.x` restores | shadows |

Synonyms: overriding = data = enforced; nonoverriding = nondata = shadowable.

| Built-in as descriptor | Kind |
|---|---|
| `property` | overriding |
| functions/methods | nonoverriding |
| `functools.cached_property` | nonoverriding |
| Django model fields | overriding |

## Worked Example
LineItem Take #3 to #5: Take 3, `Quantity('weight')` with `__init__` storing `storage_name` (explicit, error-prone). Take 4, replace `__init__` with `__set_name__`; descriptor class moves to a utility module (`model.Quantity()`). Take 5, bug: blank description. Extract `Validated` template, make `Quantity` and `NonBlank` thin subclasses; `LineItem` ends as `description = model.NonBlank(); weight = model.Quantity(); price = model.Quantity()`. Console experiments on `Managed` (with `Overriding`, `OverridingNoGet`, `NonOverriding`, `spam`) verify the table above.

## Key Takeaways
1. Use a descriptor class when the same access logic applies to many attributes/classes; use `property` for one-off.
2. Validation descriptors can implement `__set__` only and store directly in `instance.__dict__`.
3. Always implement `__set_name__` instead of passing names by hand.
4. Overriding vs nonoverriding determines whether instance attributes shadow the descriptor.
5. Caching via `__get__`-only nonoverriding descriptors: result stored under the same name shadows the descriptor next time.
6. Functions are nonoverriding descriptors; this is how bound methods are created.
7. Descriptor `__set__` never fires on class assignment; that needs a metaclass.

## Connects To
- **Ch 22**: properties/property factory, `cached_property`.
- **Ch 24**: `__set_name__` called by `type.__new__`; `Field` descriptor in `Checked`; metaclass to control class-level setting.
- **Ch 11/13**: template method; protocols (dynamic).
- **Ch 9**: function decorators vs descriptors.
