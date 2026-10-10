---
name: architecture-patterns-with-python
description: "Knowledge base from \"Architecture Patterns with Python\" by Harry Percival and Bob Gregory. Use when applying its frameworks for domain modeling, repository, unit of work, service layer, aggregates, domain events, message bus, CQRS, dependency injection, ports and adapters, studying the book, or referencing its concepts."
---

<!-- argument-hint: [topic, framework name, or chapter number] -->

# Architecture Patterns with Python
**Author**: Harry J.W. Percival & Bob Gregory | **Pages**: ~300 | **Chapters**: 13 + intro, epilogue, appendices | **Generated**: 2026-10-10

## How to Use This Skill

- **Without arguments** — load core frameworks for reference
- **With a topic** — ask about `unit of work`, `aggregate`, `CQRS`; I find and read the relevant chapter
- **With chapter** — ask for `ch07`; I load that specific chapter
- **Browse** — ask "what chapters do you have?" to see the full index

When you ask about a topic not covered in Core Frameworks below, I will read the relevant chapter file before answering.

---

## Core Frameworks & Mental Models

**Dependency Inversion Principle (DIP) is the spine.** High-level (business) modules must not depend on low-level (infrastructure) modules; both depend on abstractions; details depend on abstractions. Every pattern is DIP applied somewhere. Ports and adapters = hexagonal = onion = clean architecture: same idea. Port = interface (ABC or duck type); adapter = implementation.

**Behavior first, storage later.** Build the **Domain Model** in the business's ubiquitous language via TDD. **Entity** = identity equality (`__eq__`/`__hash__` on reference). **Value Object** = immutable, defined by data (`@dataclass(frozen=True)`). **Domain Service** = a plain function when no object owns the verb. Not everything has to be an object.

**Repository**: the illusion of an in-memory collection (`add`, `get`). Invert the ORM so it imports the model (classical mapping, `start_mappers()`). Build a `FakeRepository` — if it's hard to fake, the abstraction is too complex. One repository per aggregate.

**Service Layer**: use-case functions that fetch → check → call domain → persist. Takes primitives (later commands). Thin entrypoints (Flask, CLI, Redis consumer) only translate. Test mostly here (**high gear**); keep a small core of domain tests (**low gear**) for design feedback. Test pyramid: ~1 E2E per feature.

**Unit of Work**: abstraction over atomic operations; context manager; gives `uow.products`; **explicit commit, rollback by default**. *Don't mock what you don't own* — fake your own UoW, not the SQLAlchemy session. Prefer fakes (state) over mocks (interactions); `mock.patch` is a smell — inject instead.

**Aggregate = consistency boundary.** Smallest cluster that must be consistent; root is sole entrypoint (`Product(sku, batches, version_number)`); repos return only aggregates; one aggregate per transaction. Concurrency: optimistic (version number + REPEATABLE READ, retry) vs pessimistic (`SELECT FOR UPDATE`).

**Functional Core, Imperative Shell**: separate *what* (return action data) from *how* (do I/O). Choose abstractions by asking: can a familiar data structure represent the messy state? where's the seam? which concepts are implicit?

**Events and Commands (Part II).** Domain Event = fact, past tense, broadcast, fail independently, recorded by aggregate in `.events`, collected by UoW from `repo.seen`. Command = intent, imperative, one handler, fail noisily. Message bus = dict type → handlers with a queue. Command modifies *one* aggregate; everything else (notifications, cross-aggregate updates) is events → eventual consistency. Log every message, retry with exponential back-off.

**Microservices**: think in verbs, not nouns; integrate with async events (Redis/Kafka/RabbitMQ) to remove temporal coupling (connascence of name > execution/timing). Consumers make commands; publishers are handlers.

**CQRS**: domain models are for writing. Reads: repo → ORM → raw SQL → event-updated read model (SQL/Redis). Stale reads are unavoidable anyway. CQS: a write returns no data (202 + GET).

**Bootstrap / DI**: one composition root declares overridable defaults, runs init, injects deps (closures, partials, signature inspection), returns the `MessageBus`. Build adapters properly: ABC → real → fake → docker-fake (MailHog) → integration test.

**Validation**: syntax at the edge, semantics via preconditions/ensure, pragmatics in the domain; Tolerant Reader; skip duplicate messages (idempotency).

**Always ask of any pattern**: "What do we get for this, and what does it cost?" CRUD apps need none of it.

---

## Chapter Index

| # | Title | Key Frameworks |
|---|-------|----------------|
| [ch00](chapters/ch00-introduction.md) | Introduction | encapsulation, layering, DIP |
| [ch01](chapters/ch01-domain-modeling.md) | Domain Modeling | Entity, Value Object, Domain Service |
| [ch02](chapters/ch02-repository-pattern.md) | Repository Pattern | Repository, ports & adapters, classical mapping |
| [ch03](chapters/ch03-coupling-and-abstractions.md) | Coupling and Abstractions | FCIS, fakes vs mocks, edge-to-edge tests |
| [ch04](chapters/ch04-service-layer.md) | Service Layer | Service Layer, app vs domain service |
| [ch05](chapters/ch05-tdd-high-and-low-gear.md) | TDD in High Gear and Low Gear | test pyramid, gears |
| [ch06](chapters/ch06-unit-of-work.md) | Unit of Work | UoW, don't mock what you don't own |
| [ch07](chapters/ch07-aggregates.md) | Aggregates and Consistency Boundaries | Aggregate, optimistic concurrency |
| [ch08](chapters/ch08-events-and-message-bus.md) | Events and the Message Bus | Domain Events, Message Bus, SRP |
| [ch09](chapters/ch09-going-to-town-on-the-message-bus.md) | Going to Town on the Message Bus | handlers, preparatory refactoring |
| [ch10](chapters/ch10-commands-and-command-handler.md) | Commands and Command Handler | commands vs events, retries |
| [ch11](chapters/ch11-event-driven-microservices-integration.md) | Event-Driven Integration | Redis pub/sub, connascence |
| [ch12](chapters/ch12-cqrs.md) | CQRS | read models, CQS |
| [ch13](chapters/ch13-dependency-injection-and-bootstrapping.md) | Dependency Injection & Bootstrapping | composition root |
| [ch14](chapters/ch14-epilogue.md) | Epilogue | legacy adoption, Strangler Fig, footguns |
| [ch15](chapters/ch15-appendices-a-to-d.md) | Appendices A–D | component table, project structure, CSV, Django |
| [ch16](chapters/ch16-appendix-e-validation.md) | Appendix E: Validation | syntax/semantics/pragmatics, Tolerant Reader |

## Topic Index

- **Adapter / Port** → ch02, ch04, ch13
- **Aggregate** → ch07, ch14
- **Anemic Domain** → ch04
- **Bootstrap / DI** → ch13
- **Bounded context** → ch07
- **Command** → ch10, ch09
- **Concurrency / locking / version number** → ch07
- **Connascence** → ch11
- **CQRS / read model** → ch12
- **Django** → ch15, ch14
- **Docker / config / project structure** → ch15
- **Domain event** → ch08, ch09
- **Domain service** → ch01, ch04
- **Entity / Value Object** → ch01
- **Fakes vs mocks** → ch03, ch06
- **Functional core** → ch03
- **Idempotency** → ch14, ch16
- **Legacy / Strangler Fig** → ch14
- **Message bus** → ch08, ch09, ch10
- **Microservices / Redis** → ch11
- **Optimistic locking** → ch07
- **Repository** → ch02
- **Retry** → ch10
- **Service layer** → ch04, ch05
- **Testing strategy** → ch05, ch03
- **Unit of Work** → ch06
- **Validation** → ch16

## Supporting Files

- [glossary.md](glossary.md) — all key terms with definitions
- [patterns.md](patterns.md) — all techniques and design patterns
- [cheatsheet.md](cheatsheet.md) — quick reference tables and decision guides

---

## Scope & Limits

This skill covers the book content only (example domain: MADE.com furniture allocation; Flask/SQLAlchemy/Redis). Code is illustrative, not production-hardened. For implementation in your codebase, combine with project-specific tools. For topics beyond this book (DDD depth, reliable messaging, event sourcing), consult the books it recommends. Images and diagrams in the source were not read.
