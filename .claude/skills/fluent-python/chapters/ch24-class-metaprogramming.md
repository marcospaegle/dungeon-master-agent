# Chapter 24: Class Metaprogramming

## Core Idea
Classes are objects that can be created or customized at runtime, in ascending order of power and complexity: class factory functions with `type(...)`, `__init_subclass__`, class decorators, and metaclasses. Avoid them in application code; they are the tools of framework authors.

## Frameworks Introduced
- **Ladder of class-customization techniques (ascending complexity)**:
  1. `type(name, bases, dict)` or a *class factory function* (can set `__slots__`).
  2. `__init_subclass__` in a base class (PEP 487): transparent to users; may conflict in complex hierarchies.
  3. *Class decorator*: simpler than metaclasses; best when you must not interfere with inheritance/metaclasses (why `@dataclass` is a decorator).
  4. *Metaclass* (`type` subclass): only way to change what is passed to `type.__new__` (e.g., configure `__slots__`, `__prepare__`).
  - When to use: pick the lowest rung that works.
- **Class construction timeline** (what happens when; verified by print experiments):
  1. `__prepare__` (metaclass only) returns the namespace mapping.
  2. Class body executes, filling the namespace (descriptor instances created here; `__module__`, `__qualname__` added first).
  3. Metaclass `__new__` (or `type.__new__`) builds the class.
  4. `__set_name__` called on each descriptor.
  5. `__init_subclass__` of the superclass.
  6. Class decorator applied.
  7. Name bound in the enclosing namespace.
  - Consequence: `__slots__` is effective only if in the namespace passed to `type.__new__`, so `__init_subclass__` and decorators cannot configure it.
- **Import time vs runtime**: import runs parse, compile, then executes module top-level code on first import (cached after); a class statement is therefore executable "runtime" behavior at import time.
- **Naming convention for metaclasses**: `meta_cls` (or `mcs`) for first arg of `__new__`/`__prepare__` (class methods); `cls` instead of `self` for instance methods, since the instance is a class.
- **"Metaclasses should be implementation details"**: offer a regular base class (`Checked`, `Bunch`) so users never name the metaclass; this future-proofs the API.

## Key Concepts
- **Class attributes**: `__bases__`, `__qualname__` (e.g., `Ox.Meta`), `__subclasses__()` (weakrefs, only imported subclasses), `cls.mro()` (overridable by metaclass); none shown by `dir`.
- **`type`**: a class (metaclass) that builds classes: `type(name, bases, dict)`; `type(type) is type`.
- **Metaclass**: subclass of `type`; its instances are classes; `ABCMeta`, `EnumMeta`, `NamedTupleMeta` are examples (only six besides `type` in stdlib 3.9).
- **`__init_subclass__(subclass)`**: implicit class method, receives the *new subclass*, not the defining class; call `super().__init_subclass__()`.
- **`__prepare__(meta_cls, name, bases, **kw)`**: class method on metaclass returning the namespace mapping.
- **`__class_getitem__`** (3.9): class-level `__getitem__` without a metaclass (enables `list[int]`).
- **Class decorator**: callable taking and returning a class; often injects methods via `setattr`.
- **Metaclass conflict**: a class may have only one metaclass; derived metaclass must subclass all bases' metaclasses.

## Mental Models
- "type is an instance of itself; object is an instance of type and type is a subclass of object." Every class is an instance of `type`; only metaclasses also subclass it.
- A metaclass is a mill that builds mills; `__new__` of a metaclass works like any `__new__` one level up.
- Good frameworks are extracted, not invented (DHH). Application code implementing these is often premature abstraction.
- Martelli: custom ABCs/metaclasses in production = shiny new hammer syndrome.

## Anti-patterns
- **Metaclass when `__set_name__`, `__init_subclass__`, or a decorator suffice**: modern features made most use cases redundant (also ordered `dict` removed the main `__prepare__` use).
- **Combining metaclass + `__init_subclass__` + decorator** in one class: sign of overengineering (only used for experiments).
- **Two metaclasses**: `TypeError: metaclass conflict`; writing a combined `PersistentABCMeta` is technical debt.
- **Trying to set `__slots__` in `__init_subclass__` or decorator**: too late.
- **Assuming Mypy checks `Checked.__init__`**: kwargs signature is `**kwargs: Any`; `list[float]` is treated as `list` at runtime.
- **Forgetting `super().__init_subclass__()`**: breaks cooperating bases.
- **Using `None` as default for runtime-typed fields**: Checked calls the constructor with no args (`int()`, `str()`) for a zero value; `...` (Ellipsis) as sentinel for "not given".

## Code Examples
```python
MyClass = type('MyClass',
               (MySuperClass, MyMixin),
               {'x': 42, 'x2': lambda self: self.x * 2},
)
```
- **What it demonstrates**: a `class` statement is `type(name, bases, dict)`.

```python
def record_factory(cls_name: str, field_names: FieldNames) -> type[tuple]:
    slots = parse_identifiers(field_names)
    def __init__(self, *args, **kwargs) -> None:
        attrs = dict(zip(self.__slots__, args))
        attrs.update(kwargs)
        for name, value in attrs.items():
            setattr(self, name, value)
    def __iter__(self) -> Iterator[Any]:
        for name in self.__slots__:
            yield getattr(self, name)
    def __repr__(self):
        values = ', '.join(f'{name}={value!r}'
                           for name, value in zip(self.__slots__, self))
        cls_name = self.__class__.__name__
        return f'{cls_name}({values})'
    cls_attrs = dict(__slots__=slots, __init__=__init__,
                     __iter__=__iter__, __repr__=__repr__)
    return type(cls_name, (object,), cls_attrs)
```
```python
class Checked:
    @classmethod
    def _fields(cls) -> dict[str, type]:
        return get_type_hints(cls)
    def __init_subclass__(subclass) -> None:
        super().__init_subclass__()
        for name, constructor in subclass._fields().items():
            setattr(subclass, name, Field(name, constructor))
    def __init__(self, **kwargs: Any) -> None:
        for name in self._fields():
            value = kwargs.pop(name, ...)
            setattr(self, name, value)
        if kwargs:
            self.__flag_unknown_attrs(*kwargs)
```
- **What it demonstrates**: user writes `class Movie(Checked): title: str; year: int; box_office: float`; type hints become `Field` descriptors that call the hint as a constructor (`TypeError: 'billions' is not compatible with box_office:float`).

```python
def checked(cls: type) -> type:                 # class decorator version
    for name, constructor in _fields(cls).items():
        setattr(cls, name, Field(name, constructor))
    cls._fields = classmethod(_fields)
    instance_methods = (__init__, __repr__, __setattr__, _asdict, __flag_unknown_attrs)
    for method in instance_methods:
        setattr(cls, method.__name__, method)
    return cls
```
```python
class CheckedMeta(type):
    def __new__(meta_cls, cls_name, bases, cls_dict):
        if '__slots__' not in cls_dict:
            slots = []
            type_hints = cls_dict.get('__annotations__', {})
            for name, constructor in type_hints.items():
                field = Field(name, constructor)
                cls_dict[name] = field
                slots.append(field.storage_name)   # '_' + name
            cls_dict['__slots__'] = slots
        return super().__new__(meta_cls, cls_name, bases, cls_dict)

class Checked(metaclass=CheckedMeta):
    __slots__ = ()      # skip CheckedMeta.__new__ processing
```
- **What it demonstrates**: only a metaclass can inject `__slots__`; with slots, descriptor name and storage name must differ (`_title`), so `Field` needs `__get__`; `__setattr__` becomes unnecessary.

```python
class MetaBunch(type):
    def __new__(meta_cls, cls_name, bases, cls_dict):
        defaults = {}
        ...
        new_dict = dict(__slots__=[], __init__=__init__, __repr__=__repr__)
        for name, value in cls_dict.items():
            if name.startswith('__') and name.endswith('__'):
                if name in new_dict:
                    raise AttributeError(f"Can't set {name!r} in {cls_name!r}")
                new_dict[name] = value
            else:
                new_dict['__slots__'].append(name)
                defaults[name] = value
        return super().__new__(meta_cls, cls_name, bases, new_dict)
class Bunch(metaclass=MetaBunch): pass
```
```python
class AutoConstMeta(type):
    def __prepare__(name, bases, **kwargs):
        return WilyDict()
class AutoConst(metaclass=AutoConstMeta): pass

class WilyDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__next_value = 0
    def __missing__(self, key):
        if key.startswith('__') and key.endswith('__'):
            raise KeyError(key)
        self[key] = value = self.__next_value
        self.__next_value += 1
        return value
# class Flavor(AutoConst): banana; coconut; vanilla  ->  0, 1, 2
```
- **What it demonstrates**: `__prepare__` + `__missing__`: bare names in the class body auto-create constants.

## Reference Tables
| Technique | Runs when | Can set `__slots__` | Conflict risk |
|---|---|---|---|
| Class factory (`type()`) | explicit call | yes | none |
| `__init_subclass__` | after class built, before decorator | no | hierarchy (cooperative `super()`) |
| Class decorator | after `__init_subclass__` | no | low |
| Metaclass `__prepare__`/`__new__` | before class exists | yes | one metaclass only |

Uses of metaclasses/decorators/`__init_subclass__`: subclass registration, structural validation, decorating many methods, serialization, ORM, persistence, class-level special methods, traits/AOP, import-time performance work.

## Worked Example
Evaluation-time experiment (`builderlib.py` + `evaldemo.py`): `@deco class Klass(Builder): attr = Descriptor()`. On import the prints show: module starts; `# Klass body`; `Descriptor.__init__`; `Descriptor.__set_name__(…, Klass, 'attr')`; `Builder.__init_subclass__(Klass)`; `deco(Klass)`; module end. Adding `metaclass=MetaKlass` (with a `NosyDict` namespace) prepends `__prepare__`, then `__setitem__` for `__module__`, `__qualname__`, `attr`, `__init__`, `__repr__`, `__classcell__`, then `MetaKlass.__new__`, then the same `__set_name__`, `__init_subclass__`, `deco` sequence. Note `type.__new__` requires a real dict (`cls_dict.data`).

## Key Takeaways
1. A `class` statement is a call to `type(name, bases, namespace)`; you can do that yourself.
2. Prefer, in order: factory, `__set_name__`, `__init_subclass__`, class decorator; metaclass last.
3. `__init_subclass__` and decorators run after the class exists; only a metaclass (or factory) can shape the namespace (`__slots__`).
4. Know the order: `__prepare__` -> body -> `__new__` -> `__set_name__` -> `__init_subclass__` -> decorator.
5. A class can have one metaclass; hide it behind a base class.
6. Use these tools for libraries/frameworks, not application code.

## Connects To
- **Ch 23**: `__set_name__`, `Field` descriptors, overriding descriptors need `__setattr__` care.
- **Ch 22**: `__new__`, `__slots__`, `__missing__` (Ch 3).
- **Ch 5**: `NamedTuple`, `@dataclass` as class builders. **Ch 13/14**: ABCMeta, MRO and cooperative `super()`.
- **Ch 8**: `get_type_hints`, runtime annotation problems.
