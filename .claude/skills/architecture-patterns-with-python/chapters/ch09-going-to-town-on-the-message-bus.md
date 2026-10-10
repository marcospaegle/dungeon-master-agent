# Chapter 9: Going to Town on the Message Bus

## Core Idea
Make events fundamental: every input to the system (API call or internal fact) becomes a message, every service-layer function becomes a handler, and the app becomes a message processor. New requirements then reduce to "new event + handler" with no architectural change.

## Frameworks Introduced
- **Everything is an event handler**: `services.allocate` → handler for `AllocationRequired`; `add_batch` → handler for `BatchCreated`; new `change_batch_quantity` → handler for `BatchQuantityChanged`. Handlers and services are the same thing; all take `(event, uow)`.
- **Preparatory Refactoring** ("make the change easy; then make the easy change"): (1) refactor services into event handlers, (2) build end-to-end test with new events, (3) implement new handler emitting events the existing allocate handler already processes.
- **Bus collects events from UoW with a queue**: bus owns the loop; UoW's `publish_events` becomes `collect_new_events()` (a generator) → one-way dependency (UoW no longer imports messagebus).
- **Events as the interface** (vs primitives vs domain objects): primitives decoupled clients from the model; now clients couple to event classes (change less often, part of domain) and invoke a use case with one object; events are a good place for input validation (App. E).
- **Reallocation flow**: `BatchQuantityChanged` → handler → `Product.change_batch_quantity` sets quantity, `while batch.available_quantity < 0: line = batch.deallocate_one(); events.append(AllocationRequired(...))` → each handled by the *same* allocate handler in a *separate* transaction.

## Key Concepts
- **Situated software** (Hickey): long-running software managing real-world processes; surprises happen (water-damaged mattresses, customs holds).
- **Event storming**: workshop practice for event-based requirements/domain modeling.
- **Primitive obsession**: OO anti-pattern; Pythonistas skeptical of mindless application.
- **Fake message bus**: `FakeUnitOfWorkWithFakeMessageBus.publish_events` records `events_published` for isolated handler tests.
- **Repository query additions**: `get_by_batchref` is OK because it returns a single aggregate; complex queries (`get_most_popular_products`, `find_products_by_order_id`) are a smell → see Ch 11/12.

## Mental Models
- Use edge-to-edge tests via the real bus first; only isolate handlers with a fake bus when event chains get complex.
- Goal: complexity of app grows more slowly than its size; moving parts (events, handlers, adapters) each have one job.
- Two transactions (deallocate commit, then reallocate) can leave inconsistent state if the second fails — decide if acceptable, detect it (Footguns).

## Anti-patterns
- **Bus returning handler results** (temporary hack, `results.append(handler(...))`), because reads and writes are mixed → fixed in Ch 12.
- **Duplicated fields** between model objects and events (maintenance cost).
- Unpredictable "when does it end" from a web viewpoint.

## Code Examples
```python
def handle(event: events.Event, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [event]
    while queue:
        event = queue.pop(0)
        for handler in HANDLERS[type(event)]:
            results.append(handler(event, uow=uow))
        queue.extend(uow.collect_new_events())
    return results

HANDLERS = {
    events.BatchCreated: [handlers.add_batch],
    events.BatchQuantityChanged: [handlers.change_batch_quantity],
    events.AllocationRequired: [handlers.allocate],
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}

def change_batch_quantity(event: events.BatchQuantityChanged, uow):
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()
```
- **What it demonstrates**: queue-driven bus; thin handler delegating to the model.

## Reference Tables
| Pros | Cons |
|---|---|
| Handlers = services (simpler) | Unpredictable end of processing from a web viewpoint |
| Clean data structure for system inputs | Field duplication between model and events |

## Worked Example
`test_reallocates_if_necessary`: history = `BatchCreated("batch1","INDIFFERENT-TABLE",50,None)`, `BatchCreated("batch2",...,50,date.today())`, `AllocationRequired("order1",...,20)`, `AllocationRequired("order2",...,20)`, all via `messagebus.handle(e, uow)`. Assert batch1 available 10, batch2 50. Send `BatchQuantityChanged("batch1", 25)` → one order deallocated (25−20 = 5 available on batch1) and reallocated to the later batch2 (available 30). Isolated variant: with the fake-bus UoW, assert `[reallocation_event] = uow.events_published` is an `AllocationRequired` with orderid in `{'order1','order2'}`. Flask: `event = events.AllocationRequired(...)`; `results = messagebus.handle(event, SqlAlchemyUnitOfWork()); batchref = results.pop(0)`.

## Key Takeaways
1. Events are simple dataclasses defining inputs and internal messages; they translate to business language.
2. Handlers can call the model, call external services, or raise more events; multiple handlers per event allowed.
3. A complicated use case (change, deallocate, new transaction, reallocate, notify) added with zero new architectural categories.
4. Class-based bus (Ch 13) is a better long-term shape than module singleton.

## Connects To
- **Ch 10**: commands vs events (these "events" are really commands). **Ch 12**: remove result-returning hack. **App. E**: validation.
