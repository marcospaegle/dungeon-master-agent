# Chapter 11: Event-Driven Architecture: Using Events to Integrate Microservices

## Core Idea
Extend the message-processor model outward: consume external messages (Redis pub/sub) as commands and publish internal events externally, replacing temporally coupled HTTP calls between services with asynchronous messaging. Avoid the Distributed Ball of Mud.

## Frameworks Introduced
- **Distributed Ball of Mud / thinking in nouns**: one microservice per entity/table (Orders, Batches, Warehouse, Customers) with CRUD-over-HTTP anemic models → tangled dependency graph (Orders drives Batches drives Warehouse; Warehouse drives Batches drives Orders) and failure cascades.
- **Think in verbs, not nouns**: model processes (a system for *ordering*, a system for *allocating*) — domain model is a model of a verb. When placing an order, make sure the order is placed; everything else can happen later.
- **Temporal decoupling via asynchronous messaging**: microservices are consistency boundaries like aggregates; accept eventual consistency between services. Each service accepts commands from outside and raises events recording results.
- **Connascence** (types of coupling; strong locally, weak at a distance): Connascence of *Execution* (components must know correct order), of *Timing* (things must happen one after another), replaced by weaker Connascence of *Name* (agree only on event name and field names).
- **Message broker**: Redis pub/sub for the book (MADE.com uses Event Store; Kafka/RabbitMQ valid).
- **Event consumer / event publisher adapters**: consumer (entrypoint like Flask) deserializes JSON → `commands.ChangeBatchQuantity` → `messagebus.handle(cmd, uow)`. Publisher (downstream adapter) `r.publish(channel, json.dumps(asdict(event)))`.
- **Internal vs external events**: keep the distinction explicit; not all events are published; validate outbound events (App. E); crucial with event sourcing.

## Key Concepts
- **Temporal coupling**: every part must work at once for any to work; failure probability grows with system size.
- **Allocated event**: `orderid, sku, qty, batchref`, emitted from `Product.allocate()`.
- **At-least-once vs at-most-once delivery, ordering, idempotency**: not covered; see Footguns.

## Mental Models
- Use async events between services so one can be degraded (still take orders if allocation is down) and flows can be reordered locally.
- Event notification implies low coupling but hides the overall logical flow (Fowler quote) — hard to debug/modify.

## Anti-patterns
- **Noun-based services with HTTP CRUD**.
- **Synchronous command chains across services** (RPC style).
- **Treating publishing as "just another side effect" without validation**.

## Code Examples
```python
def handle_change_batch_quantity(m):
    logging.debug('handling %s', m)
    data = json.loads(m['data'])
    cmd = commands.ChangeBatchQuantity(ref=data['batchref'], qty=data['qty'])
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())

def publish(channel, event: events.Event):
    r.publish(channel, json.dumps(asdict(event)))

@dataclass
class Allocated(Event):
    orderid: str; sku: str; qty: int; batchref: str

EVENT_HANDLERS = {events.Allocated: [handlers.publish_allocated_event], ...}
def publish_allocated_event(event: events.Allocated, uow):
    redis_eventpublisher.publish('line_allocated', event)
```
- **What it demonstrates**: Redis is "another thin adapter around our message bus".

## Reference Tables
| Pros | Cons |
|---|---|
| Avoids distributed big ball of mud | Overall information flows harder to see |
| Decoupled services; easy to change/add | Eventual consistency is a new concept |
| | Message reliability: at-least-once vs at-most-once to think through |

## Worked Example
E2E test `test_change_batch_quantity_leading_to_reallocation`: add two batches (10 each) via API; allocate an order of 10 → earlier batch; subscribe to Redis channel `line_allocated`; publish to `change_batch_quantity` `{'batchref': earlier_batch, 'qty': 5}`; poll with `Retrying(stop=stop_after_delay(3), reraise=True)` (the message may be delayed and isn't the only one on the channel); assert last message has `orderid` and `batchref == later_batch`. Test story reads from comments: send event in → see reallocation event out.

## Key Takeaways
1. Replace temporal coupling with async messaging; services are consistency boundaries.
2. Verbs over nouns when splitting systems.
3. Redis/Kafka/RabbitMQ consumers are just entrypoints that make commands; publishers are just handlers.
4. Prepare for reliability issues: ordering, idempotency, failure handling.

## Connects To
- **Ch 10**: commands vs events. **Ch 12**: read models. **App. E**: validation of messages. **Epilogue**: footguns, microservice advice.
