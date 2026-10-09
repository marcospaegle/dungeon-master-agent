# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python 3.14 managed with uv (no pip/venv).

- Setup: `uv sync`
- Run: `uv run dungeon` (e.g. `uv run dungeon chat new`; `--help` lists commands)
- Lint: `uv run ruff check`
- Format: `uv run ruff format`
- Build: `uv build`
- Tests: none configured yet.

## CLI structure

- Source is `src/dungeon/`; the Typer root app is in `src/dungeon/cli/__init__.py`.
- Each command lives in its own module with a one-command `typer.Typer()`, composed by the parent with `add_typer`. A sub-app added without `name=` merges its command into the parent (`dungeon version`); with `name=` it becomes a group (`dungeon chat new`).

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
