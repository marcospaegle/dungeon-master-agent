from collections.abc import Callable, Mapping
from pathlib import Path

from langchain_anthropic import ChatAnthropic

from dungeon.core.adapters.langchain_agent import LangchainAgent
from dungeon.core.character import Character
from dungeon.core.ports.agent import Agent, AgentUnavailableError
from dungeon.core.ports.retriever import IndexNotBuiltError
from dungeon.core.retrieval_factory import create_retriever

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
        provider = environ.get("DUNGEON_PROVIDER") or DEFAULT_PROVIDER
        if provider not in PROVIDERS:
            raise AgentUnavailableError(
                f"Unknown DUNGEON_PROVIDER {provider!r}; "
                f"known: {', '.join(PROVIDERS)}."
            )
        model = PROVIDERS[provider](
            environ, environ.get("DUNGEON_MODEL") or DEFAULT_MODEL
        )
        retriever = create_retriever(
            index,
            embedding_model=_require(environ, "GOOGLE_EMBEDDING_MODEL"),
            api_key=_require(environ, "GOOGLE_API_KEY"),
        )
        try:
            retriever.check()
        except IndexNotBuiltError as error:
            raise AgentUnavailableError(str(error)) from error
        return LangchainAgent(model, retriever, draft)

    return create
