# Cheatsheet: Decisions

## Decision rules
| When… | Do… | Because |
|---|---|---|
| App is plain CRUD | Use Django/ActiveRecord; no domain model/repo | Cost exceeds benefit (Ch 2, 7) |
| Domain rules growing | Domain model first, schema later | Behavior drives storage (Ch 1) |
| ORM classes would be domain classes | Invert: ORM maps your plain classes | Persistence ignorance (Ch 2) |
| Orchestration creeping into controllers | Add service layer | Thin entrypoints (Ch 4) |
| Changing behavior, not model design | Test at service layer (high gear) | Low coupling (Ch 5) |
| Gnarly new domain problem | Test at domain level (low gear) | Design feedback (Ch 5) |
| Tempted to mock a 3rd-party lib | Wrap it in your own abstraction; fake that | Don't mock what you don't own (Ch 6) |
| Tempted to `mock.patch` | Inject the dependency | Design + less brittle tests (Ch 3, 13) |
| Several ops must be atomic | UoW; explicit commit | Safe by default (Ch 6) |
| Need to update 2 aggregates in one request | Merge boundary, or two handlers + event | Aggregate = consistency boundary (Ch 7, Epilogue) |
| Function described with "and/then" | Split; emit event | SRP (Ch 8) |
| Domain expert says "when X then Y" | Domain event | Causal wording = event (Ch 8) |
| User asks system to do something | Command; fail loudly | Intent (Ch 10) |
| Side effect after success | Event; log and continue; retry | Fail independently (Ch 10) |
| Splitting into services | Split by verbs/processes, not nouns | Avoid distributed mud (Ch 11) |
| Reads hurt or differ from write model | Views module → SQL → read store via events | CQRS ladder (Ch 12) |
| >1 adapter | Bootstrap + DI | Single wiring place (Ch 13) |
| Validation question | Syntax edge / semantics handler / pragmatics domain | App. E |

## Decision tree: how to get events to the bus
- Starting out → service layer calls `bus.handle(product.events)`.
- Rule of when to raise belongs in model → model appends events, service passes them.
- Tired of boilerplate → UoW collects from `repo.seen`; bus owns the queue (final form).

## Decision tree: testing level
- New feature → 1 E2E + many service tests.
- Rewrite risk in domain → small core of domain tests; delete when covered.
- Event chain complexity high → isolate handlers with fake bus (last resort).

## Trade-off matrix
| Pattern | Gain | Cost | Skip when |
|---|---|---|---|
| Repository | Fakes, swap storage | Mapping code | CRUD |
| Service layer | One API for use cases | Layer | Pure web app, simple views |
| UoW | Atomicity, repos in one place | Rollback/thread care | Session passing suffices |
| Aggregate | Concurrency scale | Mental shift | Small data/no concurrency |
| Events | Decoupling | Hidden flow | One-off scripts |
| CQRS read model | Read scale | Dual models | Reads = writes |
| DI/bootstrap | Test setup in one place | Extra module | Single adapter |

## Thresholds & defaults
- Test pyramid: ~1 E2E per feature; unit tests outnumber others by ~10×.
- ~20 active batches per product is fine to load whole; thousands → lazy-load.
- Retry events up to 3 times with exponential back-off.
- Commands: 1 handler. Events: 0..n handlers.
- Repository interface: `add`, `get` (+ aggregate-returning queries only).

## Tells & smells
- Complex query methods on repos (`get_most_popular_products`) → needs read model.
- Bidirectional object links → wrong aggregates.
- `user.account.workspaces[0].documents…` → lazy-load performance trap.
- Hard-to-write fake → abstraction too complex.
- Tests need tmpdirs/DBs for pure logic → extract functional core.
- Message names in past tense that are really requests (`BatchCreated` from API) → make it a command.
