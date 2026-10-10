# Chapter 1: Domain Modeling

## Core Idea
Model the business process as plain, dependency-free Python objects using the business's own language, driven by TDD. Behavior first; storage later. ("Most developers have never seen a domain model, only a data model.")

## Frameworks Introduced
- **Domain Model pattern**: the domain is the problem you're solving; the model is the business owners' mental map of it. Jargon = distilled understanding; listen and encode it.
  - How: hold a conversation with domain experts, agree a glossary and rules, ask for *concrete examples* of each rule, use their jargon (the **ubiquitous language**) for classes, variables, and test names.
- **Entity**: domain object with long-lived identity; equality by identity (`__eq__` on `reference`), `__hash__` from the identity attribute (ideally read-only) — or make it unhashable. Never change `__hash__` without `__eq__`.
- **Value Object**: identified only by its data, no identity; implement as immutable (`@dataclass(frozen=True)`, `NamedTuple`, `namedtuple`). Gives value equality; hash from all attributes. Can carry behavior (e.g. `Money.__add__` raising ValueError on mixed currencies).
- **Domain Service function**: an operation with no natural home on an entity/value object. In Python, just make it a function (`allocate(line, batches)`). Domain service ≠ service-layer service (domain service = business concept; service layer = application use case).
- **Domain exceptions**: name exceptions in the ubiquitous language (`OutOfStock`).

## Key Concepts
- **SKU**: stock-keeping unit; product identifier. **OrderLine**: sku + qty within an order (value object). **Batch**: reference, sku, qty, optional eta (entity). **Allocation**: linking an OrderLine to a Batch.
- **Magic methods as domain semantics**: `__gt__` on Batch makes `sorted(batches)` mean "warehouse stock first, then earliest ETA".
- **Idempotent allocate**: storing `_allocations` in a `set` makes double allocation a no-op.
- **`available_quantity`** is derived: `_purchased_quantity - allocated_quantity`.

## Mental Models
- Use a value object when there is data but no identity; an entity when it has to remain "the same thing" while attributes change (people change names; names don't).
- Let the "verbs" be functions: a `FooManager`/`BarBuilder`/`BazFactory` is often a `manage_foo()`/`build_bar()`/`get_baz()` waiting to happen.
- This is the place to apply best OO design: SOLID, has-a vs is-a, composition over inheritance.

## Anti-patterns
- **`NewType` wrapping of every primitive** (`Quantity`, `Sku`, `Reference`): authors call it "appalling" — don't.
- **Silent failure**: `allocate()`/`deallocate()` that quietly do nothing (acknowledged weakness of the first cut).
- **Starting from the DB schema** instead of the behavior.

## Code Examples
```python
@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int

class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()  # type: Set[OrderLine]
    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)
    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)
    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)
    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity
    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty
    def __eq__(self, other):
        return isinstance(other, Batch) and other.reference == self.reference
    def __hash__(self): return hash(self.reference)
    def __gt__(self, other):
        if self.eta is None: return False
        if other.eta is None: return True
        return self.eta > other.eta

def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
    except StopIteration:
        raise OutOfStock(f'Out of stock for sku {line.sku}')
    batch.allocate(line)
    return batch.reference
```
- **What it demonstrates**: entity + value object + domain service + domain exception, all in business language.

## Worked Example
Business rules from the expert conversation → tests:
1. "Allocating 2 SMALL-TABLE to a batch of 20 leaves 18" → `test_allocating_to_a_batch_reduces_the_available_quantity`.
2. "Can't allocate if available < required; equal is OK; SKUs must match" → four `can_allocate` tests built with a `make_batch_and_line(sku, batch_qty, line_qty)` helper.
3. "Can't allocate the same line twice" → `test_allocation_is_idempotent` — forces replacing a decrementing integer with a `set` of allocations (and makes `deallocate` of an unallocated line a no-op).
4. "Prefer warehouse stock (eta=None), then earliest ETA" → `allocate(line, [medium, earliest, latest])` asserts only `earliest` decreased; implemented via `sorted()` + `__gt__`.
5. "Out of stock" → `pytest.raises(OutOfStock, match='SMALL-FORK')`.
Why it works: the tests read as the agreed examples, so non-technical colleagues can validate them. Failure mode: a model that is "too trivial" tempts you to skip it; real rules (regional warehouses, delivery dates, on-demand SKUs) pile on quickly.

## Key Takeaways
1. This layer is closest to the business and most likely to change — make it easy to understand and modify.
2. Distinguish entities (identity) from value objects (data, immutable).
3. Not everything has to be an object; use functions for domain services.
4. Express domain concepts in names, magic methods, and exceptions.
5. Read a real DDD book (Evans "blue book", Vernon "red book"); this isn't one.

## Connects To
- **Ch 2**: persisting this model without contaminating it. **Ch 7**: aggregates and consistency boundaries. **App. E**: validation.
