# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python 3.14 managed with uv (no pip/venv).

- Setup: `uv sync`
- Run: `uv run dungeon` (e.g. `uv run dungeon chat`; `--help` lists commands)
- Lint: `uv run ruff check`
- Format: `uv run ruff format`
- Build: `uv build --all-packages`
- Tests: `uv run pytest` (each package keeps its tests in its own
  `tests/`, mirroring its `src/`; test file names must be unique across
  the repo because the folders have no `__init__.py`).
- Env: copy `.env.example` to `.env` and set `GOOGLE_API_KEY`
  (embeddings) and `ANTHROPIC_API_KEY` (the agent); `.env` is gitignored.
- Live check: `DUNGEON_LIVE=1 uv run pytest
  packages/core/tests/test_live_agent.py` calls the real models and
  costs a few cents.

## Layout

A uv workspace (see `docs/adr/0003-uv-workspace-with-frontends-as-packages.md`):

- `packages/core` (`dungeon_core`): everything the Frontends share. It
  never imports a Frontend.
- `apps/cli` (`dungeon_cli`): the terminal Frontend and the `dungeon`
  script. `api` and `bot` Frontends get their own `apps/` member when
  they are built.

Import names are `dungeon_core` and `dungeon_cli`, never `dungeon.*`.

## CLI structure

- The Typer root app is in `apps/cli/src/dungeon_cli/__init__.py`.
- Each command lives in its own module with a one-command `typer.Typer()`, composed by the parent with `add_typer`. A sub-app added without `name=` merges its command into the parent (`dungeon version`); with `name=` it becomes a group (`dungeon chat`, which composes the core objects, including the Concierge and its Specialists, and runs the `Terminal`).
- A Frontend is a thin layer: it reads and writes, and composes core
  objects (including the checkpointer). It holds no rules.

## Architecture

- `packages/core/src/dungeon_core/` is grouped by capability, and each
  capability that talks to the outside uses ports and adapters
  (`ports/` holds the interfaces, `adapters/` the concrete steps):
  - `knowledge/`: indexing and retrieval of the Sources.
  - `characters/`: the Character, its repository and its sheet.
  - `agents/`: one folder per Agent (`concierge/`,
    `character_builder/`), each with its prompt and its factory.
  - `tools/`: Tools shared by all Agents. An Agent gets only the Tools
    it is given (`ToolAllowlistMiddleware`).
  - `chat/`: the `Chat`, which routes text to the Active Agent, and
    the `Specialist` registry entry.
  - `config/`: `Settings`, read lazily so a missing key only affects
    the feature that needs it.
- Keep ports free of LangChain types other than `Document`.
- Deep Agents runs the Agent loop (ADR 0004); never write a tool loop.
  LangChain stays for embeddings, the vector store and text splitting.
  Never use `langchain-community`; use `pypdf` and the standalone
  `langchain-*` packages (ADR 0001).
- The user talks to the Concierge, which hands the conversation to a
  Specialist with its `hand_off` Tool; the Chat does the switch and a
  Specialist gives it back with an Outcome (ADR 0006). Commands are
  only `/help`, `/exit` and `/quit`, and never start an Agent. A new
  Specialist is a registry entry the Frontend composes; the Concierge's
  code does not change.
- Group related functions in a class. Keep a lone function a function.

## Ruleset

- The project targets D&D 5.5e (the 2024 rules) only, not the 2014 5e rules. Code, prompts and validation must follow 5.5e, and the Sources are the 5.5e books.

## Style

- Ruff is the only linter/formatter (`ruff.toml`): rules E, W, N, F, I with `preview = true`.
- Line length is 79, and docstrings and comments wrap at 72 (`max-doc-length`). This is tighter than the Ruff and Black default of 88, so don't write longer lines.

## Commits

Always write commit messages in Conventional Commits format (`type(scope): description`, e.g. `feat:`, `fix:`, `docs:`, `chore:`).

Never add a `Co-Authored-By` trailer (or any other attribution line) to commit messages.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `marcospaegle/dungeon-master-agent` (via the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### Python skills

Project skills in `.claude/skills/`. Invoke the matching one before designing or writing code in its area:

- `architecture-patterns-with-python`: ports and adapters, service layer, repository, unit of work, aggregates, domain events, dependency injection. Use when adding or changing core ports, adapters or services.
- `fluent-python`: data model and special methods, type hints and protocols, ABCs, decorators, iterators/generators, asyncio. Use when writing idiomatic Python or typing a port.
- `high-performance-python`: profiling, data structure choice, generators, concurrency and the GIL. Use only when investigating a measured performance problem, such as slow indexing or embedding throughput.
