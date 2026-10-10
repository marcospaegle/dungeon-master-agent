# Chapter 20: Concurrent Executors

## Core Idea
`concurrent.futures` executors encapsulate Simionato's pattern of "spawning a bunch of independent threads and collecting the results in a queue", for threads (`ThreadPoolExecutor`) and processes (`ProcessPoolExecutor`) with the same `Executor` API. Futures are the underlying low-level objects, mostly invisible except with `submit` and `as_completed`.

## Frameworks Introduced
- **Sequential -> concurrent refactor**: turn the body of the sequential `for` loop into a function (`download_one`), then hand it to an executor.
  - When to use: adding concurrency on top of legacy sequential code.
  - How: keep shared helpers (`get_flag`, `save_flag`); `with ThreadPoolExecutor() as executor: res = executor.map(download_one, sorted(cc_list))`.
  - Why it works / failure mode: `map` returns a generator; the first exception re-raises when you iterate to that result; leaving the `with` calls `shutdown(wait=True)`.
- **map vs submit + as_completed**: `executor.map(f, args)` = same callable over many args, results in *submission order* (blocks on the earliest not-done). `submit` + `as_completed` = results in *completion order*, can mix different callables/args and futures from multiple executors.
  - When to use: need progress display, per-task error handling, or out-of-order handling -> `submit` + `as_completed`.
  - How: `future = executor.submit(fn, *args)`; collect futures; `for future in as_completed(to_do): future.result()`.
  - Why it works / failure mode: `result()` never blocks after `as_completed` yields it; `result()` re-raises the callable's exception.
- **Future-to-context dict idiom**: `to_do_map = {executor.submit(...): cc}`; use `to_do_map[future]` to retrieve the input when an out-of-order future fails.
- **Error-handling strategy (flags2)**: handle the expected case (HTTP 404) inside `download_one`; let every other exception propagate to `download_many`, which tallies in a `Counter[DownloadStatus]`.
- **Choose pool type**: ThreadPoolExecutor for I/O-bound; ProcessPoolExecutor for CPU-bound "embarrassingly parallel" jobs; no benefit from processes for I/O.

## Key Concepts
- **future**: object representing the deferred execution of an operation; created only by the framework (`Executor.submit`), never by app code; state is framework-controlled.
- **concurrent.futures.Future vs asyncio.Future**: both have `.done()` (non-blocking), `.add_done_callback(fn)` (runs in the worker thread/process), `.result()`. `cf.Future.result(timeout)` blocks and may raise `TimeoutError`; `asyncio.Future.result()` has no timeout and you should `await` it.
- **Executor**: base interface with `submit`, `map`, `shutdown`; context-manager support.
- **max_workers (ThreadPool)**: default since 3.8 `min(32, os.cpu_count() + 4)`: at least 5 workers for I/O, avoids huge resource use; idle threads are reused.
- **max_workers (ProcessPool)**: default `os.cpu_count()`.
- **`as_completed(futures)`**: iterator yielding futures as they finish.
- **tqdm**: wraps an iterable to show progress; needs `total=` when the iterable has no `len`.
- **embarrassingly parallel**: independent subtasks needing no coordination.
- **DoS caution**: concurrent clients on public servers can look like a denial-of-service attack; use local servers (`python3 -m http.server`, `slow_server.py`).

## Mental Models
- Use `executor.map` when you want a parallel version of `map` and are fine with ordered results.
- Use `submit` + `as_completed` when results should be processed as soon as ready, or error context is needed.
- Think of an executor as infrastructure: threads, processes, and queues are managed for you ("treat them as infrastructure at your service").
- Threads and coroutines perform similarly for HTTP clients that control request count; coroutines win at server scale (memory, context switching).

## Anti-patterns
- **Instantiating `Future` yourself or mutating its state**: only the framework schedules and updates it.
- **`ProcessPoolExecutor` for I/O-bound jobs**: more memory/startup cost, no gain.
- **Polling `.done()` in a loop**: use `as_completed` or `add_done_callback`.
- **Assuming `executor.map` shows progress/ordering by completion**: it yields in input order; one slow early job holds back all output (proc_pool.py appeared stuck after the first result).
- **Hitting public servers with many concurrent requests during tests**.
- **No timeout / not checking HTTP status**: use `timeout=` and `raise_for_status()`; HTTPX does not follow redirects by default (set `follow_redirects=True` deliberately).
- **Relying on private attrs** like `executor._max_workers` (author does it with `# type: ignore`; flagged as undocumented).

## Code Examples
```python
from concurrent import futures

def download_many(cc_list: list[str]) -> int:
    with futures.ThreadPoolExecutor() as executor:
        res = executor.map(download_one, sorted(cc_list))
    return len(list(res))
```
- **What it demonstrates**: simplest concurrent version; exceptions surface when iterating `res`.

```python
def download_many(cc_list: list[str]) -> int:
    cc_list = cc_list[:5]
    with futures.ThreadPoolExecutor(max_workers=3) as executor:
        to_do: list[futures.Future] = []
        for cc in sorted(cc_list):
            future = executor.submit(download_one, cc)
            to_do.append(future)
            print(f'Scheduled for {cc}: {future}')
        for count, future in enumerate(futures.as_completed(to_do), 1):
            res: str = future.result()
            print(f'{future} result: {res!r}')
    return count
```
- **What it demonstrates**: future states (`running`, `pending`, `finished returned str`); results out of order.

```python
with ThreadPoolExecutor(max_workers=concur_req) as executor:
    to_do_map = {}
    for cc in sorted(cc_list):
        future = executor.submit(download_one, cc, base_url, verbose)
        to_do_map[future] = cc
    done_iter = as_completed(to_do_map)
    if not verbose:
        done_iter = tqdm.tqdm(done_iter, total=len(cc_list))
    for future in done_iter:
        try:
            status = future.result()
        except httpx.HTTPStatusError as exc:
            error_msg = 'HTTP error {resp.status_code} - {resp.reason_phrase}'
            error_msg = error_msg.format(resp=exc.response)
        ...
```
- **What it demonstrates**: future->context dict, progress bar, per-future error handling.

```python
with executor:
    for n, prime, elapsed in executor.map(check, numbers):
        ...
```
- **What it demonstrates**: `ProcessPoolExecutor` replaces queues/worker/poison pills (31 vs 43 lines, 28% shorter).

## Reference Tables
| | `executor.map` | `submit` + `as_completed` |
|---|---|---|
| Result order | input order | completion order |
| Callables | one callable, many args | any callable/args |
| Futures visible | no (hidden) | yes |
| Error context | lost unless wrapped | via future->input dict |
| Multiple executors | no | yes |

Timing (20 flags): sequential 7.18 s; ThreadPool 1.40 s; asyncio 1.35 s.
flags2 server labels: LOCAL :8000, REMOTE (fluentpython.com), DELAY :8001 (random 0.5-5 s), ERROR :8002 (25% "418" errors); `-m` max concurrent requests (default 30, cap 1000).

## Worked Example
`demo_executor_map.py`: `ThreadPoolExecutor(max_workers=3).map(loiter, range(5))` where `loiter(n)` sleeps n seconds and returns `n*10`. `map` returns a generator immediately; tasks 0,1,2 start; `loiter(3)` starts when 0 finishes; `loiter(4)` when 1 finishes. The `for i, result in enumerate(results)` loop blocks on each future's `.result()` in order, printing 0, 10, 20, 30, 40 as each completes.

## Key Takeaways
1. Executors turn the thread/queue pattern into one `with` block; `ThreadPoolExecutor` for I/O, `ProcessPoolExecutor` for CPU.
2. Refactor sequential loops by extracting the loop body into a function.
3. `map` is ordered; `submit` + `as_completed` is flexible and needed for progress/error handling.
4. Futures are created by frameworks, queried via `.done()/.result()/.add_done_callback()`; `result()` re-raises task exceptions.
5. Map futures to inputs with a dict to report errors for out-of-order completions.
6. Understand `max_workers` defaults; cap concurrency for safety.
7. Be careful testing against public servers; use local servers.

## Connects To
- **Ch 19**: `procs.py` homegrown pool that `ProcessPoolExecutor` simplifies; GIL and process vs thread.
- **Ch 17**: `executor.map` returns a generator; `as_completed` is a generator over futures.
- **Ch 18**: executors as context managers (`shutdown(wait=True)` on exit).
- **Ch 21**: `asyncio.Future`, `asyncio.as_completed`, `flags_asyncio.py`, `run_in_executor`.
