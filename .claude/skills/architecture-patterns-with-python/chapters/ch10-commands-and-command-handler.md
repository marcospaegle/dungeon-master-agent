# Chapter 10: Commands and Command Handler

## Core Idea
Inputs to the system are *commands* (intent, imperative, one handler, fail noisily); things that happened are *events* (facts, past tense, many handlers, fail independently). Same bus, different rules. Splitting them tells you what must succeed and what can be tidied up later.

## Frameworks Introduced
- **Command vs Event** (Table 10-1):

| | Event | Command |
|---|---|---|
| Named | Past tense (`OrderAllocated`) | Imperative mood (`Allocate`, `CreateBatch`) |
| Error handling | Fail independently | Fail noisily |
| Sent to | All listeners | One recipient |

  Commands capture intent; sender needs error info. Events broadcast facts; senders shouldn't care if receivers succeed. Events spread knowledge about successful commands.
- **Command Handler pattern** (a.k.a. what Events + Commands + Message Bus add up to): separate `EVENT_HANDLERS: Dict[Type[Event], List[Callable]]` and `COMMAND_HANDLERS: Dict[Type[Command], Callable]`; `handle(message)` dispatches by `isinstance`.
  - `commands.Allocate` replaces `AllocationRequired`; `CreateBatch` replaces `BatchCreated`; `ChangeBatchQuantity` replaces `BatchQuantityChanged`.
- **Error-handling rule**: `handle_command` logs and **re-raises** (fail fast; one handler). `handle_event` logs and **continues** to the next handler; never interrupts message processing.
- **Rule for consistency**: a command should modify a *single aggregate* and succeed or fail in totality; any other bookkeeping, cleanup, notification happens via events, which need not succeed for the command to succeed.
- **Retry with exponential back-off** (tenacity): `Retrying(stop=stop_after_attempt(3), wait=wait_exponential())` in `handle_event`; "single best way to improve resilience". UoW + command handler mean each attempt starts from a consistent state.

## Key Concepts
- **Log-driven recovery**: log line before each message; dataclass reprs can be pasted to recreate/replay messages.
- **Transient failures**: network hiccups, deadlocks, deploy downtime → retry; bugs → fix then replay.
- **Aligned transactional boundaries**: handler names/steps match business jargon and acceptance criteria.

## Mental Models
- Use "what does the customer actually care about?" to choose the command handler's scope: only that part must complete. VIP example: taking the order (`create_order_from_basket`) must succeed; `update_customer_history` and `congratulate_vip_customer` are events that may fail independently (a bug in History or an overloaded email server must not stop you taking money).
- Raising events *before* commit so everything completes together is "safer" only apparently; it couples unrelated concerns.
- Aggregates as consistency boundaries mean failure of an event handler can't leave half-allocated stock → only eventual-consistency gaps.

## Anti-patterns
- **Naming a request with a past-tense event** (`BatchCreated` posted by the API when nothing has been created yet) — conceptual wart.
- **Swallowing command errors**.
- **Giving commands multiple handlers**.
- **No monitoring** while inviting independent failure.

## Code Examples
```python
Message = Union[commands.Command, events.Event]

def handle(message: Message, uow):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise Exception(f'{message} was not an Event or Command')
    return results

def handle_event(event, queue, uow):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            logger.debug('handling event %s with handler %s', event, handler)
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception('Exception handling event %s', event)
            continue

def handle_command(command, queue, uow):
    logger.debug('handling command %s', command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception('Exception handling command %s', command)
        raise
```
- **What it demonstrates**: same queue, different failure semantics.

## Reference Tables
| Pros | Cons |
|---|---|
| Clear which things must succeed vs can be tidied later | Subtle semantic differences → bikeshedding |
| `CreateBatch` clearer than `BatchCreated`; explicit user intent | Expressly invites failure; harder to reason about; needs better monitoring |

## Worked Example
VIP flow (other project): `CreateOrder` command → `create_order_from_basket` commits and (via UoW) raises `OrderCreated` → `update_customer_history` loads `History` aggregate, `record_order()`; on the third distinct order appends `CustomerBecameVIP` → `congratulate_vip_customer` emails. Matches acceptance criteria "Given two orders… When third order… Then flagged VIP… first becomes VIP… send email". Failure analysis: only step 1 must complete; a retry on the others is safe because each handler has its own UoW.

## Key Takeaways
1. Commands: imperative, single recipient, fail loudly. Events: past tense, broadcast, fail independently.
2. One command → one aggregate → all-or-nothing; everything else is an event.
3. Log every message; retry transient failures with back-off; replay after fixing bugs.
4. Align transactional boundaries with business process steps.

## Connects To
- **Ch 7**: aggregates as consistency boundaries. **Ch 9**: events as inputs. **Ch 11**: external messages become commands. **Epilogue/Footguns**: reliability.
