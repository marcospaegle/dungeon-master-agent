# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python 3.14 managed with uv (no pip/venv).

- Setup: `uv sync`
- Run: `uv run dungeon` (e.g. `uv run dungeon chat`; `--help` lists commands)
- Lint: `uv run ruff check`
- Format: `uv run ruff format`
- Build: `uv build`
- Tests: `uv run pytest` (tests live in `tests/`, mirroring `src/dungeon/`)
- Env: copy `.env.example` to `.env` and set `GOOGLE_API_KEY` (needed for
  embeddings; `.env` is gitignored).

## CLI structure

- Source is `src/dungeon/`; the Typer root app is in `src/dungeon/cli/__init__.py`.
- Each command lives in its own module with a one-command `typer.Typer()`, composed by the parent with `add_typer`. A sub-app added without `name=` merges its command into the parent (`dungeon version`); with `name=` it becomes a group (`dungeon chat`, whose callback runs the Chat).

## Architecture

- `src/dungeon/core/` uses ports and adapters: `ports/` holds the
  interfaces, `adapters/` the concrete steps, and `IndexingService`
  depends only on ports. Keep ports free of LangChain types other than
  `Document`.
- Never use `langchain-community`; use `pypdf` and the standalone
  `langchain-*` packages (see `docs/adr/0001-no-langchain-community.md`).

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

- `architecture-patterns-with-python`: ports and adapters, service layer, repository, unit of work, aggregates, domain events, dependency injection. Use when adding or changing `core/` ports, adapters or services.
- `fluent-python`: data model and special methods, type hints and protocols, ABCs, decorators, iterators/generators, asyncio. Use when writing idiomatic Python or typing a port.
- `high-performance-python`: profiling, data structure choice, generators, concurrency and the GIL. Use only when investigating a measured performance problem, such as slow indexing or embedding throughput.
