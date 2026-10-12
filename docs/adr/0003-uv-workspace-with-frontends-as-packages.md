# A uv workspace: core and each Frontend are separate packages

The repo is a uv workspace. `packages/core` (`dungeon_core`) holds
everything the Frontends share, and each Frontend is its own member
under `apps/` (`dungeon_cli` now; `dungeon_api` and `dungeon_bot` when
they are built). Members use distinct import names rather than a
shared `dungeon.*` namespace package, which workspaces handle poorly.
The `dungeon` console script stays in `dungeon_cli`.

We chose this over one package with `core/` and `apps/` subpackages
because a workspace makes "core never imports a Frontend" a fact of
installation, and keeps a bot's or API's dependencies out of the
others. It costs packaging ceremony (one `pyproject.toml` per member)
while only one Frontend exists. Members that are not built yet get no
placeholder.
