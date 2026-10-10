# Patterns

## Domain Model (Entity / Value Object / Domain Service)
**When to use**: non-trivial business rules; domain complex enough to justify decoupling.
**How**: model in ubiquitous language via TDD; frozen dataclasses for values; `__eq__`/`__hash__` on identity for entities; functions for domain services; domain exceptions.
**Trade-offs**: more upfront code than ActiveRecord; pays off as complexity grows. Skip for CRUD (Ch 1–2).

## Repository
**When to use**: isolate the model from storage; enable fakes.
**How**: `AbstractRepository.add/get` (+ `list`); ORM imports model via classical mapping (`start_mappers`); caller commits; one repository per aggregate (Ch 2, 7).
**Trade-offs**: extra layer and hand-maintained mappings; ORM already gives some decoupling.

## Service Layer
**When to use**: orchestration appearing in controllers; multiple entrypoints.
**How**: functions that fetch → check → call domain → persist; primitives in; depend on abstractions (Ch 4–5).
**Trade-offs**: extra layer; Anemic Domain risk.

## Unit of Work
**When to use**: several operations must be atomic; narrow the ORM.
**How**: abstract context manager with `commit/rollback` and repos; rollback by default; fake UoW in tests (Ch 6).
**Trade-offs**: must handle rollback/threading/nesting; ORM sessions already do much.

## Aggregate + Optimistic Locking
**When to use**: invariants spanning several objects under concurrency.
**How**: small aggregate root (Product); repo returns only aggregates; `version_number` incremented in `allocate`; `REPEATABLE READ` or `SELECT FOR UPDATE`; retry on failure (Ch 7).
**Trade-offs**: new concept; one-aggregate-per-transaction; eventual consistency between aggregates.

## Functional Core, Imperative Shell / Edge-to-Edge Testing
**When to use**: logic tangled with I/O.
**How**: core returns action tuples; shell gathers inputs and applies outputs; inject reader/filesystem with spy fakes (Ch 3).
**Trade-offs**: explicit stateful deps ("test-induced design damage").

## Domain Events + Message Bus
**When to use**: "when X then Y" side effects; changes across aggregates.
**How**: aggregate `.events`; repo `.seen`; UoW collects events; bus queue maps type → handlers (Ch 8–9).
**Trade-offs**: hidden flow, synchronous, loops, harder to follow.

## Commands + Command Handlers
**When to use**: user intent / system inputs.
**How**: imperative dataclass commands, one handler each, errors re-raised; events log-and-continue; retry with tenacity (Ch 10).
**Trade-offs**: subtle semantics; needs monitoring.

## Event-Driven Microservice Integration
**When to use**: services collaborating without temporal coupling.
**How**: broker (Redis/Kafka/RabbitMQ); consumer → command; publisher handler for external events (Ch 11).
**Trade-offs**: flow visibility, reliability, eventual consistency.

## CQRS / Read Model
**When to use**: read access pattern differs from writes; rich domain.
**How**: ladder: repo → ORM → raw SQL → event-updated denormalized table/Redis; rebuild via replay (Ch 12).
**Trade-offs**: complexity; staleness.

## Composition Root / Bootstrap
**When to use**: more than one adapter.
**How**: `bootstrap()` with overridable defaults, inject by closures/partials/signature inspection, return `MessageBus` instance (Ch 13).
**Trade-offs**: another module; global bus caveats.

## Validation at the Edge / Tolerant Reader / Ensure
**When to use**: any message intake.
**How**: syntax on message class, semantics via `ensure` preconditions, pragmatics in the model; `SkipMessage` for idempotency (App. E).
**Trade-offs**: helper machinery; loss of typing if dynamic dataclasses.

## Strangler Fig via Event Interception
**When to use**: replacing a legacy domain.
**How**: raise events from old system → build new model consuming them → switch over; walking skeleton first (Epilogue).
**Trade-offs**: months of dual running.
