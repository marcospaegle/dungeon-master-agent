# Chapter 8: Events and the Message Bus

## Core Idea
Side effects ("when X happens, then Y") don't belong in controllers, the model, or the service layer. Have the model *record* domain events as facts, and let a message bus map events to handlers, so each unit of work stays single-purpose.

## Frameworks Introduced
- **Domain Events pattern**: an event is a value object (plain `@dataclass`, no behavior), named in domain language, subclassing an `Event` base class. The aggregate has `.events: List[Event]` and appends to it (e.g. `OutOfStock(sku)`). Don't also raise an exception for the same domain concept — events replace exception-as-control-flow (`allocate` now returns `None` when out of stock).
- **Message Bus pattern**: a dict `HANDLERS: Dict[Type[Event], List[Callable]]` + `handle(event)` that calls each subscribed handler. Simple publish/subscribe; "dumb infrastructure". Synchronous, no concurrency — the aim is conceptual separation and small UoWs.
- **Three ways to get events to the bus**:
  1. Service layer catches/uses events from the model and calls `messagebus.handle(product.events)` (e.g. in `finally`).
  2. Service layer creates and raises events itself (`if batchref is None: messagebus.handle(events.OutOfStock(sku))`).
  3. **UoW publishes events** (preferred, most elegant): `commit()` = `_commit()` then `publish_events()`; repository tracks loaded aggregates in `.seen`; UoW pops each `.events` and calls the bus. Service layer becomes free of event concerns.
- **Single Responsibility Principle test**: if you can't describe a function without "then" or "and" (`allocate_and_send_mail_if_out_of_stock`), it's violating SRP; a class should have one reason to change.
- **Choreography vs orchestration**: event-based flow replaces orchestration with choreography.

## Key Concepts
- **Domain event**: fact about what happened, past-tense in business language. **Handler**: function subscribed to an event. **`.seen`**: set of aggregates passed through the repository.
- **"When X, then Y"**: causal/temporal phrases from domain experts reveal events.
- **Eventual consistency**: use events to coordinate changes across transactionally isolated aggregates (e.g. order canceled → remove allocations from products).
- **Not Celery**: bus is like a UI event loop/actor framework; for async/off-thread work, persist events to a central store and subscribe other processes (external events).

## Mental Models
- Use events when requirements bolt on "goop around the edge" (notifications, reporting, permissions, workflows touching many objects).
- Think of the domain model's job as *knowing* it's out of stock; sending alerts is someone else's responsibility.
- Prefer composition: a `TrackingRepository` wrapper (`seen` + delegate) avoids the `_add/_get` underscore-method subclass pattern; `typing.Protocol` forces you off inheritance.

## Anti-patterns
- **Sending email in the Flask endpoint / in the model / in the service layer**.
- **try/except-reraise of OutOfStock** just to trigger side effects.
- **Hidden magic**: commit also sends emails; handlers run synchronously so the request is slow; events spread flow across many handlers (no single place to understand a request); circular handler dependencies / infinite loops.

## Code Examples
```python
@dataclass
class OutOfStock(Event):
    sku: str

class Product:
    def __init__(self, sku, batches, version_number=0):
        ...
        self.events = []  # type: List[events.Event]
    def allocate(self, line):
        try:
            ...
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            return None

def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)

HANDLERS = {events.OutOfStock: [send_out_of_stock_notification]}

class AbstractUnitOfWork(abc.ABC):
    def commit(self):
        self._commit()
        self.publish_events()
    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                messagebus.handle(product.events.pop(0))
```
- **What it demonstrates**: model records, UoW publishes, bus dispatches.

## Reference Tables
| Pros | Cons |
|---|---|
| Separates responsibilities when several actions follow a request | Extra concept; UoW-raises-events is magic (commit sends email) |
| Handlers decoupled from core logic | Synchronous: slow endpoints |
| Events are business language | No single place to see how a request is fulfilled |
| | Circular dependency / infinite loop risk |

## Worked Example
Requirement: email buying team when out of stock. Test: `test_records_out_of_stock_event_if_cannot_allocate` — allocate 10 of a 10-unit SMALL-FORK batch, then 1 more; assert `product.events[-1] == events.OutOfStock(sku="SMALL-FORK")` and `allocation is None`. Wire: `HANDLERS = {events.OutOfStock: [send_out_of_stock_notification]}`. Fakes must call `super().__init__()` and implement `_add`, `_get`, `_commit`. Why it works: the use case is still just `allocate`; changing email→SMS touches only the handler.

## Key Takeaways
1. Events help with SRP and cross-aggregate communication without long multi-table transactions.
2. A message bus is a dict from events to consumers.
3. Start simple (option 1), move rules into the model (option 2), tidy via UoW (option 3).
4. Treat "when X then Y" as a domain-event cue.

## Connects To
- **Ch 7**: aggregates need events to coordinate. **Ch 9**: bus becomes the main entrypoint. **Ch 10**: error handling in handlers. **Ch 11**: external events. **Ch 3/13**: mock.patch email → DI.
