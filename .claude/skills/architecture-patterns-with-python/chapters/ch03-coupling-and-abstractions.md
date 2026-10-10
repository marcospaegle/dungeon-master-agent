# Chapter 3: A Brief Interlude: On Coupling and Abstractions

## Core Idea
Simple abstractions hide messy I/O so the clever logic can be tested without it. Separate *what* to do from *how* to do it: make the core pure, make the shell imperative and thin.

## Frameworks Introduced
- **Coupling vs cohesion**: locally, coupling between cohesive parts is good (watch gears); globally it's a nuisance, growing superlinearly in a Ball of Mud. Reduce it by inserting a *simpler* abstraction so the dependent side has fewer kinds of dependency.
- **Functional Core, Imperative Shell (FCIS)** (Gary Bernhardt): pure core takes simple data structures and returns simple data structures; top-level function does only "gather inputs → call core → apply outputs".
  - How: (1) identify distinct responsibilities (interrogate state / decide / act); (2) represent state with a familiar data structure (dict of hash→path); (3) have the core *return commands as data* (`('COPY', src, dst)`) instead of performing them.
- **Edge-to-edge testing with fakes + dependency injection**: pass `reader` and `filesystem` into `sync()`; tests inject a `FakeFileSystem(list)` spy. Test hits the exact production function.
- **Choosing abstractions heuristics** (wrap-up questions): Can I use a familiar Python data structure to represent the messy system's state and imagine one function that returns it? Where can I carve a seam? What implicit concepts can I make explicit? What are the dependencies vs the core logic?

## Key Concepts
- **Seam**: place where an abstraction can be stuck between systems.
- **Spy**: test double recording calls (`FakeFileSystem` appends tuples). **Fake**: working in-memory implementation for tests. **Mock**: verifies how something is used (`assert_called_once_with`).
- **Test-induced design damage** (DHH): the criticism of making stateful components explicit for DI.
- **Classic vs London-school TDD**: authors are classicists—state in setup and assertions, highest abstraction level possible.

## Mental Models
- Use "what vs how": output a list of intended actions, let an executor perform them (also enables `--dry-run`, remote/cloud targets).
- TDD is a design practice first, a testing practice second; tests record design choices.
- Designing for testability = designing for extensibility.

## Anti-patterns
- **E2E tests for core logic**: tmpdir setup swamps two simple cases; slow, unreadable, bugs unrevealed (the first `shutil.move` was wrong).
- **`mock.patch` / monkeypatching**: (1) makes code testable but doesn't improve design (no `--dry-run`, no FTP); (2) couples tests to implementation interactions, so brittle; (3) overmocking buries the story. Treat as a code smell. (Ch 8 uses it for email, Ch 13 replaces it with DI.)
- **Mixing I/O with decisions** in one function.

## Code Examples
```python
def sync(source, dest):
    # imperative shell step 1, gather inputs
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)
    # step 2: call functional core
    actions = determine_actions(source_hashes, dest_hashes, source, dest)
    # imperative shell step 3, apply outputs
    for action, *paths in actions:
        if action == 'copy': shutil.copyfile(*paths)
        if action == 'move': shutil.move(*paths)
        if action == 'delete': os.remove(paths[0])

def determine_actions(src_hashes, dst_hashes, src_folder, dst_folder):
    for sha, filename in src_hashes.items():
        if sha not in dst_hashes:
            yield 'copy', Path(src_folder) / filename, Path(dst_folder) / filename
        elif dst_hashes[sha] != filename:
            yield 'move', Path(dst_folder) / dst_hashes[sha], Path(dst_folder) / filename
    for sha, filename in dst_hashes.items():
        if sha not in src_hashes:
            yield 'delete', dst_folder / filename
```
- **What it demonstrates**: tests become `determine_actions({'hash1':'fn1'}, {}, Path('/src'), Path('/dst')) == [('copy', ...)]`.

## Worked Example
Directory sync: rules = copy if only in source; rename dest if same content/different name; delete if only in dest. First hack walks both trees and acts inline → tests need `tempfile.mkdtemp()`, write files, `shutil.rmtree` in `finally`. Refactor: dicts `{'hash1':'path1'}` represent the filesystem; core yields action tuples; shell applies them. Alternative DI form: `synchronise_dirs(reader.pop, filesystem, "/source", "/dest")` with `reader = {"/source": source, "/dest": dest}` and assert `filesystem == [("MOVE","/dest/original-file","/dest/renamed-file")]`. Why it works: edge cases become cheap to enumerate. Trade-off: DI makes stateful components explicit.

## Key Takeaways
1. Isolate the clever logic behind simple data in / data out.
2. Prefer fakes (state assertions) to mocks (interaction assertions).
3. Keep E2E tests few; push coverage to fast tests.
4. Both functional and OO composition: domain = functional core; service layer + DI for stateful bits.

## Connects To
- **Ch 4**: service layer as the shell. **Ch 8/13**: mock.patch → explicit DI. **Ch 5**: test pyramid.
