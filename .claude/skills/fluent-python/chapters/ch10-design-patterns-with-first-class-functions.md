# Chapter 10: Design Patterns with First-Class Functions

## Core Idea
Language features determine which design patterns are worth implementing. With first-class functions, single-method-interface patterns (Strategy, Command) collapse into plain callables, removing classes, abstract bases and Flyweight machinery.

## Frameworks Introduced
- **Strategy pattern (GoF)**: "Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from clients that use it."
  - Participants: **Context** (delegates to a strategy; `Order`), **Strategy** (common interface; abstract `Promotion`), **Concrete strategy** (`FidelityPromo`, `BulkItemPromo`, `LargeOrderPromo`).
  - When to use: pluggable algorithm chosen by the client (discount rules, sorting keys).
  - How (Pythonic): replace each stateless single-method concrete strategy with a function; type the slot `Optional[Callable[['Order'], Decimal]]`; call `self.promotion(self)`.
  - Why it works: a function is lighter than an instance and is created once per module load, so it is already a Flyweight ("a shared object usable in multiple contexts simultaneously"). Classes are still right when strategies hold internal state.
- **Choosing the best strategy ("metastrategy")**: `max(promo(order) for promo in promos)`. Three ways to build `promos`:
  1. Manual list: simple but a new strategy can be silently forgotten.
  2. Introspection: `globals()` filtered by `_promo` suffix (hackish), or `inspect.getmembers(promotions, inspect.isfunction)` on a dedicated module (implicit assumption: every function there has the right signature).
  3. **Registration decorator** (preferred, explicit).
- **Decorator-enhanced Strategy**: `promos: list[Promotion] = []`; `def promotion(promo): promos.append(promo); return promo`.
  - Advantages: no naming convention required; decorator documents intent; disable by commenting it out; strategies may live in any module.
- **Command pattern**: decouple invoker from receiver by putting a Command object with a single `execute` between them. "Commands are an object-oriented replacement for callbacks." Pythonic: pass a function and call `command()`; compose with a callable `MacroCommand` class.
  - For undo/state: callable instance with extra methods, or a closure holding state.

## Key Concepts
- **Design pattern**: general recipe for a common design problem; language-dependent in relevance (Norvig: 16 of 23 GoF patterns become "invisible or simpler" in dynamic languages).
- **Flyweight**: shared object reused across contexts to cut creation cost; unnecessary for strategy functions.
- **Single-method interface smell**: an interface whose one method has a generic name ("execute", "run", "do_it") is a sign a callable would do.
- **Callable instance**: object with `__call__`; every Python callable implements a single-method interface named `__call__`.
- **Registration decorator**: returns the function unchanged after adding it to a module-level registry.
- **Module as first-class object**: `globals()`, `inspect.getmembers` let code discover functions dynamically.
- **Context**: object that delegates to the strategy. **Invoker / Receiver**: Command roles (menu item / document).

## Mental Models
- Use plain functions when strategies are stateless and have one method; use classes (or callable instances/closures) when they need state or extra methods.
- Think of a pattern as a step in the design process, not an end point (Ralph Johnson: "Too much emphasis on patterns as end-points").
- "Conformity to patterns is not a measure of goodness."
- `self.promotion(self)`: `promotion` is an instance attribute holding a function, not a method, so it is not auto-bound; pass `self` explicitly.

## Anti-patterns
- **Single-method classes implementing a single-method interface**: boilerplate where a function works.
- **Layering Flyweight on Strategy to fix its cost**: patterns piling up; functions already share.
- **Forgetting to add a new strategy to a manual list**: silent bug (the strategy works when passed explicitly but `best_promo` ignores it).
- **Name-suffix discovery via `globals()`**: fragile and must exclude `best_promo` to avoid infinite recursion.
- **Cargo-culting Java-style GoF patterns in Python** regardless of language features.

## Code Examples
```python
@dataclass(frozen=True)
class Order:  # the Context
    customer: Customer
    cart: Sequence[LineItem]
    promotion: Optional[Callable[['Order'], Decimal]] = None

    def total(self) -> Decimal:
        totals = (item.total() for item in self.cart)
        return sum(totals, start=Decimal(0))

    def due(self) -> Decimal:
        if self.promotion is None:
            discount = Decimal(0)
        else:
            discount = self.promotion(self)
        return self.total() - discount
```
- **What it demonstrates**: strategy injected as a callable; no abstract class.

```python
Promotion = Callable[[Order], Decimal]
promos: list[Promotion] = []

def promotion(promo: Promotion) -> Promotion:
    promos.append(promo)
    return promo

def best_promo(order: Order) -> Decimal:
    """Compute the best discount available"""
    return max(promo(order) for promo in promos)

@promotion
def fidelity(order: Order) -> Decimal:
    """5% discount for customers with 1000 or more fidelity points"""
    if order.customer.fidelity >= 1000:
        return order.total() * Decimal('0.05')
    return Decimal(0)
```
- **What it demonstrates**: registration decorator keeps the registry in sync with definitions.

```python
class MacroCommand:
    """A command that executes a list of commands"""
    def __init__(self, commands):
        self.commands = list(commands)
    def __call__(self):
        for command in self.commands:
            command()
```

## Reference Tables
| Approach to collect strategies | Explicit? | Risk |
|---|---|---|
| Hand-maintained `promos` list | yes | forgotten entries |
| `globals()` + name suffix | no | naming convention, recursion trap |
| `inspect.getmembers(module, isfunction)` | partly | signature assumptions |
| `@promotion` registration decorator | yes | none significant |

| Discount rule | Strategy |
|---|---|
| >=1000 fidelity points: 5% of order | fidelity |
| line item >=20 units: 10% of that item | bulk_item |
| >=10 distinct items: 7% of order | large_order |

## Worked Example
Classic `Order` + abstract `Promotion` + three subclasses -> delete the ABC and classes, make each rule a function taking an `Order`, pass the function as `promotion`. Then add `best_promo` as a function that maxes over a list of functions. Finally fix the "forgotten registration" bug by decorating each rule with `@promotion`. Result: shorter code, no per-order strategy instantiation.

## Key Takeaways
1. Check whether a pattern is needed in your language before implementing it.
2. Stateless single-method strategy classes should be functions.
3. Data structures holding functions (`promos`) are natural in Python.
4. Registration decorators beat introspection hacks and manual lists.
5. Command = callback; use functions, callable classes (`__call__`), or closures.
6. Patterns are steps in a design process, not goals.

## Connects To
- **Ch 9**: registration decorators, closures.
- **Ch 7**: callables, `__call__`, first-class functions.
- **Ch 17**: Iterator pattern is built into generators.
- **Ch 5/8**: dataclass, type hints (`Callable`).
