from pathlib import Path

from deepagents import create_deep_agent
from langgraph.checkpoint.base import BaseCheckpointSaver

from dungeon_core.agents.agent import AgentUnavailableError
from dungeon_core.agents.allowlist import ToolAllowlistMiddleware
from dungeon_core.agents.character_builder.builder import CharacterBuilder
from dungeon_core.agents.character_builder.prompt import SYSTEM_PROMPT
from dungeon_core.agents.model_factory import ModelFactory
from dungeon_core.agents.session import AgentSession
from dungeon_core.characters.draft import CharacterDraft
from dungeon_core.characters.service import CharacterService
from dungeon_core.chat.specialist import Specialist
from dungeon_core.config.settings import MissingSettingError
from dungeon_core.knowledge.factory import KnowledgeFactory
from dungeon_core.knowledge.ports.retriever import IndexNotBuiltError
from dungeon_core.tools.character_tools import CharacterTools
from dungeon_core.tools.return_tool import ReturnTool
from dungeon_core.tools.rules_search import RulesSearchTool


class CharacterBuilderFactory:
    """Assembles a Character Builder with its tools and its model.

    The checkpointer is the Frontend's choice, since where a
    conversation is kept depends on where the Frontend runs. Nothing
    is read until a Character creation starts, so a missing key only
    matters to the user of Character creation.
    """

    def __init__(
        self,
        models: ModelFactory,
        knowledge: KnowledgeFactory,
        index: Path,
        characters: CharacterService,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._models = models
        self._knowledge = knowledge
        self._index = index
        self._characters = characters
        self._checkpointer = checkpointer

    def specialist(self) -> Specialist:
        """The Specialist the Concierge hands Character creation to."""
        return Specialist(
            name="character-builder",
            description=(
                "Create a new Character or edit a saved one, step by step"
            ),
            start=self.create,
        )

    def create(self) -> CharacterBuilder:
        model = self._models.create()
        try:
            retriever = self._knowledge.retriever(self._index)
            retriever.check()
        except (MissingSettingError, IndexNotBuiltError) as error:
            raise AgentUnavailableError(str(error)) from error
        draft = CharacterDraft()
        returning = ReturnTool()
        tools = [
            *RulesSearchTool(retriever).tools(),
            *CharacterTools(draft, self._characters).tools(),
            *returning.tools(),
        ]
        graph = create_deep_agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=[ToolAllowlistMiddleware(tool.name for tool in tools)],
            checkpointer=self._checkpointer,
        )
        return CharacterBuilder(
            AgentSession(graph, done=lambda: draft.saved), draft, returning
        )
