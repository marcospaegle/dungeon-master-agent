# Chapter 13: Dependency Injection (and Bootstrapping)

## Core Idea
Once you have several adapters (UoW, email, Redis publisher), passing dependencies around by hand hurts. Declare dependencies explicitly, and inject them once, in a **bootstrap script (composition root)** that also does one-off init and gives you the configured message bus.

## Frameworks Introduced
- **Explicit vs implicit dependencies**: implicit = hardcoded import + `mock.patch` (needs a patch per test that triggers the side effect; tied to `import email` vs `from email import send_mail`). Explicit = declare the dependency as an argument (`send_mail: Callable`) — an instance of DIP (Zen of Python: explicit is better than implicit). Cost: marginally more app code; benefit: easier tests.
- **Composition Root / bootstrap script**: single place that (1) declares default dependencies but allows overrides, (2) does init (`orm.start_mappers()`, logging), (3) injects dependencies into handlers, (4) returns the message bus. Mark Seemann: "Pure DI" / "Vanilla DI".
- **Manual DI options**:
  - Closures/lambdas or `functools.partial` (closures late-bind; partials don't — matters with mutable deps).
  - Classes with `__init__` taking deps and `__call__` handling the message (`AllocateHandler(uow)`).
  - `inject_dependencies(handler, dependencies)` via `inspect.signature` matching param names to a deps dict.
  - Even-more-manual: write the lambdas inline per handler (one line each; fine for dozens of handlers).
  - Real DI framework only if DI is needed at multiple levels / dependency chains (Inject, Punq, DRY-Python `dependencies`).
- **MessageBus as a class**: given already-injected `event_handlers`, `command_handlers`, and `uow`; handlers take only the message. `self.queue` isn't thread-safe.
- **Building an adapter "properly"** (6 steps): (1) define API with an ABC; (2) implement real thing; (3) build a fake for unit/service/handler tests; (4) find a less-fake version for Docker (MailHog for SMTP); (5) test the less-fake real thing; (6) profit.

## Key Concepts
- **Simple dependency**: a function (`send_mail`, `publish`). **Complex dependency**: ABC (UoW, `AbstractNotifications`), e.g. S3 client, KV store, requests session.
- **`start_orm` flag**: skip mappers when using the fake UoW.
- Entrypoints reduce to `bus = bootstrap.bootstrap()` then `bus.handle(cmd)`.

## Mental Models
- Defaults in bootstrap = production config in one place; tests override with fakes/noops (`send_mail=lambda *args: None`).
- If a bootstrapper default has side effects at construction, default it to `None`.
- Don't let `config.py` import spread; bootstrap is the only place (besides tests) that needs it.

## Anti-patterns
- **`mock.patch` for every test** that might send email.
- **Message bus responsible for passing every dependency** (SRP violation).
- **Flask global bus** hindering in-process tests (use app factories).

## Code Examples
```python
def bootstrap(
    start_orm: bool = True,
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
    notifications: AbstractNotifications = EmailNotifications(),
    publish: Callable = redis_eventpublisher.publish,
) -> messagebus.MessageBus:
    if start_orm:
        orm.start_mappers()
    dependencies = {'uow': uow, 'notifications': notifications, 'publish': publish}
    injected_event_handlers = {
        event_type: [inject_dependencies(h, dependencies) for h in handlers_]
        for event_type, handlers_ in handlers.EVENT_HANDLERS.items()
    }
    injected_command_handlers = {
        command_type: inject_dependencies(h, dependencies)
        for command_type, h in handlers.COMMAND_HANDLERS.items()
    }
    return messagebus.MessageBus(uow=uow, event_handlers=injected_event_handlers,
                                 command_handlers=injected_command_handlers)

def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {name: dep for name, dep in dependencies.items() if name in params}
    return lambda message: handler(message, **deps)
```
- **What it demonstrates**: DI by matching handler parameter names to a dependency dict.

## Worked Example
Replace `send_mail` with a notifications adapter. ABC `AbstractNotifications.send(destination, message)`; `EmailNotifications(smtp_host, port)` uses smtplib. Fake: `FakeNotifications` with `self.sent = defaultdict(list)`. Unit test: bootstrap with `start_orm=False, uow=FakeUnitOfWork(), notifications=fake_notifs, publish=lambda *args: None`; handle `CreateBatch("b1","POPULAR-CURTAINS",9,None)` then `Allocate("o1","POPULAR-CURTAINS",10)`; assert `fake_notifs.sent['stock@made.com'] == ["Out of stock for POPULAR-CURTAINS"]`. Integration test: bus with real `EmailNotifications()` against MailHog in docker-compose (ports 11025/18025), fetch `/api/v2/messages`, check From/To/Data. Exercise: swap to SMS/Slack; make the Redis publisher a formal adapter.

## Key Takeaways
1. More than one adapter → use DI; bootstrap is the natural home for all one-time setup.
2. One place to default and override adapters for tests.
3. Functions for simple dependencies, ABCs for complex ones.
4. Pick closures/partials vs classes per team taste.

## Connects To
- **Ch 3**: functional vs OO DI and mock critique. **Ch 6/10/11**: UoW, bus, Redis. **App. B**: config.py.
