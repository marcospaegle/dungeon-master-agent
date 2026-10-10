# Chapter 6: Unit of Work Pattern

## Core Idea
If Repository abstracts storage, Unit of Work (UoW) abstracts *atomic operations*: a context manager that is the single entrypoint to persistence, hands out repositories, and commits or rolls back as a block. It fully decouples the service layer from the data layer.

## Frameworks Introduced
- **Unit of Work pattern**: gives (1) a stable snapshot of the DB during an operation, (2) all changes persisted at once (no inconsistent partial state), (3) a simple persistence API and a place to get repositories (`uow.batches`).
  - How: `with uow:` → `uow.batches.get/list/add` → `uow.commit()`. `__exit__` calls `rollback()`; rollback is a no-op after commit.
- **Explicit commit, rollback by default**: authors prefer requiring `uow.commit()` (safe by default; only one path leads to change: total success + explicit commit; any exception or early exit is safe). Alternative implicit-commit-on-clean-exit saves a line but is less safe.
- **"Don't mock what you don't own"**: fake your own thin UoW, not SQLAlchemy `Session` (complex, invites ad hoc queries all over the code). Forces building simple abstractions over messy subsystems with the same test-speed benefit.
- **Collaborators**: `FakeUnitOfWork` and `FakeRepository` are tightly coupled by design, like their real counterparts.

## Key Concepts
- **Context manager** (`__enter__`/`__exit__`): idiomatic Python scoping; `@contextmanager` is a functional alternative.
- **Session factory injection**: `SqlAlchemyUnitOfWork(session_factory=DEFAULT_SESSION_FACTORY)` lets integration tests use SQLite.
- **Object neighborhoods**: clusters of collaborating objects (responsibility-driven design).

## Mental Models
- Use a UoW whenever several operations must succeed or fail together (reallocate = deallocate + allocate; change batch quantity = change qty + deallocate lines until `available_quantity >= 0`).
- SQLAlchemy `Session` already *is* a UoW; wrap it to narrow the interface (start, commit, discard) and to expose repositories.
- Atomicity isn't only about transactions — later it governs events and the message bus.

## Anti-patterns
- **Passing `session` into services** (service coupled to the ORM).
- **Mocking `Session`** directly.
- **Keeping all three DB test files**: `test_orm.py` was a learning tool; consider discarding in favor of the highest abstraction level.
- Ignoring rollbacks, multithreading, nested transactions complexity.

## Code Examples
```python
class AbstractUnitOfWork(abc.ABC):
    batches: repository.AbstractRepository
    def __exit__(self, *args):
        self.rollback()
    @abc.abstractmethod
    def commit(self): raise NotImplementedError
    @abc.abstractmethod
    def rollback(self): raise NotImplementedError

class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory
    def __enter__(self):
        self.session = self.session_factory()  # type: Session
        self.batches = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()
    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()
    def commit(self): self.session.commit()
    def rollback(self): self.session.rollback()

class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.batches = FakeRepository([])
        self.committed = False
    def commit(self): self.committed = True
    def rollback(self): pass

def allocate(orderid: str, sku: str, qty: int, uow) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f'Invalid sku {line.sku}')
        batchref = model.allocate(line, batches)
        uow.commit()
    return batchref
```
- **What it demonstrates**: service depends only on an abstract UoW.

## Reference Tables
| Pros | Cons |
|---|---|
| Visual grouping of atomic code; safe by default | ORM already has atomicity abstractions; passing a session may suffice |
| Explicit transaction start/finish | Rollbacks, threading, nested transactions need care |
| One place to reach all repositories | |
| Helps with events/message bus later | |

## Worked Example
Integration tests drive the UoW: `test_uow_can_retrieve_a_batch_and_allocate_to_it` (insert batch via SQL; `with uow: batch = uow.batches.get(reference='batch1'); batch.allocate(line); uow.commit()`; read back via SQL), `test_rolls_back_uncommitted_work_by_default` (insert inside `with`, no commit; a *new* session sees `[]`), `test_rolls_back_on_error` (raise inside `with pytest.raises(MyException)`; new session sees `[]`). Service tests then use `FakeUnitOfWork` asserting `uow.committed`. Reallocate example: `batch.deallocate(line); allocate(line); uow.commit()` — if allocate fails, the deallocate is never committed.

## Key Takeaways
1. UoW = abstraction around data integrity; each use case runs in one UoW that succeeds or fails as a block.
2. Context managers make system safe by default.
3. Prefer explicit commit.
4. Narrow the ORM interface; depend on a thin abstraction, attach the concrete one at the system edge.
5. Test rollback behavior against the real engine when it matters.

## Connects To
- **Ch 2**: repository. **Ch 4**: service layer. **Ch 7**: aggregates (`uow.products`). **Ch 8/9**: UoW collects events.
