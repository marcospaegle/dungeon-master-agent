from collections.abc import Mapping

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-5-5"


class MissingSettingError(Exception):
    """A setting a feature needs is not set; the message says which."""


class Settings:
    """The program's configuration, read from an environment mapping.

    A setting is read when a feature asks for it, so a missing one
    only matters to the feature that needs it.
    """

    def __init__(self, environ: Mapping[str, str]) -> None:
        self._environ = environ

    @property
    def provider(self) -> str:
        return self._environ.get("DUNGEON_PROVIDER") or DEFAULT_PROVIDER

    @property
    def model(self) -> str:
        return self._environ.get("DUNGEON_MODEL") or DEFAULT_MODEL

    @property
    def anthropic_api_key(self) -> str:
        return self._require("ANTHROPIC_API_KEY")

    @property
    def embedding_model(self) -> str:
        return self._require("GOOGLE_EMBEDDING_MODEL")

    @property
    def google_api_key(self) -> str:
        return self._require("GOOGLE_API_KEY")

    def _require(self, name: str) -> str:
        value = self._environ.get(name)
        if not value:
            raise MissingSettingError(
                f"{name} is not set (environment or .env)."
            )
        return value
