# Chapter 12: Command-Query Responsibility Segregation (CQRS)

## Core Idea
Reads and writes are different: domain models are for writing. Separate them (command-query separation), and when the domain is rich enough, serve reads from simple, possibly denormalized and eventually-consistent read models kept up to date by event handlers.

## Frameworks Introduced
- **Reads vs writes** (Table 12-1): Read side = simple read, highly cacheable, can be stale. Write side = complex business logic, uncacheable, transactionally consistent. "Most users aren't going to buy your furniture": 100 orders/hour vs 100 product views/second.
- **Stale data is unavoidable**: data is stale the moment it renders; you always re-check at allocation time; reality (the forklift drops the dresser) is always inconsistent with software → business processes cope. So trading read consistency for performance is safe.
- **Command-Query Separation (CQS)**: functions either modify state or answer questions, never both ("Are the lights on?" without flicking the switch). Post/Redirect/Get is a web example; API returns `202 Accepted` plus a read endpoint (`GET /allocations/<orderid>`). Fixes Ch 9's result-returning bus hack.
- **CQRS options ladder** (pick the simplest that works):
  1. Use repositories (add `for_order()`, `Batch.orderids`): consistent but clunky; Python loops/filters instead of DB.
  2. Use ORM queries: another query language; possible SELECT N+1 (SQLAlchemy mostly avoids; use eager loading).
  3. Hand-rolled SQL in `views.py`: fine control, performance, "SQL is just SQL".
  4. Separate denormalized read store (`allocations_view` table, or Redis hash) updated by event handlers on `Allocated` / `Deallocated`.
- **Rebuilding a view model**: write a tool that queries write-side state and calls the read-model handler for each item; also create new read models from history. Event handlers make swapping read storage (SQL→Redis) trivial; same integration tests pass.

## Key Concepts
- **View model / read model**: query-optimized structure; no foreign keys needed.
- **Read replicas scale horizontally** because no write locks; inconsistency allows unlimited copies.
- **Views module separation**: even without full CQRS, keep read-only code (`views.py`) apart from state-changing handlers.
- **Domain model ≠ data model**: workflows/rules irrelevant for reads.

## Mental Models
- Use plain repositories/ORM when reads act on the same conceptual objects as writes; go to raw SQL/read stores when reads concern different entities (users want allocations per *order*, domain thinks in batches per *SKU*).
- Ask "can I build a simpler read model?" when struggling to scale a complex store.
- Ask "what happens when it breaks?" first — read model failures are just independent event failures; the allocate service still protects correctness.

## Anti-patterns
- **Returning data from a write endpoint** (200 + batchref).
- **Forcing the domain model to serve reads** (adding helpers, looping in Python).
- **Test setup via internals** — set up integration tests through the message bus.
- Full CQRS where a simple CRUD/domain model suffices.

## Code Examples
```python
def allocations(orderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = list(uow.session.execute(
            'SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid',
            dict(orderid=orderid)))
        return [{'sku': sku, 'batchref': batchref} for sku, batchref in results]

EVENT_HANDLERS = {
    events.Allocated: [handlers.publish_allocated_event, handlers.add_allocation_to_read_model],
    events.Deallocated: [handlers.remove_allocation_from_read_model, handlers.reallocate],
}

def add_allocation_to_read_model(event: events.Allocated, uow):
    with uow:
        uow.session.execute(
            'INSERT INTO allocations_view (orderid, sku, batchref) VALUES (:orderid, :sku, :batchref)',
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref))
        uow.commit()

# Redis read model
def update_readmodel(orderid, sku, batchref): r.hset(orderid, sku, batchref)
def get_readmodel(orderid): return r.hgetall(orderid)
```
- **What it demonstrates**: read side = trivial query; write side keeps it fresh via events.

## Reference Tables
| Option | Pros | Cons |
|---|---|---|
| Repositories | Simple, consistent | Perf issues with complex queries |
| ORM custom queries | Reuse DB config/models | Another query language |
| Hand-rolled SQL | Fine control, standard syntax | Schema changes in two places; normalized schemas still slow |
| Separate read store via events | Scales out; simple queries | Complex; suspicion |

## Worked Example
E2E: `POST /allocate` returns 202, then `api_client.get_allocation(orderid)` returns `[{'sku': sku, 'batchref': earlybatch}]`; unhappy path: POST returns 400 `Invalid sku`, then GET returns 404. Integration test `test_allocations_view`: create batches `sku1batch`, `sku2batch`, allocate `order1` for both SKUs, add spurious `sku1batch-later` and `otherorder` allocations to verify filtering; assert `views.allocations('order1', uow)` equals both entries. Setup uses `messagebus.handle(commands.CreateBatch(...))` so it works for any storage option.

## Key Takeaways
1. Domain models are for writing; reads need not use them.
2. Splitting read-only views from handlers is worthwhile even without full CQRS.
3. Denormalized read models updated by event handlers are easy to rebuild and swap.
4. MADE.com's real allocation service uses Redis read model plus Varnish — but this book's service probably wouldn't need it.

## Connects To
- **Ch 9/10**: bus result hack and command handling. **Ch 11**: Redis. **Ch 13**: bootstrap. **Epilogue**: query complexity.
