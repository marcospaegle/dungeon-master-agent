# Chapter 7: Aggregates and Consistency Boundaries

## Core Idea
Nominate a small cluster of domain objects as an Aggregate with a single root entrypoint that guards invariants. The aggregate is the consistency boundary: one transaction per aggregate, which is what lets you scale without locking everything.

## Frameworks Introduced
- **Aggregate pattern** (DDD): "a cluster of associated objects that we treat as a unit for the purpose of data changes" (Evans). Only modify inner objects by loading the whole aggregate and calling methods on the root. Aggregates are the "public classes" of the model; the rest are "private".
- **Choosing an aggregate**: draw a boundary around the *smallest* set of objects that must be consistent with each other; give it a good name. Shipment/Warehouse had wrong granularity (can't allocate DEADLY-SPOON and FLIMSY-DESK concurrently); chosen: **Product** (sku + its batches), identified by sku. There is no one correct aggregate; revisit if performance suffers.
- **One Aggregate = One Repository**: repositories return only aggregates (`ProductRepository`, `uow.products`); this enforces "aggregates are the only way in".
- **Bounded context**: model only data needed for the calculations in this context (allocation's `Product(sku, batches)` vs ecommerce `Product(sku, description, price, ...)`); each microservice owns its own notion of a concept.
- **Optimistic concurrency with version numbers**: Product has `version_number`, incremented on each `allocate`; concurrent transactions both try to update the product row → one loses. Retry the failed operation from the start (re-reads fresh state; may now raise OutOfStock).
- **Pessimistic alternative**: `SELECT ... FOR UPDATE` (`.with_for_update()` in repo `get`) turns read1,read2,write1,write2(fail) into read1,write1,read2,write2(succeed).

## Key Concepts
- **Invariant**: condition always true when an operation finishes. **Constraint**: rule restricting possible states.
- **Consistency boundary**: scope within which invariants hold transactionally; across boundaries = eventual consistency.
- **Isolation level**: `REPEATABLE READ` set on the engine makes Postgres reject concurrent updates ("could not serialize access due to concurrent update"). Definitions differ per DB (Oracle SERIALIZABLE ≈ Postgres REPEATABLE READ).
- **Read-modify-write failure mode**.

## Mental Models
- Use version numbers as "something that changes on every write" to a row you fight over (could equally be a UUID).
- Where to put the version number: (1) domain — `Product.allocate` increments (chosen: cleanest trade-off), (2) service layer (mixes state mutation), (3) UoW/repo magic (assumes everything changed).
- Performance of loading all batches: single read + single write per use case, few small rows, ~20 active batches per product; lazy-load if thousands.
- Rule: modify one aggregate per transaction.

## Anti-patterns
- **Locking whole tables** for every allocation (deadlocks, poor throughput).
- **"CSV over SMTP" spreadsheet architecture**: low initial complexity, can't maintain constraints/consistency.
- **Repositories for non-aggregates**.
- **Copy-pasting concurrency code**: requirements vary; evaluate and measure.

## Code Examples
```python
class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            raise OutOfStock(f'Out of stock for sku {line.sku}')

def allocate(orderid: str, sku: str, qty: int, uow) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f'Invalid sku {line.sku}')
        batchref = product.allocate(line)
        uow.commit()
        return batchref
```
- **What it demonstrates**: domain service becomes an aggregate method; service layer fetches the aggregate by sku.

## Reference Tables
| Pros | Cons |
|---|---|
| Choose which classes are public vs internal | A third kind of domain object to learn |
| Avoids ORM performance problems via explicit boundaries | "One aggregate per transaction" is a big mental shift |
| Sole charge of state changes → easier invariants | Eventual consistency between aggregates can be complex |

| Concurrency | Mechanism | Failure handling |
|---|---|---|
| Optimistic | version number + REPEATABLE READ | must retry |
| Pessimistic | SELECT FOR UPDATE | no failures, beware deadlocks |

## Worked Example
Concurrency test: `try_to_allocate(orderid, sku, exceptions)` runs `with SqlAlchemyUnitOfWork() as uow: product = uow.products.get(sku); product.allocate(line); time.sleep(0.2); uow.commit()`, appending any exception. `test_concurrent_updates_to_version_are_not_allowed` inserts a batch (product_version=1), starts two threads, joins, then asserts: version == 2 (incremented once), exactly one exception containing 'could not serialize access due to concurrent update', and exactly one row in `allocations`. Use the test to compare REPEATABLE READ vs FOR UPDATE and as a perf-experiment base. (Sleep is crude; prefer semaphores.)

## Key Takeaways
1. Aggregates are entrypoints into the domain model.
2. Aggregates own a consistency boundary and its invariants.
3. Aggregate choice is a performance decision as much as a conceptual one.
4. Part I result: DB-agnostic domain models, living-documentation tests, healthy pyramid. If your app is simple CRUD, skip all this and use Django.

## Connects To
- **Ch 8-9**: cross-aggregate processes via events (eventual consistency). **Ch 12**: reads bypass aggregates. **Footguns (Epilogue)**: retries.
