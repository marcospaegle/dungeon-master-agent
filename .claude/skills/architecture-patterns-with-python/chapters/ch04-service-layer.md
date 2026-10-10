# Chapter 4: Our First Use Case: Flask API and Service Layer

## Core Idea
Pull orchestration (fetch, validate against current state, call domain, commit) out of the web handler into a Service Layer — the single entrypoint to the domain — so use cases can be tested in memory with a fake repository.

## Frameworks Introduced
- **Service Layer pattern** (a.k.a. orchestration / use-case layer): typical service function steps: (1) fetch objects from repo, (2) check request against current state, (3) call domain service, (4) save/update changed state.
  - When to use: when orchestration logic starts creeping into controllers (and you have more than one entrypoint, e.g. API + CLI). Not before.
- **Application service vs domain service**: application service (service layer) handles outside requests and orchestrates (get data, update model, persist). Domain service is stateless business logic with no natural entity home (e.g. `calculate_tax`).
- **Depend on abstractions (DIP in action)**: `allocate(line, repo: AbstractRepository, session)` works with `FakeRepository` in tests and `SqlAlchemyRepository` in prod.
- **Project layout**: `domain/` (model, exceptions, later commands/events), `service_layer/` (services, unit_of_work), `adapters/` (orm, repository, redis_client — secondary/driven adapters), `entrypoints/` (flask_app — primary/driving adapters), `tests/{unit,integration,e2e}`. Ports live next to their adapters.

## Key Concepts
- **E2E test**: real HTTP + real DB; keep to happy and unhappy path.
- **Thin controller**: Flask does only per-request session, parse JSON, status codes, response JSON.
- **Anemic Domain**: anti-pattern from putting too much logic in the service layer.
- **Ice-cream cone**: inverted test pyramid from too many E2E tests.

## Mental Models
- Think of the service layer as the API of your domain; tests and CLIs are adapters to it too.
- Use "fat models, thin controllers" instead when the app is simple (Django-style) — adding a layer isn't always worth it.
- Reads: do "the simplest thing that can possibly work" (`repo.get()` in the handler); see Ch 12.

## Anti-patterns
- **Orchestration in the Flask handler** (validation against DB, error mapping, commit) — each new case adds E2E tests.
- **Forgetting `commit`** — E2E test `test_allocations_are_persisted` catches it.
- **Anemic domain model** via an overstuffed service layer.

## Code Examples
```python
class InvalidSku(Exception): pass

def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}

def allocate(line: OrderLine, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f'Invalid sku {line.sku}')
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref

@app.route("/allocate", methods=['POST'])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    line = model.OrderLine(request.json['orderid'], request.json['sku'], request.json['qty'])
    try:
        batchref = services.allocate(line, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400
    return jsonify({'batchref': batchref}), 201
```
- **What it demonstrates**: handler = web stuff only; use case = service.

## Reference Tables
| Pros | Cons |
|---|---|
| Single place for all use cases | Yet another abstraction layer |
| Domain behind an API → free to refactor | Too much logic here → Anemic Domain; add only after orchestration creeps into controllers |
| HTTP vs allocation concerns separated | Pure web app: view functions may already be the use-case place |
| Fake repo → high-level workflow tests without integration tests | "Fat models, thin controllers" gets many benefits without the layer |

## Worked Example
Evolution: (1) E2E `test_api_returns_allocation` against Flask+Postgres using `add_stock` SQL fixture and random sku/batchref helpers. (2) Naive Flask app lists batches, allocates, forgets commit → add `test_allocations_are_persisted`. (3) Add `test_400_message_for_out_of_stock` and `test_400_message_for_invalid_sku`; handler gets crufty. (4) Extract `services.allocate`; move three tests to service level using `FakeRepository([batch])` and `FakeSession` (`committed` flag): `test_returns_allocation`, `test_error_for_invalid_sku` (`pytest.raises(services.InvalidSku, match=...)`), `test_commits`. (5) Reduce E2E to happy path (201 + earliest batch) and unhappy path (400 + message). Failure mode avoided: combinatorial E2E explosion. Remaining awkwardness: service takes `OrderLine` (fixed Ch 5) and a `session` (fixed Ch 6).

## Key Takeaways
1. Test web stuff E2E; test orchestration against the service layer in memory.
2. Make dependencies explicit and typed to abstractions.
3. Only add the layer when orchestration appears in controllers.
4. Entrypoints and adapters are both "adapters" in ports-and-adapters terms.

## Connects To
- **Ch 5**: test strategy and primitives in the service API. **Ch 6**: Unit of Work replaces `session`. **Ch 12**: reads. **App. C**: CLI entrypoint reusing services.
