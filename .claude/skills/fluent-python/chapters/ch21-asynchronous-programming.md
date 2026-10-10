# Chapter 21: Asynchronous Programming

## Core Idea
Native coroutines (`async def`/`await`), async context managers, async iterators/generators and asyncio let one thread interleave many I/O waits. It is all-or-nothing: any blocking call stalls the event loop, so every I/O function must be a coroutine or be delegated to a thread/process.

## Frameworks Introduced
- **Guido's trick to read async code**: squint and pretend `async` and `await` are not there; coroutines read like plain sequential functions that magically never block.
  - When to use: reading or reasoning about any asyncio code.
  - How: `await x()` suspends the current coroutine and yields control to the event loop (not to the caller coroutine); the loop drives other pending coroutines and resumes this one when `x` completes.
- **Awaitable**: "`for` works with iterables; `await` works with awaitables."
  - Daily awaitables: native coroutine objects; `asyncio.Task` (from `asyncio.create_task`). Low-level: objects with `__await__` returning an iterator (`asyncio.Future`; Task subclasses Future).
  - `create_task(coro())` = schedule for concurrent execution, no waiting; `await coro()` = run now and wait for the result.
- **Structure of an asyncio script**: `main` (or `supervisor`) is a coroutine, driven by `asyncio.run(main())` inside `if __name__ == '__main__':`. A plain function bridges (`download_many` calls `asyncio.run(supervisor(...))`).
- **Delegate blocking work to executors**: file I/O and CPU work block the loop.
  - How: `await asyncio.to_thread(func, *args, **kw)` (3.9+); before 3.9 `loop.run_in_executor(None, func, *args)` (None = default ThreadPoolExecutor; kwargs need `functools.partial`). For CPU-bound work pass a `ProcessPoolExecutor`, created once in the supervisor (high startup cost).
  - Failure mode (Caleb's warning): executor "cancellation" is only a pretense; the thread cannot be cancelled and `asyncio.run` waits forever at shutdown for runaway executor jobs.
- **Throttle with `asyncio.Semaphore`**: internal counter decremented by `await acquire()`, incremented by `release()` (not a coroutine). Use `async with semaphore:` and hold it for the shortest possible time.
- **Structured concurrency** (Curio `TaskGroup`, Trio nurseries): all tasks spawned in an `async with TaskGroup()` block are completed or cancelled on exit, with one entry and one exit point (analogy: block statements vs GOTO). Coming to asyncio via PEP 654.
- **Avoiding CPU-bound traps** (options when a CPU hog is found): process pool; external task queue (choose it at project start); rewrite in Cython/C/Rust releasing the GIL; or do nothing but record the decision (technical debt). Add automated performance-regression tests.

## Key Concepts
- **Native coroutine**: function defined with `async def`; always a coroutine even if it has no `await`; `await` is only legal inside one (except in `python -m asyncio` REPL).
- **Classic / generator-based coroutine**: `yield`-based `.send()` coroutines; `@asyncio.coroutine` deprecated 3.8, removed 3.11; `@types.coroutine` stays for Curio/Trio internals.
- **Asynchronous generator**: `async def` containing `yield`; returns `async_generator` object with `__anext__`; driven by `async for`; only empty `return`; not awaitable.
- **Asynchronous context manager**: implements `__aenter__`/`__aexit__` as coroutines; used with `async with` (PEP 492). `httpx.AsyncClient` and `asyncio.Semaphore` are examples.
- **Asynchronous iterable/iterator**: `__aiter__` is a regular method (not coroutine) returning an async iterator; async iterator has `__anext__` coroutine and `__aiter__` returning self.
- **`asyncio.gather(*aws)`**: waits for all, returns results in submission order. `asyncio.as_completed(aws)`: classic generator yielding awaitables in completion order (needed for progress bars).
- **`asyncio.get_running_loop()`**: 3.7+, raises RuntimeError if no loop; prefer over `get_event_loop` (deprecated 3.10).
- **Async comprehensions** (PEP 530): `[i async for i in aiter() if i % 2]`, `[await f() for f in funcs]`; legal only inside `async def` (or async REPL); the async *generator expression* is the one form legal anywhere.
- **ASGI / FastAPI**: async web framework on Starlette/asyncio; routes can be `async def` or plain `def`; run with `uvicorn module:app`.
- **Streams API**: `asyncio.start_server(cb, host, port)`; callback gets `(StreamReader, StreamWriter)`.

## Mental Models
- Your code sits between the asyncio loop and async libraries: the loop makes the `.send()` calls; your `await` chain ends at a low-level awaitable (a generator) driven by timers/network events.
- Use `asyncio.gather` when you need all results ordered; use `as_completed` when you need results as they arrive; use `create_task` when you do not need the result.
- "I/O-bound systems" do not exist; only I/O-bound functions. Any nontrivial system has CPU-bound parts, and they block the loop.
- A semaphore is held by several coroutines up to a configured maximum; it throttles concurrency like `max_workers` does for a thread pool.
- Await replaces callback "pyramid of doom": sequential requests share the driving coroutine's local scope.

## Anti-patterns
- **Blocking calls inside coroutines** (file I/O, `requests`, heavy parsing): freezes every task; use `to_thread`/executor or an async library.
- **Reusing sync I/O helpers unchanged** (e.g., the threaded `get_flag`): must be rewritten as coroutines; "you rewrite all your code so none of it blocks."
- **Forgetting `await`** on coroutine methods like `StreamWriter.drain()`/`readline()`; conversely `await`ing plain functions like `write`/`writelines`. Check which API methods are coroutines.
- **Holding a semaphore/lock across unrelated awaits**: keep the `async with` block as short as possible.
- **Application code full of callbacks** (`add_done_callback`): old pattern; justified only in low-level/legacy-bridging libraries.
- **Using `run_in_executor` and assuming cancellation works**.
- **Waiting until slowdown hurts** before handling CPU-bound code: fix then needs architectural rework (Twisted story: project cancelled).
- **Using `await` in comprehension as a gather replacement blindly**: `gather` gives `return_exceptions`; Caleb recommends `return_exceptions=True` (default is False).

## Code Examples
```python
import asyncio, socket
from keyword import kwlist

async def probe(domain: str) -> tuple[str, bool]:
    loop = asyncio.get_running_loop()
    try:
        await loop.getaddrinfo(domain, None)
    except socket.gaierror:
        return (domain, False)
    return (domain, True)

async def main() -> None:
    names = (kw for kw in kwlist if len(kw) <= 4)
    domains = (f'{name}.dev'.lower() for name in names)
    coros = [probe(domain) for domain in domains]
    for coro in asyncio.as_completed(coros):
        domain, found = await coro
        print(f"{'+' if found else ' '} {domain}")

if __name__ == '__main__':
    asyncio.run(main())
```
- **What it demonstrates**: coroutine objects built eagerly, consumed in completion order; total time is about the slowest probe, not the sum.

```python
async def download_one(client, cc, base_url, semaphore, verbose):
    try:
        async with semaphore:
            image = await get_flag(client, base_url, cc)
    except httpx.HTTPStatusError as exc:
        ...
    else:
        await asyncio.to_thread(save_flag, image, f'{cc}.gif')
```
- **What it demonstrates**: semaphore as async context manager; blocking disk write pushed to a thread.

```python
async def multi_probe(domains: Iterable[str]) -> AsyncIterator[Result]:
    loop = asyncio.get_running_loop()
    coros = [probe(domain, loop) for domain in domains]
    for coro in asyncio.as_completed(coros):   # classic generator: plain for
        result = await coro
        yield result                            # makes it an async generator
```
```python
@asynccontextmanager
async def web_page(url):                        # must be an async generator
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, download_webpage, url)
    yield data                                  # before yield = __aenter__
    await loop.run_in_executor(None, update_stats, url)  # after = __aexit__
```
```python
async def finder(index, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    writer.write(PROMPT)         # plain function: can't await
    await writer.drain()         # coroutine: must await
    data = await reader.readline()
# server: asyncio.start_server(functools.partial(finder, index), host, port); await server.serve_forever()
```
```python
>>> gen_found = (name async for name, found in multi_probe(names) if found)
>>> {name for name in names if (await probe(name)).found}   # parens: dot binds tighter than await
```

## Reference Tables
| Concept | Coroutine? | Notes |
|---|---|---|
| `StreamWriter.write`, `writelines` | no | buffer only |
| `StreamWriter.drain`, `StreamReader.readline`, `wait_closed` | yes | must await |
| `Semaphore.acquire` | yes | `release` is plain |
| `__aiter__` | no (regular method) | returns async iterator |
| `__anext__`, `__aenter__`, `__aexit__` | yes | |

| Native coroutine vs async generator | Coroutine | Async generator |
|---|---|---|
| Declared | `async def` | `async def` |
| `yield` in body | never | always |
| `return value` | allowed | empty return only |
| Awaitable | yes | no |
| Driven by | `await`, `create_task` | `async for`, async comprehension |

| Latency (cycles) | |
|---|---|
| L1 3; L2 14; RAM 250; disk 41,000,000 (human scale 1.3 yr); network 240,000,000 (7.6 yr) | |

Type hints: `Coroutine[T_co, T_contra, V_co]`, `AsyncIterator[T_co]`, `AsyncGenerator[T_co, T_contra]` (no return type), `Awaitable`, `AsyncContextManager`; prefer `collections.abc` versions (3.9+). All covariant on yielded type; send type contravariant. Native coroutine return annotation = type you get when awaiting it.

## Worked Example
flags2_asyncio: `supervisor` creates a `Semaphore(concur_req)` and `httpx.AsyncClient`, builds one `download_one(...)` coroutine per country code, wraps `asyncio.as_completed(to_do)` in `tqdm` for progress, awaits each finished coroutine, catches `HTTPStatusError`/`RequestError`, and counts statuses in a `Counter`. Because the awaitables from `as_completed` may be replaced internally, you cannot map them back to country codes via a dict (unlike futures in Ch 20), so the code extracts `cc` from the exception's request URL. flags3 adds `get_country` (metadata.json): two sequential `async with semaphore:` blocks, simple local variables, no nested callbacks; `gather` was rejected because a failed flag makes the country request pointless.

## Key Takeaways
1. Everything on the path to I/O must be a coroutine or be offloaded (`to_thread`, executor, task queue).
2. `asyncio.run(main())` is the entry point; `main` is a coroutine; get the loop with `get_running_loop()`.
3. `gather` for ordered all-results; `as_completed` for incremental results; `Semaphore` to throttle.
4. `async with`/`async for`/async generators/comprehensions mirror their sync counterparts; `__aiter__` stays a regular method.
5. async/await is not tied to asyncio (Curio, Trio); structured concurrency (TaskGroup) is the direction.
6. Plan for CPU-bound code from day one; tests for performance regressions.
7. Know which library methods are coroutines before calling them.

## Connects To
- **Ch 17**: generators and classic coroutines; `await` borrows `yield from`.
- **Ch 18**: context managers; `@contextmanager` vs `@asynccontextmanager`.
- **Ch 19/20**: concurrency models, executors, `as_completed`, flags examples; GIL.
- **Ch 15**: variance rules behind async type hints.
