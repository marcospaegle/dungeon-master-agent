# Dungeon Master Agent

A Python project for building an AI agent that can act as the Dungeon Master in a Dungeons & Dragons game. It drives the session by narrating scenes, voicing NPCs, and reacting to player choices, while also handling the practical side of play: creating player characters, generating encounters, tracking stats and initiative, and applying the rules. Whether you’re missing a DM, want help prepping a campaign, or just want to play solo, dungeon-master-agent aims to be a tireless, creative partner at the table.


## Layout

A uv workspace:

- `packages/core`: the shared core (agents, tools, characters,
  knowledge, chat).
- `apps/cli`: the terminal chat. An API and a bot will join it under
  `apps/`.

Decisions are in `docs/adr/` and the vocabulary in `GLOSSARY.md`.

## Usage

```
uv sync
cp .env.example .env        # then fill in the keys
uv run dungeon build        # index the PDFs in storage/books
uv run dungeon chat         # then /help, /char
```
