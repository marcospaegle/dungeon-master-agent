# Chapter 2: Repository Pattern

## Core Idea
Apply DIP to data access: the ORM imports the domain model (never the reverse), and a Repository gives the illusion that all objects live in an in-memory collection, which makes faking storage trivial.

## Frameworks Introduced
- **Repository pattern**: abstraction over persistent storage that "pretends all of our data is in memory".
  - When to use: domain complex enough that decoupling from infrastructure pays off (not for simple CRUD).
  - How: simplest repo has just `add()` and `get()`. Stick rigidly to them in domain and service layer. Caller owns `commit()`. No `.save()`; fetch, mutate in memory. Deletes are soft (`batch.cancel()`); updates handled by Unit of Work (Ch 6).
- **Inverting the dependency (classical mapping)**: define tables separately with SQLAlchemy `Table`, then `start_mappers()` binds model classes to tables. If you never call `start_mappers()`, the model stays unaware of the DB. Keeps alembic migrations.
- **Persistence ignorance**: the model need not know how it is loaded/saved.
- **Ports and Adapters** (= hexagonal = onion = clean architecture — all names for DIP): *port* = interface between app and what you abstract; *adapter* = implementation behind it. In Python the ABC is the port, or, with duck typing, the method names + argument types your core expects. Here `AbstractRepository` = port; `SqlAlchemyRepository`, `FakeRepository` = adapters.

## Key Concepts
- **ORM**: bridges objects and relational tables; declarative style makes the model depend on ORM (bad here).
- **Onion architecture**: dependencies flow inward toward the model.
- **Fake**: working in-memory test-only implementation (`FakeRepository` wraps a `set`).
- **PEP 544 protocols**: typing for duck types without inheritance; alternative to ABCs.

## Mental Models
- Use "ORM depends on model" when you want a pure model; accept the trade-off ("practicality beats purity") if the ORM fights your model.
- Think of building a fake as design feedback: if it's hard to fake, the abstraction is too complicated.
- The more complex the domain, the more decoupling pays off (Fig 2-6: simple CRUD → plain ORM/ActiveRecord wins).

## Anti-patterns
- **Declarative ORM models as domain classes** (Django models / SQLAlchemy declarative): model properties coupled to DB columns.
- **ABCs left unmaintained**: authors sometimes delete them in production because they rot and mislead; duck typing + linters may suffice.
- **Keeping throwaway ORM tests** once the repository tests exist.

## Code Examples
```python
class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch): raise NotImplementedError
    @abc.abstractmethod
    def get(self, reference) -> model.Batch: raise NotImplementedError

class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session): self.session = session
    def add(self, batch): self.session.add(batch)
    def get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).one()
    def list(self): return self.session.query(model.Batch).all()

class FakeRepository(AbstractRepository):
    def __init__(self, batches): self._batches = set(batches)
    def add(self, batch): self._batches.add(batch)
    def get(self, reference): return next(b for b in self._batches if b.reference == reference)
    def list(self): return list(self._batches)

# orm.py
def start_mappers():
    lines_mapper = mapper(model.OrderLine, order_lines)
```
- **What it demonstrates**: one port, two adapters; mapping defined outside the model.

## Reference Tables
| Pros | Cons |
|---|---|
| Simple interface between storage and model | ORM already buys some decoupling (MySQL↔Postgres) |
| Easy fakes; swap storage (App. C) | Hand-maintained mappings = extra code |
| Model before schema; no FK/migration worries early | Extra indirection, "WTF factor" for newcomers |
| Simple schema, full mapping control | |

## Worked Example
Test-first repository: (1) `test_repository_can_save_a_batch` — `repo.add(batch)`, `session.commit()` outside the repo, assert via raw SQL rows `[("batch1","RUSTY-SOAPDISH",100,None)]`. (2) `test_repository_can_retrieve_a_batch_with_allocations` — insert order line, two batches, one allocation with raw SQL helpers; `repo.get("batch1")` then assert `==` (entity equality compares only reference) *and* explicitly check `sku`, `_purchased_quantity`, and `_allocations == {OrderLine(...)}`. Keep these integration tests long-term when the mapping is nontrivial (here, the `_allocations` set). Failure mode if skipped: relationship mapping silently breaks. Whether to test every model is a judgment call — one fully-tested class, then minimal round-trips for similar ones.

## Key Takeaways
1. ORM imports model; model imports nothing infrastructural.
2. Repository = in-memory collection illusion; `add`/`get` only.
3. FakeRepository makes service tests fast and trivial.
4. The pattern is among the easiest in the book once you're doing DDD + DIP.
5. For plain CRUD apps, skip it.

## Connects To
- **Ch 3**: abstraction choice. **Ch 4**: service layer uses the repo. **Ch 6**: Unit of Work owns commit. **App. C**: swap to CSV/CLI. **App. D**: Django.
