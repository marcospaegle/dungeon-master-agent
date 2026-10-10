# Appendices A–D: Summary Table, Project Structure, CSV Swap, Django

## Core Idea
Reference material: the component table (A), a template project layout and config approach (B), proof that infrastructure is swappable (C), and how the patterns fit Django (D).

## Appendix A — Components of the Architecture
| Layer | Component | What it does |
|---|---|---|
| Domain | Entity | Attributes may change, identity persists |
| | Value object | Immutable, fully defined by attributes, fungible |
| | Aggregate | Unit for data changes; enforces a consistency boundary |
| | Event | Something that happened |
| | Command | A job the system should perform |
| Service layer | Handler | Receives a command/event and does what's needed |
| | Unit of work | Atomic update abstraction; exposes repos; tracks new events |
| | Message bus (internal) | Routes commands/events to handlers |
| Adapters (secondary) | Repository | Abstraction over persistent storage; one per aggregate |
| | Event publisher | Pushes events to the external bus |
| Entrypoints (primary adapters) | Web | Requests → commands → internal bus |
| | Event consumer | External bus events → commands → internal bus |
| N/A | External message bus (broker) | Services intercommunicate via events |

## Appendix B — Template Project Structure
- `src/allocation/` installed via `pip install -e` with a three-line `setup.py` (`name`, `version`, `packages`); tests in `tests/{unit,integration,e2e}` with shared `conftest.py` and `pytest.ini`.
- `Makefile` (build, test…) as the entrypoint for common commands (runnable documentation); Invoke is a pure-Python alternative. `docker-compose.yml` + `Dockerfile` run app and tests; avoid many images.
- **Config via env vars (12-factor)** in `config.py` with *functions* (not import-time constants) and local-dev defaults (e.g. `DB_HOST` default `localhost` → port 54321 else 5432). Don't make it a dumping ground; keep immutable; ideally only bootstrap and tests import it. Prefer failing hard on missing vars if defaults are insecure.
- Containers reach each other by service hostnames; outside Docker use localhost + mapped ports. `PYTHONDONTWRITEBYTECODE=1` avoids root-owned `.pyc` with mounted volumes; mount source/tests as volumes to avoid rebuilds.
- **Dockerfile ordering**: install in order of change frequency (system deps → requirements → source) to maximize cache reuse.

## Appendix C — Swapping Infrastructure: CSVs
- Scenario: business wants a CLI that reads `batches.csv` and `orders.csv` and writes `allocations.csv` instead of the API.
- Naive script (load batches, allocate, write) breaks when existing allocations must persist (second E2E test).
- Solution: reimplement abstractions — `CsvRepository(folder)` loading batches and allocations (`get`, `add`, `list`) and `CsvUnitOfWork(folder)` whose `commit()` rewrites `allocations.csv` from `batch._allocations`, `rollback()` is `pass`. CLI `main(folder)` just loops order rows and calls `services.allocate(orderid, sku, qty, uow)`.
- Lesson: domain + service layer reused untouched; ports/adapters pay off.

## Appendix D — Django
- Put Django in a separate package (`djangoproject`) beside `allocation`; use `pytest-django` (`@pytest.mark.django_db`, `transaction=True` for rollback tests).
- Django has no classical mapper, so Active Record ≠ domain object: write translation methods (`Batch.update_from_domain`, `to_domain`) behind `DjangoRepository`; entity upserts need try-get/except; relationships need custom handling.
- `DjangoUnitOfWork`: `transaction.set_autocommit(False)` on enter, explicit `commit()` that updates every `seen` batch back into the ORM, then `transaction.commit()`; rollback via `transaction.rollback()`.
- Views are thin adapters (`csrf_exempt`, parse JSON, call services, return `JsonResponse`/400/201); service layer unchanged.
- **Why hard?** Django is tied to the DB and optimized for CRUD; the Django admin bypasses domain rules (dangerous for rule-heavy workflows).
- **If you already have Django**: Repository + UoW = lots of work, mainly faster unit tests and future decoupling; Service Layer helps duplicated views; "fat models" with Entity/Value Object/Aggregate can work until inter-app dependencies bite.
- **Steps along the way**: `logic.py` in every app from day one; business layer may start on Django models and decouple later; centralize reads (poor man's CQRS); don't let Django apps hierarchy dictate module boundaries.

## Key Takeaways
1. Table A is the vocabulary: domain / service layer / adapters / entrypoints.
2. Config in env vars, centralized and immutable; Docker for dev/CI parity.
3. If swapping the infrastructure is a rewrite of only repo + UoW, the architecture is working.
4. In Django, evaluate cost/benefit per pattern; start with service layer and a `logic.py`.

## Connects To
- **Ch 2/4/6**: repo, service, UoW. **Ch 13**: bootstrap uses config. **Epilogue**: legacy adoption.
