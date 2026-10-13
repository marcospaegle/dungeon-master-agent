from collections.abc import Sequence
from pathlib import Path

from deepagents import create_deep_agent
from langgraph.checkpoint.base import BaseCheckpointSaver

from dungeon_core.agents.agent import AgentUnavailableError
from dungeon_core.agents.allowlist import ToolAllowlistMiddleware
from dungeon_core.agents.concierge.concierge import Concierge
from dungeon_core.agents.concierge.prompt import system_prompt
from dungeon_core.agents.model_factory import ModelFactory
from dungeon_core.agents.session import AgentSession
from dungeon_core.chat.specialist import Specialist
from dungeon_core.config.settings import MissingSettingError
from dungeon_core.knowledge.factory import KnowledgeFactory
from dungeon_core.tools.handoff_tool import HandoffTool
from dungeon_core.tools.rules_search import RulesSearchTool


class ConciergeFactory:
    """Assembles the Concierge for the Specialists it can hand over to.

    Besides handing over, it answers general D&D questions from the
    indexed Sources, so it gets the rules search.

    The checkpointer is the Frontend's choice, as for the other
    Agents. Nothing is read until the first message.
    """

    def __init__(
        self,
        models: ModelFactory,
        specialists: Sequence[Specialist],
        knowledge: KnowledgeFactory,
        index: Path,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._models = models
        self._specialists = specialists
        self._knowledge = knowledge
        self._index = index
        self._checkpointer = checkpointer

    def create(self) -> Concierge:
        handoff = HandoffTool(
            specialist.name for specialist in self._specialists
        )
        return Concierge(lambda: self._session(handoff), handoff)

    def _session(self, handoff: HandoffTool) -> AgentSession:
        try:
            retriever = self._knowledge.retriever(self._index)
        except MissingSettingError as error:
            raise AgentUnavailableError(str(error)) from error
        tools = [*handoff.tools(), *RulesSearchTool(retriever).tools()]
        graph = create_deep_agent(
            model=self._models.create(),
            tools=tools,
            system_prompt=system_prompt(self._specialists),
            middleware=[ToolAllowlistMiddleware(tool.name for tool in tools)],
            checkpointer=self._checkpointer,
        )
        return AgentSession(graph)
