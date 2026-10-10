# Appendix E: Validation

## Core Idea
"Where should validation live?" depends on *what kind* of validation. Validation = checking preconditions, in three kinds borrowed from linguistics: syntax (shape), semantics (meaning), pragmatics (context/business rules). Validate at the edge so handlers and the domain see only valid input.

## Frameworks Introduced
- **Syntax / Semantics / Pragmatics**:
  - Syntax: message well-formed (Allocate has orderid, sku, qty; qty positive int; sku string). Validate on the message class / at the edge. Rule: a handler receives only well-formed messages.
  - Semantics: message meaningful (`{"orderid":"superman","sku":"zygote","qty":-1}` parses but is nonsense; unknown SKU). Validate in the handler layer / message bus via **preconditions** (`ensure.py`).
  - Pragmatics: meaning in context (allocate 3 million SCARCE-CLOCK when stock insufficient). Belongs in the **domain model** as business rules.
- **Tolerant Reader / Postel's law**: be liberal in what you accept, conservative in what you emit. Read only the fields you need; ignore extras (`ignore_extra_keys=True`); treat SKU/order numbers as opaque strings (no `COMFY-CHAISE-LONGUE` or `CHEAP-CARPET-2` breakage); don't share message definitions across systems. Public internet APIs may warrant stricter input.
- **Ensure pattern** (contract-style preconditions): `ensure.product_exists(event, uow)` raising `ProductNotFound(MessageUnprocessable)`; specific exception types map easily to HTTP (404).
- **SkipMessage** for idempotency: `batch_is_new` raises `SkipMessage("Batch with id … already exists")`; the bus catches it, logs a warning, continues.
- **Validating at the edge**: invalid data inside the system is a time bomb. Bus method `handle_message(name, body)` finds message type by name, `from_json`, handles; on `ValidationError` logs and re-raises; entrypoints just report success/failure (Flask → 400; Redis consumer → "Skipping invalid message"). Count received/processed/skipped/invalid in metrics and alert on spikes.

## Key Concepts
- **`schema` library**: declarative message schemas; a `command(name, **fields)` helper using `make_dataclass` unifies declaration and validation (cost: loses dataclass typing).
- **Message boundary**: entrypoints only get messages in and report out; bus validates and routes; handlers focus on use case logic.

## Mental Models
- Rule of thumb: if a rule can be tested in the domain model, test it there; don't push business logic into precondition helpers.
- Use the same UoW for precondition checks as for the main logic, or risk concurrency bugs.
- Validate as little as possible at integration boundaries you control, to let services evolve independently.

## Anti-patterns
- **Defensive checks inside the domain model** for shape/range.
- **Format-validating opaque identifiers**.
- **Shared schema libraries** coupling services.
- **Hiding business rules in `ensure`**.

## Code Examples
```python
class MessageUnprocessable(Exception):
    def __init__(self, message): self.message = message

class ProductNotFound(MessageUnprocessable):
    def __init__(self, message):
        super().__init__(message)
        self.sku = message.sku

def product_exists(event, uow):
    product = uow.products.get(event.sku)
    if product is None:
        raise ProductNotFound(event)

def allocate(event, uow):
    line = mode.OrderLine(event.orderid, event.sku, event.qty)
    with uow:
        ensure.product_exists(uow, event)
        product = uow.products.get(line.sku)
        product.allocate(line)
        uow.commit()
```
- **What it demonstrates**: service logic stays declarative; preconditions are named and typed.

## Key Takeaways
1. Be explicit about which of syntax/semantics/pragmatics you're validating.
2. Syntax at the edge, semantics in service layer/bus, pragmatics in the domain.
3. Only validate what you need (Tolerant Reader).
4. Invest in declarative validation helpers; boring code should be easy to maintain.

## Connects To
- **Ch 9**: events as input (place for validation). **Ch 11**: outbound event validation. **Ch 10**: SkipMessage-like handling vs retry.
