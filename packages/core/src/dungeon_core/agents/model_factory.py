from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from dungeon_core.agents.agent import AgentUnavailableError
from dungeon_core.config.settings import MissingSettingError, Settings


class ModelFactory:
    """Builds the chat model the settings choose.

    A new provider is a new method here and an entry in the table.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._providers = {"anthropic": self._anthropic}

    def create(self) -> BaseChatModel:
        provider = self._settings.provider
        if provider not in self._providers:
            raise AgentUnavailableError(
                f"Unknown provider {provider!r}; "
                f"known: {', '.join(self._providers)}."
            )
        try:
            return self._providers[provider]()
        except MissingSettingError as error:
            raise AgentUnavailableError(str(error)) from error

    def _anthropic(self) -> BaseChatModel:
        return ChatAnthropic(
            model=self._settings.model,
            api_key=self._settings.anthropic_api_key,
        )
