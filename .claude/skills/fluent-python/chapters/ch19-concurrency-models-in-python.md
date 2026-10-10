# Chapter 19: Concurrency Models in Python

## Core Idea
Python has three native concurrency models (threads, processes, coroutines) with different trade-offs; the GIL makes threads useless for CPU-bound work but fine for I/O, so CPU-bound work needs processes, and Python scales in practice via ecosystem tools (WSGI servers, task queues, C/GPU libraries). Rob Pike: "Concurrency is about dealing with lots of things at once. Parallelism is about doing lots of things at once."

## Frameworks Introduced
- **Three models, same spinner**: the same "slow job + animated spinner" implemented with `threading`, `multiprocessing`, `asyncio`.
  - When to use: choose model by workload. I/O-bound: threads or coroutines. CPU-bound: processes. Thousands of tasks / server scale: coroutines (less memory, cheaper switching).
  - How: threads use `Thread` + `Event` signalling; processes mirror the Thread API with `Process` (+ `multiprocessing.Event`); coroutines use `asyncio.run`, `create_task`, `await`.
  - Why it works / failure mode: threads are preemptive (OS scheduler may interrupt anywhere -> locks); coroutines are cooperative (only switch at `await`, safe cancellation at await points, but any blocking call freezes everything).
- **The GIL in 10 points** (author's list): each interpreter is a process; one thread runs Python code at a time; GIL switch interval 5 ms (`sys.getswitchinterval()`); stdlib syscalls (disk, network, `time.sleep`) release the GIL; C extensions (NumPy, zlib, bz2) may release it; GIL contention slows CPU-bound threads; use multiple processes for CPU-bound code. "Python threads are great at doing nothing" (Beazley).
- **Experiment: Break the spinner**: replace `await asyncio.sleep(3)` with `time.sleep(3)` or CPU-bound `is_prime(n)`: the spinner never appears. Quiz answers: processes -> spins; threads -> spins (GIL released every 5 ms, only 2 threads); asyncio -> freezes (single flow of execution).
- **Worker + queues + poison pill**: loop `while n := jobs.get(): results.put(check(n))`; one sentinel per worker to shut down; results come back out of order so carry the input (`n`) in the result tuple.
- **Producer/consumer decoupling (task queues)**: producer puts request in a queue, doesn't call consumer; add workers to scale horizontally (Celery, RQ).
- **Constraints manage complexity (Soapbox)**: threads-and-locks has too few constraints; actor model enforces them (private state, message passing with copies, one message at a time); CSP (channels) similar.

## Key Concepts
- **concurrency / parallelism**: structure for many pending tasks vs executing simultaneously (needs multiple cores).
- **execution unit**: process, thread, or coroutine, each with independent state and call stack.
- **preemptive vs cooperative multitasking**: OS preempts processes/threads; coroutines must `await`/`yield`.
- **process**: isolated memory; communicates via bytes, so objects must be pickled.
- **GIL**: lock protecting refcounts/interpreter state; one Python thread at a time; CPython implementation detail, not language spec.
- **event loop**: single-thread scheduler driving coroutines and I/O events.
- **Task**: wraps a coroutine and schedules it (`asyncio.create_task`); roughly `Thread`'s analog but already scheduled when created; `cancel()` raises `CancelledError` at the current `await`.
- **poison pill**: sentinel that tells a worker to quit; `None` or `...` (Ellipsis survives pickling; `object()` does not).
- **race condition**: bug dependent on the order of concurrent actions.
- **contention**: dispute over limited asset (lock, CPU, storage).
- **greenlet / gevent**: cooperative lightweight coroutines without `async`/`await`; gevent monkey-patches sockets.
- **WSGI / ASGI**: sync / async server gateway interfaces; app servers (Gunicorn, uWSGI, mod_wsgi, NGINX Unit) fork multiple processes.

## Mental Models
- Use processes when the job is CPU-bound; Python threads only help while a thread is waiting (I/O, sleep).
- Think of an asyncio program as having one flow of execution: concurrency is control passing between coroutines at `await`.
- Think of threads as "cheap to start, hard to reason about"; coroutines as "synchronized by definition" (no locks needed for code between awaits).
- Use a task queue (Celery/RQ) when a web request needs work that outlives the response (email, PDF).
- Treat `asyncio.sleep(0)` as a stopgap, not a fix, for CPU-bound code in a coroutine.

## Anti-patterns
- **`time.sleep()` or any blocking/CPU-heavy call in a coroutine**: freezes the event loop and all coroutines.
- **Threads for CPU-bound work**: slower than sequential and gets worse with more threads (GIL contention, context-switch costs).
- **Sharing mutable data between threads without locks**; locks are advisory.
- **`object()` as a sentinel across processes**: unpickled copy is not equal.
- **Trying to terminate a thread from outside**: no API; send a message (e.g. `Event.set()`).
- **Web-scale envy**: picking complex architecture "because we might need to scale" (Thoughtworks).
- **Main process exiting before workers are done**: confusing `FileNotFoundError` tracebacks from multiprocessing locks.

## Code Examples
```python
def spin(msg: str, done: Event) -> None:
    for char in itertools.cycle(r'\|/-'):
        status = f'\r{char} {msg}'
        print(status, end='', flush=True)
        if done.wait(.1):
            break
    blanks = ' ' * len(status)
    print(f'\r{blanks}\r', end='')

def supervisor() -> int:
    done = Event()
    spinner = Thread(target=spin, args=('thinking!', done))
    spinner.start()
    result = slow()
    done.set()
    spinner.join()
    return result
```
- **What it demonstrates**: thread signalling via `Event`; `time.sleep` releases the GIL.

```python
async def supervisor() -> int:
    spinner = asyncio.create_task(spin('thinking!'))
    result = await slow()
    spinner.cancel()
    return result

def main() -> None:
    result = asyncio.run(supervisor())
```
- **What it demonstrates**: three ways to run a coroutine: `asyncio.run(coro())` (from sync code), `asyncio.create_task(coro())` (schedule, don't suspend), `await coro()` (transfer control).

```python
def worker(jobs: JobQueue, results: ResultQueue) -> None:
    while n := jobs.get():
        results.put(check(n))
    results.put(PrimeResult(0, False, 0.0))
```
- **What it demonstrates**: poison-pill (0) worker loop; sentinel per worker; "done" marker returned.

## Reference Tables
| | Thread | Process | Coroutine |
|---|---|---|---|
| Scheduling | preemptive (OS) | preemptive (OS) | cooperative (event loop) |
| Memory | shared | isolated (pickle) | shared, one thread |
| Cost | medium | high | lowest |
| CPU-bound benefit | none (GIL) | yes | none; blocks loop |
| Needs locks | yes | for shared memory | not between awaits |
| Cancel | no API; message | terminate/message | `Task.cancel()` |

| Spinner | Thread | asyncio |
|---|---|---|
| Unit | `Thread` calls callable | `Task` drives coroutine |
| Start | `.start()` | scheduled on `create_task` |
| Stop | `Event.set()` | `.cancel()` -> `CancelledError` |

Results on 12-thread (6-core) laptop: sequential 40.31 s; procs.py (12 procs) 9.58 s (4.2x); best median at 6 processes 10.39 s; threads slower than sequential.

## Worked Example
Prime checker: `sequential.py` loops `check(n)` over 20 numbers (40 s). `procs.py` puts numbers in a `jobs` `SimpleQueue`, starts `cpu_count()` `Process` workers, each running the poison-pill loop; main drains `results` until `procs_done == procs`, counting each `n == 0` marker. Results arrive out of order, hence `PrimeResult(n, prime, elapsed)`. Type hints use `multiprocessing.queues.SimpleQueue` (the module-level `SimpleQueue` is a bound method, not a class).

## Key Takeaways
1. Pick the model by workload: I/O-bound -> threads or coroutines; CPU-bound -> processes.
2. The GIL is released on syscalls and by many C libs; it hurts CPU-bound threads, barely I/O-bound ones.
3. Never block inside a coroutine; delegate CPU work to another process or executor.
4. Processes communicate through serialized bytes; queues and poison pills are the standard coordination idiom.
5. App servers (WSGI/ASGI) and task queues give Python web scale; most devs never touch threading directly.
6. Data science escapes the GIL via C/C++/GPU libraries (NumPy, Dask, TensorFlow, PyTorch).
7. Threads-and-locks lack constraints; prefer higher-level models (actors, CSP, executors).

## Connects To
- **Ch 17**: classic coroutines, `yield from` precursor to `await`.
- **Ch 20**: `ProcessPoolExecutor` simplifies `procs.py`.
- **Ch 21**: asyncio in depth, `run_in_executor` for CPU work.
- **Ch 18**: locks and events as context managers.
