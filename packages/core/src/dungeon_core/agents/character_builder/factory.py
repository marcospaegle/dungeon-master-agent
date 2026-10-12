from collections.abc import Callable, Mapping
from pathlib import Path

from langchain_anthropic import ChatAnthropic

from dungeon_core.agents.character_builder.agent import (
    Agent,
    AgentUnavailableError,
)
from dungeon_core.agents.character_builder.langchain_agent import (
    LangchainAgent,
)
from dungeon_core.characters.character import Character
from dungeon_core.config.settings import MissingSettingError, Settings
from dungeon_core.knowledge.factory import KnowledgeFactory
from dungeon_core.knowledge.ports.retriever import IndexNotBuiltError

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-5-5"


def _require(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name)
    if not value:
        raise AgentUnavailableError(
            f"{name} is not set (environment or .env)."
        )
    return value


def _anthropic(environ: Mapping[str, str], model: str):
    return ChatAnthropic(
        model=model, api_key=_require(environ, "ANTHROPIC_API_KEY")
    )


# A new provider is a new entry here, one adapter and a config change.
PROVIDERS = {"anthropic": _anthropic}


def create_chat_model(environ: Mapping[str, str], provider: str, model: str):
    """The chat model for a provider, from the provider table."""
    if provider not in PROVIDERS:
        raise AgentUnavailableError(
            f"Unknown provider {provider!r}; known: {', '.join(PROVIDERS)}."
        )
    return PROVIDERS[provider](environ, model)


def create_agent_factory(
    index: Path, environ: Mapping[str, str]
) -> Callable[[Character | None], Agent]:
    """Assemble the Character creation agent with its real adapters.

    The provider and model come from DUNGEON_PROVIDER and
    DUNGEON_MODEL, the keys from the environment. All of it is read
    when a Character creation starts, so a missing key only matters
    to the user of /char.
    """

    def create(draft: Character | None) -> Agent:
        model = create_chat_model(
            environ,
            environ.get("DUNGEON_PROVIDER") or DEFAULT_PROVIDER,
            environ.get("DUNGEON_MODEL") or DEFAULT_MODEL,
        )
        try:
            retriever = KnowledgeFactory(Settings(environ)).retriever(index)
            retriever.check()
        except (MissingSettingError, IndexNotBuiltError) as error:
            raise AgentUnavailableError(str(error)) from error
        return LangchainAgent(model, retriever, draft)

    return create
