# Epilogue: How Do I Get There from Here?

## Core Idea
You can adopt these patterns incrementally in an existing ball of mud. Start with a concrete problem (hard to change? slow? weird bugs?), build a service layer first, then find aggregates, read models, and events, and be honest about the footguns.

## Frameworks Introduced
- **Architecture tax**: tie big cleanups to feature work (3 weeks of cleanup inside a 6-month project) and make a reasoned argument.
- **Separating entangled responsibilities** — use-case extraction: list system use cases with imperative names (Apply Billing Charges, Raise Purchase Order). Each becomes one function/class that: starts its own transaction if needed, fetches required data, checks preconditions (Ensure pattern, App. E), updates the domain model, persists. Atomic success/fail; avoid use cases calling each other; accept duplication; avoid long DB transactions. Copy-paste into new clean place, redirect callers, delete the mess.
- **Identifying aggregates & bounded contexts** (case study: collaboration platform with a deeply connected object graph; `user.account.workspaces[0].documents.versions[1].owner...`): each use case updates one aggregate; replace direct object references with identifiers (Document holds `parent_folder` id, no Folder access); bidirectional links signal wrong aggregates; replace nested ORM loops with straight SQL/stored procedure for reads; for writes, query IDs then `bus.handle(LockWorkspace(workspace_id))` per workspace.
- **Strangler Fig via event interception**: (1) raise events representing changes in the system to replace, (2) build a second system consuming them to build its own domain model, (3) replace the old system. Start with a "walking skeleton" that only logs its input (`batch_created` JSON) to force infra/deploy questions early.
- **Convincing stakeholders**: start with domain modeling (event storming, CRC cards, event modeling); treat domain problems as TDD katas / lunchtime workshops; use ubiquitous language.
- **View builder / view fetcher split** for read-heavy-logic systems (permissions): test builder with dicts.

## Key Concepts
- **MADE.com availability service**: carved from monoliths linked by XML-RPC; stock answers in 2–3 ms with Redis view model; hundreds of requests/second.
- **Small steps** (David Seddon): pick a specific problem, apply ideas imperfectly, move on if too hard; don't boil the ocean.

## Mental Models
- Use "service layer first" even with a messy Django ORM — it reveals operation boundaries; then push logic into the model and validation/error handling to entrypoints.
- Updating two aggregates atomically in one use case → boundary is wrong: merge into one aggregate, or split into two handlers linked by a domain event.
- Microservices are not required; these techniques predate them. CQRS not required either — view builders on repositories are fine.

## Anti-patterns
- **Model objects that make DB calls / copy files**; manager methods calling manager methods (treasure hunts).
- **Bizarre model rules** born of years of hacks (user "joins a company" when no company concept exists) — domain/engineering language drift.
- **Rewriting everything at once**.

## Reference Tables (Footguns)
| Footgun | Mitigation |
|---|---|
| Reliable messaging is hard (Redis pub/sub unreliable) | Event Store/RabbitMQ/EventBridge/Kafka; read Tyler Treat on exactly-once |
| Small independent transactions fail separately | Monitoring, replay tooling, transaction-log broker, Outbox pattern |
| Idempotency not discussed | Make handlers idempotent so retries are safe |
| Event schemas change | Document with JSON Schema + markdown; versioning (Greg Young) |

## Key Takeaways
1. Name the problem first; communicate reasons to the team.
2. Extract use cases → find aggregates → read models → events.
3. One aggregate per use case; reference by identifier.
4. Deploy a walking skeleton before the domain is rich.
5. Further reading: Legacy Code (Feathers), Clean Architectures in Python, Enterprise Integration Patterns, Monolith to Microservices.

## Connects To
- **Ch 4/7/10/12**: patterns being introduced into legacy. **App. D**: Django.
