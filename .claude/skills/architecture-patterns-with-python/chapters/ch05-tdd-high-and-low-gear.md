# Chapter 5: TDD in High Gear and Low Gear

## Core Idea
With a service layer, write most tests against it (high gear, low coupling, edge-to-edge) and keep a small set of domain-model tests (low gear) for design feedback. Express the service API in primitives so tests and clients are decoupled from the model.

## Frameworks Introduced
- **Test pyramid** (target): ~one E2E per feature; bulk at service layer; small core of domain-model tests. Example count after Ch 4: 15 unit, 8 integration, 2 E2E.
- **High gear / low gear**:
  - High gear (default for features/bug fixes): tests against services — less coupling, more coverage.
  - Low gear (new project, gnarly problem): tests against domain model — best design feedback and executable documentation.
- **Coupling vs design-feedback spectrum**: HTTP tests survive a full rewrite (confidence for big changes, zero design feedback); domain tests give design feedback in domain language (living documentation) but pin the implementation. "Every line of code in a test is a blob of glue holding the system in a particular shape."
- **Primitives in the service API**: `allocate(orderid: str, sku: str, qty: int, repo, session)`.
- **Mitigation ladder** for domain dependencies in service tests: (1) keep model construction in fixture/factory functions (`FakeRepository.for_batch(...)`); (2) add the missing service (`add_batch`) and use it for setup; (3) add an API endpoint (`/add_batch`) so E2E tests need no SQL.

## Key Concepts
- **Edge-to-edge test**: service layer + fakes for I/O.
- **Living documentation**: domain tests written in the ubiquitous language.
- **Error handling counts as a feature**: handle uniformly at entrypoints; test happy path per feature, one E2E for all unhappy paths.

## Mental Models
- Use service-layer tests when changing behavior without redesigning the model; drop to domain tests to sketch/design, then delete them if the service layer covers it.
- If you need domain-layer stuff directly in service tests, the service layer is probably incomplete (but don't add a service solely to remove test dependencies unless you'd need it anyway).

## Anti-patterns
- **Too many domain-model tests**: refactoring breaks tens/hundreds of tests.
- **Tests that reach into private attributes** (`_allocations`).
- **Hardcoded SQL in E2E fixtures** (`add_stock`) — replace with API calls.
- Caveat: higher-level tests can cause combinatorial explosion in complex use cases; drop down to domain unit tests then (see Ch 8/9 fake message bus).

## Code Examples
```python
def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], repo: AbstractRepository, session):
    repo.add(model.Batch(ref, sku, qty, eta))
    session.commit()

def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, repo, session)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)
    assert result == "batch1"
```
- **What it demonstrates**: service tests fully expressed in services and primitives — free to refactor the model.

## Worked Example
The domain test `test_prefers_current_stock_batches_to_shipments` is rewritten as service test `test_prefers_warehouse_batches_to_shipments` (build batches, wrap in `FakeRepository`, call `services.allocate(line, repo, session)`, assert quantities). Then decouple stepwise: replace `OrderLine` param by primitives → still instantiating `Batch` → factory `FakeRepository.for_batch("batch1","COMPLICATED-LAMP",100,eta=None)` → finally `add_batch` service. Endpoint `/add_batch` (parse `eta` via `datetime.fromisoformat(eta).date()`, return `'OK', 201`) removes SQL from `conftest`; E2E uses `post_to_add_batch(ref, sku, qty, eta)`.

## Reference Tables
| Test level | Quantity | Purpose |
|---|---|---|
| E2E (HTTP) | one per feature | wiring works |
| Service layer | bulk; all edge cases | coverage, speed, low coupling |
| Domain model | small core | design feedback; deletable |

## Key Takeaways
1. Aim for one E2E test per feature.
2. Write the bulk of tests against the service layer.
3. Keep a small core of domain tests; delete when redundant.
4. Express services in primitives; have all services needed for setup.
5. Fast test suite (seconds/minutes vs "wait 'til tomorrow") changes team behavior.

## Connects To
- **Ch 3**: fakes vs mocks. **Ch 6**: UoW replaces FakeSession. **Ch 9**: fake message bus unit tests.
